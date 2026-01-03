"""Base processor interface for all instrument processors."""

from abc import ABC, abstractmethod
from loaders.base import DataLoader


class BaseProcessor(ABC):
    """Abstract base class for all instrument processors."""
    
    def __init__(self, loader, exchange=None):
        """
        Initialize processor with a data loader.
        
        Args:
            loader: An instance of DataLoader (e.g., CSVDataLoader, DatabaseDataLoader)
            exchange: Optional exchange code (e.g., 'XHKG', 'XNSE') for exchange-specific validation
        """
        self.loader = loader
        self.exchange = exchange
        self._validator = None
    
    @property
    @abstractmethod
    def product_type(self):
        """
        Return the type of product this processor handles.
        
        Returns:
            str: Product type (e.g., 'stock', 'future', 'option')
        """
        pass
    
    @property
    @abstractmethod
    def validator(self):
        """
        Return the validator instance for this processor type.
        
        Returns:
            Validator instance appropriate for the instrument type
        """
        pass
    
    def process(self, source, exchange=None, custom_rules=None, custom_rule_names=None):
        """
        Load data from source and validate the instrument data.
        
        Args:
            source: The data source identifier (filename, table name, etc.)
            exchange: Optional exchange code. If provided, applies exchange-specific rules.
                     If None, uses the exchange from initialization.
            custom_rules: Optional list of custom rule dictionaries (programmatic).
            custom_rule_names: Optional list of custom rule set names from YAML.
                             Rules are applied in order: base -> exchange -> custom (YAML) -> custom (programmatic)
            
        Returns:
            ValidationResult: The validation results
        """
        df = self._load_data(source)
        
        # Use exchange parameter if provided, otherwise use instance exchange
        exchange_to_use = exchange if exchange is not None else self.exchange
        
        rule_info = self._format_rule_info(exchange_to_use, custom_rule_names, custom_rules)
        print(f"\n{rule_info}")
        
        results = self.validator.validate(
            df,
            exchange=exchange_to_use,
            custom_rules=custom_rules,
            custom_rule_names=custom_rule_names,
            product_type=self.product_type
        )
        
        self._log_results(results)
        
        return results
    
    def _load_data(self, source):
        """
        Load data from source.
        
        Args:
            source: The data source identifier
            
        Returns:
            pd.DataFrame: The loaded data
        """
        print(f"Loading data from source: {source}")
        
        # For database loaders, pass exchange and product_type explicitly
        # For CSV loaders, pass source (filename) as before
        from loaders.database_loader import DatabaseDataLoader
        if isinstance(self.loader, DatabaseDataLoader):
            # For database loaders, source is the exchange code
            df = self.loader.load(source, product_type=self.product_type, exchange=self.exchange or source)
        else:
            df = self.loader.load(source)
        
        print(f"Loaded {len(df)} records")
        return df
    
    def _format_rule_info(self, exchange, custom_rule_names, custom_rules):
        """
        Format rule information for logging.
        
        Args:
            exchange: Exchange code
            custom_rule_names: List of custom rule names
            custom_rules: List of custom rules
            
        Returns:
            str: Formatted rule information
        """
        rule_info = []
        if exchange:
            rule_info.append(f"exchange: {exchange}")
        if custom_rule_names:
            rule_info.append(f"custom YAML: {', '.join(custom_rule_names)}")
        if custom_rules:
            rule_info.append(f"custom programmatic: {len(custom_rules)} rule(s)")
        
        if rule_info:
            return f"Validating data with: {', '.join(rule_info)}"
        else:
            return "Validating data with base rules only..."
    
    def _log_results(self, results):
        """Log validation results."""
        if results.success:
            print(f"\n✅ SUCCESS: {self.product_type.capitalize()} data is valid!")
        else:
            print(f"\n❌ FAILURE: {self.product_type.capitalize()} data validation failed.")
            print(results)




