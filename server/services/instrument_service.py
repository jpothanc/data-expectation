"""Service for instrument data operations."""

import pandas as pd
from loaders.csv_loader import CSVDataLoader
from loaders.database_loader import DatabaseDataLoader
from .constants import DEFAULT_EXCHANGE_MAP


class InstrumentService:
    """Service for managing instrument data operations."""
    
    def __init__(self, loader, exchange_map=None, product_type='stock'):
        """
        Initialize service with data loader.
        
        Args:
            loader: DataLoader instance (CSVDataLoader, DatabaseDataLoader, etc.)
            exchange_map: Optional dict mapping exchange codes to data sources.
                         Only used for CSV loaders. For database loaders, exchange codes
                         are used directly in queries.
            product_type: Product type ('stock', 'option', 'future'). Defaults to 'stock'.
        """
        self.loader = loader
        self.product_type = product_type
        self.is_csv_loader = isinstance(loader, CSVDataLoader)
        self.is_database_loader = isinstance(loader, DatabaseDataLoader)
        
        # Initialize exchange_map based on loader type
        self.exchange_map = self._initialize_exchange_map(exchange_map, product_type)
        self.ALL_EXCHANGES = list(self.exchange_map.keys()) if self.exchange_map else []
    
    def _initialize_exchange_map(self, exchange_map, product_type):
        """
        Initialize exchange map based on loader type and provided exchange_map.
        
        Args:
            exchange_map: Optional exchange map dict
            product_type: Product type for selecting default map
            
        Returns:
            dict: Initialized exchange map
        """
        # Extract exchange_map for product_type if nested structure
        resolved_map = self._extract_product_type_map(exchange_map, product_type)
        
        if self.is_csv_loader:
            # For CSV loaders, use provided map or default
            return resolved_map or DEFAULT_EXCHANGE_MAP.get(product_type, DEFAULT_EXCHANGE_MAP['stock'])
        
        elif self.is_database_loader:
            # For database loaders, use provided map or create from defaults
            if resolved_map:
                return resolved_map
            # Create map with exchange codes as both keys and values
            default_map = DEFAULT_EXCHANGE_MAP.get(product_type, DEFAULT_EXCHANGE_MAP['stock'])
            return {code: code for code in default_map.keys()}
        
        else:
            # Unknown loader type - use provided map or default
            return resolved_map or DEFAULT_EXCHANGE_MAP.get(product_type, DEFAULT_EXCHANGE_MAP['stock'])
    
    @staticmethod
    def _extract_product_type_map(exchange_map, product_type):
        """
        Extract exchange map for specific product type from nested structure.
        
        Args:
            exchange_map: Exchange map dict (can be nested by product_type or flat)
            product_type: Product type to extract
            
        Returns:
            dict or None: Extracted exchange map or None if not found
        """
        if not exchange_map:
            return None
        
        # If nested structure with product_type keys
        if isinstance(exchange_map, dict) and product_type in exchange_map:
            return exchange_map[product_type]
        
        # If flat structure (old format) - all values are strings
        if isinstance(exchange_map, dict) and all(isinstance(v, str) for v in exchange_map.values()):
            return exchange_map
        
        # Return as-is if structure is unclear
        return exchange_map
    
    def get_all_exchanges(self):
        """
        Get all configured exchanges with their data sources.
        
        Returns:
            Dictionary with exchange codes as keys and data source info as values
        """
        exchanges = []
        
        if self.exchange_map:
            for exchange_code, data_source in self.exchange_map.items():
                exchanges.append({
                    "exchange": exchange_code,
                    "data_source": data_source,
                    "available": True
                })
        
        return {
            "exchanges": sorted(exchanges, key=lambda x: x["exchange"]),
            "count": len(exchanges)
        }
    
    def load_exchange_data(self, exchange):
        """
        Load exchange data without caching.
        
        For CSV loaders: Uses exchange_map to find the CSV file.
        For database loaders: Uses exchange code directly in the query.
        """
        self._validate_exchange(exchange)
        
        if self.is_csv_loader:
            data_source = self.exchange_map[exchange]
            try:
                return self.loader.load(data_source)
            except FileNotFoundError:
                raise FileNotFoundError(f"Data source for exchange '{exchange}' not found")
        
        elif self.is_database_loader:
            return self.loader.load(exchange, product_type=self.product_type)
        
        else:
            # Fallback for unknown loader types
            data_source = self.exchange_map[exchange]
            return self.loader.load(data_source)
    
    def _validate_exchange(self, exchange):
        """Validate that exchange exists in exchange_map."""
        if exchange not in self.exchange_map:
            raise ValueError(
                f"Exchange '{exchange}' not found. "
                f"Available: {', '.join(self.ALL_EXCHANGES)}"
            )
    
    def find_by_ric(self, ric, exchange=None):
        """Find instrument(s) by RIC code."""
        if exchange:
            return self._find_in_exchange(exchange, lambda df: df[df["RIC"] == ric], multiple=True)
        
        return self._search_all_exchanges(lambda df: df[df["RIC"] == ric], multiple=True)
    
    def find_by_id(self, instrument_id, exchange=None):
        """Find instrument by MasterId."""
        return self.find_by_masterid(instrument_id, exchange)
    
    def find_by_masterid(self, master_id, exchange=None):
        """Find instrument by MasterId."""
        master_id_str = str(master_id)
        match_func = lambda df: df[df["MasterId"].astype(str) == master_id_str]
        
        if exchange:
            return self._find_in_exchange(exchange, match_func, multiple=False)
        
        return self._search_all_exchanges(match_func, multiple=False)
    
    def _find_in_exchange(self, exchange, match_func, multiple=False):
        """
        Find records in a specific exchange.
        
        Args:
            exchange: Exchange code
            match_func: Function that takes DataFrame and returns matching rows
            multiple: If True, return list; if False, return single record or None
            
        Returns:
            List of records, single record dict, or None
        """
        df = self.load_exchange_data(exchange)
        matches = match_func(df)
        
        if matches.empty:
            return [] if multiple else None
        
        records = matches.to_dict(orient="records")
        cleaned = self._clean_nan_values(records)
        
        return cleaned if multiple else cleaned[0]
    
    def _search_all_exchanges(self, match_func, multiple=False):
        """
        Search across all exchanges.
        
        Args:
            match_func: Function that takes DataFrame and returns matching rows
            multiple: If True, return list; if False, return single record or None
            
        Returns:
            List of records, single record dict, or None
        """
        if not self.ALL_EXCHANGES:
            raise ValueError(
                "Cannot search all exchanges: exchange parameter is required for database loaders"
            )
        
        results = []
        for exchange in self.ALL_EXCHANGES:
            try:
                df = self.load_exchange_data(exchange)
                matches = match_func(df)
                if not matches.empty:
                    records = matches.to_dict(orient="records")
                    cleaned = self._clean_nan_values(records)
                    if multiple:
                        results.extend(cleaned)
                    else:
                        return cleaned[0]
            except Exception:
                continue
        
        return results if multiple else None
    
    def get_by_exchange(self, exchange, limit=None, offset=0):
        """Get all instruments for an exchange with pagination."""
        df = self.load_exchange_data(exchange)
        
        if offset:
            df = df.iloc[offset:]
        if limit:
            df = df.iloc[:limit]
        
        records = df.to_dict(orient="records")
        cleaned_records = self._clean_nan_values(records)
        
        return {
            "exchange": exchange,
            "count": len(df),
            "instruments": cleaned_records
        }
    
    def _clean_nan_values(self, data):
        """
        Replace NaN values with None to make data JSON-serializable.
        
        Args:
            data: Can be a dict, list of dicts, or any nested structure
            
        Returns:
            Data with NaN values replaced by None
        """
        import math
        
        if isinstance(data, dict):
            return {key: self._clean_nan_values(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_nan_values(item) for item in data]
        elif isinstance(data, float) and math.isnan(data):
            return None
        else:
            return data
