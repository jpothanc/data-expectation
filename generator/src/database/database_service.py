"""Database service for managing database connections with connection pooling."""

import logging
import os
import json
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections with SQLAlchemy connection pooling."""
    
    def __init__(self, connection_string=None):
        """
        Initialize database service with connection pooling.
        
        Args:
            connection_string: SQL Server connection string. If None, will try to get from config.
        """
        try:
            self.pyodbc = pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for DatabaseService. "
                "Install it with: pip install pyodbc"
            )
        
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError(
                "sqlalchemy is required for DatabaseService. "
                "Install it with: pip install sqlalchemy"
            )
        
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = self._get_connection_string_from_config()
        
        # Convert to SQLAlchemy URL and create engine with connection pooling
        sqlalchemy_url = self._convert_to_sqlalchemy_url(self.connection_string)
        
        # Create SQLAlchemy engine with connection pooling
        # For batch operations, we use a smaller pool but allow overflow
        self.engine = create_engine(
            sqlalchemy_url,
            poolclass=QueuePool,
            pool_size=3,
            max_overflow=7,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before using
            echo=False
        )
        
        # Keep direct connection for backward compatibility (will be lazily created)
        self._connection = None
        logger.info("DatabaseService initialized with SQLAlchemy connection pooling (pool_size=3, max_overflow=7)")
    
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
        encoded = quote_plus(connection_string)
        return f"mssql+pyodbc:///?odbc_connect={encoded}"
    
    def _get_connection_string_from_config(self):
        """Get connection string from config.json and modify for RubyUsers database."""
        # Try generator/config.json first, then fall back to parent config.json
        # From generator/src/database/database_service.py, go up to generator/config.json
        generator_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config.json'
        )
        # Also check parent directory (instruments_ge_app/config.json)
        parent_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'config.json'
        )
        
        config_path = None
        if os.path.exists(generator_config_path):
            config_path = generator_config_path
            logger.info(f"Using generator config.json: {config_path}")
        elif os.path.exists(parent_config_path):
            config_path = parent_config_path
            logger.info(f"Using parent config.json: {config_path}")
        else:
            raise FileNotFoundError(
                f"Config file not found. Tried:\n"
                f"  - {generator_config_path}\n"
                f"  - {parent_config_path}"
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Try to get connection string from database section
            db_config = config.get('database', {})
            base_connection = db_config.get('connection_string_apac_uat', '')
            
            if not base_connection:
                raise ValueError(
                    f"No 'connection_string_apac_uat' found in database section of {config_path}"
                )
            
            # Replace DATABASE=Instruments with DATABASE=RubyUsers
            if 'DATABASE=' in base_connection:
                connection_string = base_connection.replace(
                    'DATABASE=Instruments', 'DATABASE=RubyUsers'
                ).replace(
                    'DATABASE=Instruments;', 'DATABASE=RubyUsers;'
                )
            else:
                # If no DATABASE specified, add it
                connection_string = base_connection.rstrip(';') + ';DATABASE=RubyUsers;'
            
            logger.debug(f"Using connection string (database modified to RubyUsers)")
            return connection_string
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Error loading config from {config_path}: {e}")
    
    def get_connection(self):
        """
        Get database connection from pool.
        
        Returns:
            Connection object from SQLAlchemy engine pool
        """
        # Use SQLAlchemy engine connection (from pool)
        return self.engine.connect()
    
    def get_pyodbc_connection(self):
        """
        Get direct pyodbc connection (for backward compatibility).
        Creates a new connection if needed.
        """
        if self._connection is None:
            try:
                print(f"  🔌 Connecting to database (direct pyodbc)...")
                print(f"  📍 Connection String: {self._mask_connection_string(self.connection_string)}")
                # Connect with autocommit=False to use transactions
                self._connection = self.pyodbc.connect(self.connection_string, autocommit=False)
                print(f"  ✅ Database connection established successfully")
                print(f"  📊 Autocommit: False (using transactions)")
                logger.info("Direct pyodbc connection established with autocommit=False")
            except Exception as e:
                error_msg = f"Failed to connect to database: {e}"
                print(f"  ❌ {error_msg}")
                logger.error(error_msg)
                raise
        return self._connection
    
    def _mask_connection_string(self, conn_str):
        """Mask sensitive information in connection string for logging."""
        # Mask password if present
        if 'PWD=' in conn_str or 'Password=' in conn_str:
            import re
            conn_str = re.sub(r'(PWD|Password)=[^;]+', r'\1=***', conn_str, flags=re.IGNORECASE)
        return conn_str
    
    def close(self):
        """Close database connections and dispose of engine pool."""
        # Close direct pyodbc connection if exists
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Direct pyodbc connection closed")
            except Exception as e:
                logger.error(f"Error closing direct pyodbc connection: {e}")
        
        # Dispose of SQLAlchemy engine pool
        if self.engine:
            try:
                self.engine.dispose()
                logger.info("SQLAlchemy engine pool disposed")
            except Exception as e:
                logger.error(f"Error disposing SQLAlchemy engine: {e}")
    
    def test_connection(self):
        """Test database connection."""
        try:
            print(f"  🧪 Testing database connection...")
            conn = self.get_connection()
            try:
                # Use SQLAlchemy connection
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                print(f"  ✅ Database connection test passed")
                return True
            finally:
                conn.close()
        except Exception as e:
            error_msg = f"Database connection test failed: {e}"
            print(f"  ❌ {error_msg}")
            logger.error(error_msg)
            return False
    
    def get_pool_stats(self):
        """
        Get connection pool statistics (for monitoring).
        
        Returns:
            dict: Pool statistics including size, checked out connections, etc.
        """
        if not self.engine:
            return {"status": "no_pool", "message": "Engine not initialized"}
        
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

