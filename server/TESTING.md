# Testing Guide

## Running Tests

### Command Line

**Basic test run:**
```bash
cd server
pytest
```

**With verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_rule_loader.py
```

**Run specific test:**
```bash
pytest tests/test_rule_loader.py::TestRuleLoader::test_load_base_rules
```

**Run with coverage:**
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

**Run by marker:**
```bash
pytest -m api          # API tests only
pytest -m unit         # Unit tests only
pytest -m "not slow"   # Skip slow tests
```

### PyCharm Configuration

If PyCharm is using the wrong Python interpreter:

1. **File → Settings → Project → Python Interpreter**
2. Select the correct interpreter for this project
3. If needed, create a new virtual environment:
   - Click the gear icon → Add
   - Choose "New Environment"
   - Location: `server/.venv` (or `server/venv`)
   - Base interpreter: Your Python installation
   - Click OK

4. **File → Settings → Tools → Python Integrated Tools**
   - Testing: Select "pytest"
   - Default test runner: pytest

5. **Right-click on `server/tests` folder → Run 'pytest in tests'**

### VS Code Configuration

Create `.vscode/settings.json`:
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.cwd": "${workspaceFolder}/server"
}
```

## Test Structure

```
server/
├── pytest.ini              # Pytest configuration
├── .coveragerc            # Coverage configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Shared fixtures
│   ├── test_app.py
│   ├── test_config_service.py
│   ├── test_rule_loader.py
│   ├── test_instrument_controller.py
│   ├── test_validation_service.py
│   └── test_instrument_validator.py
```

## Common Issues

### Issue: Wrong Python Interpreter

**Symptom:** Tests run with Python from different project

**Solution:**
- Configure PyCharm/IDE to use correct interpreter
- Ensure virtual environment is activated
- Check `PYTHONPATH` environment variable

### Issue: Coverage Options Error

**Symptom:** `unrecognized arguments: --cov`

**Solution:**
- Install pytest-cov: `pip install pytest-cov`
- Or run without coverage: `pytest` (coverage options removed from pytest.ini)

### Issue: Import Errors

**Symptom:** `ModuleNotFoundError`

**Solution:**
- Ensure you're in the `server` directory
- Check that `server` is in Python path
- Install dependencies: `pip install -r requirements.txt`

### Issue: Great Expectations Errors

**Symptom:** File handle or context errors

**Solution:**
- Tests use mocks to avoid GE file handle issues
- Ensure test fixtures are properly set up
- Check that temporary directories are cleaned up

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd server
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd server
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./server/coverage.xml
```

## Writing Tests

### Example Test Structure

```python
import pytest
from your_module import YourClass

class TestYourClass:
    """Test cases for YourClass."""
    
    def test_something(self, fixture_name):
        """Test description."""
        # Arrange
        obj = YourClass()
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected_value
```

### Using Fixtures

```python
def test_with_fixture(self, temp_rules_dir, sample_instrument_data):
    """Test using fixtures from conftest.py."""
    loader = RuleLoader(rules_dir=str(temp_rules_dir))
    # Use sample_instrument_data...
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_with_mock(self):
    """Test with mocked dependencies."""
    with patch('module.ExternalService') as mock_service:
        mock_service.return_value.method.return_value = 'result'
        # Test code...
```

## Coverage Reports

After running with coverage:
```bash
pytest --cov=. --cov-report=html
```

Open `htmlcov/index.html` in browser to view detailed coverage report.


