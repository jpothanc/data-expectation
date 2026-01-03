"""Result formatting utilities for console output."""


class ResultFormatter:
    """Formats validation results for console output."""
    
    def __init__(self, separator="=", width=80):
        """
        Initialize result formatter.
        
        Args:
            separator: Character to use for separators
            width: Width of formatted output
        """
        self.separator = separator
        self.width = width
    
    def print_result(self, result):
        """Print a single validation result."""
        product_type = result.get("product_type", "unknown")
        exchange = result.get("exchange", "unknown")
        
        if result.get("success"):
            api_result = result.get("api_result", {})
            total = api_result.get("total_expectations", 0)
            successful = api_result.get("successful_expectations", 0)
            failed = api_result.get("failed_expectations", 0)
            
            status_icon = "✅" if failed == 0 else "⚠️"
            print(f"  {status_icon} {product_type.upper()}/{exchange}: "
                  f"Total={total}, Passed={successful}, Failed={failed}")
        else:
            error = result.get("error")
            api_result = result.get("api_result", {})
            
            # If no error message but we have API result, try to extract error info from summary
            if not error or error == "None" or (isinstance(error, str) and error.strip() == ""):
                # Check if there's error info in API result summary
                if api_result:
                    results = api_result.get("results", {})
                    summary = results.get("summary", {})
                    
                    if summary:
                        failed_count = summary.get("failed", 0)
                        total_count = summary.get("total", 0)
                        successful_count = summary.get("successful", 0)
                        if failed_count > 0:
                            error = f"Validation failed: {failed_count} out of {total_count} expectations failed ({successful_count} passed)"
                        else:
                            error = "Validation failed (no error details available)"
                    else:
                        # Fallback to top-level fields
                        failed_count = api_result.get("failed_expectations", 0)
                        total_count = api_result.get("total_expectations", 0)
                        successful_count = api_result.get("successful_expectations", 0)
                        if failed_count > 0:
                            error = f"Validation failed: {failed_count} out of {total_count} expectations failed ({successful_count} passed)"
                        else:
                            error = "Validation failed (no error details available)"
                else:
                    error = "Unknown error occurred (check logs for details)"
            
            print(f"  ❌ {product_type.upper()}/{exchange}: {error}")
    
    def print_summary(self, summary):
        """Print validation summary."""
        region = summary.get("region", "unknown")
        total = summary.get("total", 0)
        successful = summary.get("successful", 0)
        failed = summary.get("failed", 0)
        
        separator_line = self.separator * self.width
        print(f"\n{separator_line}")
        print(f"Validation Summary for {region.upper()}")
        print(separator_line)
        print(f"Total Validations: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"{separator_line}\n")
    
    def print_header(self, region):
        """Print validation header."""
        separator_line = self.separator * self.width
        print(f"\n{separator_line}")
        print(f"Validating Region: {region.upper()}")
        print(f"{separator_line}\n")
