"""Utility class for exporting SQL query results to CSV."""

import pandas as pd
from pathlib import Path
from config.config_service import ConfigService


class QueryExporter:
    """Utility class to execute SQL queries and export results to CSV."""
    
    def __init__(self, connection_string=None, config_service=None):
        """
        Initialize QueryExporter.
        
        Args:
            connection_string: Optional ODBC connection string.
                              If None, will use ConfigService to get from config.json
            config_service: Optional ConfigService instance.
                           If None, creates a new one.
        """
        self.config_service = config_service or ConfigService()
        
        if connection_string:
            self.connection_string = connection_string
        else:
            # Get from config
            self.connection_string = self.config_service.get_database_config().get(
                'connection_string_apac_uat'
            )
        
        if not self.connection_string:
            raise ValueError(
                "Connection string not provided and not found in config.json"
            )
        
        # Ensure data folder exists
        self.data_folder = Path(self.config_service.get_data_folder())
        self.data_folder.mkdir(exist_ok=True)
    
    def export_query_to_csv(self, query, filename):
        """
        Execute a SQL query and export results to CSV file.
        
        Args:
            query: SQL query string to execute
            filename: Name of the CSV file (will be saved in data folder)
                     Can include or exclude .csv extension
        
        Returns:
            str: Path to the created CSV file
        
        Raises:
            ImportError: If pyodbc is not installed
            Exception: If query execution fails
        """
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for QueryExporter. "
                "Install it with: pip install pyodbc"
            )
        
        # Ensure filename has .csv extension
        if not filename.endswith('.csv'):
            filename = f"{filename}.csv"
        
        # Build full file path
        file_path = self.data_folder / filename
        
        try:
            # Connect to database
            connection = pyodbc.connect(self.connection_string)
            
            try:
                # Execute query and load into DataFrame
                df = pd.read_sql(query, connection)
                
                # Export to CSV
                df.to_csv(file_path, index=False)
                
                return str(file_path)
            
            finally:
                # Always close connection
                connection.close()
        
        except Exception as e:
            raise Exception(f"Failed to export query to CSV: {str(e)}")
    
    def export_query_to_csv_with_params(self, query_template, filename, **params):
        """
        Execute a parameterized SQL query and export results to CSV.
        
        Args:
            query_template: SQL query template with placeholders (e.g., {exchange})
            filename: Name of the CSV file
            **params: Parameters to substitute in query template
        
        Returns:
            str: Path to the created CSV file
        """
        # Format query with parameters
        query = query_template.format(**params)
        return self.export_query_to_csv(query, filename)
    
    def get_data_folder(self):
        """Get the data folder path."""
        return str(self.data_folder)

