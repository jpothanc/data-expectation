"""Pytest configuration and shared fixtures."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import yaml
from unittest.mock import Mock, MagicMock, patch

# Add server directory to path
import sys
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))


@pytest.fixture
def temp_rules_dir():
    """Create a temporary rules directory for testing."""
    temp_dir = tempfile.mkdtemp()
    rules_dir = Path(temp_dir) / "rules"
    rules_dir.mkdir()
    
    # Create base.yaml
    base_yaml = rules_dir / "base.yaml"
    base_yaml.write_text("""
- type: ExpectColumnValuesToBeUnique
  column: MasterId
- type: ExpectColumnValuesToNotBeNull
  column: MasterId
""")
    
    # Create stock directory
    stock_dir = rules_dir / "stock"
    stock_dir.mkdir()
    (stock_dir / "base.yaml").write_text("""
- type: ExpectColumnValuesToNotBeNull
  column: Symbol
- type: ExpectColumnValuesToMatchRegex
  column: Symbol
  regex: '^[A-Z0-9]+$'
""")
    
    # Create stock/exchanges/xhkg directory
    xhkg_dir = stock_dir / "exchanges" / "xhkg"
    xhkg_dir.mkdir(parents=True)
    (xhkg_dir / "exchange.yaml").write_text("""
- type: ExpectColumnValuesToMatchRegex
  column: Symbol
  regex: '^[0-9]{4}\\.HK$'
""")
    
    yield rules_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_instrument_data():
    """Sample instrument data for testing."""
    return pd.DataFrame({
        'MasterId': ['HK0001', 'HK0002', 'HK0003'],
        'RIC': ['0001.HK', '0002.HK', '0003.HK'],
        'Symbol': ['0001.HK', '0002.HK', '0003.HK'],
        'Exchange': ['XHKG', 'XHKG', 'XHKG'],
        'SecurityType': ['Common Stock', 'Common Stock', 'Common Stock'],
        'Currency': ['HKD', 'HKD', 'HKD'],
        'TradingStatus': ['Active', 'Active', 'Suspended']
    })


@pytest.fixture
def sample_instrument_data_invalid():
    """Sample invalid instrument data for testing."""
    return pd.DataFrame({
        'MasterId': ['HK0001', 'HK0001', None],  # Duplicate and null
        'RIC': ['0001.HK', '0002.HK', '0003.HK'],
        'Symbol': ['INVALID', '0002.HK', '0003.HK'],  # Invalid format
        'Exchange': ['XHKG', 'XHKG', 'XHKG'],
        'SecurityType': ['Common Stock', 'Common Stock', 'Common Stock'],
        'Currency': ['HKD', 'HKD', 'HKD'],
        'TradingStatus': ['Active', 'Active', 'Suspended']
    })


@pytest.fixture
def mock_config_service():
    """Mock ConfigService for testing."""
    mock = Mock()
    mock.get_rules_dir.return_value = "rules"
    mock.get_csv_config.return_value = {
        "data_folder": "data",
        "exchange_map": {
            "stock": {
                "XHKG": "stocks/db_hkg.csv",
                "XNSE": "stocks/db_nse.csv"
            }
        }
    }
    mock.get_exchange_map.return_value = {
        "XHKG": "stocks/db_hkg.csv",
        "XNSE": "stocks/db_nse.csv"
    }
    return mock


@pytest.fixture
def mock_loader():
    """Mock data loader for testing."""
    mock = Mock()
    mock.load_data.return_value = pd.DataFrame({
        'MasterId': ['HK0001', 'HK0002'],
        'RIC': ['0001.HK', '0002.HK'],
        'Symbol': ['0001.HK', '0002.HK'],
        'Exchange': ['XHKG', 'XHKG']
    })
    return mock


@pytest.fixture
def app():
    """Create Flask application for testing."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    return app


@pytest.fixture
def client(app):
    """Create test client for Flask app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner for Flask app."""
    return app.test_cli_runner()


