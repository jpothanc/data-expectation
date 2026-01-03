"""Validation result model."""


class ValidationResult:
    """Represents a single validation result."""
    
    def __init__(self, region, product_type, exchange):
        """Initialize validation result."""
        self.region = region
        self.product_type = product_type
        self.exchange = exchange
        self.success = False
        self.error = None
        self.api_result = None
    
    def to_dict(self):
        """Convert result to dictionary."""
        return {
            "region": self.region,
            "product_type": self.product_type,
            "exchange": self.exchange,
            "success": self.success,
            "error": self.error,
            "api_result": self.api_result
        }

