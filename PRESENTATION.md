# Data Expectations Platform
## Reference Data Management & Validation System

---

## Slide 1: Title Slide

# Data Expectations Platform

**Reference Data Management & Validation System**

A comprehensive platform for validating financial instrument reference data across multiple product types, exchanges, and regions.

---

## Slide 2: Project Overview

### What is Data Expectations?

- **Purpose**: Automated validation of financial instrument reference data
- **Scope**: Stocks, Options, and Futures across multiple exchanges
- **Regions**: APAC, EMEA, and US markets
- **Technology**: Python backend + Svelte frontend + Great Expectations framework

### Key Capabilities

- ✅ Instrument data validation
- ✅ Rule-based validation engine
- ✅ Multi-level rule inheritance and overrides
- ✅ Real-time analytics and dashboards
- ✅ RESTful API for integration

---

## Slide 3: Architecture Overview

### Three Main Components

```
┌─────────────────┐
│   Client (UI)   │  ← Svelte Frontend
│   Port: 5173    │     Analytics Dashboard
└────────┬────────┘     Instrument Management
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│  Server (API)   │  ← Flask Backend
│  Port: 5006     │     Validation Engine
└────────┬────────┘     Rule Management
         │
         │
┌────────▼────────┐
│   Generator     │  ← Batch Processing
│   (CLI Tool)    │     Database Integration
└─────────────────┘
```

---

## Slide 4: Component 1 - Client (Frontend)

### Svelte-Based Web Application

**Key Features:**
- Modern, responsive UI with dark theme
- Real-time analytics dashboards
- Interactive charts and visualizations
- Instrument search and management

**Main Sections:**
1. **Analytics Dashboard**
   - Overview: Pass/Fail by Region
   - Trends: Time-series analysis
   - Breakdown: Regional analysis
   - Rules: Rule analysis

2. **Instrument Management**
   - Stocks, Options, Futures tabs
   - Search by Exchange, RIC, or MasterId
   - Detailed instrument views

**Technologies:**
- Svelte 5
- Chart.js for visualizations
- TypeScript
- Tailwind CSS

---

## Slide 5: Component 2 - Server (Backend API)

### Flask REST API

**Core Services:**

1. **Instrument Service**
   - Retrieve instruments by RIC, MasterId, or Exchange
   - Support for Stock, Option, Future product types
   - CSV and Database data sources

2. **Validation Service**
   - Execute validation rules
   - Combine base, product-type, and exchange-specific rules
   - Return detailed validation results

3. **Analytics Service**
   - Generate trend data
   - Heatmap visualizations
   - Regional breakdowns

**API Endpoints:**
- `/api/v1/instruments/*` - Instrument retrieval
- `/api/v1/rules/*` - Rule management and validation
- `/api/v1/validation/*` - Analytics endpoints

**Documentation:** Swagger UI at `/api-docs`

---

## Slide 6: Component 3 - Generator (Batch Processing)

### Command-Line Batch Validator

**Purpose:**
- Batch validation across multiple regions/exchanges
- Database persistence of results
- Scheduled validation runs

**Features:**
- Multi-threaded processing
- Database integration (SQL Server)
- Comprehensive logging
- Regional configuration support

**Usage:**
```bash
python main.py validate --region apac --product-type stock
```

**Output:**
- Validation results stored in database
- Console summaries
- Detailed logs

---

## Slide 7: Data Flow

### How Data Moves Through the System

```
┌─────────────┐
│ Data Source │
│ (CSV/DB)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Loader    │ ← CSV Loader or Database Loader
│   Factory   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Processor  │ ← Stock/Option/Future Processor
│  (Product)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validator  │ ← Great Expectations Validator
│  (Rules)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Results   │ ← Validation Results
│   Formatter │
└─────────────┘
```

---

## Slide 8: Rules Architecture - Overview

### Hierarchical Rule System

Rules are organized in a **layered inheritance structure**:

```
Level 1: Base Rules (rules/base.yaml)
    ↓
Level 2: Product Type Rules (rules/stock/base.yaml)
    ↓
Level 3: Exchange Rules (rules/exchanges/{exchange}.yaml)
    ↓
Level 4: Product+Exchange Rules (rules/stock/exchanges/{exchange}/exchange.yaml)
    ↓
Level 5: Custom Rules (rules/stock/exchanges/{exchange}/custom.yaml)
```

**Key Principle:** More specific rules override general rules

---

## Slide 9: Rules Directory Structure

### File Organization

```
rules/
├── base.yaml                    # Global base rules
├── stock/
│   ├── base.yaml                # Stock-specific base rules
│   ├── combined.yaml            # Combined stock rules
│   ├── custom.yaml              # Stock custom rules
│   └── exchanges/
│       ├── xhkg/
│       │   ├── exchange.yaml    # XHKG stock rules
│       │   ├── custom.yaml      # XHKG stock custom rules
│       │   └── combined.yaml    # XHKG stock combined rules
│       ├── xnse/
│       └── xtks/
├── options/
│   └── base.yaml                # Options-specific rules
└── future/
    └── base.yaml                # Futures-specific rules
```

---

## Slide 10: Rule Loading Order

### How Rules Are Combined

**Loading Sequence:**
1. **Base Rules** (`rules/base.yaml`)
   - Universal rules for all products
   - Example: MasterId uniqueness

2. **Product Type Rules** (`rules/{product_type}/base.yaml`)
   - Rules specific to product type
   - Example: Stock-specific validations

3. **Exchange Rules** (`rules/exchanges/{exchange}.yaml`)
   - Rules for specific exchange (all products)
   - Example: Exchange-specific formats

4. **Product+Exchange Rules** (`rules/{product_type}/exchanges/{exchange}/exchange.yaml`)
   - Most specific: Product type + Exchange combination
   - Example: Stock rules for Hong Kong exchange

5. **Custom Rules** (YAML or programmatic)
   - Ad-hoc rules for specific scenarios
   - Highest priority

**Result:** Final rule set = Base + Product + Exchange + Product+Exchange + Custom

---

## Slide 11: Rule Override Mechanism

### How Overrides Work

**Example Scenario:**
Validating **Stock** instruments from **XHKG** exchange

**Rule Loading Process:**

```
Step 1: Load base.yaml
  → ExpectColumnValuesToBeUnique(MasterId)
  → ExpectColumnValuesToNotBeNull(MasterId)

Step 2: Load stock/base.yaml
  → ExpectColumnValuesToBeInSet(Currency, ['USD', 'HKD'])
  → ExpectColumnValuesToMatchRegex(Symbol, '^[0-9]{4}\.HK$')

Step 3: Load exchanges/xhkg.yaml (if exists)
  → Exchange-wide rules

Step 4: Load stock/exchanges/xhkg/exchange.yaml
  → ExpectColumnValuesToMatchRegex(Symbol, '^[0-9]{4}\.HK$')  [OVERRIDES Step 2]
  → ExpectColumnValuesToBeBetween(Price, 0.01, 1000000)

Step 5: Load custom rules (if specified)
  → Additional ad-hoc validations
```

**Final Rule Set:** All rules combined, with later rules overriding earlier ones

---

## Slide 12: Rule Definition Format

### YAML Rule Structure

**Base Rule Example** (`rules/base.yaml`):
```yaml
- type: ExpectColumnValuesToBeUnique
  column: MasterId

- type: ExpectColumnValuesToNotBeNull
  column: MasterId
```

**Product Type Rule Example** (`rules/stock/base.yaml`):
```yaml
- type: ExpectColumnValuesToBeInSet
  column: SecurityType
  value_set: ['Common Stock', 'Preferred Stock']

- type: ExpectColumnValuesToMatchRegex
  column: Symbol
  regex: '^[A-Z0-9]+$'
```

**Exchange-Specific Rule Example** (`rules/stock/exchanges/xhkg/exchange.yaml`):
```yaml
- type: ExpectColumnValuesToMatchRegex
  column: Symbol
  regex: '^[0-9]{4}\.HK$'  # Overrides stock/base.yaml regex

- type: ExpectColumnValuesToBeBetween
  column: Price
  min_value: 0.01
  max_value: 1000000
```

---

## Slide 13: Rule Types Supported

### Great Expectations Expectations

**Common Rule Types:**

1. **Uniqueness**
   - `ExpectColumnValuesToBeUnique`
   - `ExpectCompoundColumnsToBeUnique`

2. **Null Checks**
   - `ExpectColumnValuesToNotBeNull`
   - `ExpectColumnValuesToBeNull`

3. **Value Sets**
   - `ExpectColumnValuesToBeInSet`
   - `ExpectColumnValuesToNotBeInSet`

4. **Ranges**
   - `ExpectColumnValuesToBeBetween`
   - `ExpectColumnValuesToBeGreaterThan`

5. **Patterns**
   - `ExpectColumnValuesToMatchRegex`
   - `ExpectColumnValuesToMatchRegexList`

6. **Data Types**
   - `ExpectColumnValuesToBeOfType`
   - `ExpectColumnValuesToBeInTypeList`

7. **Relationships**
   - `ExpectColumnPairValuesToBeEqual`
   - `ExpectColumnPairValuesAToBeGreaterThanB`

---

## Slide 14: Product Type Support

### Three Product Types

**1. Stocks**
- Path: `rules/stock/`
- Exchanges: XHKG, XNSE, XTKS, XLON, XPAR, XNYS, XNAS
- Common validations: Symbol format, Security type, Trading status

**2. Options**
- Path: `rules/options/`
- Exchanges: XHKG, XTKS, XLON, XPAR, XNYS, XNAS
- Common validations: Option type, Strike price, Expiration date

**3. Futures**
- Path: `rules/future/`
- Exchanges: XHKG, XTKS, XLON, XPAR, XNYS, XNAS
- Common validations: Contract size, Settlement type, Delivery date

**Each product type:**
- Has its own base rules
- Can have exchange-specific overrides
- Supports custom rule sets

---

## Slide 15: Exchange Support

### Supported Exchanges

**APAC Region:**
- **XHKG** - Hong Kong Stock Exchange
- **XNSE** - National Stock Exchange of India
- **XTKS** - Tokyo Stock Exchange

**EMEA Region:**
- **XLON** - London Stock Exchange
- **XPAR** - Euronext Paris

**US Region:**
- **XNYS** - New York Stock Exchange
- **XNAS** - NASDAQ

**Exchange-Specific Features:**
- Exchange-level rules (applies to all products)
- Product+Exchange rules (most specific)
- Custom rule sets per exchange

---

## Slide 16: Validation Process Flow

### Step-by-Step Validation

```
1. Request Received
   ↓
2. Identify Product Type & Exchange
   ↓
3. Load Data Source (CSV or Database)
   ↓
4. RuleLoader.load_combined_rules()
   ├─ Load base.yaml
   ├─ Load {product_type}/base.yaml
   ├─ Load exchanges/{exchange}.yaml
   ├─ Load {product_type}/exchanges/{exchange}/exchange.yaml
   └─ Load custom rules (if any)
   ↓
5. Create Great Expectations Validator
   ↓
6. Apply Rules to Data
   ↓
7. Generate Validation Results
   ├─ Passed expectations
   ├─ Failed expectations
   └─ Statistics
   ↓
8. Format & Return Results
```

---

## Slide 17: API Endpoints

### Key Endpoints

**Instruments:**
- `GET /api/v1/instruments/exchange/{exchange}?product_type={type}`
- `GET /api/v1/instruments/ric/{ric}?product_type={type}`
- `GET /api/v1/instruments/id/{id}?product_type={type}`

**Validation:**
- `GET /api/v1/rules/validate/{product_type}/{exchange}`
- `POST /api/v1/rules/validate-custom/{product_type}/{exchange}`
- `GET /api/v1/rules/rules/{product_type}/{exchange}`

**Analytics:**
- `GET /api/v1/validation/global-view?days={days}`
- `GET /api/v1/validation/heatmap?days={days}`
- `GET /api/v1/validation/regional-trends?days={days}`

**Documentation:** `/api-docs` (Swagger UI)

---

## Slide 18: Analytics Dashboard

### Visualization Features

**Overview Dashboard:**
- Pass vs Fail by Region (Stacked Bar Chart)
- Region x Product Success Rates (Heatmap)

**Trends Dashboard:**
- Line Chart: Failure trends over time
- Heatmap: Failure distribution by region/date
- Sparklines: Regional overview
- Stacked Area: Cumulative trends

**Breakdown Dashboard:**
- Regional performance analysis
- Exchange-level details
- Product type comparisons

**Rule Analysis:**
- Rule failure rates
- Most common failures
- Rule effectiveness metrics

---

## Slide 19: Configuration Management

### Configuration Files

**Server Config** (`server/config.json`):
```json
{
  "server": { "port": 5006 },
  "rules": { "rules_dir": "rules" },
  "data_loader": {
    "type": "csv",
    "csv": { "data_folder": "data" }
  },
  "regions": {
    "apac": { "stock": "XHKG,XNSE,XTKS" }
  }
}
```

**Client Config** (`client/src/lib/config.json`):
- API endpoints
- Timeout settings
- Feature flags

**Environment-Specific:**
- `config_dev.json`
- `config_uat.json`
- `config_prod.json`

---

## Slide 20: Data Sources

### Supported Data Loaders

**1. CSV Loader**
- Reads from `data/{product_type}/` directory
- Files: `db_{exchange}.csv`
- Example: `data/stocks/db_hkg.csv`

**2. Database Loader**
- Connects to SQL Server
- Queries: `SELECT * FROM {ProductType}Master WHERE Exchange = '{exchange}'`
- Supports multiple database connections

**Loader Factory:**
- Automatically selects loader based on config
- Supports both sources simultaneously
- Product-type aware

---

## Slide 21: Key Technologies

### Technology Stack

**Backend:**
- **Python 3.x** - Core language
- **Flask** - Web framework
- **Great Expectations** - Validation framework
- **Pandas** - Data manipulation
- **PyYAML** - Rule parsing
- **Flasgger** - API documentation

**Frontend:**
- **Svelte 5** - UI framework
- **TypeScript** - Type safety
- **Chart.js** - Data visualization
- **Tailwind CSS** - Styling
- **Vite** - Build tool

**Database:**
- **SQL Server** - Data persistence
- **ODBC** - Database connectivity

---

## Slide 22: Use Cases

### Real-World Applications

**1. Data Quality Assurance**
- Validate instrument data before trading
- Ensure compliance with exchange requirements
- Detect data anomalies early

**2. Regulatory Compliance**
- Verify data meets regulatory standards
- Generate compliance reports
- Track validation history

**3. Data Migration**
- Validate data during system migrations
- Ensure data integrity across systems
- Compare data sources

**4. Continuous Monitoring**
- Scheduled batch validations
- Real-time API validations
- Trend analysis and alerting

---

## Slide 23: Benefits

### Why Use This Platform?

**For Data Teams:**
- ✅ Centralized validation rules
- ✅ Reusable rule definitions
- ✅ Easy rule maintenance
- ✅ Comprehensive reporting

**For Developers:**
- ✅ RESTful API integration
- ✅ Well-documented endpoints
- ✅ Flexible rule system
- ✅ Extensible architecture

**For Business:**
- ✅ Improved data quality
- ✅ Reduced manual effort
- ✅ Faster issue detection
- ✅ Better decision-making

---

## Slide 24: Rule Override Example

### Practical Example: Stock Symbol Validation

**Scenario:** Validate stock symbols for Hong Kong Exchange (XHKG)

**Rule Hierarchy:**

1. **Base Rule** (`rules/base.yaml`):
   ```yaml
   - type: ExpectColumnValuesToNotBeNull
     column: Symbol
   ```

2. **Stock Rule** (`rules/stock/base.yaml`):
   ```yaml
   - type: ExpectColumnValuesToMatchRegex
     column: Symbol
     regex: '^[A-Z0-9]+$'  # General stock symbol format
   ```

3. **XHKG Stock Rule** (`rules/stock/exchanges/xhkg/exchange.yaml`):
   ```yaml
   - type: ExpectColumnValuesToMatchRegex
     column: Symbol
     regex: '^[0-9]{4}\.HK$'  # OVERRIDES: HK-specific format
   ```

**Result:** XHKG stocks validated with `^[0-9]{4}\.HK$` pattern
- Base rule ensures Symbol is not null
- Stock rule provides general format
- XHKG rule overrides with specific format

---

## Slide 25: Custom Rules

### Adding Custom Rules

**Method 1: YAML Files**
```yaml
# rules/stock/exchanges/xhkg/custom.yaml
- type: ExpectColumnValuesToBeBetween
  column: MarketCap
  min_value: 1000000
  max_value: 1000000000000
```

**Method 2: Programmatic (API)**
```python
custom_rules = [
    {
        'type': 'ExpectColumnValuesToBeInSet',
        'column': 'TradingStatus',
        'value_set': ['Active', 'Suspended']
    }
]
```

**Method 3: Combined Rules**
- Named rule sets in `combined.yaml`
- Reference by name in API calls
- Supports complex rule combinations

---

## Slide 26: Validation Results

### Result Structure

**Validation Response:**
```json
{
  "success": true,
  "total_expectations": 15,
  "successful_expectations": 12,
  "failed_expectations": 3,
  "results": [
    {
      "expectation_type": "ExpectColumnValuesToBeUnique",
      "column": "MasterId",
      "success": true,
      "result": {...}
    },
    {
      "expectation_type": "ExpectColumnValuesToMatchRegex",
      "column": "Symbol",
      "success": false,
      "result": {
        "unexpected_count": 5,
        "unexpected_list": ["INVALID1", "INVALID2", ...]
      }
    }
  ]
}
```

**Analytics Integration:**
- Results stored for trend analysis
- Failure patterns identified
- Success rates calculated

---

## Slide 27: Deployment

### Deployment Architecture

**Development:**
- Local Flask server (port 5006)
- Svelte dev server (port 5173)
- Local CSV data files

**Production:**
- Flask app with Gunicorn/uWSGI
- Svelte build served via Nginx
- Database backend
- Environment-specific configs

**Configuration:**
- Environment variables
- Config files per environment
- Port configuration in config.json

---

## Slide 28: Future Enhancements

### Roadmap

**Planned Features:**
- 🔄 Real-time validation streaming
- 📊 Advanced analytics and ML insights
- 🔔 Alert system for failures
- 📧 Email notifications
- 🔐 User authentication and authorization
- 📱 Mobile-responsive improvements
- 🌐 Multi-language support
- 🔗 Integration with external data sources

**Technical Improvements:**
- Performance optimization
- Caching layer
- GraphQL API option
- Enhanced error handling
- Comprehensive test coverage

---

## Slide 29: Summary

### Key Takeaways

**Platform Purpose:**
- Automated validation of financial instrument reference data
- Multi-product, multi-exchange, multi-region support

**Core Architecture:**
- Three components: Client (UI), Server (API), Generator (Batch)
- Hierarchical rule system with inheritance and overrides

**Rule System:**
- Base → Product Type → Exchange → Product+Exchange → Custom
- YAML-based rule definitions
- Great Expectations framework

**Benefits:**
- Improved data quality
- Centralized rule management
- Comprehensive analytics
- Easy integration via REST API

---

## Slide 30: Questions & Contact

### Thank You!

**Questions?**

**Project Repository:**
- GitHub: [Repository URL]
- Documentation: `/api-docs` (Swagger UI)

**Key Resources:**
- API Documentation: `/api-docs`
- Rule Examples: `server/rules/`
- Configuration: `server/config.json`

---

## Appendix: Rule Loading Code Flow

### Technical Deep Dive

**RuleLoader.load_combined_rules()**:
```python
1. rules = load_base_rules()                    # Level 1
2. rules.extend(load_product_type_rules())      # Level 2
3. rules.extend(load_exchange_rules())           # Level 3
4. rules.extend(load_product_exchange_rules())   # Level 4
5. rules.extend(load_custom_rules())             # Level 5
return rules
```

**Key Classes:**
- `RuleLoader` - Rule loading and parsing
- `ValidationService` - Validation orchestration
- `InstrumentValidator` - Great Expectations integration
- `ValidationService` - Business logic

---

## Appendix: Directory Structure

### Project Organization

```
data-expectation/
├── client/          # Svelte frontend
│   ├── src/
│   │   ├── routes/  # Page routes
│   │   └── lib/     # Components & services
│   └── package.json
├── server/          # Flask backend
│   ├── controllers/ # API endpoints
│   ├── services/    # Business logic
│   ├── validators/  # Validation engine
│   ├── rules/       # Rule definitions
│   └── data/        # CSV data files
└── generator/       # Batch processing CLI
    ├── src/
    └── database/    # DB integration
```

---

## End of Presentation

**Thank you for your attention!**


