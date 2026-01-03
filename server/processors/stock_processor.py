"""Stock processor for validating stock instrument data."""

from validators.instrument_validator import InstrumentValidator
from .base_processor import BaseProcessor


class StockProcessor(BaseProcessor):
    """Processor for stock instrument data validation."""
    
    def __init__(self, loader, exchange=None):
        """
        Initialize stock processor with a data loader.
        
        Args:
            loader: An instance of DataLoader (e.g., CSVDataLoader, DatabaseDataLoader)
            exchange: Optional exchange code (e.g., 'XHKG', 'XNSE') for exchange-specific validation
        """
        super().__init__(loader, exchange)
        self._validator_instance = InstrumentValidator(exchange=exchange, product_type="stock")
    
    @property
    def product_type(self):
        """Return the product type."""
        return "stock"
    
    @property
    def validator(self):
        """Return the validator instance."""
        return self._validator_instance
    


