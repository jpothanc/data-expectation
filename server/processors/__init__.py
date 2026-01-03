"""Data processing modules for orchestrating workflows."""

from .base_processor import BaseProcessor
from .stock_processor import StockProcessor
from .future_processor import FutureProcessor
from .option_processor import OptionProcessor
from .processor_factory import ProcessorFactory

# Backward compatibility alias
InstrumentProcessor = StockProcessor

__all__ = [
    "BaseProcessor",
    "StockProcessor",
    "FutureProcessor",
    "OptionProcessor",
    "ProcessorFactory",
    "InstrumentProcessor",  # Backward compatibility
]

