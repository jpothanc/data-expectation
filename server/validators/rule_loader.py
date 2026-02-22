"""Loads validation rules from YAML configuration files."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RuleLoader:
    """Loads and parses validation rules from YAML files.
    
    Supports both modular structure (config/rules/) and single-file structure (validation_rules.yaml).
    """
    
    def __init__(self, config_path=None, rules_dir=None):
        """
        Initialize rule loader.
        
        Args:
            config_path: Path to the single YAML configuration file (for backward compatibility)
            rules_dir: Path to the modular rules directory (default: "config/rules/")
        """
        self.config_path = Path(config_path) if config_path else None
        self.rules_dir = Path(rules_dir) if rules_dir else Path("config/rules")
        self._config = None
        self._use_modular = self._detect_modular_structure()
    
    def _detect_modular_structure(self):
        """Detect if modular rules structure exists."""
        base_file = self.rules_dir / "base.yaml"
        return base_file.exists()
    
    def _load_yaml_file(self, file_path, allow_empty=False):
        """
        Load a YAML file.
        
        Args:
            file_path: Path to the YAML file
            allow_empty: If True, return None for empty files instead of raising an error
            
        Returns:
            Parsed YAML content, or None if empty and allow_empty=True
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty and allow_empty=False
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for RuleLoader. Install it with: pip install pyyaml"
            )
        
        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        # Use explicit file handle management to avoid conflicts
        # Read file content first, then parse to avoid file handle issues
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Parse YAML from string content (avoids file handle issues)
            content = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {file_path}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error reading YAML file {file_path}: {str(e)}")
        
        if content is None:
            if allow_empty:
                return None
            raise ValueError(f"YAML file is empty or invalid: {file_path}")
        
        return content
    
    def _load_config(self):
        """Load and cache YAML configuration (for backward compatibility)."""
        if self._config is None:
            if self.config_path and self.config_path.exists():
                self._config = self._load_yaml_file(self.config_path)
            else:
                raise FileNotFoundError(f"Validation rules file not found: {self.config_path}")
        
        return self._config
    
    def load_base_rules(self):
        """
        Load base/common validation rules that apply to all exchanges.
        
        Returns:
            List of base rule dictionaries (empty list if file is empty or doesn't exist)
            
        Raises:
            ValueError: If base_rules file exists but contains invalid content
        """
        if self._use_modular:
            # Load from modular structure
            base_file = self.rules_dir / "base.yaml"
            if not base_file.exists():
                # base.yaml doesn't exist, return empty list
                return []
            
            rules = self._load_yaml_file(base_file, allow_empty=True)
            if rules is None:
                # File exists but is empty (only comments), return empty list
                return []
            if not isinstance(rules, list):
                raise ValueError("base.yaml must contain a list of rules")
            return rules
        else:
            # Load from single file (backward compatibility)
            config = self._load_config()
            
            if 'base_rules' not in config:
                raise ValueError("YAML file must contain a 'base_rules' key")
            
            if not isinstance(config['base_rules'], list):
                raise ValueError("'base_rules' must be a list")
            
            return config['base_rules']
    
    def load_exchange_rules(self, exchange):
        """
        Load exchange-specific validation rules from root exchanges folder.
        
        Args:
            exchange: Exchange code (e.g., 'XNSE', 'XHKG')
            
        Returns:
            List of exchange-specific rule dictionaries, or empty list if file doesn't exist
        """
        if self._use_modular:
            # Load from modular structure: rules/exchanges/{exchange}.yaml
            exchange_file = self.rules_dir / "exchanges" / f"{exchange.lower()}.yaml"
            if not exchange_file.exists():
                # File doesn't exist, return empty list (not an error)
                return []
            rules = self._load_yaml_file(exchange_file, allow_empty=True)
            if rules is None:
                return []
            if not isinstance(rules, list):
                raise ValueError(f"Exchange file '{exchange_file}' must contain a list of rules")
            return rules
        else:
            # Load from single file (backward compatibility)
            config = self._load_config()
            
            if 'exchanges' not in config:
                return []  # No exchange-specific rules defined
            
            if not isinstance(config['exchanges'], dict):
                raise ValueError("'exchanges' must be a dictionary")
            
            if exchange not in config['exchanges']:
                raise ValueError(
                    f"Exchange '{exchange}' not found in configuration. "
                    f"Available exchanges: {list(config['exchanges'].keys())}"
                )
            
            exchange_rules = config['exchanges'][exchange]
            
            if not isinstance(exchange_rules, list):
                raise ValueError(f"Rules for exchange '{exchange}' must be a list")
            
            return exchange_rules
    
    def get_available_exchanges(self):
        """
        Get list of available exchange codes.
        
        Returns:
            List of exchange codes
        """
        if self._use_modular:
            # Load from modular structure
            exchanges_dir = self.rules_dir / "exchanges"
            if not exchanges_dir.exists():
                return []
            
            exchanges = []
            for file in exchanges_dir.glob("*.yaml"):
                # Extract exchange code from filename (e.g., hkg.yaml -> HKG)
                exchange_code = file.stem.upper()
                exchanges.append(exchange_code)
            
            return sorted(exchanges)
        else:
            # Load from single file (backward compatibility)
            config = self._load_config()
            
            if 'exchanges' not in config:
                return []
            
            if not isinstance(config['exchanges'], dict):
                return []
            
            return list(config['exchanges'].keys())
    
    def _load_custom_rule_file(self, rule_name, product_type=None, exchange=None):
        """
        Load a custom rule file from modular structure.
        
        Priority order (highest to lowest):
        1. Exchange-level custom.yaml (overrides product type rules)
        2. Exchange-level combined.yaml
        3. Product type custom.yaml
        4. Product type combined.yaml
        5. Root custom.yaml
        6. Root combined.yaml
        7. Backward compatibility paths
        
        Args:
            rule_name: Name of the custom rule set to load
            product_type: Optional product type (e.g., 'stock', 'future', 'options')
            exchange: Optional exchange code (e.g., 'XNSE', 'XHKG')
            
        Returns:
            Custom rule set dictionary or None if not found
        """
        # Try exchange-level custom.yaml first (highest priority - overrides product type)
        if exchange and product_type:
            normalized_type = self._normalize_product_type(product_type)
            exchange_custom_yaml_file = (
                self.rules_dir / normalized_type / "exchanges" / exchange.lower() / "custom.yaml"
            )
            if exchange_custom_yaml_file.exists():
                custom_config = self._load_yaml_file(exchange_custom_yaml_file, allow_empty=True)
                if custom_config and isinstance(custom_config, dict) and rule_name in custom_config:
                    return custom_config[rule_name]
            
            # Try exchange-level combined.yaml
            exchange_combined_yaml_file = (
                self.rules_dir / normalized_type / "exchanges" / exchange.lower() / "combined.yaml"
            )
            if exchange_combined_yaml_file.exists():
                combined_config = self._load_yaml_file(exchange_combined_yaml_file, allow_empty=True)
                if combined_config and isinstance(combined_config, dict) and rule_name in combined_config:
                    return combined_config[rule_name]
        
        # Try product type-specific custom.yaml file (if product_type is specified)
        if product_type:
            normalized_type = self._normalize_product_type(product_type)
            product_custom_yaml_file = self.rules_dir / normalized_type / "custom.yaml"
            if product_custom_yaml_file.exists():
                custom_config = self._load_yaml_file(product_custom_yaml_file, allow_empty=True)
                if custom_config and isinstance(custom_config, dict) and rule_name in custom_config:
                    return custom_config[rule_name]
            
            # Try product type-specific combined.yaml file
            product_combined_yaml_file = self.rules_dir / normalized_type / "combined.yaml"
            if product_combined_yaml_file.exists():
                combined_config = self._load_yaml_file(product_combined_yaml_file, allow_empty=True)
                if combined_config and isinstance(combined_config, dict) and rule_name in combined_config:
                    return combined_config[rule_name]
        
        # Try custom.yaml file (root level)
        custom_yaml_file = self.rules_dir / "custom.yaml"
        if custom_yaml_file.exists():
            custom_config = self._load_yaml_file(custom_yaml_file, allow_empty=True)
            if custom_config and isinstance(custom_config, dict) and rule_name in custom_config:
                return custom_config[rule_name]
        
        # Try combined.yaml file (root level)
        combined_yaml_file = self.rules_dir / "combined.yaml"
        if combined_yaml_file.exists():
            combined_config = self._load_yaml_file(combined_yaml_file, allow_empty=True)
            if combined_config and isinstance(combined_config, dict) and rule_name in combined_config:
                return combined_config[rule_name]
        
        # Try custom/ directory (for backward compatibility)
        custom_file = self.rules_dir / "custom" / f"{rule_name}.yaml"
        if custom_file.exists():
            return self._load_yaml_file(custom_file)
        
        # Try custom/combined/ directory (for backward compatibility)
        combined_file = self.rules_dir / "custom" / "combined" / f"{rule_name}.yaml"
        if combined_file.exists():
            return self._load_yaml_file(combined_file)
        
        return None
    
    def _resolve_custom_rule_set(self, rule_name, visited=None, product_type=None, exchange=None):
        """
        Recursively resolve a custom rule set, handling includes and preventing circular references.
        
        Args:
            rule_name: Name of the custom rule set to resolve
            visited: Set of rule names already visited (to prevent circular references)
            product_type: Optional product type to load product type-specific custom rules
            exchange: Optional exchange code to load exchange-specific custom rules (overrides product type rules)
            
        Returns:
            List of resolved rule dictionaries
            
        Raises:
            ValueError: If rule not found or circular reference detected
        """
        if visited is None:
            visited = set()
        
        if rule_name in visited:
            raise ValueError(f"Circular reference detected in custom rule set '{rule_name}'")
        
        visited.add(rule_name)
        
        # Try modular structure first
        if self._use_modular:
            rule_set = self._load_custom_rule_file(rule_name, product_type=product_type, exchange=exchange)
            if rule_set is None:
                # Include both custom and combined rules in the error message
                available_custom = self.get_available_custom_rule_sets(product_type=product_type, exchange=exchange)
                available_combined = self.get_available_combined_rule_sets(product_type=product_type, exchange=exchange)
                all_available = sorted(set(available_custom + available_combined))
                raise ValueError(
                    f"Custom rule set '{rule_name}' not found. "
                    f"Available custom rule sets: {available_custom}. "
                    f"Available combined rule sets: {available_combined}. "
                    f"All available: {all_available}"
                )
        else:
            # Load from single file (backward compatibility)
            config = self._load_config()
            
            if 'custom_rules' not in config:
                raise ValueError("No custom_rules section found in configuration")
            
            if rule_name not in config['custom_rules']:
                raise ValueError(
                    f"Custom rule set '{rule_name}' not found. "
                    f"Available custom rule sets: {list(config['custom_rules'].keys())}"
                )
            
            rule_set = config['custom_rules'][rule_name]
        
        # Handle rule set with 'include' key (combining other rules)
        if isinstance(rule_set, dict) and 'include' in rule_set:
            rules = []
            
            # Resolve included rule sets
            if isinstance(rule_set['include'], list):
                for included_rule_name in rule_set['include']:
                    try:
                        included_rules = self._resolve_custom_rule_set(
                            included_rule_name, visited.copy(), product_type=product_type, exchange=exchange
                        )
                        rules.extend(included_rules)
                    except ValueError as e:
                        # Provide more context about which included rule failed
                        raise ValueError(
                            f"Error resolving included rule '{included_rule_name}' in '{rule_name}': {str(e)}"
                        )
            elif isinstance(rule_set['include'], str):
                try:
                    included_rules = self._resolve_custom_rule_set(
                        rule_set['include'], visited.copy(), product_type=product_type, exchange=exchange
                    )
                    rules.extend(included_rules)
                except ValueError as e:
                    # Provide more context about which included rule failed
                    raise ValueError(
                        f"Error resolving included rule '{rule_set['include']}' in '{rule_name}': {str(e)}"
                    )
            
            # Add any additional direct rules after includes
            # Look for list items that are not the 'include' key
            for key, value in rule_set.items():
                if key != 'include':
                    if isinstance(value, list):
                        # This handles the case where rules are defined as a list under a key
                        rules.extend(value)
                    elif isinstance(value, dict) and 'type' in value:
                        # This handles individual rule dictionaries
                        rules.append(value)
            
            return rules
        
        # Handle regular list of rules
        if not isinstance(rule_set, list):
            raise ValueError(f"Custom rule set '{rule_name}' must be a list or dict with 'include' key")
        
        return rule_set.copy()
    
    def load_custom_rules_from_yaml(self, custom_rule_names=None, product_type=None, exchange=None):
        """
        Load custom rules from YAML configuration by name(s).
        Supports combining rules using 'include' key in YAML.
        Exchange-level custom rules override product type custom rules when they have the same name.
        
        Args:
            custom_rule_names: Optional list of custom rule set names to load
            product_type: Optional product type to load product type-specific custom rules
            exchange: Optional exchange code to load exchange-specific custom rules (overrides product type rules)
            
        Returns:
            List of custom rule dictionaries (resolved and flattened)
            
        Raises:
            ValueError: If custom rule name not found or circular reference detected
        """
        if custom_rule_names is None or len(custom_rule_names) == 0:
            return []
        
        rules = []
        for rule_name in custom_rule_names:
            resolved_rules = self._resolve_custom_rule_set(
                rule_name, product_type=product_type, exchange=exchange
            )
            rules.extend(resolved_rules)
        
        return rules
    
    def get_available_custom_rule_sets(self, product_type=None, exchange=None):
        """
        Get list of available custom rule set names.
        Includes exchange-level custom rules if exchange is provided.
        
        Args:
            product_type: Optional product type to get product type-specific custom rule sets
            exchange: Optional exchange code to get exchange-specific custom rule sets
            
        Returns:
            List of custom rule set names
        """
        if self._use_modular:
            rule_sets = []
            
            # Get rules from exchange-level custom.yaml first (highest priority)
            if exchange and product_type:
                normalized_type = self._normalize_product_type(product_type)
                exchange_custom_yaml_file = (
                    self.rules_dir / normalized_type / "exchanges" / exchange.lower() / "custom.yaml"
                )
                if exchange_custom_yaml_file.exists():
                    custom_config = self._load_yaml_file(exchange_custom_yaml_file, allow_empty=True)
                    if isinstance(custom_config, dict):
                        rule_sets.extend(custom_config.keys())
                
                exchange_combined_yaml_file = (
                    self.rules_dir / normalized_type / "exchanges" / exchange.lower() / "combined.yaml"
                )
                if exchange_combined_yaml_file.exists():
                    combined_config = self._load_yaml_file(exchange_combined_yaml_file, allow_empty=True)
                    if isinstance(combined_config, dict):
                        rule_sets.extend(combined_config.keys())
            
            # Get rules from product type-specific custom.yaml file (if product_type is specified)
            if product_type:
                normalized_type = self._normalize_product_type(product_type)
                product_custom_yaml_file = self.rules_dir / normalized_type / "custom.yaml"
                if product_custom_yaml_file.exists():
                    custom_config = self._load_yaml_file(product_custom_yaml_file, allow_empty=True)
                    if isinstance(custom_config, dict):
                        rule_sets.extend(custom_config.keys())
                
                product_combined_yaml_file = self.rules_dir / normalized_type / "combined.yaml"
                if product_combined_yaml_file.exists():
                    combined_config = self._load_yaml_file(product_combined_yaml_file, allow_empty=True)
                    if isinstance(combined_config, dict):
                        rule_sets.extend(combined_config.keys())
            
            # Get rules from custom.yaml file (root level)
            custom_yaml_file = self.rules_dir / "custom.yaml"
            if custom_yaml_file.exists():
                custom_config = self._load_yaml_file(custom_yaml_file, allow_empty=True)
                if isinstance(custom_config, dict):
                    rule_sets.extend(custom_config.keys())
            
            # Get rules from combined.yaml file (root level)
            combined_yaml_file = self.rules_dir / "combined.yaml"
            if combined_yaml_file.exists():
                combined_config = self._load_yaml_file(combined_yaml_file, allow_empty=True)
                if isinstance(combined_config, dict):
                    rule_sets.extend(combined_config.keys())
            
            # Get rules from custom/ directory (for backward compatibility)
            custom_dir = self.rules_dir / "custom"
            if custom_dir.exists():
                for file in custom_dir.glob("*.yaml"):
                    rule_sets.append(file.stem)
                
                # Get rules from custom/combined/ directory (for backward compatibility)
                combined_dir = custom_dir / "combined"
                if combined_dir.exists():
                    for file in combined_dir.glob("*.yaml"):
                        rule_sets.append(file.stem)
            
            return sorted(set(rule_sets))  # Remove duplicates
        else:
            # Load from single file (backward compatibility)
            config = self._load_config()
            
            if 'custom_rules' not in config:
                return []
            
            if not isinstance(config['custom_rules'], dict):
                return []
            
            return list(config['custom_rules'].keys())
    
    def get_available_combined_rule_sets(self, product_type=None, exchange=None):
        """
        Get list of available combined rule set names only (from combined.yaml files).
        Includes exchange-level combined rules if exchange is provided.
        
        Args:
            product_type: Optional product type to get product type-specific combined rule sets
            exchange: Optional exchange code to get exchange-specific combined rule sets
            
        Returns:
            List of combined rule set names
        """
        if self._use_modular:
            combined_rule_sets = []
            
            # Get rules from exchange-level combined.yaml first (highest priority)
            if exchange and product_type:
                normalized_type = self._normalize_product_type(product_type)
                exchange_combined_yaml_file = (
                    self.rules_dir / normalized_type / "exchanges" / exchange.lower() / "combined.yaml"
                )
                if exchange_combined_yaml_file.exists():
                    combined_config = self._load_yaml_file(exchange_combined_yaml_file, allow_empty=True)
                    if isinstance(combined_config, dict):
                        combined_rule_sets.extend(combined_config.keys())
            
            # Get rules from product type-specific combined.yaml file (if product_type is specified)
            if product_type:
                normalized_type = self._normalize_product_type(product_type)
                product_combined_yaml_file = self.rules_dir / normalized_type / "combined.yaml"
                if product_combined_yaml_file.exists():
                    combined_config = self._load_yaml_file(product_combined_yaml_file, allow_empty=True)
                    if isinstance(combined_config, dict):
                        combined_rule_sets.extend(combined_config.keys())
            
            # Get rules from combined.yaml file (root level)
            combined_yaml_file = self.rules_dir / "combined.yaml"
            if combined_yaml_file.exists():
                combined_config = self._load_yaml_file(combined_yaml_file, allow_empty=True)
                if isinstance(combined_config, dict):
                    combined_rule_sets.extend(combined_config.keys())
            
            # Get rules from custom/combined/ directory (for backward compatibility)
            combined_dir = self.rules_dir / "custom" / "combined"
            if combined_dir.exists():
                for file in combined_dir.glob("*.yaml"):
                    combined_rule_sets.append(file.stem)
            
            return sorted(set(combined_rule_sets))  # Remove duplicates
        else:
            # Load from single file (backward compatibility)
            config = self._load_config()
            
            if 'combined_rules' not in config:
                return []
            
            if not isinstance(config['combined_rules'], dict):
                return []
            
            return list(config['combined_rules'].keys())
    
    def load_custom_rules(self, custom_rules=None):
        """
        Load custom rules (programmatically provided).
        
        Args:
            custom_rules: Optional list of custom rule dictionaries
            
        Returns:
            List of custom rule dictionaries
        """
        if custom_rules is None:
            return []
        
        if not isinstance(custom_rules, list):
            raise ValueError("custom_rules must be a list")
        
        return custom_rules
    
    def _normalize_product_type(self, product_type):
        """
        Normalize product type to match folder names.
        Converts 'stocks' -> 'stock', 'option' -> 'options', etc.
        """
        if not product_type:
            return None
        normalized = product_type.lower().strip()
        # Handle common variations
        if normalized == 'stocks':
            return 'stock'
        if normalized == 'option':
            return 'options'
        return normalized
    
    def load_product_type_rules(self, product_type):
        """
        Load product type-specific base rules (e.g., stock, future, options).
        
        Args:
            product_type: Product type name (e.g., 'stock', 'stocks', 'future', 'option', 'options')
            
        Returns:
            List of product type-specific rule dictionaries, or empty list if not found or empty
        """
        if not product_type:
            return []
        
        normalized_type = self._normalize_product_type(product_type)
        product_type_file = self.rules_dir / normalized_type / "base.yaml"
        if product_type_file.exists():
            rules = self._load_yaml_file(product_type_file, allow_empty=True)
            if rules is None:
                # File exists but is empty (only comments), return empty list
                return []
            if not isinstance(rules, list):
                raise ValueError(f"Product type file '{product_type_file}' must contain a list of rules")
            return rules
        return []
    
    def load_product_type_exchange_rules(self, product_type, exchange):
        """
        Load product type-specific exchange rules (e.g., stock/exchanges/xnse/exchange.yaml).
        
        Args:
            product_type: Product type name (e.g., 'stock', 'stocks', 'future', 'option', 'options')
            exchange: Exchange code (e.g., 'XNSE', 'XHKG')
            
        Returns:
            List of product type-specific exchange rule dictionaries, or empty list if not found or empty
        """
        if not product_type or not exchange:
            return []
        
        normalized_type = self._normalize_product_type(product_type)
        # New structure: stock/exchanges/xhkg/exchange.yaml
        product_type_exchange_file = (
            self.rules_dir / normalized_type / "exchanges" / exchange.lower() / "exchange.yaml"
        )
        if product_type_exchange_file.exists():
            rules = self._load_yaml_file(product_type_exchange_file, allow_empty=True)
            if rules is None:
                # File exists but is empty (only comments), return empty list
                return []
            if not isinstance(rules, list):
                raise ValueError(f"Product type exchange file '{product_type_exchange_file}' must contain a list of rules")
            return rules
        
        # Fallback to old structure for backward compatibility: stock/exchanges/xhkg.yaml
        old_product_type_exchange_file = self.rules_dir / normalized_type / "exchanges" / f"{exchange.lower()}.yaml"
        if old_product_type_exchange_file.exists():
            rules = self._load_yaml_file(old_product_type_exchange_file, allow_empty=True)
            if rules is None:
                return []
            if not isinstance(rules, list):
                raise ValueError(f"Product type exchange file '{old_product_type_exchange_file}' must contain a list of rules")
            return rules
        
        return []
    
    def load_combined_rules(self, exchange=None, custom_rules=None, custom_rule_names=None, product_type=None):
        """
        Load combined rules: base rules + product type rules + exchange-specific rules + custom rules.
        
        Args:
            exchange: Optional exchange code. If provided, includes exchange-specific rules.
            custom_rules: Optional list of custom rule dictionaries (programmatic).
            custom_rule_names: Optional list of custom rule set names from YAML.
            product_type: Optional product type (e.g., 'stock', 'future', 'options'). If provided, includes product type-specific rules.
            
        Returns:
            Combined list of rule dictionaries in order: 
            base -> product_type/base -> exchange -> product_type/exchange -> custom (YAML) -> custom (programmatic)
        """
        rules = self.load_base_rules()
        logger.debug("Loaded %d base rules", len(rules))

        if product_type:
            try:
                product_type_rules = self.load_product_type_rules(product_type)
                rules.extend(product_type_rules)
                logger.debug("Loaded %d product-type rules for %s", len(product_type_rules), product_type)
            except (ValueError, FileNotFoundError):
                pass

        if exchange:
            exchange_rules = self.load_exchange_rules(exchange)
            rules.extend(exchange_rules)
            logger.debug("Loaded %d root-exchange rules for %s", len(exchange_rules), exchange)

        if product_type and exchange:
            try:
                product_type_exchange_rules = self.load_product_type_exchange_rules(product_type, exchange)
                rules.extend(product_type_exchange_rules)
                logger.debug("Loaded %d product-type/exchange rules for %s/%s",
                             len(product_type_exchange_rules), product_type, exchange)
            except (ValueError, FileNotFoundError):
                pass

        if custom_rule_names:
            yaml_custom_rules = self.load_custom_rules_from_yaml(
                custom_rule_names, product_type=product_type, exchange=exchange
            )
            rules.extend(yaml_custom_rules)
            logger.debug("Loaded %d custom YAML rules (%s)", len(yaml_custom_rules), custom_rule_names)

        if custom_rules:
            programmatic_custom = self.load_custom_rules(custom_rules)
            rules.extend(programmatic_custom)
            logger.debug("Loaded %d programmatic custom rules", len(programmatic_custom))

        logger.info("Combined rules for %s/%s: %d total", product_type or "-", exchange or "-", len(rules))
        return rules
    
    def reload_rules(self):
        """Force reload configuration from file (useful if file was updated)."""
        self._config = None
    
    # Backward compatibility method
    def load_rules(self):
        """
        Load rules (backward compatibility - returns base rules only).
        
        Returns:
            List of base rule dictionaries
        """
        return self.load_base_rules()

