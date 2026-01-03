"""Validator orchestrator for batch validation."""

import logging
import time

from ..config.config_loader import ConfigLoader
from ..api.api_client import ValidationAPIClient
from .result_formatter import ResultFormatter
from ..models.validation_result import ValidationResult
from ..models.validation_summary import ValidationSummary

logger = logging.getLogger(__name__)


class BatchValidator:
    """Orchestrates batch validation across regions, product types, and exchanges."""
    
    def __init__(self, config_path=None, api_base_url="http://127.0.0.1:5006", save_to_database=False, database_service=None):
        """
        Initialize batch validator.
        
        Args:
            config_path: Path to regions.yaml config file
            api_base_url: Base URL of the validation API
            save_to_database: If True, save results to database
            database_service: Optional DatabaseService instance. If None and save_to_database=True, will create one.
        """
        self.config_loader = ConfigLoader(config_path)
        self.api_client = ValidationAPIClient(api_base_url)
        self.result_formatter = ResultFormatter()
        self.save_to_database = save_to_database
        
        if save_to_database:
            print(f"\n🗄️  Database saving is ENABLED")
            if database_service:
                self.database_service = database_service
                print(f"  📍 Using provided database service")
            else:
                from ..database.database_service import DatabaseService
                print(f"  📍 Creating database service from config...")
                self.database_service = DatabaseService()
            
            from ..database.database_repository import ValidationRepository
            self.repository = ValidationRepository(self.database_service)
            
            # Test database connection
            print(f"  🧪 Testing database connection...")
            if not self.database_service.test_connection():
                print(f"  ⚠️  WARNING: Database connection test failed. Database saving may not work.")
                logger.warning("Database connection test failed. Database saving may not work.")
            else:
                print(f"  ✅ Database is ready for saving results")
        else:
            print(f"\n🗄️  Database saving is DISABLED (use --save-to-database to enable)")
            self.database_service = None
            self.repository = None
    
    def validate_region(self, region, custom_rule_names=None, verbose=True):
        """
        Validate all product types and exchanges for a given region.
        
        Args:
            region: Region name (e.g., 'apac', 'emea', 'us')
            custom_rule_names: Optional list of custom rule names to apply
            verbose: If True, print results to console
            
        Returns:
            ValidationSummary object
        """
        if verbose:
            self.result_formatter.print_header(region)
            if self.save_to_database:
                print(f"  💾 Database saving: ENABLED")
            else:
                print(f"  💾 Database saving: DISABLED")
        
        if not self._check_api_health(verbose):
            summary = ValidationSummary(region, 0)
            summary.error = "API unavailable"
            return summary
        
        combinations = self.config_loader.get_all_combinations(region=region)
        
        if not combinations:
            if verbose:
                print(f"⚠️  No configurations found for region '{region}'")
            return ValidationSummary(region, 0)
        
        summary = ValidationSummary(region, len(combinations))
        saved_run_ids = []
        failed_saves = 0
        
        for reg, product_type, exchange in combinations:
            result = self._validate_single(
                reg, product_type, exchange, custom_rule_names, verbose
            )
            summary.add_result(result)
            
            # Track if this result was saved to database
            if self.save_to_database and hasattr(result, '_run_id') and result._run_id:
                saved_run_ids.append(result._run_id)
            elif self.save_to_database and result.api_result:
                # If we tried to save but don't have run_id, it likely failed
                failed_saves += 1
        
        if verbose:
            self.result_formatter.print_summary(summary.to_dict())
            if self.save_to_database:
                print(f"\n  💾 ===== DATABASE SAVE SUMMARY =====")
                print(f"     - Total Validations: {len(combinations)}")
                print(f"     - Successfully Saved: {len(saved_run_ids)}")
                if saved_run_ids:
                    print(f"     - RunIds: {', '.join(map(str, saved_run_ids))}")
                if failed_saves > 0:
                    print(f"     - Failed to Save: {failed_saves}")
                print(f"  💾 =================================")
        
        return summary
    
    def _check_api_health(self, verbose):
        """Check API health and print error if unavailable."""
        if not self.api_client.health_check():
            error_msg = f"API is not available at {self.api_client.base_url}"
            logger.error(error_msg)
            if verbose:
                print(f"❌ ERROR: {error_msg}")
                print("Please ensure the validation API is running.")
            return False
        return True
    
    def _validate_single(self, region, product_type, exchange, custom_rule_names, verbose):
        """
        Validate a single product type and exchange combination.
        
        Returns:
            ValidationResult object
        """
        result = ValidationResult(region, product_type, exchange)
        start_time = time.time()
        
        if verbose:
            print(f"\nValidating: {product_type.upper()} / {exchange}")
            print(f"  Region: {region.upper()}")
            if custom_rule_names:
                print(f"  Custom Rules: {', '.join(custom_rule_names)}")
        
        try:
            api_result = self.api_client.validate_exchange(
                product_type=product_type,
                exchange=exchange,
                custom_rule_names=custom_rule_names
            )
            
            # Calculate execution duration
            execution_duration_ms = int((time.time() - start_time) * 1000)
            
            result.success = api_result.get("success", False)
            result.api_result = api_result
            
            # Add execution duration and API URL to api_result for database
            api_result["execution_duration_ms"] = execution_duration_ms
            api_result["api_url"] = f"{self.api_client.base_url}/api/v1/rules/validate/{product_type}/{exchange}"
            
            # If API call succeeded but validation failed, set error message from summary
            if not result.success:
                # Try to get summary from results.summary first
                results = api_result.get("results", {})
                summary = results.get("summary", {})
                
                if summary:
                    failed_count = summary.get("failed", 0)
                    total_count = summary.get("total", 0)
                    successful_count = summary.get("successful", 0)
                    if failed_count > 0:
                        result.error = f"Validation failed: {failed_count} out of {total_count} expectations failed ({successful_count} passed)"
                    else:
                        result.error = "Validation failed (check API response for details)"
                else:
                    # Fallback to top-level fields
                    failed_count = api_result.get("failed_expectations", 0)
                    total_count = api_result.get("total_expectations", 0)
                    successful_count = api_result.get("successful_expectations", 0)
                    if failed_count > 0:
                        result.error = f"Validation failed: {failed_count} out of {total_count} expectations failed ({successful_count} passed)"
                    else:
                        result.error = "Validation failed (check API response for details)"
            
            # Save to database if enabled
            if self.save_to_database and self.repository:
                try:
                    run_id = self.repository.save_complete_validation(
                        result,
                        api_result,
                        execution_duration_ms
                    )
                    result._run_id = run_id  # Store run_id for summary tracking
                    print(f"  ✅ Database save completed successfully (RunId: {run_id})")
                except Exception as db_error:
                    error_type = type(db_error).__name__
                    error_msg = str(db_error)
                    logger.error(f"Failed to save to database: {db_error}", exc_info=True)
                    print(f"  ❌ Database Save Failed:")
                    print(f"     Error Type: {error_type}")
                    print(f"     Error Message: {error_msg}")
                    import traceback
                    print(f"     Full Traceback:")
                    for line in traceback.format_exc().split('\n'):
                        if line.strip():
                            print(f"       {line}")
                    # Don't raise - allow validation to continue even if DB save fails
            
            if verbose:
                self.result_formatter.print_result(result.to_dict())
            
        except Exception as e:
            # Capture detailed error information
            error_type = type(e).__name__
            error_str = str(e)
            
            # Build comprehensive error message
            if error_str and error_str.strip():
                error_msg = error_str
            else:
                error_msg = f"{error_type}: API call failed for {product_type}/{exchange}"
            
            # Always print detailed error to console (not just verbose mode)
            print(f"  Error Type: {error_type}")
            print(f"  Error Message: {error_msg}")
            
            # Print exception details if available
            if hasattr(e, 'response'):
                # HTTP error - show response details
                try:
                    response = e.response
                    print(f"  HTTP Status: {response.status_code}")
                    if response.text:
                        print(f"  Response: {response.text[:500]}")
                except Exception as resp_err:
                    print(f"  Could not read response: {str(resp_err)}")
            
            # Print full traceback for debugging (always show, not just verbose)
            import traceback
            print(f"  Full Error Details:")
            traceback_lines = traceback.format_exc().split('\n')
            for line in traceback_lines:
                if line.strip():
                    print(f"    {line}")
            
            result.error = error_msg
            logger.error(f"Validation failed for {product_type}/{exchange}: {error_msg}", exc_info=True)
            
            if verbose:
                self.result_formatter.print_result(result.to_dict())
            else:
                # Even if not verbose, show the error result
                self.result_formatter.print_result(result.to_dict())
        
        return result
    
    def close(self):
        """Close database connection if opened."""
        if self.database_service:
            self.database_service.close()
