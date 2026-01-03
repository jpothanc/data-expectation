"""Tests for InstrumentValidator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from validators.instrument_validator import InstrumentValidator


class TestInstrumentValidator:
    """Test cases for InstrumentValidator."""
    
    def test_init_with_defaults(self, temp_rules_dir):
        """Test InstrumentValidator initialization with defaults."""
        with patch('validators.instrument_validator.ConfigService') as mock_config:
            mock_config.return_value.get_rules_dir.return_value = str(temp_rules_dir)
            
            validator = InstrumentValidator()
            
            assert validator is not None
            assert validator.rule_loader is not None
    
    def test_init_with_rules_dir(self, temp_rules_dir):
        """Test InstrumentValidator initialization with custom rules directory."""
        validator = InstrumentValidator(rules_dir=str(temp_rules_dir))
        
        assert validator is not None
        assert str(validator.rule_loader.rules_dir) == str(temp_rules_dir)
    
    def test_create_expectation_suite(self, temp_rules_dir):
        """Test creating expectation suite."""
        validator = InstrumentValidator(rules_dir=str(temp_rules_dir))
        
        suite = validator.create_expectation_suite(
            suite_name="test_suite",
            product_type='stock'
        )
        
        assert suite is not None
        # Great Expectations suite should have expectations if rules exist
        assert hasattr(suite, 'expectations')
    
    def test_validate_with_valid_data(self, temp_rules_dir, sample_instrument_data):
        """Test validation with valid data."""
        validator = InstrumentValidator(rules_dir=str(temp_rules_dir))
        
        # Mock the batch definition and validation result
        mock_batch = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.statistics = {'evaluated_expectations': 2, 'successful_expectations': 2}
        mock_batch.validate.return_value = mock_result
        
        validator.batch_definition = MagicMock()
        validator.batch_definition.get_batch.return_value = mock_batch
        
        results = validator.validate(
            sample_instrument_data,
            product_type='stock'
        )
        
        assert results is not None
        assert results.success is True
    
    def test_validate_with_invalid_data(self, temp_rules_dir, sample_instrument_data_invalid):
        """Test validation with invalid data."""
        validator = InstrumentValidator(rules_dir=str(temp_rules_dir))
        
        # Mock the batch definition and validation result
        mock_batch = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.statistics = {'evaluated_expectations': 2, 'successful_expectations': 0}
        mock_batch.validate.return_value = mock_result
        
        validator.batch_definition = MagicMock()
        validator.batch_definition.get_batch.return_value = mock_batch
        
        results = validator.validate(
            sample_instrument_data_invalid,
            product_type='stock'
        )
        
        assert results is not None
        assert results.success is False

