# Server Tests

Test suite for the Data Expectations server project.

## Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_app.py              # Flask application tests
├── test_config_service.py   # ConfigService tests
├── test_rule_loader.py      # RuleLoader tests
├── test_instrument_controller.py  # Instrument API tests
├── test_validation_service.py     # ValidationService tests
└── test_instrument_validator.py   # InstrumentValidator tests
```

## Running Tests

### Run all tests
```bash
cd server
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_rule_loader.py
```

### Run specific test
```bash
pytest tests/test_rule_loader.py::TestRuleLoader::test_load_base_rules
```

### Run by marker
```bash
pytest -m api          # Run only API tests
pytest -m unit         # Run only unit tests
pytest -m "not slow"   # Skip slow tests
```

## Test Categories

Tests are marked with markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.slow` - Slow running tests

## Fixtures

Common fixtures available in `conftest.py`:

- `temp_rules_dir` - Temporary rules directory with sample rules
- `sample_instrument_data` - Sample valid instrument DataFrame
- `sample_instrument_data_invalid` - Sample invalid instrument DataFrame
- `mock_config_service` - Mock ConfigService
- `mock_loader` - Mock data loader
- `app` - Flask application instance
- `client` - Flask test client
- `runner` - Flask CLI test runner

## Writing New Tests

### Example Unit Test
```python
import pytest
from validators.rule_loader import RuleLoader

class TestRuleLoader:
    def test_load_base_rules(self, temp_rules_dir):
        loader = RuleLoader(rules_dir=str(temp_rules_dir))
        rules = loader.load_base_rules()
        
        assert isinstance(rules, list)
        assert len(rules) > 0
```

### Example API Test
```python
import pytest

@pytest.mark.api
def test_get_instrument_by_ric(self, client):
    response = client.get('/api/v1/instruments/ric/0001.HK?product_type=stock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
```

## Coverage

Coverage reports are generated in HTML format:

```bash
pytest --cov=. --cov-report=html
```

Open `htmlcov/index.html` in a browser to view coverage report.

## Continuous Integration

Tests should be run in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd server
    pip install -r requirements.txt
    pytest --cov=. --cov-report=xml
```

## Notes

- Tests use temporary directories and mocks to avoid modifying actual data
- Great Expectations validations are mocked to avoid file handle issues
- API tests use Flask test client for isolated testing
- Fixtures provide reusable test data and mocks

