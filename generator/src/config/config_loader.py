"""Configuration loader for generator."""

import yaml
from pathlib import Path


class ConfigLoader:
    """Loads and manages regional configuration."""
    
    def __init__(self, config_path=None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to regions.yaml config file. 
                        Defaults to generator/config/regions.yaml
        """
        if config_path is None:
            # Go up from src/config/config_loader.py to generator/config/regions.yaml
            config_dir = Path(__file__).parent.parent.parent / "config"
            config_path = config_dir / "regions.yaml"
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {str(e)}")
        
        if not isinstance(self._config, dict):
            raise ValueError("Configuration file must contain a dictionary")
    
    def get_regions(self):
        """Get list of available regions."""
        return list(self._config.keys())
    
    def get_product_types(self, region):
        """
        Get list of product types for a region.
        
        Args:
            region: Region name (e.g., 'apac', 'emea', 'us')
            
        Returns:
            List of product type names
            
        Raises:
            KeyError: If region not found
        """
        if region not in self._config:
            available = self.get_regions()
            raise KeyError(f"Region '{region}' not found. Available regions: {available}")
        
        return list(self._config[region].keys())
    
    def get_exchanges(self, region, product_type):
        """
        Get list of exchanges for a region and product type.
        
        Args:
            region: Region name (e.g., 'apac', 'emea', 'us')
            product_type: Product type name (e.g., 'stock', 'option', 'future')
            
        Returns:
            List of exchange codes
            
        Raises:
            KeyError: If region or product type not found
        """
        if region not in self._config:
            available = self.get_regions()
            raise KeyError(f"Region '{region}' not found. Available regions: {available}")
        
        if product_type not in self._config[region]:
            available_types = self.get_product_types(region)
            raise KeyError(
                f"Product type '{product_type}' not found in region '{region}'. "
                f"Available product types: {available_types}"
            )
        
        exchanges = self._config[region][product_type]
        if not isinstance(exchanges, list):
            raise ValueError(
                f"Exchanges for {region}/{product_type} must be a list. "
                f"Got: {type(exchanges)}"
            )
        
        return exchanges
    
    def get_all_combinations(self, region=None):
        """
        Get all combinations of (region, product_type, exchange).
        
        Args:
            region: Optional region filter. If None, returns all regions.
            
        Returns:
            List of tuples: (region, product_type, exchange)
        """
        combinations = []
        regions = [region] if region else self.get_regions()
        
        for reg in regions:
            for product_type in self.get_product_types(reg):
                for exchange in self.get_exchanges(reg, product_type):
                    combinations.append((reg, product_type, exchange))
        
        return combinations
