"""Abstract base class for data loaders."""

import pandas as pd
from abc import ABC, abstractmethod


class DataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load(self, source: str) -> pd.DataFrame:
        """
        Load data from a source and return as DataFrame.
        
        Args:
            source: The source identifier (filename, table name, etc.)
            
        Returns:
            pd.DataFrame: The loaded data
        """
        pass

