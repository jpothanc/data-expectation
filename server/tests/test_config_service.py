"""Tests for ConfigService."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from config.config_service import ConfigService


class TestConfigService:
    """Test cases for ConfigService."""
    
    def test_init_with_default_env(self):
        """Test ConfigService initialization with default environment."""
        # This will use the actual config.json if it exists
        # In a real scenario, you'd mock the file system
        try:
            service = ConfigService()
            assert service.env == 'dev'
        except FileNotFoundError:
            pytest.skip("config.json not found")
    
    def test_init_with_specific_env(self):
        """Test ConfigService initialization with specific environment."""
        try:
            service = ConfigService(env='dev')
            assert service.env == 'dev'
        except FileNotFoundError:
            pytest.skip("config.json not found")
    
    def test_init_with_invalid_env(self):
        """Test ConfigService initialization with invalid environment."""
        with pytest.raises(ValueError, match="Invalid environment"):
            ConfigService(env='invalid')
    
    def test_get_rules_dir(self):
        """Test getting rules directory from config."""
        try:
            service = ConfigService()
            rules_dir = service.get_rules_dir()
            assert isinstance(rules_dir, str)
            assert rules_dir == "rules"  # Based on current config
        except FileNotFoundError:
            pytest.skip("config.json not found")
    
    def test_get_data_folder(self):
        """Test getting data folder from config."""
        try:
            service = ConfigService()
            data_folder = service.get_data_folder()
            assert isinstance(data_folder, str)
            assert data_folder == "data"  # Based on current config
        except FileNotFoundError:
            pytest.skip("config.json not found")
    
    def test_get_csv_config(self):
        """Test getting CSV configuration."""
        try:
            service = ConfigService()
            csv_config = service.get_csv_config()
            assert isinstance(csv_config, dict)
            assert 'data_folder' in csv_config or 'exchange_map' in csv_config
        except FileNotFoundError:
            pytest.skip("config.json not found")
    
    def test_get_csv_exchange_map(self):
        """Test getting CSV exchange map for product type."""
        try:
            service = ConfigService()
            exchange_map = service.get_csv_exchange_map('stock')
            assert isinstance(exchange_map, dict)
        except FileNotFoundError:
            pytest.skip("config.json not found")
    
    def test_get_exchanges_by_region(self):
        """Test getting exchanges organized by region."""
        try:
            service = ConfigService()
            exchanges = service.get_exchanges_by_region('stock')
            assert isinstance(exchanges, dict)
        except FileNotFoundError:
            pytest.skip("config.json not found")

