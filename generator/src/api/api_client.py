"""API client for calling validation endpoints."""

import requests
import logging

logger = logging.getLogger(__name__)


class ValidationAPIClient:
    """Client for calling validation API endpoints."""
    
    def __init__(self, base_url="http://127.0.0.1:5006"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the validation API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def validate_exchange(self, product_type, exchange, custom_rule_names=None, timeout=30):
        """
        Call validation API for a specific product type and exchange.
        
        Args:
            product_type: Product type (e.g., 'stock', 'future', 'option')
            exchange: Exchange code (e.g., 'XHKG', 'XNSE', 'XTKS')
            custom_rule_names: Optional list of custom rule names
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/api/v1/rules/validate/{product_type}/{exchange}"
        
        params = {}
        if custom_rule_names:
            params['custom_rule_names'] = ','.join(custom_rule_names)
        
        # Build full URL with query string for logging
        full_url = url
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{query_string}"
        
        # Log API call details
        print(f"  📡 API Call: GET {full_url}")
        if params:
            print(f"     Parameters: {params}")
        
        try:
            logger.debug(f"Calling API: {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=timeout)
            
            # Log response details
            print(f"  📥 Response Status: {response.status_code}")
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.debug(f"Response text: {response.text[:500]}")
                print(f"  ⚠️  Response Error: {response.text[:200]}")
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                result = response.json()
                print(f"  ✅ API Call Successful")
                print(f"  📊 Response Summary: success={result.get('success', 'N/A')}, total_expectations={result.get('total_expectations', 'N/A')}, failed={result.get('failed_expectations', 'N/A')}")
                return result
            except ValueError as json_error:
                # If JSON parsing fails, show detailed error
                print(f"  ❌ JSON Parse Error: {str(json_error)}")
                print(f"  📄 Response Content (first 500 chars): {response.text[:500]}")
                print(f"  📄 Response Content Type: {response.headers.get('Content-Type', 'unknown')}")
                
                # Try to identify the issue
                if 'np.' in response.text or 'nan' in response.text:
                    print(f"  ⚠️  Warning: Response contains numpy types or NaN values that may cause parsing issues")
                
                error_msg = f"Invalid JSON response: {str(json_error)}. Response preview: {response.text[:200]}"
                raise Exception(error_msg)
            except Exception as parse_error:
                # Catch any other parsing errors
                print(f"  ❌ Parse Error: {str(parse_error)}")
                print(f"  📄 Response Content (first 500 chars): {response.text[:500]}")
                raise Exception(f"Failed to parse response: {str(parse_error)}")
            
        except requests.exceptions.HTTPError as e:
            response = e.response
            if response is not None:
                try:
                    error_text = response.text[:200] if response.text else ""
                    error_msg = f"HTTP {response.status_code}"
                    if error_text:
                        error_msg += f": {error_text}"
                    else:
                        error_msg += f": {str(e)}"
                except:
                    error_msg = f"HTTP {response.status_code}: {str(e)}"
            else:
                error_msg = f"HTTP Error: {str(e)}"
            logger.error(f"API call failed for {product_type}/{exchange}: {error_msg}")
            raise Exception(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: Unable to connect to {url}"
            logger.error(f"API call failed for {product_type}/{exchange}: {error_msg}")
            raise Exception(error_msg) from e
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout: API did not respond within {timeout} seconds"
            logger.error(f"API call failed for {product_type}/{exchange}: {error_msg}")
            raise Exception(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = str(e) if str(e) else f"Request failed: {type(e).__name__}"
            logger.error(f"API call failed for {product_type}/{exchange}: {error_msg}")
            raise Exception(error_msg) from e
    
    def health_check(self):
        """
        Check if API is available.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            print(f"  🔍 Health Check: GET {url}")
            response = self.session.get(url, timeout=5)
            is_healthy = response.status_code == 200
            if is_healthy:
                print(f"  ✅ API Health Check: OK")
            else:
                print(f"  ❌ API Health Check: Failed (Status: {response.status_code})")
            return is_healthy
        except requests.exceptions.RequestException as e:
            print(f"  ❌ API Health Check: Connection Failed - {str(e)}")
            return False
