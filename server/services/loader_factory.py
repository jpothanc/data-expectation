"""Factory for creating data loaders based on configuration."""

from loaders.csv_loader import CSVDataLoader
from loaders.database_loader import DatabaseDataLoader
from config.config_service import ConfigService


class LoaderFactory:
    """Factory for creating data loaders."""
    
    def __init__(self, config_service=None):
        """Initialize factory with config service."""
        self.config_service = config_service or ConfigService()
    
    def create_loader(self):
        """Create data loader based on configuration."""
        loader_type = self.config_service.get_data_loader_type()
        
        if loader_type == 'database':
            return self._create_database_loader()
        else:  # default to csv
            return self._create_csv_loader()
    
    def _create_csv_loader(self):
        """Create CSV data loader."""
        data_folder = self.config_service.get_data_folder()
        return CSVDataLoader(data_folder=data_folder)
    
    def _create_database_loader(self):
        """Create database data loader."""
        db_config = self.config_service.get_database_config()
        connection_string = db_config.get('connection_string_apac_uat')
        
        if not connection_string:
            raise ValueError(
                "Database loader requires connection_string_apac_uat in config.json"
            )
        
        # Get query templates from config
        query_templates = db_config.get('query_templates', {})
        
        return DatabaseDataLoader(
            connection_string=connection_string,
            query_templates=query_templates
        )
    
    def get_exchange_map(self, product_type='stock'):
        """
        Get exchange map based on loader type and product type.
        
        Args:
            product_type: Product type ('stock', 'stocks', 'option', 'options', 'future'). Defaults to 'stock'.
        """
        # Normalize product type (e.g., 'stocks' -> 'stock', 'option' -> 'options')
        normalized_type = self._normalize_product_type(product_type)
        
        loader_type = self.config_service.get_data_loader_type()
        
        if loader_type == 'database':
            db_config = self.config_service.get_database_config()
            exchange_map = db_config.get('exchange_map', {})
            # If exchange_map is not configured, use default exchanges
            # For database loaders, values are not used, so we use exchange codes as both key and value
            if not exchange_map:
                from services.constants import DEFAULT_EXCHANGE_MAP
                default_map = DEFAULT_EXCHANGE_MAP.get(normalized_type, DEFAULT_EXCHANGE_MAP['stock'])
                # Create a map where keys and values are the same (exchange codes)
                exchange_map = {code: code for code in default_map.keys()}
            return exchange_map
        else:
            # Check if CSV exchange map is configured
            csv_exchange_map = self.config_service.get_csv_exchange_map(product_type=normalized_type)
            if csv_exchange_map:
                return csv_exchange_map
            
            # Return default CSV exchange map for product type
            from services.constants import DEFAULT_EXCHANGE_MAP
            return DEFAULT_EXCHANGE_MAP.get(normalized_type, DEFAULT_EXCHANGE_MAP['stock'])
    
    def _normalize_product_type(self, product_type):
        """
        Normalize product type to match config.json keys.
        Converts 'stocks' -> 'stock', 'option' -> 'options', etc.
        """
        if not product_type:
            return 'stock'
        normalized = product_type.lower().strip()
        # Handle common variations
        if normalized == 'stocks':
            return 'stock'
        if normalized == 'option':
            return 'options'
        if normalized == 'multilegs':
            return 'multileg'
        return normalized

