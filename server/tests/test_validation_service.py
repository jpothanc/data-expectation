"""Tests for ValidationService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from services.validation_service import ValidationService


class TestValidationService:
    """Test cases for ValidationService."""
    
    def test_init_with_defaults(self, mock_loader, temp_rules_dir):
        """Test ValidationService initialization with defaults."""
        with patch('services.validation_service.ConfigService') as mock_config:
            mock_config.return_value.get_rules_dir.return_value = str(temp_rules_dir)
            
            service = ValidationService(
                loader=mock_loader,
                product_type='stock'
            )
            
            assert service.product_type == 'stock'
            assert service.rule_loader is not None
    
    def test_init_with_product_type(self, mock_loader, temp_rules_dir):
        """Test ValidationService initialization with product type."""
        with patch('services.validation_service.ConfigService') as mock_config:
            mock_config.return_value.get_rules_dir.return_value = str(temp_rules_dir)
            
            service = ValidationService(
                loader=mock_loader,
                product_type='option'
            )
            
            assert service.product_type == 'option'
    
    def test_get_data_source(self, mock_loader, temp_rules_dir):
        """Test getting data source for exchange."""
        with patch('services.validation_service.ConfigService') as mock_config:
            mock_config.return_value.get_rules_dir.return_value = str(temp_rules_dir)
            
            # Exchange map can be flat or nested by product type
            exchange_map = {
                'XHKG': 'stocks/db_hkg.csv',
                'XNSE': 'stocks/db_nse.csv'
            }
            
            service = ValidationService(
                loader=mock_loader,
                exchange_map=exchange_map,
                product_type='stock'
            )
            
            data_source = service._get_data_source('XHKG', 'stock')
            assert data_source == 'stocks/db_hkg.csv'
    
    def test_get_data_source_invalid_exchange(self, mock_loader, temp_rules_dir):
        """Test getting data source for invalid exchange."""
        with patch('services.validation_service.ConfigService') as mock_config:
            mock_config.return_value.get_rules_dir.return_value = str(temp_rules_dir)
            
            exchange_map = {'XHKG': 'stocks/db_hkg.csv'}
            
            service = ValidationService(
                loader=mock_loader,
                exchange_map=exchange_map,
                product_type='stock'
            )
            
            with pytest.raises(ValueError):
                service._get_data_source('INVALID', 'stock')

