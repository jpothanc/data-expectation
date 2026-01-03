"""Database repository for validation results."""

import logging
import json
import ast
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationRepository:
    """Repository for storing validation results in database."""
    
    def __init__(self, database_service):
        """
        Initialize validation repository.
        
        Args:
            database_service: DatabaseService instance
        """
        self.db_service = database_service
    
    def save_validation_run(self, validation_result, api_result, execution_duration_ms=None):
        """
        Save a validation run to the database.
        
        Args:
            validation_result: ValidationResult object
            api_result: API response dictionary
            execution_duration_ms: Optional execution duration in milliseconds
            
        Returns:
            RunId (int) of the inserted record
        """
        print(f"\n  💾 Starting database save for {validation_result.product_type}/{validation_result.exchange}...")
        
        conn = self.db_service.get_connection()
        cursor = conn.cursor()
        
        try:
            # Extract data from API result
            results = api_result.get("results", {})
            summary = results.get("summary", {})
            
            total_expectations = api_result.get("total_expectations", summary.get("total", 0))
            successful_expectations = api_result.get("successful_expectations", summary.get("successful", 0))
            failed_expectations = api_result.get("failed_expectations", summary.get("failed", 0))
            
            print(f"  📊 Extracted data:")
            print(f"     - Total Expectations: {total_expectations}")
            print(f"     - Successful: {successful_expectations}")
            print(f"     - Failed: {failed_expectations}")
            print(f"     - Execution Duration: {execution_duration_ms}ms")
            
            # Determine rules applied type and extract custom rule names
            rules_applied = "base"
            custom_rule_names = None
            
            # Check API URL to determine rule type
            api_url = api_result.get("api_url", "")
            if "validate-custom" in api_url:
                rules_applied = "custom"
                # Try to extract custom rule names from URL query parameters
                if "custom_rule_names=" in api_url:
                    try:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(api_url)
                        params = urllib.parse.parse_qs(parsed.query)
                        if "custom_rule_names" in params:
                            custom_rule_names = params["custom_rule_names"][0]
                            # Check if it's a combined rule (contains comma or is a known combined rule)
                            if "," in custom_rule_names or any(
                                combined in custom_rule_names.lower() 
                                for combined in ["combined", "is_tradable", "tradable"]
                            ):
                                rules_applied = "combined"
                    except:
                        pass
            elif "validate-by-masterid" in api_url:
                rules_applied = "combined"
                # Extract combined rule name from URL
                parts = api_url.split("/")
                if len(parts) >= 2:
                    # URL format: /validate-by-masterid/{master_id}/{combined_rule_name}
                    if "validate-by-masterid" in parts:
                        idx = parts.index("validate-by-masterid")
                        if idx + 2 < len(parts):
                            custom_rule_names = parts[idx + 2]
            
            # If still base, check if we can infer from validation result structure
            if rules_applied == "base":
                # Check if there are expectation results that suggest exchange rules
                results = api_result.get("results", {})
                if results:
                    rules_applied = "exchange"  # If we have results, likely used exchange rules too
            
            # Insert into GeValidationRuns using OUTPUT clause to get RunId
            insert_query = """
                INSERT INTO [dbo].[GeValidationRuns] (
                    [RunTimestamp], [Region], [ProductType], [Exchange],
                    [Success], [TotalExpectations], [SuccessfulExpectations], [FailedExpectations],
                    [RulesApplied], [CustomRuleNames], [ApiUrl], [ExecutionDurationMs]
                )
                OUTPUT INSERTED.[RunId]
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            api_url_value = api_result.get("api_url") or f"/api/v1/rules/validate/{validation_result.product_type}/{validation_result.exchange}"
            
            insert_values = (
                datetime.now(),
                validation_result.region,
                validation_result.product_type,
                validation_result.exchange,
                1 if validation_result.success else 0,
                total_expectations,
                successful_expectations,
                failed_expectations,
                rules_applied,
                custom_rule_names,
                api_url_value,
                execution_duration_ms
            )
            
            print(f"  📝 Inserting into GeValidationRuns:")
            print(f"     - Region: {validation_result.region}")
            print(f"     - ProductType: {validation_result.product_type}")
            print(f"     - Exchange: {validation_result.exchange}")
            print(f"     - Success: {validation_result.success}")
            print(f"     - RulesApplied: {rules_applied}")
            print(f"     - CustomRuleNames: {custom_rule_names}")
            
            # Execute insert and get RunId directly from OUTPUT clause
            cursor.execute(insert_query, insert_values)
            result = cursor.fetchone()
            
            if result is None:
                raise ValueError("Failed to retrieve RunId from INSERT OUTPUT clause")
            
            run_id = result[0]
            
            if run_id is None:
                raise ValueError("RunId is None after insert - INSERT may have failed")
            
            # Commit the transaction
            conn.commit()
            print(f"  ✅ Successfully inserted validation run with RunId: {run_id}")
            print(f"  ✅ Transaction committed successfully")
            logger.info(f"Inserted validation run with RunId: {run_id}")
            
            # Verify the insert by querying back
            verify_cursor = conn.cursor()
            verify_cursor.execute("SELECT [RunId], [Region], [ProductType], [Exchange], [RunTimestamp] FROM [dbo].[GeValidationRuns] WHERE [RunId] = ?", run_id)
            verify_result = verify_cursor.fetchone()
            verify_cursor.close()
            
            if verify_result:
                print(f"  ✅ Verified: Record exists in database (RunId: {verify_result[0]}, Timestamp: {verify_result[4]})")
            else:
                print(f"  ⚠️  WARNING: Could not verify record in database after commit!")
            
            return run_id
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error saving validation run: {e}"
            print(f"  ❌ Database Error: {error_msg}")
            import traceback
            print(f"  📋 Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"     {line}")
            logger.error(error_msg, exc_info=True)
            raise
        finally:
            cursor.close()
    
    def save_expectation_results(self, run_id, api_result):
        """
        Save expectation results for a validation run.
        
        Args:
            run_id: RunId from GeValidationRuns table
            api_result: API response dictionary containing expectation results
        """
        if run_id is None:
            raise ValueError("Cannot save expectation results: RunId is None")
        
        print(f"  💾 Saving expectation results for RunId: {run_id}...")
        
        conn = self.db_service.get_connection()
        cursor = conn.cursor()
        
        try:
            # Extract expectation results from API response
            results = api_result.get("results", {})
            expectation_results = results.get("expectation_results", [])
            
            # Debug: Log the structure of the API response
            print(f"  🔍 Debug: API result keys: {list(api_result.keys())}")
            print(f"  🔍 Debug: Results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
            print(f"  🔍 Debug: Expectation results type: {type(expectation_results)}, length: {len(expectation_results) if isinstance(expectation_results, list) else 'N/A'}")
            
            if not expectation_results:
                print(f"  ⚠️  No expectation results found in API response")
                print(f"  🔍 Debug: Full API result structure:")
                print(f"     - Top level keys: {list(api_result.keys())}")
                if "results" in api_result:
                    print(f"     - Results keys: {list(api_result['results'].keys()) if isinstance(api_result['results'], dict) else type(api_result['results'])}")
                logger.debug(f"No expectation results to save for RunId: {run_id}")
                return
            
            # Count failed expectations
            failed_count = sum(1 for exp in expectation_results if not exp.get("success", True))
            print(f"  📊 Found {len(expectation_results)} expectation results to save ({failed_count} failed, {len(expectation_results) - failed_count} passed)")
            
            insert_query = """
                INSERT INTO [dbo].[GeExpectationResults] (
                    [RunId], [ColumnName], [ExpectationType], [Success],
                    [ElementCount], [UnexpectedCount], [UnexpectedPercent],
                    [MissingCount], [MissingPercent], [ResultDetails]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for exp_result in expectation_results:
                column_name = exp_result.get("column", "")
                expectation_type = exp_result.get("expectation_type", "")
                success = exp_result.get("success", False)
                
                # Log failed expectations specifically
                if not success:
                    print(f"  ⚠️  FAILED EXPECTATION: {column_name}/{expectation_type}")
                
                # Parse result string if it's a string, otherwise use dict
                result_data = exp_result.get("result", {})
                if isinstance(result_data, str):
                    # Try to parse Python dict string (may contain numpy types)
                    try:
                        # Replace numpy type strings with their values
                        # Handle np.int64(123) -> 123, np.float64(45.6) -> 45.6, nan -> None
                        def clean_numpy_types(s):
                            # Replace np.int64(value) with value
                            s = re.sub(r'np\.int64\((\d+)\)', r'\1', s)
                            # Replace np.float64(value) with value (handles decimals)
                            s = re.sub(r'np\.float64\(([\d.eE+-]+)\)', r'\1', s)
                            # Replace nan with None (Python null)
                            s = re.sub(r'\bnan\b', 'None', s)
                            return s
                        
                        cleaned = clean_numpy_types(result_data)
                        # Use ast.literal_eval to safely parse Python dict string
                        result_data = ast.literal_eval(cleaned)
                        print(f"  📋 Parsed result for {column_name}/{expectation_type}: {len(str(result_data))} chars")
                    except Exception as e:
                        logger.warning(f"Failed to parse result data: {e}. Result preview: {result_data[:200]}")
                        print(f"  ⚠️  Warning: Failed to parse result data for {column_name}/{expectation_type}: {str(e)}")
                        result_data = {}
                elif not isinstance(result_data, dict):
                    result_data = {}
                
                # Convert numpy types to native Python types for JSON serialization
                def convert_numpy_types(obj):
                    """Recursively convert numpy types to native Python types."""
                    if isinstance(obj, dict):
                        return {k: convert_numpy_types(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_numpy_types(item) for item in obj]
                    elif hasattr(obj, 'item'):  # numpy scalar
                        return obj.item()
                    elif hasattr(obj, 'tolist'):  # numpy array
                        return obj.tolist()
                    elif str(type(obj)).startswith("<class 'numpy."):
                        # Fallback for other numpy types
                        return float(obj) if 'float' in str(type(obj)) else int(obj)
                    else:
                        return obj
                
                # Convert numpy types
                result_data = convert_numpy_types(result_data)
                
                element_count = result_data.get("element_count") or 0
                unexpected_count = result_data.get("unexpected_count") or 0
                unexpected_percent = result_data.get("unexpected_percent") or 0.0
                missing_count = result_data.get("missing_count") or 0
                missing_percent = result_data.get("missing_percent") or 0.0
                
                # Store FULL detailed result as JSON (includes partial_unexpected_counts and all other fields)
                # This preserves all the detailed information from the API response
                result_details_json = json.dumps(result_data, default=str)
                
                # Log if partial_unexpected_counts exists
                if result_data.get("partial_unexpected_counts"):
                    counts = result_data.get("partial_unexpected_counts", [])
                    print(f"  📊 Storing partial_unexpected_counts: {len(counts)} entries")
                    for item in counts[:3]:  # Show first 3
                        print(f"     - Value: {item.get('value')}, Count: {item.get('count')}")
                
                cursor.execute(
                    insert_query,
                    (
                        run_id,
                        column_name,
                        expectation_type,
                        1 if success else 0,
                        element_count,
                        unexpected_count,
                        float(unexpected_percent) if unexpected_percent else 0.0,
                        missing_count,
                        float(missing_percent) if missing_percent else 0.0,
                        result_details_json
                    )
                )
            
            conn.commit()
            print(f"  ✅ Successfully inserted {len(expectation_results)} expectation results")
            logger.info(f"Inserted {len(expectation_results)} expectation results for RunId: {run_id}")
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error saving expectation results: {e}"
            print(f"  ❌ Database Error: {error_msg}")
            import traceback
            print(f"  📋 Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"     {line}")
            logger.error(error_msg, exc_info=True)
            raise
        finally:
            cursor.close()
    
    def save_rules_applied(self, run_id, api_result, validation_result):
        """
        Save rules applied for a validation run.
        
        Args:
            run_id: RunId from GeValidationRuns table
            api_result: API response dictionary
            validation_result: ValidationResult object
        """
        if run_id is None:
            raise ValueError("Cannot save rules applied: RunId is None")
        
        print(f"  💾 Saving rules applied for RunId: {run_id}...")
        
        conn = self.db_service.get_connection()
        cursor = conn.cursor()
        
        try:
            rules_info = []
            
            # Extract rules based on API URL and result
            api_url = api_result.get("api_url", "")
            
            # Base rules (always applied unless custom-only)
            if "validate-custom" not in api_url:
                rules_info.append({
                    "rule_name": "base_validation",
                    "rule_type": "base",
                    "rule_level": "root",
                    "rule_source": "config/rules/base.yaml"
                })
                
                # Product type rules
                rules_info.append({
                    "rule_name": f"{validation_result.product_type}_validation",
                    "rule_type": "product_type",
                    "rule_level": "product_type",
                    "rule_source": f"config/rules/{validation_result.product_type}/base.yaml"
                })
                
                # Exchange rules
                rules_info.append({
                    "rule_name": f"{validation_result.exchange.lower()}_exchange_validation",
                    "rule_type": "exchange",
                    "rule_level": "exchange",
                    "rule_source": f"config/rules/{validation_result.product_type}/exchanges/{validation_result.exchange.lower()}/exchange.yaml"
                })
            
            # Custom/Combined rules
            custom_rule_names_str = None
            if "validate-custom" in api_url or "validate-by-masterid" in api_url:
                # Extract custom rule names from URL
                if "custom_rule_names=" in api_url:
                    try:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(api_url)
                        params = urllib.parse.parse_qs(parsed.query)
                        if "custom_rule_names" in params:
                            custom_rule_names_str = params["custom_rule_names"][0]
                    except:
                        pass
                elif "validate-by-masterid" in api_url:
                    # Extract from path: /validate-by-masterid/{master_id}/{combined_rule_name}
                    parts = api_url.split("/")
                    if "validate-by-masterid" in parts:
                        idx = parts.index("validate-by-masterid")
                        if idx + 2 < len(parts):
                            custom_rule_names_str = parts[idx + 2]
            
            # Add custom/combined rules
            if custom_rule_names_str:
                rule_names = [name.strip() for name in custom_rule_names_str.split(",")]
                for rule_name in rule_names:
                    # Determine if it's combined or custom based on name patterns
                    rule_type = "combined" if any(
                        keyword in rule_name.lower() 
                        for keyword in ["combined", "is_tradable", "tradable", "comprehensive"]
                    ) else "custom"
                    
                    # Determine rule level (exchange-level takes precedence)
                    rule_level = "exchange"
                    rule_source = f"config/rules/{validation_result.product_type}/exchanges/{validation_result.exchange.lower()}/{rule_type}.yaml"
                    
                    rules_info.append({
                        "rule_name": rule_name,
                        "rule_type": rule_type,
                        "rule_level": rule_level,
                        "rule_source": rule_source
                    })
            
            # If no rules found, add at least a default entry
            if not rules_info:
                rules_info.append({
                    "rule_name": f"{validation_result.product_type}_validation",
                    "rule_type": "product_type",
                    "rule_level": "product_type",
                    "rule_source": f"config/rules/{validation_result.product_type}/base.yaml"
                })
            
            insert_query = """
                INSERT INTO [dbo].[GeValidationRulesApplied] (
                    [RunId], [RuleName], [RuleType], [RuleLevel], [RuleSource]
                ) VALUES (?, ?, ?, ?, ?)
            """
            
            print(f"  📋 Found {len(rules_info)} rules to save:")
            for rule in rules_info:
                print(f"     - {rule['rule_name']} ({rule['rule_type']}, {rule['rule_level']})")
                cursor.execute(
                    insert_query,
                    (
                        run_id,
                        rule["rule_name"],
                        rule["rule_type"],
                        rule["rule_level"],
                        rule["rule_source"]
                    )
                )
            
            conn.commit()
            print(f"  ✅ Successfully inserted {len(rules_info)} rules applied")
            logger.info(f"Inserted {len(rules_info)} rules applied for RunId: {run_id}")
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error saving rules applied: {e}"
            print(f"  ❌ Database Error: {error_msg}")
            import traceback
            print(f"  📋 Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"     {line}")
            logger.error(error_msg, exc_info=True)
            raise
        finally:
            cursor.close()
    
    def save_complete_validation(self, validation_result, api_result, execution_duration_ms=None):
        """
        Save complete validation run including all related data.
        
        Args:
            validation_result: ValidationResult object
            api_result: API response dictionary
            execution_duration_ms: Optional execution duration in milliseconds
            
        Returns:
            RunId (int) of the inserted record
        """
        try:
            print(f"\n  🗄️  ===== DATABASE SAVE START =====")
            print(f"  📍 Saving validation for: {validation_result.region}/{validation_result.product_type}/{validation_result.exchange}")
            
            # Save validation run
            run_id = self.save_validation_run(validation_result, api_result, execution_duration_ms)
            
            # Validate run_id before proceeding
            if run_id is None:
                raise ValueError("Failed to get RunId from save_validation_run - cannot proceed with saving related records")
            
            print(f"  ✅ RunId obtained: {run_id}")
            
            # Save expectation results
            self.save_expectation_results(run_id, api_result)
            
            # Save rules applied
            self.save_rules_applied(run_id, api_result, validation_result)
            
            print(f"  ✅ ===== DATABASE SAVE COMPLETE =====")
            print(f"  📊 Summary: RunId={run_id}, All data saved successfully")
            logger.info(f"Successfully saved complete validation for {validation_result.product_type}/{validation_result.exchange} (RunId: {run_id})")
            
            return run_id
            
        except Exception as e:
            print(f"  ❌ ===== DATABASE SAVE FAILED =====")
            print(f"  Error: {str(e)}")
            logger.error(f"Error saving complete validation: {e}", exc_info=True)
            raise

