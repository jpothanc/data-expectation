"""Service for formatting validation results."""


class ValidationResultFormatter:
    """Formats Great Expectations validation results for API responses."""
    
    @staticmethod
    def to_native_bool(value):
        """Convert numpy bool or other bool types to native Python bool."""
        if value is None:
            return False
        return bool(value)
    
    @staticmethod
    def format_result_item(result_item):
        """Format a single expectation result item."""
        result_dict = {
            "success": ValidationResultFormatter.to_native_bool(
                result_item.success
            ) if hasattr(result_item, 'success') else False,
        }
        
        # Initialize defaults
        expectation_type = 'Unknown'
        column = 'Unknown'
        
        # Add expectation type and column if available
        if hasattr(result_item, 'expectation_config'):
            exp_config = result_item.expectation_config
            
            # Convert to dict if possible (Great Expectations configs often have to_dict method)
            config_dict = {}
            try:
                if isinstance(exp_config, dict):
                    config_dict = exp_config
                elif hasattr(exp_config, 'to_dict'):
                    config_dict = exp_config.to_dict()
                elif hasattr(exp_config, '__dict__'):
                    config_dict = exp_config.__dict__
                else:
                    # Try to access as dict-like object
                    config_dict = dict(exp_config) if hasattr(exp_config, '__iter__') and not isinstance(exp_config, str) else {}
            except Exception:
                # Fallback: try direct attribute access
                pass
            
            # Debug: Print structure to understand what we're working with
            # Uncomment for debugging:
            # print(f"DEBUG exp_config type: {type(exp_config)}")
            # print(f"DEBUG config_dict keys: {list(config_dict.keys()) if config_dict else 'None'}")
            # print(f"DEBUG exp_config dir: {[x for x in dir(exp_config) if not x.startswith('_')]}")
            
            # Get expectation_type - try multiple approaches
            expectation_type = None
            
            # Method 1: Try to get from config_dict (most common)
            # Great Expectations stores it as "type" (lowercase) in the dict representation
            if config_dict:
                expectation_type = (
                    config_dict.get('expectation_type') or 
                    config_dict.get('expectationType') or 
                    config_dict.get('type')  # This is the actual key used by GE
                )
            
            # Method 2: Try direct attribute access
            if not expectation_type:
                if hasattr(exp_config, 'expectation_type'):
                    expectation_type = getattr(exp_config, 'expectation_type', None)
                elif hasattr(exp_config, 'expectationType'):
                    expectation_type = getattr(exp_config, 'expectationType', None)
            
            # Method 3: Try accessing via get method if it's a dict-like object
            if not expectation_type and hasattr(exp_config, 'get'):
                try:
                    expectation_type = (
                        exp_config.get('expectation_type') or 
                        exp_config.get('expectationType') or 
                        exp_config.get('type')  # This is the actual key used by GE
                    )
                except Exception:
                    pass
            
            # Method 4: Try to get from the expectation class name
            if not expectation_type:
                try:
                    # Check if we can get the type from the expectation class
                    if hasattr(exp_config, 'expectation_type_name'):
                        expectation_type = exp_config.expectation_type_name
                    elif hasattr(exp_config, '__class__'):
                        class_name = exp_config.__class__.__name__
                        # Extract expectation type from class name (e.g., "ExpectColumnValuesToNotBeNull")
                        if 'Expect' in class_name:
                            expectation_type = class_name
                except Exception:
                    pass
            
            # Method 5: Try to get from result_item's expectation_type if available
            if not expectation_type and hasattr(result_item, 'expectation_type'):
                expectation_type = getattr(result_item, 'expectation_type', None)
            
            # Method 6: Try accessing through meta if available
            if not expectation_type:
                try:
                    if hasattr(exp_config, 'meta') and isinstance(exp_config.meta, dict):
                        expectation_type = exp_config.meta.get('expectation_type')
                except Exception:
                    pass
            
            # Method 7: Try to get from the expectation object itself if it exists
            if not expectation_type:
                try:
                    # Some GE versions store the expectation object
                    if hasattr(exp_config, 'expectation') and hasattr(exp_config.expectation, '__class__'):
                        class_name = exp_config.expectation.__class__.__name__
                        if 'Expect' in class_name:
                            expectation_type = class_name
                except Exception:
                    pass
            
            # Method 8: Last resort - try to infer from the config_dict structure or class
            if not expectation_type:
                try:
                    # Check if config_dict has any clues
                    if config_dict:
                        # Sometimes it's stored under different keys
                        # Note: GE uses lowercase "type" like "expect_column_values_to_be_unique"
                        for key in ['type', 'expectationType', 'expectation_type', 'expectation_type_name', 'name']:
                            if key in config_dict:
                                potential_type = config_dict[key]
                                if potential_type:
                                    # Convert GE format (expect_column_values_to_be_unique) to class name format
                                    if isinstance(potential_type, str):
                                        # Convert snake_case to PascalCase: expect_column_values_to_be_unique -> ExpectColumnValuesToBeUnique
                                        if not potential_type.startswith('Expect'):
                                            parts = potential_type.split('_')
                                            potential_type = ''.join(word.capitalize() for word in parts)
                                            if not potential_type.startswith('Expect'):
                                                potential_type = 'Expect' + potential_type
                                        expectation_type = potential_type
                                        break
                    
                    # Try to get from the class name of exp_config itself
                    if not expectation_type:
                        class_name = exp_config.__class__.__name__
                        if 'Expect' in class_name:
                            expectation_type = class_name
                except Exception:
                    pass
            
            # Convert snake_case to PascalCase if needed (e.g., "expect_column_values_to_be_unique" -> "ExpectColumnValuesToBeUnique")
            if expectation_type:
                if isinstance(expectation_type, str):
                    # If it's already in PascalCase format, use it as is
                    if expectation_type.startswith('Expect'):
                        pass  # Already in correct format
                    else:
                        # Convert snake_case to PascalCase
                        parts = expectation_type.split('_')
                        expectation_type = ''.join(word.capitalize() for word in parts)
                        if not expectation_type.startswith('Expect'):
                            expectation_type = 'Expect' + expectation_type
            
            expectation_type = str(expectation_type) if expectation_type else 'Unknown'
            
            # Get kwargs and column
            kwargs = {}
            if config_dict:
                kwargs = config_dict.get('kwargs', {})
            elif hasattr(exp_config, 'kwargs'):
                kwargs = getattr(exp_config, 'kwargs', {})
            
            if isinstance(kwargs, dict):
                column = str(kwargs.get('column', 'Unknown'))
            else:
                column = 'Unknown'
        
        # Set the values
        result_dict["expectation_type"] = expectation_type
        result_dict["column"] = column
        
        # Add result details if available
        if hasattr(result_item, 'result'):
            try:
                result_obj = result_item.result
                if hasattr(result_obj, 'observed_value'):
                    observed_val = result_obj.observed_value
                    # Convert numpy types to native Python types for JSON serialization
                    import numpy as np
                    if isinstance(observed_val, (np.integer, np.floating)):
                        observed_val = float(observed_val) if isinstance(observed_val, np.floating) else int(observed_val)
                    elif isinstance(observed_val, np.ndarray):
                        observed_val = observed_val.tolist()
                    result_dict["observed_value"] = observed_val
                if hasattr(result_obj, 'element_count'):
                    element_count = result_obj.element_count
                    # Convert numpy types to native Python types
                    import numpy as np
                    if isinstance(element_count, (np.integer, np.floating)):
                        element_count = int(element_count) if isinstance(element_count, np.integer) else float(element_count)
                    result_dict["element_count"] = element_count
                
                # Convert result to string, handling numpy types
                import numpy as np
                import json
                try:
                    # Try to convert result_obj to a JSON-serializable dict first
                    if hasattr(result_obj, '__dict__'):
                        result_dict_obj = {}
                        for key, value in result_obj.__dict__.items():
                            # Convert numpy types to native Python types
                            if isinstance(value, np.integer):
                                result_dict_obj[key] = int(value)
                            elif isinstance(value, np.floating):
                                if np.isnan(value):
                                    result_dict_obj[key] = None
                                elif np.isinf(value):
                                    result_dict_obj[key] = None
                                else:
                                    result_dict_obj[key] = float(value)
                            elif isinstance(value, np.ndarray):
                                result_dict_obj[key] = value.tolist()
                            elif isinstance(value, list):
                                # Handle lists that might contain numpy types
                                result_dict_obj[key] = [
                                    int(v) if isinstance(v, np.integer) else 
                                    (float(v) if isinstance(v, np.floating) and not (np.isnan(v) or np.isinf(v)) else None) if isinstance(v, np.floating) else
                                    v.tolist() if isinstance(v, np.ndarray) else v
                                    for v in value
                                ]
                            else:
                                result_dict_obj[key] = value
                        result_dict["result"] = json.dumps(result_dict_obj, default=str)
                    else:
                        result_dict["result"] = str(result_obj)
                except Exception:
                    # Fallback to string representation
                    result_str = str(result_obj)
                    # Replace numpy type strings with native types for better readability
                    import re
                    result_str = re.sub(r'np\.int64\((-?\d+)\)', r'\1', result_str)
                    result_str = re.sub(r'np\.float64\((-?[\d.]+(?:[eE][+-]?\d+)?)\)', r'\1', result_str)
                    result_str = result_str.replace('nan', 'null')
                    result_dict["result"] = result_str
            except Exception as e:
                result_dict["result"] = f"N/A (Error: {str(e)})"
        
        return result_dict
    
    @staticmethod
    def format_results(validation_results, exchange, rules_applied=None):
        """Format complete validation results for API response."""
        if not hasattr(validation_results, 'results'):
            return {
                "exchange": exchange,
                "success": False,
                "total_expectations": 0,
                "successful_expectations": 0,
                "failed_expectations": 0,
                "results": {
                    "expectation_results": [],
                    "summary": {
                        "success": False,
                        "total": 0,
                        "successful": 0,
                        "failed": 0
                    }
                }
            }
        
        results_list = validation_results.results
        total_expectations = len(results_list)
        
        successful_expectations = sum(
            1 for r in results_list
            if hasattr(r, 'success') and ValidationResultFormatter.to_native_bool(r.success)
        )
        
        failed_expectations = total_expectations - successful_expectations
        overall_success = ValidationResultFormatter.to_native_bool(
            validation_results.success
        ) if hasattr(validation_results, 'success') else False
        
        formatted_results = [
            ValidationResultFormatter.format_result_item(r)
            for r in results_list
        ]
        
        response = {
            "exchange": exchange,
            "success": overall_success,
            "total_expectations": int(total_expectations),
            "successful_expectations": int(successful_expectations),
            "failed_expectations": int(failed_expectations),
            "results": {
                "expectation_results": formatted_results,
                "summary": {
                    "success": overall_success,
                    "total": int(total_expectations),
                    "successful": int(successful_expectations),
                    "failed": int(failed_expectations)
                }
            }
        }
        
        if rules_applied:
            response["rules_applied"] = rules_applied
        
        return response


