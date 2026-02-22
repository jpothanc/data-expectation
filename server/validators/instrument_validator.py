"""Great Expectations validator for instrument data."""

import logging
import time

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd
from .rule_loader import RuleLoader

logger = logging.getLogger(__name__)


class InstrumentValidator:
    """Handles Great Expectations validation for instrument data."""
    
    def __init__(self, context_name="instruments_context", rules_dir=None, exchange=None, product_type=None):
        """
        Initialize the instrument validator.
        
        Args:
            context_name: Name for the Great Expectations context
            rules_dir: Optional path to rules directory. If None, reads from config.json or defaults to "config/rules"
            exchange: Optional exchange code (e.g., 'HKG', 'NYSE') to apply exchange-specific rules
            product_type: Optional product type (e.g., 'stock', 'future', 'options') to apply product type-specific rules
        """
        if rules_dir is None:
            try:
                from config.config_service import ConfigService
                config_service = ConfigService()
                rules_dir = config_service.get_rules_dir()
            except Exception:
                rules_dir = "config/rules"

        t0 = time.perf_counter()
        context_errors = []
        try:
            self.context = gx.get_context(mode="ephemeral")
        except Exception as e1:
            context_errors.append(f"Ephemeral mode failed: {e1}")
            try:
                self.context = gx.get_context()
            except Exception as e2:
                context_errors.append(f"Regular context failed: {e2}")
                raise Exception(
                    f"Failed to initialize Great Expectations context. "
                    f"Errors: {'; '.join(context_errors)}. "
                    "This may be due to YAML parsing issues or file handle conflicts."
                )
        logger.debug("[TIMING] GE context init completed in %.1f ms", (time.perf_counter() - t0) * 1000)
        
        self.context_name = context_name
        self.exchange = exchange
        self.product_type = product_type
        self.rule_loader = RuleLoader(rules_dir=rules_dir)
        
        try:
            self._setup_data_source()
        except Exception as e:
            raise Exception(f"Failed to setup data source: {str(e)}")
    
    def _setup_data_source(self):
        """Setup the pandas data source for validation.

        Uses unique UUIDs per call to avoid name conflicts under concurrent load.
        Retries up to 3 times when GE's internal BytesIO buffer is closed prematurely
        (a known transient error in ephemeral mode under parallel requests).
        """
        import uuid

        _TRANSIENT_MSGS = ("i/o operation on closed file", "closed file")
        _YAML_MSGS = ("nodeevent", "documentstartevent")
        MAX_RETRIES = 3

        last_exc: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            uid = uuid.uuid4().hex[:10]
            try:
                self.data_source = self.context.data_sources.add_pandas(f"src_{uid}")
                self.data_asset = self.data_source.add_dataframe_asset(name=f"asset_{uid}")
                self.batch_definition = self.data_asset.add_batch_definition_whole_dataframe(f"batch_{uid}")
                return  # success

            except Exception as exc:
                msg_lower = str(exc).lower()
                last_exc = exc

                if any(tok in msg_lower for tok in _TRANSIENT_MSGS):
                    # GE ephemeral BytesIO buffer was closed under concurrent load.
                    # Recreate the context and retry — this resolves itself on a fresh context.
                    logger.warning(
                        "[GE] Transient 'closed file' error on attempt %d/%d — recreating context",
                        attempt, MAX_RETRIES,
                    )
                    try:
                        self.context = gx.get_context(mode="ephemeral")
                    except Exception as ctx_err:
                        logger.warning("[GE] Failed to recreate context: %s", ctx_err)
                    continue  # retry with fresh context + new UUID

                if any(tok in msg_lower for tok in _YAML_MSGS):
                    # YAML serialisation glitch inside GE — same remedy: fresh context
                    logger.warning("[GE] YAML parse error on attempt %d/%d — recreating context", attempt, MAX_RETRIES)
                    try:
                        self.context = gx.get_context(mode="ephemeral")
                    except Exception:
                        pass
                    continue

                # Any other error is not transient — surface immediately
                raise Exception(f"Failed to setup data source: {exc}") from exc

        raise Exception(
            f"Failed to setup data source after {MAX_RETRIES} retries "
            f"(transient GE BytesIO error): {last_exc}"
        )
    
    def _expand_rules_with_multiple_columns(self, rules):
        """
        Expand rules that have comma-separated columns into multiple rules.
        
        Args:
            rules: List of rule dictionaries
            
        Returns:
            List of expanded rule dictionaries (one per column)
        """
        expanded_rules = []
        
        for rule in rules:
            if not isinstance(rule, dict) or 'column' not in rule:
                expanded_rules.append(rule)
                continue
            
            column = rule.get('column', '')
            
            # Check if column contains comma-separated values
            if ',' in column:
                # Split by comma and strip whitespace
                columns = [col.strip() for col in column.split(',')]
                
                # Create a rule for each column
                for col in columns:
                    if col:  # Skip empty columns
                        expanded_rule = rule.copy()
                        expanded_rule['column'] = col
                        expanded_rules.append(expanded_rule)
            else:
                # Single column, keep as is
                expanded_rules.append(rule)
        
        return expanded_rules
    
    def _create_expectation_from_rule(self, rule: dict):
        """
        Create a Great Expectations expectation object from a rule dictionary.
        
        Args:
            rule: Dictionary containing expectation type and parameters
            
        Returns:
            Expectation object
            
        Raises:
            ValueError: If rule is invalid or missing required fields
        """
        if not isinstance(rule, dict):
            raise ValueError(f"Rule must be a dictionary, got {type(rule)}")
        
        if 'type' not in rule:
            raise ValueError("Rule must contain a 'type' field")
        
        expectation_type = rule['type']
        column = rule.get('column')
        
        if not column:
            raise ValueError(f"Rule must contain a 'column' field: {rule}")
        
        # Map expectation types to their classes
        expectation_map = {
            'ExpectColumnValuesToBeUnique': gxe.ExpectColumnValuesToBeUnique,
            'ExpectColumnValuesToNotBeNull': gxe.ExpectColumnValuesToNotBeNull,
            'ExpectColumnValuesToBeInSet': gxe.ExpectColumnValuesToBeInSet,
            'ExpectColumnValuesToBeBetween': gxe.ExpectColumnValuesToBeBetween,
            'ExpectColumnValuesToMatchRegex': gxe.ExpectColumnValuesToMatchRegex,
        }
        
        if expectation_type not in expectation_map:
            raise ValueError(
                f"Unknown expectation type: {expectation_type}. "
                f"Supported types: {list(expectation_map.keys())}"
            )
        
        expectation_class = expectation_map[expectation_type]
        
        # Build parameters for the expectation
        params = {'column': column}
        
        # Add additional parameters based on expectation type
        if 'value_set' in rule:
            params['value_set'] = rule['value_set']
        if 'min_value' in rule:
            params['min_value'] = rule['min_value']
        if 'max_value' in rule:
            params['max_value'] = rule['max_value']
        if 'regex' in rule:
            params['regex'] = rule['regex']

        # Support conditional rules: only validate rows where condition is true.
        # Uses pandas query syntax, e.g. condition: "SecurityType == 'Bond'"
        if 'condition' in rule and rule['condition']:
            params['row_condition'] = rule['condition']
            params['condition_parser'] = 'pandas'
        
        try:
            return expectation_class(**params)
        except Exception as e:
            raise ValueError(f"Failed to create expectation {expectation_type}: {e}")
    
    def create_expectation_suite(self, suite_name="instruments_suite", exchange=None, custom_rules=None, custom_rule_names=None, product_type=None):
        """
        Create and configure the expectation suite with validation rules.
        
        Args:
            suite_name: Name for the expectation suite
            exchange: Optional exchange code. If provided, applies exchange-specific rules.
                     If None, uses the exchange from initialization.
            custom_rules: Optional list of custom rule dictionaries (programmatic).
            custom_rule_names: Optional list of custom rule set names from YAML.
            product_type: Optional product type. If provided, applies product type-specific rules.
                         If None, uses the product_type from initialization.
                             Rules are applied in order: base -> product_type/base -> exchange -> product_type/exchange -> custom (YAML) -> custom (programmatic)
            
        Returns:
            ExpectationSuite: The configured expectation suite
        """
        # Create suite, handling case where it might already exist
        # Generate unique name if suite already exists to avoid conflicts
        unique_suite_name = suite_name
        counter = 1
        while True:
            try:
                suite = self.context.suites.add(gx.ExpectationSuite(name=unique_suite_name))
                break
            except Exception:
                # Suite with this name already exists, try with unique name
                unique_suite_name = f"{suite_name}_{counter}"
                counter += 1
                if counter > 1000:  # Safety limit
                    raise ValueError(f"Could not create unique suite name after {counter} attempts")
        
        # Use exchange parameter if provided, otherwise use instance exchange
        exchange_to_use = exchange if exchange is not None else self.exchange
        # Use product_type parameter if provided, otherwise use instance product_type
        product_type_to_use = product_type if product_type is not None else self.product_type
        
        # Load combined rules: base + product_type/base + exchange + product_type/exchange + custom (YAML) + custom (programmatic)
        rules = self.rule_loader.load_combined_rules(
            exchange=exchange_to_use,
            custom_rules=custom_rules,
            custom_rule_names=custom_rule_names,
            product_type=product_type_to_use
        )
        
        # Expand rules with comma-separated columns
        expanded_rules = self._expand_rules_with_multiple_columns(rules)
        
        # Add each rule as an expectation
        for rule in expanded_rules:
            expectation = self._create_expectation_from_rule(rule)
            suite.add_expectation(expectation)
        
        return suite
    
    def create_expectation_suite_custom_only(self, suite_name="instruments_suite", custom_rules=None, custom_rule_names=None, exchange=None, product_type=None):
        """
        Create expectation suite with ONLY custom rules (no base or exchange rules).
        
        Args:
            suite_name: Name for the expectation suite
            custom_rules: Optional list of custom rule dictionaries (programmatic).
            custom_rule_names: Optional list of custom rule set names from YAML.
            exchange: Optional exchange code. If provided, loads exchange-specific custom rules.
                     If None, uses the exchange from initialization.
            product_type: Optional product type. If provided, loads product type-specific custom rules.
                         If None, uses the product_type from initialization.
            
        Returns:
            ExpectationSuite: The configured expectation suite with only custom rules
        """
        # Create suite, handling case where it might already exist
        unique_suite_name = suite_name
        counter = 1
        while True:
            try:
                suite = self.context.suites.add(gx.ExpectationSuite(name=unique_suite_name))
                break
            except Exception:
                unique_suite_name = f"{suite_name}_{counter}"
                counter += 1
                if counter > 1000:
                    raise ValueError(f"Could not create unique suite name after {counter} attempts")
        
        rules = []
        
        # Use product_type parameter if provided, otherwise use instance product_type
        product_type_to_use = product_type if product_type is not None else self.product_type
        
        # Load custom rules from YAML by name (exchange-level rules override product type rules)
        if custom_rule_names:
            # Use exchange parameter if provided, otherwise use instance exchange
            exchange_to_use = exchange if exchange is not None else self.exchange
            yaml_custom_rules = self.rule_loader.load_custom_rules_from_yaml(
                custom_rule_names, product_type=product_type_to_use, exchange=exchange_to_use
            )
            rules.extend(yaml_custom_rules)
        
        # Load programmatic custom rules
        if custom_rules:
            programmatic_custom = self.rule_loader.load_custom_rules(custom_rules)
            rules.extend(programmatic_custom)
        
        # Expand rules with comma-separated columns
        expanded_rules = self._expand_rules_with_multiple_columns(rules)
        
        # Add each rule as an expectation
        for rule in expanded_rules:
            expectation = self._create_expectation_from_rule(rule)
            suite.add_expectation(expectation)
        
        return suite
    
    def validate(self, df, suite_name="instruments_suite", exchange=None, custom_rules=None, custom_rule_names=None, product_type=None):
        """
        Validate a dataframe against the expectation suite.
        
        Args:
            df: The dataframe to validate
            suite_name: Name of the expectation suite to use
            exchange: Optional exchange code. If provided, applies exchange-specific rules.
                     If None, uses the exchange from initialization.
            custom_rules: Optional list of custom rule dictionaries (programmatic).
            custom_rule_names: Optional list of custom rule set names from YAML.
            product_type: Optional product type. If provided, applies product type-specific rules.
                         If None, uses the product_type from initialization.
                             Rules are applied in order: base -> product_type/base -> exchange -> product_type/exchange -> custom (YAML) -> custom (programmatic)
            
        Returns:
            ValidationResult: The validation results
        """
        t0 = time.perf_counter()
        suite = self.create_expectation_suite(
            suite_name,
            exchange=exchange,
            custom_rules=custom_rules,
            custom_rule_names=custom_rule_names,
            product_type=product_type,
        )
        logger.debug("[TIMING] create_expectation_suite for %s/%s: %.1f ms",
                     product_type or self.product_type, exchange or self.exchange,
                     (time.perf_counter() - t0) * 1000)

        t1 = time.perf_counter()
        batch = self.batch_definition.get_batch(batch_parameters={"dataframe": df})
        results = batch.validate(suite)
        logger.info("[TIMING] GE batch.validate for %s/%s: %.1f ms (%d expectations)",
                    product_type or self.product_type, exchange or self.exchange,
                    (time.perf_counter() - t1) * 1000, len(suite.expectations))
        return results
    
    def validate_custom_only(self, df, suite_name="instruments_suite", custom_rules=None, custom_rule_names=None, exchange=None, product_type=None):
        """
        Validate a dataframe against ONLY custom rules (no base or exchange rules).
        
        Args:
            df: The dataframe to validate
            suite_name: Name of the expectation suite to use
            custom_rules: Optional list of custom rule dictionaries (programmatic).
            custom_rule_names: Optional list of custom rule set names from YAML.
            exchange: Optional exchange code. If provided, loads exchange-specific custom rules.
                     If None, uses the exchange from initialization.
            product_type: Optional product type. If provided, loads product type-specific custom rules.
                         If None, uses the product_type from initialization.
            
        Returns:
            ValidationResult: The validation results
        """
        suite = self.create_expectation_suite_custom_only(
            suite_name, 
            custom_rules=custom_rules,
            custom_rule_names=custom_rule_names,
            exchange=exchange,
            product_type=product_type
        )
        batch = self.batch_definition.get_batch(batch_parameters={"dataframe": df})
        results = batch.validate(suite)
        return results

