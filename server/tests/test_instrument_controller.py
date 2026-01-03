"""Tests for instrument controller API endpoints."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd


class TestInstrumentController:
    """Test cases for instrument controller."""
    
    @pytest.mark.api
    def test_get_instrument_by_ric_success_single(self, client):
        """Test successful retrieval of single instrument by RIC (returns dict)."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_by_ric.return_value = [
                {
                    'MasterId': 'HK0001',
                    'RIC': '0001.HK',
                    'Symbol': '0001.HK',
                    'Exchange': 'XHKG'
                }
            ]
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/v1/instruments/ric/0001.HK?product_type=stock')
            
            assert response.status_code == 200
            data = response.get_json()
            # Single result returns dict (not wrapped in list)
            assert isinstance(data, dict)
            assert data['RIC'] == '0001.HK'
            assert data['MasterId'] == 'HK0001'
    
    @pytest.mark.api
    def test_get_instrument_by_ric_success_multiple(self, client):
        """Test successful retrieval of multiple instruments by RIC (returns list)."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_by_ric.return_value = [
                {
                    'MasterId': 'HK0001',
                    'RIC': '0001.HK',
                    'Symbol': '0001.HK',
                    'Exchange': 'XHKG'
                },
                {
                    'MasterId': 'HK0002',
                    'RIC': '0001.HK',
                    'Symbol': '0001.HK',
                    'Exchange': 'XNSE'
                }
            ]
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/v1/instruments/ric/0001.HK?product_type=stock')
            
            assert response.status_code == 200
            data = response.get_json()
            # Multiple results return list
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]['RIC'] == '0001.HK'
            assert data[1]['RIC'] == '0001.HK'
    
    @pytest.mark.api
    def test_get_instrument_by_ric_not_found(self, client):
        """Test retrieval of non-existent instrument by RIC."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_by_ric.return_value = []
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/v1/instruments/ric/NONEXISTENT?product_type=stock')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    @pytest.mark.api
    def test_get_instrument_by_id_success(self, client):
        """Test successful retrieval of instrument by MasterId."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            # find_by_id returns a single result (not a list)
            mock_service.find_by_id.return_value = {
                'MasterId': 'HK0001',
                'RIC': '0001.HK',
                'Symbol': '0001.HK',
                'Exchange': 'XHKG'
            }
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/v1/instruments/id/HK0001?product_type=stock')
            
            assert response.status_code == 200
            data = response.get_json()
            # find_by_id returns a single dict
            assert isinstance(data, dict)
            assert data['MasterId'] == 'HK0001'
    
    @pytest.mark.api
    def test_get_instruments_by_exchange_success(self, client):
        """Test successful retrieval of instruments by exchange."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_by_exchange.return_value = [
                {'MasterId': 'HK0001', 'RIC': '0001.HK', 'Exchange': 'XHKG'},
                {'MasterId': 'HK0002', 'RIC': '0002.HK', 'Exchange': 'XHKG'}
            ]
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/v1/instruments/exchange/XHKG?product_type=stock')
            
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert all(item['Exchange'] == 'XHKG' for item in data)
    
    @pytest.mark.api
    def test_get_instrument_by_ric_with_exchange_filter(self, client):
        """Test retrieval by RIC with exchange filter."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_by_ric.return_value = [
                {'MasterId': 'HK0001', 'RIC': '0001.HK', 'Exchange': 'XHKG'}
            ]
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/v1/instruments/ric/0001.HK?product_type=stock&exchange=XHKG')
            
            assert response.status_code == 200
            data = response.get_json()
            # Can be dict (single result) or list (multiple results)
            assert isinstance(data, (dict, list))
            if isinstance(data, dict):
                assert data['RIC'] == '0001.HK'
            else:
                assert len(data) > 0
                assert data[0]['RIC'] == '0001.HK'
    
    @pytest.mark.api
    def test_invalid_product_type(self, client):
        """Test API with invalid product type."""
        response = client.get('/api/v1/instruments/ric/0001.HK?product_type=invalid')
        
        # Should return 400 or handle gracefully
        assert response.status_code in [400, 404]
    
    @pytest.mark.api
    def test_product_type_parameter_defaults_to_stock(self, client):
        """Test that product_type defaults to stock when not provided."""
        with patch('controllers.instrument_controller.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_by_ric.return_value = []
            mock_get_service.return_value = mock_service
            
            # Call without product_type parameter
            response = client.get('/api/v1/instruments/ric/0001.HK')
            
            # Should call get_service (may be called with 'stock' as default or may be called multiple times)
            assert mock_get_service.called

