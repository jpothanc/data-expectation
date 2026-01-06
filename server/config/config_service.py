import json
import os


class ConfigService:
    def __init__(self, env=None):
        """
        Initialize config service with environment-specific configuration.
        
        Args:
            env: Environment name ('dev', 'uat', 'prod'). 
                 If None, reads from ENV environment variable or defaults to 'dev'.
        """
        # Determine environment: parameter > environment variable > default
        self.env = env or os.getenv('ENV', 'dev').lower()
        
        # Validate environment
        valid_envs = ['dev', 'uat', 'prod']
        if self.env not in valid_envs:
            raise ValueError(
                f"Invalid environment '{self.env}'. Must be one of: {', '.join(valid_envs)}"
            )
        
        # Load environment-specific config file
        config_dir = os.path.dirname(os.path.dirname(__file__))
        config_filename = f'config_{self.env}.json'
        config_path = os.path.join(config_dir, config_filename)
        
        # Fallback to config.json if environment-specific file doesn't exist
        if not os.path.exists(config_path):
            fallback_path = os.path.join(config_dir, 'config.json')
            if os.path.exists(fallback_path):
                config_path = fallback_path
                print(f"Warning: {config_filename} not found, using config.json instead")
            else:
                raise FileNotFoundError(
                    f"Config file not found. Tried:\n"
                    f"  - {config_path}\n"
                    f"  - {fallback_path}"
                )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as config_file:
                self._config = json.load(config_file)
            print(f"Loaded configuration from: {os.path.basename(config_path)} (env: {self.env})")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
        except Exception as e:
            raise Exception(f"Error loading config file {config_path}: {e}")

    def get_database_connection_string(self, region='apac', env='uat'):
        connection_key = f'connection_string_{region.lower()}_{env.lower()}'
        return self._config['database'][connection_key]

    def get(self, path):
        """
        Get any config value using dot notation
        Example: config_service.get('database.connection_string')
        """
        keys = path.split('.')
        value = self._config
        for key in keys:
            value = value[key]
        return value
    
    def get_data_loader_type(self):
        """Get the configured data loader type."""
        return self._config.get('data_loader', {}).get('type', 'csv')
    
    def get_csv_config(self):
        """Get CSV loader configuration."""
        return self._config.get('data_loader', {}).get('csv', {})
    
    def get_csv_exchange_map(self, product_type='stock'):
        """
        Get CSV exchange map from configuration for a specific product type.
        Flattens region-based structure for backward compatibility.
        
        Args:
            product_type: Product type ('stock', 'stocks', 'option', 'options', 'future'). Defaults to 'stock'.
            
        Returns:
            Dictionary mapping exchange codes to CSV filenames (flattened from regions)
        """
        # Normalize product type (e.g., 'stocks' -> 'stock', 'options' -> 'option')
        normalized_type = self._normalize_product_type(product_type)
        
        csv_config = self.get_csv_config()
        exchange_map = csv_config.get('exchange_map', {})
        
        # Check if exchange_map is organized by product type
        if isinstance(exchange_map, dict) and normalized_type in exchange_map:
            product_exchanges = exchange_map[normalized_type]
            
            # Check if it's organized by region (new format)
            if isinstance(product_exchanges, dict) and any(
                region in product_exchanges for region in ['apac', 'emea', 'us']
            ):
                # Flatten region-based structure for backward compatibility
                flattened = {}
                for region, exchanges in product_exchanges.items():
                    if isinstance(exchanges, dict):
                        flattened.update(exchanges)
                return flattened
            
            # If it's already flat (old format), return as-is
            return product_exchanges
        
        # Fallback: if exchange_map is flat (old format), return as-is
        return exchange_map
    
    def get_exchanges_by_region(self, product_type=None):
        """
        Get exchanges organized by region and product type.
        
        Args:
            product_type: Optional product type filter ('stock', 'option', 'future'). 
                         If None, returns all product types.
        
        Returns:
            Dictionary organized by product_type -> region -> exchange -> data_source
        """
        csv_config = self.get_csv_config()
        exchange_map = csv_config.get('exchange_map', {})
        
        if product_type:
            # Normalize product type
            normalized_type = self._normalize_product_type(product_type)
            if normalized_type in exchange_map:
                return {normalized_type: exchange_map[normalized_type]}
            return {}
        
        # Return all product types
        return exchange_map
    
    @staticmethod
    def _normalize_product_type(product_type):
        """
        Normalize product type to match config.json keys.
        Converts 'stocks' -> 'stock', 'options' -> 'option', etc.
        Note: config.json uses 'option' (singular), not 'options'
        """
        if not product_type:
            return 'stock'
        normalized = product_type.lower().strip()
        # Handle common variations
        if normalized == 'stocks':
            return 'stock'
        if normalized == 'options':
            return 'option'
        # 'option' stays as 'option' (matches config.json)
        return normalized
    
    def get_database_config(self):
        """Get database loader configuration."""
        return self._config.get('data_loader', {}).get('database', {})
    
    def get_database_query_template(self, product_type='stock'):
        """
        Get database query template for a specific product type.
        
        Args:
            product_type: Product type ('stock', 'option', 'future'). Defaults to 'stock'.
            
        Returns:
            Query template string with '{exchange}' placeholder, or None if not configured.
        """
        db_config = self.get_database_config()
        query_templates = db_config.get('query_templates', {})
        return query_templates.get(product_type)
    
    def get_rules_dir(self):
        """
        Get the configured rules directory path.
        
        Returns:
            str: Path to the rules directory (defaults to "config/rules" if not configured)
        """
        return self._config.get('rules', {}).get('rules_dir', 'config/rules')
    
    def get_data_folder(self):
        """
        Get the configured data folder path.
        Checks both top-level 'data' section and 'data_loader.csv.data_folder' for backward compatibility.
        
        Returns:
            str: Path to the data folder (defaults to "data" if not configured)
        """
        # Check top-level data section first
        data_folder = self._config.get('data', {}).get('data_folder')
        if data_folder:
            return data_folder
        
        # Fallback to data_loader.csv.data_folder for backward compatibility
        csv_config = self.get_csv_config()
        return csv_config.get('data_folder', 'data')

