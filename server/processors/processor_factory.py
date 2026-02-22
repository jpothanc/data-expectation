"""Factory for creating processors based on instrument type."""

from .stock_processor import StockProcessor
from .future_processor import FutureProcessor
from .option_processor import OptionProcessor
from .multileg_processor import MultilegProcessor
from .base_processor import BaseProcessor


class ProcessorFactory:
    """Factory for creating instrument processors."""

    # Registry of available processor types
    PROCESSOR_TYPES = {
        'stock': StockProcessor,
        'future': FutureProcessor,
        'option': OptionProcessor,
        'multileg': MultilegProcessor,
    }
    
    @classmethod
    def create(cls, product_type, loader, exchange=None):
        """
        Create a processor instance for the specified product type.
        
        Args:
            product_type: Type of product ('stock', 'future', 'option')
            loader: DataLoader instance
            exchange: Optional exchange code
        
        Returns:
            BaseProcessor: Processor instance for the product type
        
        Raises:
            ValueError: If product_type is not supported
        """
        product_type = product_type.lower()
        
        if product_type not in cls.PROCESSOR_TYPES:
            available = ', '.join(cls.PROCESSOR_TYPES.keys())
            raise ValueError(
                f"Unknown product type: '{product_type}'. "
                f"Available types: {available}"
            )
        
        processor_class = cls.PROCESSOR_TYPES[product_type]
        return processor_class(loader=loader, exchange=exchange)
    
    @classmethod
    def get_available_types(cls):
        """
        Get list of available processor types.
        
        Returns:
            list: List of available instrument types
        """
        return list(cls.PROCESSOR_TYPES.keys())
    
    @classmethod
    def register(cls, product_type, processor_class):
        """
        Register a new processor type.
        
        Args:
            product_type: Name of the product type
            processor_class: Processor class that extends BaseProcessor
        """
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError(
                f"Processor class must extend BaseProcessor. "
                f"Got: {processor_class}"
            )
        
        cls.PROCESSOR_TYPES[product_type.lower()] = processor_class




