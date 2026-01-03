# Generator Project

A modular Python project for batch validation of instruments across regions, product types, and exchanges.

## Features

- **Batch Validation**: Validate multiple product types and exchanges across regions
- **Database Integration**: Optionally save validation results to SQL Server database
- **Comprehensive Logging**: Detailed console output for all operations
- **Modular Design**: Clean, OOP-based architecture

## Setup

### 1. Create Virtual Environment

```bash
cd generator
py -m venv venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell) - Recommended:**
```powershell
.\activate.ps1
```

**Windows (PowerShell) - Alternative:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Database Configuration

The generator uses `config.json` for database connection settings. The connection string will automatically be modified to use the `RubyUsers` database instead of `Instruments`.

**Setup:**
1. Copy `config.example.json` to `config.json`:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` with your database connection string:
   ```json
   {
     "database": {
       "connection_string_apac_uat": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER;..."
     }
   }
   ```

**Note:** The generator will automatically change `DATABASE=Instruments` to `DATABASE=RubyUsers` when connecting.

### Regional Configuration

Edit `config/regions.yaml` to configure regions, product types, and exchanges:

```yaml
apac:
  stock:
    - XHKG
    - XTKS
    - XNSE
  option:
    - XHKG
  future:
    - XSGS
```

## Usage

### Basic Usage

**Important:** Run commands from the **parent directory** (instruments_ge_app), not from the generator directory.

```bash
# 1. Navigate to generator directory and activate virtual environment
cd generator
.\activate.ps1

# 2. Navigate back to parent directory
cd ..

# 3. Run validation for a single region
py -m generator.main apac

# Run validation for multiple regions (comma-separated)
py -m generator.main apac,emea,us

# Run with custom rules
py -m generator.main apac --custom-rules "is_tradable_stocks"

# Run multiple regions with custom rules
py -m generator.main apac,emea --custom-rules "is_tradable_stocks"

# Run with database saving enabled
py -m generator.main apac --save-to-database

# Run multiple regions and save to database
py -m generator.main apac,emea,us --save-to-database

# Run with custom database connection string
py -m generator.main apac --save-to-database --database-connection "DRIVER={...};SERVER=...;DATABASE=...;"

# List available regions
py -m generator.main --list-regions
```

**Alternative:** You can also run directly from the generator directory using Python's path:
```bash
cd generator
.\activate.ps1
py main.py apac --save-to-database

# Multiple regions
py main.py apac,emea,us --save-to-database
```

### Command Line Options

- `--region`: Region to validate (required)
- `--api-url`: Base URL for validation API (default: http://127.0.0.1:5006)
- `--config`: Path to regions.yaml config file (default: config/regions.yaml)
- `--custom-rules`: Comma-separated list of custom rule names
- `--save-to-database`: Enable saving results to database
- `--database-connection`: SQL Server connection string (overrides config.json)
- `--verbose`: Enable verbose logging (default: True)

## Database Integration

The generator can save validation results to a SQL Server database. See [DATABASE_USAGE.md](DATABASE_USAGE.md) for details.

### Prerequisites

- SQL Server database (local or remote)
- ODBC Driver 17 for SQL Server (or SQL Server driver)
- Database connection string configured in `config.json` or provided via `--database-connection`

### Database Schema

The database schema is defined in `database/schema.sql`. Run this script to create the necessary tables:

- `GeValidationRuns`: Main validation run records
- `GeExpectationResults`: Individual expectation results
- `GeValidationRulesApplied`: Rules applied in each run

## Project Structure

```
generator/
├── __init__.py
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── DATABASE_USAGE.md      # Database integration guide
├── config/
│   └── regions.yaml       # Regional configuration
├── database/
│   ├── schema.sql         # Database schema
│   ├── insert_statements.sql  # Sample inserts
│   └── analytics_queries.sql   # Analytics queries
└── src/
    ├── cli.py             # Command-line interface
    ├── validator.py       # Batch validation orchestrator
    ├── api_client.py      # API client for validation endpoints
    ├── config_loader.py   # Configuration loader
    ├── database_service.py    # Database connection service
    ├── database_repository.py # Database operations
    ├── validation_result.py   # Validation result model
    ├── validation_summary.py  # Validation summary model
    └── result_formatter.py   # Console output formatter
```

## Examples

See `example_usage.py` for programmatic usage examples.

## Troubleshooting

### Virtual Environment Issues

If you encounter issues activating the virtual environment:

1. Ensure Python is installed: `py --version`
2. Recreate the virtual environment: `py -m venv venv --clear`
3. Check PowerShell execution policy: `Get-ExecutionPolicy`
   - If Restricted, run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Database Connection Issues

- Verify ODBC drivers are installed: `py -c "import pyodbc; print(pyodbc.drivers())"`
- Test connection string format
- Check SQL Server is running and accessible
- Verify database exists (will be created automatically if connection allows)

### API Connection Issues

- Ensure the validation API is running: `http://127.0.0.1:5006`
- Check API health: `curl http://127.0.0.1:5006/api/v1/rules/health`
- Verify network connectivity

## License

See parent project LICENSE file.
