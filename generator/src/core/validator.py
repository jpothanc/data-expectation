"""Batch validator — orchestrates concurrent validation across exchanges."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config.config_loader import ConfigLoader
from ..api.api_client import ValidationAPIClient
from .result_formatter import ResultFormatter
from ..models.validation_result import ValidationResult
from ..models.validation_summary import ValidationSummary

logger = logging.getLogger(__name__)

_DEFAULT_WORKERS = 4   # concurrent exchange validations per region


class BatchValidator:
    """Validates all exchanges in a region, running them concurrently."""

    def __init__(self, config_path=None, api_base_url="http://127.0.0.1:5006",
                 save_to_database=False, database_service=None):
        self.config_loader = ConfigLoader(config_path)
        self.api_client = ValidationAPIClient(api_base_url)
        self.result_formatter = ResultFormatter()
        self.save_to_database = save_to_database
        self.database_service = None
        self.repository = None

        if save_to_database:
            self._init_database(database_service)
        else:
            logger.info("Database saving is DISABLED")
            print("\nDatabase saving: DISABLED (use --save-to-database to enable)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_region(self, region, custom_rule_names=None, verbose=True,
                        max_workers=_DEFAULT_WORKERS):
        """Validate every exchange in *region* concurrently.

        Args:
            region: Region name (e.g. 'apac', 'emea', 'us').
            custom_rule_names: Optional list of custom rule names to apply.
            verbose: Print per-exchange progress to stdout.
            max_workers: Maximum number of concurrent exchange validations.

        Returns:
            ValidationSummary
        """
        if verbose:
            self.result_formatter.print_header(region)
            status = "ENABLED" if self.save_to_database else "DISABLED"
            print(f"  Database saving: {status}")
            print(f"  Workers: {max_workers}")

        if not self._check_api_health(verbose):
            summary = ValidationSummary(region, 0)
            summary.error = "API unavailable"
            return summary

        combinations = self.config_loader.get_all_combinations(region=region)
        if not combinations:
            if verbose:
                print(f"  No configurations found for region '{region}'")
            return ValidationSummary(region, 0)

        summary = ValidationSummary(region, len(combinations))

        with ThreadPoolExecutor(max_workers=max_workers,
                                thread_name_prefix="validator") as pool:
            futures = {
                pool.submit(
                    self._validate_single,
                    reg, product_type, exchange, custom_rule_names, verbose
                ): (reg, product_type, exchange)
                for reg, product_type, exchange in combinations
            }
            for future in as_completed(futures):
                reg, product_type, exchange = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = ValidationResult(reg, product_type, exchange)
                    result.error = str(exc)
                    logger.error("Unhandled error for %s/%s: %s", product_type, exchange, exc)
                summary.add_result(result)

        if verbose:
            self.result_formatter.print_summary(summary.to_dict())
            if self.save_to_database:
                saved = sum(1 for r in summary.results if getattr(r, '_run_id', None))
                print(f"\n  Database save — saved: {saved} / {len(combinations)}")

        return summary

    def close(self):
        """Dispose of database connections if open."""
        if self.database_service:
            self.database_service.close()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_database(self, database_service):
        print("\nDatabase saving: ENABLED")
        if database_service:
            self.database_service = database_service
        else:
            from ..database.database_service import DatabaseService
            self.database_service = DatabaseService()

        from ..database.database_repository import ValidationRepository
        self.repository = ValidationRepository(self.database_service)

        if not self.database_service.test_connection():
            logger.warning("Database connection test failed — saves may not work")
            print("  WARNING: database connection test failed")
        else:
            print("  Database ready")

    def _check_api_health(self, verbose):
        if not self.api_client.health_check():
            msg = f"API not available at {self.api_client.base_url}"
            logger.error(msg)
            if verbose:
                print(f"  ERROR: {msg}")
            return False
        return True

    def _validate_single(self, region, product_type, exchange, custom_rule_names, verbose):
        """Validate one (product_type, exchange) pair and optionally save to DB."""
        result = ValidationResult(region, product_type, exchange)
        start = time.monotonic()

        if verbose:
            print(f"\n  [{region.upper()}] {product_type.upper()} / {exchange}")

        try:
            api_result = self.api_client.validate_exchange(
                product_type=product_type,
                exchange=exchange,
                custom_rule_names=custom_rule_names,
            )

            duration_ms = int((time.monotonic() - start) * 1000)
            api_result["execution_duration_ms"] = duration_ms
            api_result["api_url"] = (
                f"{self.api_client.base_url}/api/v1/rules/validate/{product_type}/{exchange}"
            )

            result.success = api_result.get("success", False)
            result.api_result = api_result

            if not result.success:
                result.error = _build_failure_message(api_result)

            if self.save_to_database and self.repository:
                try:
                    run_id = self.repository.save_complete_validation(
                        result, api_result, duration_ms
                    )
                    result._run_id = run_id
                    logger.info("Saved to DB (RunId=%s) for %s/%s", run_id, product_type, exchange)
                except Exception as db_err:
                    logger.error("DB save failed for %s/%s: %s", product_type, exchange, db_err)

            if verbose:
                self.result_formatter.print_result(result.to_dict())

        except Exception as exc:
            result.error = str(exc)
            logger.error("Validation error for %s/%s: %s", product_type, exchange, exc,
                         exc_info=True)
            if verbose:
                self.result_formatter.print_result(result.to_dict())

        return result


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _build_failure_message(api_result):
    """Extract a human-readable failure description from an API result dict."""
    results = api_result.get("results", {})
    summary = results.get("summary", {})
    failed = summary.get("failed") or api_result.get("failed_expectations", 0)
    total = summary.get("total") or api_result.get("total_expectations", 0)
    passed = summary.get("successful") or api_result.get("successful_expectations", 0)
    if failed:
        return f"Validation failed: {failed}/{total} expectations failed ({passed} passed)"
    return "Validation failed (check API response for details)"
