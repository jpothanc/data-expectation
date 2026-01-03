"""Database data loader implementation using pyodbc."""

import pandas as pd
from .base import DataLoader


class DatabaseDataLoader(DataLoader):
    """Handles loading data from database tables using pyodbc."""
    
    def __init__(self, connection_string=None, pyodbc_connection=None, query_templates=None):
        """
        Initialize database data loader.
        
        Args:
            connection_string: ODBC connection string for pyodbc
                              (e.g., 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=...')
            pyodbc_connection: Optional pyodbc connection object. 
                              If provided, connection_string is ignored.
            query_templates: Optional dict mapping product_type to query template strings.
                           Templates should contain '{exchange}' placeholder.
                           Example: {'stock': "SELECT * FROM StockMaster WHERE Exchange = '{exchange}'"}
        
        Raises:
            ImportError: If pyodbc is not installed
        """
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for DatabaseDataLoader. "
                "Install it with: pip install pyodbc"
            )
        
        if pyodbc_connection:
            self._connection = pyodbc_connection
        elif connection_string:
            self._connection = pyodbc.connect(connection_string)
        else:
            raise ValueError("Either connection_string or pyodbc_connection must be provided")
        
        self.query_templates = query_templates or {}
    
    def load(self, source, product_type='stock', query=None, exchange=None):
        """
        Load data from a database table using configured query template or custom query.
        
        Args:
            source: Exchange code (e.g., 'XNYS', 'XHKG') to use as parameter in query template.
                   For backward compatibility, this is the primary parameter.
            product_type: Product type ('stock', 'option', 'future'). Defaults to 'stock'.
                        Used to select the appropriate query template.
            query: Optional SQL query. If provided, source, exchange, and product_type are ignored 
                  and query is executed directly.
            exchange: Optional exchange code. If provided, overrides source parameter.
                     This allows explicit exchange specification while maintaining backward compatibility.
            
        Returns:
            pd.DataFrame: The loaded data
        """
        if query:
            return pd.read_sql(query, self._connection)
        
        # Use exchange parameter if provided, otherwise use source (for backward compatibility)
        exchange_code = exchange if exchange is not None else source
        
        # Use query template if available
        query_template = self.query_templates.get(product_type)
        if query_template:
            # Replace {exchange} placeholder with actual exchange code
            query = query_template.format(exchange=exchange_code)
            return pd.read_sql(query, self._connection)
        
        # Fallback to default behavior for backward compatibility
        return pd.read_sql(f"SELECT * FROM StockMaster WHERE Exchange = '{exchange_code}'", self._connection)
    
    def load_query(self, query):
        """
        Execute a custom SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            pd.DataFrame: Query results
        """
        return pd.read_sql(query, self._connection)
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

