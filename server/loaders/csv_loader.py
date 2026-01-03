"""CSV file data loader implementation."""

import pandas as pd
from pathlib import Path
from .base import DataLoader


class CSVDataLoader(DataLoader):
    """Handles loading CSV files from the data folder."""
    
    def __init__(self, data_folder="data"):
        """
        Initialize CSV data loader.
        
        Args:
            data_folder: Path to the folder containing CSV files
        """
        self.data_folder = Path(data_folder)
    
    def load(self, filename):
        """
        Load a CSV file from the data folder.
        Supports both relative paths (e.g., "stocks/file.csv") and absolute paths.
        
        Args:
            filename: Name of the CSV file to load (can include subfolder path)
            
        Returns:
            pd.DataFrame: The loaded data
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            pd.errors.EmptyDataError: If the CSV file is empty
            pd.errors.ParserError: If the CSV file cannot be parsed
        """
        # Handle both relative paths (stocks/file.csv) and absolute paths
        if Path(filename).is_absolute():
            file_path = Path(filename)
        else:
            file_path = self.data_folder / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                raise pd.errors.EmptyDataError(f"CSV file is empty: {file_path}")
            return df
        except pd.errors.EmptyDataError:
            raise
        except pd.errors.ParserError as e:
            raise pd.errors.ParserError(f"Error parsing CSV file {file_path}: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error loading CSV file {file_path}: {str(e)}")

