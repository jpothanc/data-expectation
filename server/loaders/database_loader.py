"""Database data loader implementation using SQLAlchemy with connection pooling."""

import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from .base import DataLoader

logger = logging.getLogger(__name__)


class DatabaseDataLoader(DataLoader):
    """Handles loading data from database tables using SQLAlchemy with connection pooling."""
    
    def __init__(self, connection_string=None, pyodbc_connection=None, query_templates=None):
        """
        Initialize database data loader with SQLAlchemy connection pooling.
        
        Args:
            connection_string: ODBC connection string for SQLAlchemy
                              (e.g., 'mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=...')
                              or ODBC connection string (will be converted to SQLAlchemy format)
            pyodbc_connection: Optional pyodbc connection object (for backward compatibility).
                              If provided, connection_string is ignored and a single connection is used.
            query_templates: Optional dict mapping product_type to query template strings.
                           Templates should contain '{exchange}' placeholder for parameterized queries.
                           Example: {'stock': "SELECT * FROM StockMaster WHERE Exchange = :exchange"}
        
        Raises:
            ImportError: If sqlalchemy or pyodbc is not installed
        """
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError(
                "sqlalchemy is required for DatabaseDataLoader. "
                "Install it with: pip install sqlalchemy"
            )
        
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for DatabaseDataLoader. "
                "Install it with: pip install pyodbc"
            )
        
        self.query_templates = query_templates or {}
        
        # Handle backward compatibility with pyodbc_connection
        if pyodbc_connection:
            # For backward compatibility, create engine from existing connection
            # Note: This doesn't use pooling, but maintains compatibility
            logger.warning("Using pyodbc_connection directly - connection pooling disabled")
            self._connection = pyodbc_connection
            self.engine = None
        elif connection_string:
            sqlalchemy_url = self._convert_to_sqlalchemy_url(connection_string)

            # Load pool settings from config (with safe fallback defaults)
            pool_cfg: dict = {}
            try:
                from config.config_service import ConfigService
                pool_cfg = ConfigService().get_db_pool_config()
            except Exception:
                pass

            pool_size = pool_cfg.get('pool_size', 5)
            max_overflow = pool_cfg.get('max_overflow', 15)
            pool_recycle = pool_cfg.get('pool_recycle_seconds', 3600)
            pool_pre_ping = pool_cfg.get('pool_pre_ping', True)

            self.engine = create_engine(
                sqlalchemy_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,
                echo=False,
            )
            self._connection = None
            logger.info(
                "DatabaseDataLoader initialised with connection pooling "
                "(pool_size=%d, max_overflow=%d, pool_recycle=%ds)",
                pool_size, max_overflow, pool_recycle,
            )
        else:
            raise ValueError("Either connection_string or pyodbc_connection must be provided")
    
    def _convert_to_sqlalchemy_url(self, connection_string):
        """
        Convert ODBC connection string to SQLAlchemy URL format.
        
        Args:
            connection_string: ODBC connection string
            
        Returns:
            str: SQLAlchemy URL
        """
        # If already in SQLAlchemy format, return as-is
        if connection_string.startswith('mssql+pyodbc://'):
            return connection_string
        
        # Convert ODBC connection string to SQLAlchemy URL
        # Format: mssql+pyodbc:///?odbc_connect=<url_encoded_connection_string>
        from urllib.parse import quote_plus
        encoded = quote_plus(connection_string)
        return f"mssql+pyodbc:///?odbc_connect={encoded}"
    
    def load(self, source, product_type='stock', query=None, exchange=None, limit=None, offset=0):
        """
        Load data from a database table using configured query template or custom query.
        Supports database-level pagination for better performance.
        
        Args:
            source: Exchange code (e.g., 'XNYS', 'XHKG') to use as parameter in query template.
                   For backward compatibility, this is the primary parameter.
            product_type: Product type ('stock', 'option', 'future'). Defaults to 'stock'.
                        Used to select the appropriate query template.
            query: Optional SQL query. If provided, source, exchange, and product_type are ignored 
                  and query is executed directly.
            exchange: Optional exchange code. If provided, overrides source parameter.
                     This allows explicit exchange specification while maintaining backward compatibility.
            limit: Optional limit for pagination. If provided, only this many rows will be returned.
            offset: Optional offset for pagination. Defaults to 0.
            
        Returns:
            pd.DataFrame: The loaded data
        """
        # Use exchange parameter if provided, otherwise use source (for backward compatibility)
        exchange_code = exchange if exchange is not None else source
        
        # Determine connection to use (engine for pooling, or direct connection for backward compat)
        if self.engine:
            connection = self.engine.connect()
            use_context_manager = True
        else:
            connection = self._connection
            use_context_manager = False
        
        try:
            if query:
                # Custom query - execute directly
                if use_context_manager:
                    return pd.read_sql(text(query), connection)
                else:
                    return pd.read_sql(query, connection)
            
            # Use query template if available
            query_template = self.query_templates.get(product_type)
            if query_template:
                # Convert template to parameterized query if it uses {exchange} format
                if '{exchange}' in query_template:
                    # Old format with string formatting - convert to parameterized
                    query_template = query_template.replace('{exchange}', ':exchange')
                
                # Add pagination if limit is specified
                if limit is not None:
                    # SQL Server uses OFFSET/FETCH NEXT syntax
                    query_template = f"{query_template} OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
                    params = {'exchange': exchange_code, 'offset': offset, 'limit': limit}
                else:
                    params = {'exchange': exchange_code}
                
                # Execute parameterized query
                if use_context_manager:
                    result = pd.read_sql(text(query_template), connection, params=params)
                else:
                    # Fallback for old pyodbc connection - use string formatting
                    formatted_query = query_template.replace(':exchange', f"'{exchange_code}'")
                    if limit is not None:
                        formatted_query = formatted_query.replace(':offset', str(offset))
                        formatted_query = formatted_query.replace(':limit', str(limit))
                    result = pd.read_sql(formatted_query, connection)
                
                return result
            
            # Fallback to default behavior for backward compatibility
            fallback_query = f"SELECT * FROM StockMaster WHERE Exchange = '{exchange_code}'"
            if limit is not None:
                fallback_query += f" OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
            
            if use_context_manager:
                return pd.read_sql(text(fallback_query), connection)
            else:
                return pd.read_sql(fallback_query, connection)
        
        finally:
            # Close connection if using context manager (from engine)
            if use_context_manager and connection:
                connection.close()
    
    def load_query(self, query):
        """
        Execute a custom SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            pd.DataFrame: Query results
        """
        if self.engine:
            with self.engine.connect() as connection:
                return pd.read_sql(text(query), connection)
        else:
            return pd.read_sql(query, self._connection)
    
    def close(self):
        """Close the database connection or engine."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_pool_stats(self):
        """
        Get connection pool statistics (for monitoring).
        
        Returns:
            dict: Pool statistics including size, checked out connections, etc.
        """
        if not self.engine:
            return {"status": "no_pool", "message": "Using direct connection (no pooling)"}
        
        try:
            pool = self.engine.pool
            stats = {
                "status": "pooled",
                "pool_size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "checked_in": pool.checkedin(),
                "total_connections": pool.size() + pool.overflow()
            }
            logger.debug(f"Connection pool stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

