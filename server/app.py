"""Flask application for instruments validation API."""

import logging
import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from controllers.instrument_controller import instrument_api
from controllers.rule_controller import rule_api
from controllers.validation_controller import validation_api
from utils import QueryExporter

# Swagger configuration
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api-docs"
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Instruments Validation API",
        "description": "API for retrieving instruments and running validation rules",
        "version": "1.0.0",
        "contact": {
            "name": "API Support"
        }
    },
    "basePath": "/api/v1",
    "schemes": ["http", "https"],
    "tags": [
        {
            "name": "Instruments",
            "description": "Operations for retrieving instrument data"
        },
        {
            "name": "Rules",
            "description": "Operations for validation rules and rule management"
        },
        {
            "name": "Validation Analytics",
            "description": "Operations for validation analytics and chart data"
        }
    ]
}


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize Swagger
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)
    
    app.register_blueprint(instrument_api, url_prefix='/api/v1/instruments/')
    app.register_blueprint(rule_api, url_prefix='/api/v1/rules/')
    app.register_blueprint(validation_api, url_prefix='/api/v1/validation/')
    
    return app
def export():
    exporter = QueryExporter()
    query = """
        SELECT *
        FROM StockMaster
        WHERE Exchange = 'XHKG'
    """
    csv_path = exporter.export_query_to_csv(query, "db_hkg.csv")
    print(f"Exported to: {csv_path}")
    query = """
            SELECT *
            FROM StockMaster
            WHERE Exchange = 'XTKS'
        """
    csv_path = exporter.export_query_to_csv(query, "db_tks.csv")
    print(f"Exported to: {csv_path}")
    query = """
            SELECT *
            FROM StockMaster
            WHERE Exchange = 'XNSE'
        """
    csv_path = exporter.export_query_to_csv(query, "db_nse.csv")
    print(f"Exported to: {csv_path}")


def init_logging():
    """Initialize logging from config.json."""
    from config.config_service import ConfigService
    import os
    from pathlib import Path
    
    config_service = ConfigService()
    
    # Get logging configuration from config.json
    log_config = config_service._config.get('logging', {})
    log_folder = log_config.get('log_folder', 'log')
    log_file = log_config.get('log_file', 'data-ex-api.log')
    log_level = log_config.get('level', 'INFO')
    log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
    
    # Create log folder if it doesn't exist
    log_path = Path(log_folder)
    log_path.mkdir(exist_ok=True)
    
    # Build full log file path
    log_file_path = log_path / log_file
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.FileHandler(str(log_file_path)),
            logging.StreamHandler()
        ]
    )


app = create_app()


@app.route('/')
def root():
    """Root endpoint."""
    return jsonify({
        "message": "Instruments Validation API",
        "version": "1.0.0",
        "api_version": "v1",
        "documentation": {
            "swagger_ui": "/api-docs",
            "swagger_json": "/apispec.json"
        },
        "endpoints": {
            "instruments": {
                "get_by_ric": "/api/v1/instruments/ric/{ric}",
                "get_by_id": "/api/v1/instruments/id/{instrument_id}",
                "get_by_exchange": "/api/v1/instruments/exchange/{exchange}"
            },
            "rules": {
                "validate": "/api/v1/rules/validate/{product_type}/{exchange}",
                "validate_custom": "/api/v1/rules/validate-custom/{product_type}/{exchange}",
                "get_rules": "/api/v1/rules/rules/{product_type}/{exchange}",
                "get_rules_yaml": "/api/v1/rules/rules-yaml/{product_type}/{exchange}",
                "get_combined_rules": "/api/v1/rules/combined-rules/{product_type}/{exchange}",
                "get_combined_rules_details": "/api/v1/rules/combined-rules-details/{product_type}/{exchange}",
                "get_combined_rules_details_yaml": "/api/v1/rules/combined-rules-details-yaml/{product_type}/{exchange}?rule_name={rule_name}",
                "validate_by_masterid": "/api/v1/rules/validate-by-masterid/{master_id}/{combined_rule_name}?product_type={product_type}"
            },
            "validation_analytics": {
                "global_view": "/api/v1/validation/global-view?days={days}",
                "heatmap": "/api/v1/validation/heatmap?days={days}",
                "treemap": "/api/v1/validation/treemap?days={days}",
                "rule_failures": "/api/v1/validation/rule-failures?days={days}&limit={limit}",
                "combined_rule": "/api/v1/validation/combined-rule/{combined_rule_name}?days={days}",
                "exchange_results": "/api/v1/validation/exchange/{exchange}?days={days}&limit={limit}",
                "regional_trends": "/api/v1/validation/regional-trends?days={days}",
                "region_date_results": "/api/v1/validation/region-date/{region}/{date}?days={days}&limit={limit}"
            }
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


def get_environment():
    """
    Get environment from command line argument or environment variable.
    
    Returns:
        str: Environment name ('dev', 'uat', 'prod'). Defaults to 'dev'.
    """
    # Check command line arguments first
    if len(sys.argv) > 1:
        env = sys.argv[1].lower()
        if env in ['dev', 'uat', 'prod']:
            return env
        else:
            print(f"Warning: Invalid environment '{env}'. Using default 'dev'.")
    
    # Check environment variable
    env = os.getenv('ENV', 'dev').lower()
    if env not in ['dev', 'uat', 'prod']:
        print(f"Warning: Invalid ENV variable '{env}'. Using default 'dev'.")
        return 'dev'
    
    return env


if __name__ == '__main__':
    # Set environment before initializing logging and app
    env = get_environment()
    os.environ['ENV'] = env
    
    init_logging()
    # export()
    app.run(debug=True, host='0.0.0.0', port=5006)

