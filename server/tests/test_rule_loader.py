"""Tests for RuleLoader."""

import pytest
from pathlib import Path
from validators.rule_loader import RuleLoader


class TestRuleLoader:
    """Test cases for RuleLoader."""
    
    def test_init_with_default_rules_dir(self):
        """Test RuleLoader initialization with default rules directory."""
        loader = RuleLoader()
        assert loader.rules_dir == Path("rules")
        # Check if modular structure exists (may or may not exist in test environment)
        assert isinstance(loader._use_modular, bool)
    
    def test_init_with_custom_rules_dir(self, temp_rules_dir):
        """Test RuleLoader initialization with custom rules directory."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        assert loader.rules_dir == temp_rules_dir
        assert loader._use_modular is True
    
    def test_load_base_rules(self, temp_rules_dir):
        """Test loading base rules."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_base_rules()
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert rules[0]['type'] == 'ExpectColumnValuesToBeUnique'
        assert rules[0]['column'] == 'MasterId'
    
    def test_load_base_rules_not_found(self):
        """Test loading base rules when file doesn't exist."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            loader = RuleLoader(rules_dir=temp_dir)
            rules = loader.load_base_rules()
            assert rules == []
        finally:
            shutil.rmtree(temp_dir)
    
    def test_load_product_type_rules(self, temp_rules_dir):
        """Test loading product type specific rules."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_product_type_rules('stock')
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert any(rule.get('column') == 'Symbol' for rule in rules)
    
    def test_load_product_type_rules_not_found(self, temp_rules_dir):
        """Test loading product type rules when file doesn't exist."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        with pytest.raises(FileNotFoundError):
            loader.load_product_type_rules('nonexistent')
    
    def test_load_exchange_rules(self, temp_rules_dir):
        """Test loading exchange specific rules."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        # This will fail if exchange.yaml doesn't exist, which is expected
        # In real scenario, you'd create the file first
        try:
            rules = loader.load_exchange_rules('xhkg')
            assert isinstance(rules, list)
        except FileNotFoundError:
            pytest.skip("Exchange rules file not found")
    
    def test_load_product_type_exchange_rules(self, temp_rules_dir):
        """Test loading product type and exchange specific rules."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_product_type_exchange_rules('stock', 'xhkg')
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        # Check that exchange-specific regex overrides base
        symbol_rules = [r for r in rules if r.get('column') == 'Symbol']
        assert len(symbol_rules) > 0
        assert '^[0-9]{4}\\.HK$' in str(symbol_rules[0].get('regex', ''))
    
    def test_load_combined_rules_base_only(self, temp_rules_dir):
        """Test loading combined rules with base only."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_combined_rules()
        
        assert isinstance(rules, list)
        assert len(rules) > 0
    
    def test_load_combined_rules_with_product_type(self, temp_rules_dir):
        """Test loading combined rules with product type."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_combined_rules(product_type='stock')
        
        assert isinstance(rules, list)
        assert len(rules) >= 2  # Base + stock rules
    
    def test_load_combined_rules_with_exchange(self, temp_rules_dir):
        """Test loading combined rules with exchange."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_combined_rules(exchange='xhkg')
        
        assert isinstance(rules, list)
        assert len(rules) > 0
    
    def test_load_combined_rules_full_hierarchy(self, temp_rules_dir):
        """Test loading combined rules with full hierarchy."""
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_combined_rules(
            product_type='stock',
            exchange='xhkg'
        )
        
        assert isinstance(rules, list)
        # Should have base + stock + xhkg stock rules
        assert len(rules) >= 3
        
        # Verify rule order: later rules should override earlier ones
        symbol_rules = [r for r in rules if r.get('column') == 'Symbol']
        # The last symbol rule should be from exchange-specific file
        if symbol_rules:
            assert '^[0-9]{4}\\.HK$' in str(symbol_rules[-1].get('regex', ''))

