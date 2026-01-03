"""Database service for managing database connections."""

import logging
import os
import json
import pyodbc
logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections."""
    
    def __init__(self, connection_string=None):
        """
        Initialize database service.
        
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
        
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = self._get_connection_string_from_config()
        
        self._connection = None
    
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
        """Get or create database connection."""
        if self._connection is None:
            try:
                print(f"  🔌 Connecting to database...")
                print(f"  📍 Connection String: {self._mask_connection_string(self.connection_string)}")
                # Connect with autocommit=False to use transactions
                self._connection = self.pyodbc.connect(self.connection_string, autocommit=False)
                print(f"  ✅ Database connection established successfully")
                print(f"  📊 Autocommit: False (using transactions)")
                logger.info("Database connection established with autocommit=False")
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
        """Close database connection."""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
    
    def test_connection(self):
        """Test database connection."""
        try:
            print(f"  🧪 Testing database connection...")
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            print(f"  ✅ Database connection test passed")
            return True
        except Exception as e:
            error_msg = f"Database connection test failed: {e}"
            print(f"  ❌ {error_msg}")
            logger.error(error_msg)
            return False

