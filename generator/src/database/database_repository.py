"""Database repository for validation results.

All three insert operations (validation run, expectation results, rules applied)
share a single connection and commit in one transaction, eliminating the
overhead of opening and closing the pool three times per save.
"""

import json
import ast
import re
import logging
import urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationRepository:
    """Persist validation results to the database."""

    def __init__(self, database_service):
        self.db_service = database_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_complete_validation(self, validation_result, api_result,
                                 execution_duration_ms=None):
        """Insert a full validation run (header + expectations + rules) in one transaction.

        Opens a single connection from the pool, performs all three inserts,
        commits once, and returns the RunId.

        Returns:
            int — the RunId assigned to this run.
        """
        conn = self.db_service.get_connection()
        pyodbc_conn = conn.connection
        cursor = pyodbc_conn.cursor()

        try:
            run_id = self._insert_run(
                cursor, validation_result, api_result, execution_duration_ms
            )
            self._insert_expectations(cursor, run_id, api_result)
            self._insert_rules(cursor, run_id, api_result, validation_result)

            pyodbc_conn.commit()
            logger.info(
                "Saved validation RunId=%s for %s/%s",
                run_id, validation_result.product_type, validation_result.exchange
            )
            return run_id

        except Exception:
            pyodbc_conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    # ------------------------------------------------------------------
    # Private insert methods  (all receive an open cursor — no connection
    # management here, that lives entirely in save_complete_validation)
    # ------------------------------------------------------------------

    def _insert_run(self, cursor, validation_result, api_result, execution_duration_ms):
        """Insert into GeValidationRuns; return the new RunId via OUTPUT clause."""
        results = api_result.get("results", {})
        summary = results.get("summary", {})

        total = api_result.get("total_expectations", summary.get("total", 0))
        successful = api_result.get("successful_expectations", summary.get("successful", 0))
        failed = api_result.get("failed_expectations", summary.get("failed", 0))

        rules_applied, custom_names = _classify_rules(api_result, validation_result)

        api_url = (
            api_result.get("api_url")
            or f"/api/v1/rules/validate/{validation_result.product_type}/{validation_result.exchange}"
        )

        sql = """
            INSERT INTO [dbo].[GeValidationRuns] (
                [RunTimestamp], [Region], [ProductType], [Exchange],
                [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
                [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
            )
            OUTPUT INSERTED.[RunId]
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (
            datetime.now(),
            validation_result.region,
            validation_result.product_type,
            validation_result.exchange,
            1 if validation_result.success else 0,
            total, successful, failed,
            rules_applied, custom_names, api_url, execution_duration_ms,
        ))

        row = cursor.fetchone()
        if not row or row[0] is None:
            raise ValueError("Failed to retrieve RunId from INSERT OUTPUT clause")

        return row[0]

    def _insert_expectations(self, cursor, run_id, api_result):
        """Batch-insert expectation results for *run_id*."""
        results = api_result.get("results", {})
        exp_results = results.get("expectation_results", [])

        if not exp_results:
            logger.debug("No expectation results to save for RunId=%s", run_id)
            return

        sql = """
            INSERT INTO [dbo].[GeExpectationResults] (
                [RunId], [ColumnName], [ExpectationType], [Success],
                [ElementCount], [UnexpectedCount], [UnexpectedPercent],
                [MissingCount], [MissingPercent], [ResultDetails]
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        batch = []
        for exp in exp_results:
            result_data = _parse_result_data(exp.get("result", {}))
            batch.append((
                run_id,
                exp.get("column", ""),
                exp.get("expectation_type", ""),
                1 if exp.get("success", False) else 0,
                result_data.get("element_count") or 0,
                result_data.get("unexpected_count") or 0,
                float(result_data.get("unexpected_percent") or 0.0),
                result_data.get("missing_count") or 0,
                float(result_data.get("missing_percent") or 0.0),
                json.dumps(result_data, default=str),
            ))

        cursor.executemany(sql, batch)
        logger.debug("Inserted %d expectation results for RunId=%s", len(batch), run_id)

    def _insert_rules(self, cursor, run_id, api_result, validation_result):
        """Batch-insert the rules applied for *run_id*."""
        rules = _build_rules_list(api_result, validation_result)
        if not rules:
            return

        sql = """
            INSERT INTO [dbo].[GeValidationRulesApplied] (
                [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
            ) VALUES (?, ?, ?, ?, ?)
        """
        batch = [
            (run_id, r["rule_name"], r["rule_type"], r["rule_level"], r["rule_source"])
            for r in rules
        ]
        cursor.executemany(sql, batch)
        logger.debug("Inserted %d rules for RunId=%s", len(batch), run_id)


# ------------------------------------------------------------------
# Module-level helpers (pure functions — easy to test in isolation)
# ------------------------------------------------------------------

def _classify_rules(api_result, validation_result):
    """Return (rules_applied_label, custom_names_str) based on the API URL."""
    api_url = api_result.get("api_url", "")

    if "validate-custom" in api_url:
        custom_names = _extract_param(api_url, "custom_rule_names")
        is_combined = custom_names and (
            "," in custom_names
            or any(kw in custom_names.lower() for kw in ("combined", "is_tradable", "tradable"))
        )
        return ("combined" if is_combined else "custom"), custom_names

    if "validate-by-masterid" in api_url:
        custom_names = _extract_path_segment(api_url, "validate-by-masterid", offset=2)
        return "combined", custom_names

    # Standard validate — mark as "exchange" if results present
    if api_result.get("results"):
        return "exchange", None

    return "base", None


def _build_rules_list(api_result, validation_result):
    """Build the list of rule dicts to be persisted for a run."""
    api_url = api_result.get("api_url", "")
    pt = validation_result.product_type
    ex = validation_result.exchange.lower()
    rules = []

    if "validate-custom" not in api_url:
        rules += [
            {
                "rule_name": "base_validation",
                "rule_type": "base",
                "rule_level": "root",
                "rule_source": "config/rules/base.yaml",
            },
            {
                "rule_name": f"{pt}_validation",
                "rule_type": "product_type",
                "rule_level": "product_type",
                "rule_source": f"config/rules/{pt}/base.yaml",
            },
            {
                "rule_name": f"{ex}_exchange_validation",
                "rule_type": "exchange",
                "rule_level": "exchange",
                "rule_source": f"config/rules/{pt}/exchanges/{ex}/exchange.yaml",
            },
        ]

    custom_str = None
    if "validate-custom" in api_url:
        custom_str = _extract_param(api_url, "custom_rule_names")
    elif "validate-by-masterid" in api_url:
        custom_str = _extract_path_segment(api_url, "validate-by-masterid", offset=2)

    if custom_str:
        for name in (n.strip() for n in custom_str.split(",") if n.strip()):
            is_combined = any(
                kw in name.lower()
                for kw in ("combined", "is_tradable", "tradable", "comprehensive")
            )
            rule_type = "combined" if is_combined else "custom"
            rules.append({
                "rule_name": name,
                "rule_type": rule_type,
                "rule_level": "exchange",
                "rule_source": f"config/rules/{pt}/exchanges/{ex}/{rule_type}.yaml",
            })

    if not rules:
        rules.append({
            "rule_name": f"{pt}_validation",
            "rule_type": "product_type",
            "rule_level": "product_type",
            "rule_source": f"config/rules/{pt}/base.yaml",
        })

    return rules


def _extract_param(url, param_name):
    """Return the first value of *param_name* from the URL query string, or None."""
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        values = params.get(param_name)
        return values[0] if values else None
    except Exception:
        return None


def _extract_path_segment(url, anchor, offset=1):
    """Return the path segment *offset* positions after *anchor*, or None."""
    parts = url.split("/")
    if anchor in parts:
        idx = parts.index(anchor)
        target = idx + offset
        if target < len(parts):
            return parts[target]
    return None


def _parse_result_data(raw):
    """Normalise raw expectation result data to a plain Python dict."""
    if isinstance(raw, dict):
        return _convert_numpy(raw)

    if isinstance(raw, str):
        try:
            cleaned = re.sub(r'np\.int64\((\d+)\)', r'\1', raw)
            cleaned = re.sub(r'np\.float64\(([\d.eE+\-]+)\)', r'\1', cleaned)
            cleaned = re.sub(r'\bnan\b', 'None', cleaned)
            parsed = ast.literal_eval(cleaned)
            if isinstance(parsed, dict):
                return _convert_numpy(parsed)
        except Exception as exc:
            logger.debug("Could not parse result data string: %s", exc)

    return {}


def _convert_numpy(obj):
    """Recursively replace numpy scalars/arrays with native Python types."""
    if isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_numpy(item) for item in obj]
    if hasattr(obj, 'item'):          # numpy scalar
        return obj.item()
    if hasattr(obj, 'tolist'):        # numpy array
        return obj.tolist()
    t = str(type(obj))
    if t.startswith("<class 'numpy."):
        return float(obj) if 'float' in t else int(obj)
    return obj
