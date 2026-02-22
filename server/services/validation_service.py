"""Service for validation operations."""

import logging
import time

import pandas as pd
from processors.processor_factory import ProcessorFactory
from services.validation_result_formatter import ValidationResultFormatter
from services.instrument_service import InstrumentService
from services.constants import DEFAULT_EXCHANGE_MAP
from validators.rule_loader import RuleLoader
from config.config_service import ConfigService

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for managing validation operations."""
    
    def __init__(self, loader, exchange_map=None, product_type='stock', rules_dir=None):
        """
        Initialize service with a data loader.
        
        Args:
            loader: DataLoader instance (CSVDataLoader, DatabaseDataLoader, etc.)
            exchange_map: Optional dict mapping exchange codes to data sources.
                         If None, uses default CSV file mapping for the product type.
            product_type: Product type ('stock', 'stocks', 'option', 'options', 'future'). Defaults to 'stock'.
            rules_dir: Optional path to rules directory. If None, reads from config.json or defaults to "config/rules".
        """
        self.loader = loader
        # Normalize product type (e.g., 'stocks' -> 'stock', 'option' -> 'options')
        self.product_type = self._normalize_product_type(product_type)
        
        # Handle both old flat format and new product-type format
        if exchange_map:
            # If exchange_map is a dict with product_type keys, extract the right one
            if isinstance(exchange_map, dict) and self.product_type in exchange_map:
                self.exchange_map = exchange_map[self.product_type]
            # If exchange_map is flat (old format), use as-is
            elif isinstance(exchange_map, dict) and all(isinstance(v, str) for v in exchange_map.values()):
                self.exchange_map = exchange_map
            else:
                self.exchange_map = exchange_map
        else:
            # Use default for product type
            self.exchange_map = DEFAULT_EXCHANGE_MAP.get(self.product_type, DEFAULT_EXCHANGE_MAP['stock'])
        
        # Get rules directory from config if not provided
        if rules_dir is None:
            try:
                config_service = ConfigService()
                rules_dir = config_service.get_rules_dir()
            except Exception:
                # Fallback to default if config service fails
                rules_dir = "config/rules"
        
        self.rule_loader = RuleLoader(rules_dir=rules_dir)
        self.instrument_service = InstrumentService(loader, exchange_map=self.exchange_map, product_type=product_type)
    
    def _get_data_source(self, exchange, product_type=None):
        """
        Get data source identifier for an exchange.
        
        Args:
            exchange: Exchange code
            product_type: Optional product type. If provided, will use product-specific exchange map.
        """
        # If product_type is provided and different from current, get the right exchange map
        if product_type and product_type != self.product_type:
            if isinstance(DEFAULT_EXCHANGE_MAP, dict) and product_type in DEFAULT_EXCHANGE_MAP:
                exchange_map = DEFAULT_EXCHANGE_MAP[product_type]
            else:
                exchange_map = self.exchange_map
        else:
            exchange_map = self.exchange_map
        
        if exchange not in exchange_map:
            raise ValueError(
                f"Exchange '{exchange}' not found for product type '{product_type or self.product_type}'. "
                f"Available: {', '.join(exchange_map.keys())}"
            )
        return exchange_map[exchange]
    
    def validate_exchange(self, exchange, custom_rule_names=None, custom_rules=None, product_type='stock'):
        """
        Validate exchange data with base + exchange + custom rules.
        
        Args:
            exchange: Exchange code
            custom_rule_names: Optional list of custom rule names
            custom_rules: Optional list of custom rules
            product_type: Type of product ('stock', 'future', 'option'). Defaults to 'stock'.
        
        Returns:
            dict: Formatted validation results (JSON-serializable)
        
        Raises:
            ValueError: If exchange not found or data is invalid
            FileNotFoundError: If data source file not found
            Exception: Other validation errors
        """
        try:
            data_source = self._get_data_source(exchange, product_type=product_type)
            logger.debug("Data source for %s (%s): %s | exchange_map keys: %s",
                         exchange, product_type, data_source, list(self.exchange_map.keys()))
        except ValueError as e:
            logger.error("Exchange %s not found in exchange_map for product_type %s. Available: %s",
                         exchange, product_type, list(self.exchange_map.keys()))
            raise ValueError(f"Exchange validation failed: {str(e)}")

        try:
            processor = ProcessorFactory.create(
                product_type=product_type,
                loader=self.loader,
                exchange=exchange,
            )
        except IOError as e:
            logger.error("IOError creating processor for %s: %s", product_type, e)
            raise ValueError(
                f"File access error creating processor for {product_type}: {e}. "
                "This may be due to a closed file handle or file locking issue."
            )
        except Exception as e:
            logger.error("Error creating processor for %s: %s", product_type, e)
            raise ValueError(f"Failed to create processor for {product_type}: {e}")

        t0 = time.perf_counter()
        try:
            results = processor.process(
                data_source,
                exchange=exchange,
                custom_rules=custom_rules,
                custom_rule_names=custom_rule_names,
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Data file not found for {exchange}: {e}")
        except ValueError as e:
            raise ValueError(f"Validation failed for {exchange}: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required column in data for {exchange}: {e}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Data file for {exchange} is empty")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error parsing data file for {exchange}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error during validation for {exchange} ({type(e).__name__}): {e}")
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("[TIMING] validate_exchange %s/%s completed in %.1f ms",
                        product_type, exchange, elapsed_ms)

        if results is None:
            raise ValueError(f"Validation returned no results for {exchange}")

        try:
            formatted = ValidationResultFormatter.format_results(results, exchange)
            return formatted
        except AttributeError as e:
            raise Exception(f"Invalid validation results format for {exchange}: {e}")
        except Exception as e:
            raise Exception(f"Failed to format validation results for {exchange}: {e}")
    
    def validate_custom_only(self, exchange, custom_rule_names=None, custom_rules=None, product_type='stock'):
        """
        Validate exchange data with ONLY custom rules.
        
        Args:
            exchange: Exchange code
            custom_rule_names: Optional list of custom rule names
            custom_rules: Optional list of custom rules
            product_type: Type of product ('stock', 'future', 'option'). Defaults to 'stock'.
        
        Returns:
            dict: Formatted validation results (JSON-serializable)
        """
        if not custom_rule_names and not custom_rules:
            raise ValueError(
                "At least one custom rule must be provided. "
                "Use 'custom_rule_names' or 'custom_rules' parameter."
            )
        
        data_source = self._get_data_source(exchange)
        
        processor = ProcessorFactory.create(
            product_type=product_type,
            loader=self.loader,
            exchange=exchange
        )
        
        # For database loaders, pass exchange and product_type explicitly
        # For CSV loaders, pass data_source (filename) as before
        from loaders.database_loader import DatabaseDataLoader
        if isinstance(self.loader, DatabaseDataLoader):
            df = self.loader.load(data_source, product_type=product_type, exchange=exchange)
        else:
            df = self.loader.load(data_source)
        
        # Pass exchange and product_type to allow exchange-level custom rules to override product type rules
        results = processor.validator.validate_custom_only(
            df,
            custom_rules=custom_rules,
            custom_rule_names=custom_rule_names,
            exchange=exchange,
            product_type=product_type
        )
        return ValidationResultFormatter.format_results(results, exchange, rules_applied="custom_only")
    
    def get_rules_for_exchange(self, exchange, product_type='stock', custom_rule_names=None):
        """
        Get all rules that would be applied for a given exchange and product type.
        Rules are merged in the same order they would be applied during validation.
        
        Args:
            exchange: Exchange code (e.g., 'XNSE', 'XHKG', 'XTKS')
            product_type: Type of product ('stock', 'stocks', 'future', 'option', 'options'). Defaults to 'stock'.
            custom_rule_names: Optional list of custom rule names to include
            
        Returns:
            dict: Dictionary containing merged rules list and summary
        """
        if exchange not in self.exchange_map:
            raise ValueError(
                f"Exchange '{exchange}' not found. "
                f"Available: {', '.join(self.exchange_map.keys())}"
            )
        
        # Normalize product type (e.g., 'stocks' -> 'stock', 'option' -> 'options')
        normalized_type = self.rule_loader._normalize_product_type(product_type) if product_type else None
        
        # Use the same method that loads rules for validation to ensure consistency
        merged_rules = self.rule_loader.load_combined_rules(
            exchange=exchange,
            custom_rule_names=custom_rule_names,
            product_type=normalized_type
        )
        
        return {
            "exchange": exchange,
            "product_type": normalized_type or product_type,
            "rules": merged_rules,
            "count": len(merged_rules)
        }
    
    def get_combined_rule_names(self, product_type='stock', exchange=None):
        """
        Get available combined rule names for a given product type and optionally exchange.
        Returns both product type level and exchange level combined rules separately.
        
        Args:
            product_type: Type of product ('stock', 'stocks', 'future', 'option', 'options'). Defaults to 'stock'.
            exchange: Optional exchange code to get exchange-specific combined rule sets
            
        Returns:
            dict: Dictionary containing lists of combined rule names from both product type and exchange levels
        """
        # Normalize product type (e.g., 'stocks' -> 'stock', 'option' -> 'options')
        normalized_type = self.rule_loader._normalize_product_type(product_type) if product_type else None
        
        # Get product type level combined rules (without exchange)
        product_type_combined_rules = self.rule_loader.get_available_combined_rule_sets(
            product_type=normalized_type, exchange=None
        )
        
        # Get exchange level combined rules directly from the exchange combined.yaml file
        exchange_combined_rules = []
        if exchange and normalized_type:
            exchange_combined_yaml_file = (
                self.rule_loader.rules_dir / normalized_type / "exchanges" / exchange.lower() / "combined.yaml"
            )
            if exchange_combined_yaml_file.exists():
                try:
                    exchange_combined_config = self.rule_loader._load_yaml_file(
                        exchange_combined_yaml_file, allow_empty=True
                    )
                    if isinstance(exchange_combined_config, dict):
                        exchange_combined_rules = sorted(list(exchange_combined_config.keys()))
                except Exception:
                    # If there's an error loading the file, just continue with empty list
                    pass
        
        # Get all unique combined rules (union of both levels)
        # Exchange-level rules override product type rules, so we include all from both
        all_combined_rule_names = sorted(set(product_type_combined_rules + exchange_combined_rules))
        
        return {
            "product_type": normalized_type or product_type,
            "exchange": exchange,
            "product_type_level": {
                "combined_rule_names": product_type_combined_rules,
                "count": len(product_type_combined_rules)
            },
            "exchange_level": {
                "combined_rule_names": exchange_combined_rules,
                "count": len(exchange_combined_rules)
            },
            "all_combined_rule_names": all_combined_rule_names,
            "count": len(all_combined_rule_names)
        }
    
    def get_combined_rule_details(self, product_type='stock', exchange=None):
        """
        Get detailed information about combined rules for a given product type and exchange.
        Shows what rules are included in each combined rule set and what would be applied.
        
        Args:
            product_type: Type of product ('stock', 'stocks', 'future', 'option', 'options'). Defaults to 'stock'.
            exchange: Optional exchange code (e.g., 'XNSE', 'XHKG', 'XTKS')
            
        Returns:
            dict: Dictionary containing detailed information about combined rules
        """
        # Normalize product type
        normalized_type = self.rule_loader._normalize_product_type(product_type) if product_type else None
        
        # Get available combined rule names (include exchange-level rules)
        combined_rule_names = self.rule_loader.get_available_combined_rule_sets(
            product_type=normalized_type, exchange=exchange
        )
        
        # Get the raw combined rule definitions
        combined_rules_details = {}
        
        # Load exchange-level combined.yaml first (highest priority - overrides product type rules)
        if exchange and normalized_type:
            exchange_combined_yaml_file = (
                self.rule_loader.rules_dir / normalized_type / "exchanges" / exchange.lower() / "combined.yaml"
            )
            if exchange_combined_yaml_file.exists():
                exchange_combined_config = self.rule_loader._load_yaml_file(exchange_combined_yaml_file, allow_empty=True)
                if isinstance(exchange_combined_config, dict):
                    combined_rules_details.update(exchange_combined_config)
        
        # Load the product type combined.yaml file
        if normalized_type:
            combined_yaml_file = self.rule_loader.rules_dir / normalized_type / "combined.yaml"
            if combined_yaml_file.exists():
                combined_config = self.rule_loader._load_yaml_file(combined_yaml_file, allow_empty=True)
                if isinstance(combined_config, dict):
                    # Merge with exchange rules (exchange takes precedence, so only add if not already present)
                    for key, value in combined_config.items():
                        if key not in combined_rules_details:
                            combined_rules_details[key] = value
        
        # Also check root level combined.yaml
        root_combined_yaml_file = self.rule_loader.rules_dir / "combined.yaml"
        if root_combined_yaml_file.exists():
            root_combined_config = self.rule_loader._load_yaml_file(root_combined_yaml_file, allow_empty=True)
            if isinstance(root_combined_config, dict):
                # Merge with existing rules (only add if not already present)
                for key, value in root_combined_config.items():
                    if key not in combined_rules_details:
                        combined_rules_details[key] = value
        
        # Build detailed response for each combined rule
        detailed_rules = []
        
        for rule_name in combined_rule_names:
            rule_info = {
                "name": rule_name,
                "definition": combined_rules_details.get(rule_name, {}),
                "includes": [],
                "resolved_rules": []
            }
            
            # Get the includes if it's a combined rule
            if rule_name in combined_rules_details:
                rule_def = combined_rules_details[rule_name]
                if isinstance(rule_def, dict) and 'include' in rule_def:
                    includes = rule_def['include']
                    if isinstance(includes, list):
                        rule_info["includes"] = includes
                    elif isinstance(includes, str):
                        rule_info["includes"] = [includes]
            
            # Resolve the actual rules that would be applied
            try:
                # Load base + exchange + combined rules
                all_rules = self.rule_loader.load_combined_rules(
                    exchange=exchange,
                    custom_rule_names=[rule_name],
                    product_type=normalized_type
                )
                
                # Get just the rules from the combined rule (not base/exchange)
                # Pass exchange to allow exchange-level custom rules to override product type rules
                combined_only_rules = self.rule_loader.load_custom_rules_from_yaml(
                    [rule_name],
                    product_type=normalized_type,
                    exchange=exchange
                )
                
                rule_info["resolved_rules"] = combined_only_rules
                rule_info["resolved_rule_count"] = len(combined_only_rules)
                
                # If exchange is provided, show what the full rule set would be
                if exchange:
                    rule_info["full_rule_set_count"] = len(all_rules)
                    rule_info["base_and_exchange_rules_count"] = len(all_rules) - len(combined_only_rules)
            except Exception as e:
                rule_info["error"] = str(e)
            
            detailed_rules.append(rule_info)
        
        return {
            "product_type": normalized_type or product_type,
            "exchange": exchange,
            "combined_rules": detailed_rules,
            "count": len(detailed_rules)
        }
    
    def validate_record_by_masterid(self, master_id, combined_rule_name, product_type='stock'):
        """
        Validate a single record by MasterId using a combined rule name.
        The exchange is identified from the record, and rules are applied with preference
        to exchange-specific definitions, falling back to base rules.
        
        Args:
            master_id: MasterId of the record to validate
            combined_rule_name: Name of the combined rule set to use for validation
            product_type: Type of product ('stock', 'future', 'option'). Defaults to 'stock'.
        
        Returns:
            dict: Formatted validation results (JSON-serializable)
        
        Raises:
            ValueError: If record not found, exchange cannot be identified, or rule not found
        """
        # Fetch the record by masterid
        record = self.instrument_service.find_by_masterid(master_id)
        if not record:
            raise ValueError(f"Record with MasterId '{master_id}' not found")
        
        # Extract exchange from the record
        exchange = record.get('Exchange')
        if not exchange:
            raise ValueError(f"Exchange not found in record with MasterId '{master_id}'")
        
        # Normalize product type
        normalized_type = self.rule_loader._normalize_product_type(product_type) if product_type else None
        
        # Verify the combined rule exists before proceeding
        try:
            available_rules = self.rule_loader.get_available_combined_rule_sets(
                product_type=normalized_type, exchange=exchange
            )
            # Also check custom rules in case it's not a combined rule (include exchange-level rules)
            available_custom = self.rule_loader.get_available_custom_rule_sets(
                product_type=normalized_type, exchange=exchange
            )
            all_available = list(set(available_rules + available_custom))
            
            # Try to load the rule to see if it exists (exchange-level rules override product type rules)
            test_rules = self.rule_loader.load_custom_rules_from_yaml(
                [combined_rule_name], product_type=normalized_type, exchange=exchange
            )
            if not test_rules and combined_rule_name not in all_available:
                raise ValueError(
                    f"Combined rule '{combined_rule_name}' not found. "
                    f"Available combined rules: {available_rules}. "
                    f"Available custom rules: {available_custom}"
                )
        except ValueError as e:
            # Re-raise with helpful message
            if "not found" in str(e) or "Custom rule set" in str(e):
                raise e
            # If it's a different ValueError, wrap it
            raise ValueError(f"Error loading rule '{combined_rule_name}': {str(e)}")
        
        # Convert record to DataFrame (single row)
        df = pd.DataFrame([record])
        
        # Create processor for validation
        processor = ProcessorFactory.create(
            product_type=product_type,
            loader=self.loader,
            exchange=exchange
        )
        
        # Validate using the combined rule name
        # The load_combined_rules method already prioritizes exchange-specific rules
        # Order: base -> product_type/base -> exchange -> product_type/exchange -> custom (YAML)
        try:
            results = processor.validator.validate(
                df,
                exchange=exchange,
                custom_rule_names=[combined_rule_name],
                product_type=normalized_type
            )
        except ValueError as e:
            # Provide helpful error message with available rules (include exchange-level rules)
            available_rules = self.rule_loader.get_available_combined_rule_sets(
                product_type=normalized_type, exchange=exchange
            )
            available_custom = self.rule_loader.get_available_custom_rule_sets(
                product_type=normalized_type, exchange=exchange
            )
            raise ValueError(
                f"Error validating with rule '{combined_rule_name}': {str(e)}. "
                f"Available combined rules: {available_rules}"
            )
        
        # Format results with additional context
        formatted_results = ValidationResultFormatter.format_results(results, exchange)
        formatted_results['master_id'] = master_id
        formatted_results['combined_rule_name'] = combined_rule_name
        formatted_results['record'] = record
        
        return formatted_results
    
    @staticmethod
    def _normalize_product_type(product_type):
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
        return normalized

