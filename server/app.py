"""Flask application for instruments validation API."""

import logging
import os
import sys
import time

from flask import Flask, jsonify, g, request
from flask_cors import CORS
from flask_caching import Cache
from flasgger import Swagger

from controllers.instrument_controller import instrument_api
from controllers.rule_controller import rule_api
from controllers.validation_controller import validation_api
from controllers.report_controller import report_api
from utils import QueryExporter

logger = logging.getLogger(__name__)

# Initialize Flask-Caching (will be configured in create_app once config is loaded)
cache = Cache()

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
    from config.config_service import ConfigService
    _cfg = ConfigService()

    server_cfg = _cfg.get_server_config()
    cache_cfg = _cfg.get_cache_config()

    app = Flask(__name__)
    cors_origins = server_cfg.get('cors_origins', '*')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.before_request
    def _start_timer():
        g._request_start = time.perf_counter()

    @app.after_request
    def _log_request(response):
        if hasattr(g, '_request_start'):
            elapsed_ms = (time.perf_counter() - g._request_start) * 1000
            logger.info(
                "[REQUEST] %s %s -> %s  %.1f ms",
                request.method, request.path, response.status_code, elapsed_ms,
            )
        return response

    # Initialize Flask-Caching with config-driven values
    cache.init_app(app, config={
        'CACHE_TYPE': cache_cfg.get('type', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': cache_cfg.get('default_timeout_seconds', 300),
    })
    
    # Initialize Swagger
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)
    
    app.register_blueprint(instrument_api, url_prefix='/api/v1/instruments/')
    app.register_blueprint(rule_api, url_prefix='/api/v1/rules/')
    app.register_blueprint(validation_api, url_prefix='/api/v1/validation/')
    app.register_blueprint(report_api, url_prefix='/api/v1/reports/')
    
    # Initialize cache for instrument_api blueprint (shares the same cache instance)
    from controllers.instrument_controller import init_cache
    init_cache(app, cache)
    
    return app
def export():
    """Export selected exchange data to CSV files (dev/utility only)."""
    _export_logger = logging.getLogger(__name__ + ".export")
    exporter = QueryExporter()
    exports = [
        ("SELECT * FROM StockMaster WHERE Exchange = 'XHKG'", "db_hkg.csv"),
        ("SELECT * FROM StockMaster WHERE Exchange = 'XTKS'", "db_tks.csv"),
        ("SELECT * FROM StockMaster WHERE Exchange = 'XNSE'", "db_nse.csv"),
    ]
    for query, filename in exports:
        csv_path = exporter.export_query_to_csv(query, filename)
        _export_logger.info("Exported to: %s", csv_path)


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
    
    import sys
    stream_handler = logging.StreamHandler()
    # Reconfigure stdout to UTF-8 so Unicode chars in log messages don't crash on Windows cp1252
    if hasattr(stream_handler.stream, 'reconfigure'):
        stream_handler.stream.reconfigure(encoding='utf-8', errors='replace')
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.FileHandler(str(log_file_path), encoding='utf-8'),
            stream_handler,
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


@app.route('/health/detailed')
def detailed_health_check():
    """Detailed health check endpoint with cache and connection pool stats."""
    from controllers.instrument_controller import get_service
    from loaders.database_loader import DatabaseDataLoader
    
    health_data = {
        "status": "healthy",
        "cache": {},
        "connection_pools": {}
    }
    
    # Get cache stats
    try:
        # SimpleCache doesn't expose stats directly, but we can check if it's initialized
        health_data["cache"]["type"] = "SimpleCache"
        health_data["cache"]["status"] = "initialized" if cache else "not_initialized"
    except Exception as e:
        health_data["cache"]["error"] = str(e)
    
    # Get connection pool stats for each product type
    try:
        from controllers.instrument_controller import _services_cache
        for product_type, service in _services_cache.items():
            if isinstance(service.loader, DatabaseDataLoader):
                pool_stats = service.loader.get_pool_stats()
                health_data["connection_pools"][product_type] = pool_stats
    except Exception as e:
        health_data["connection_pools"]["error"] = str(e)
    
    return jsonify(health_data)


_VALID_ENVS = ('dev', 'uat', 'prod')


def get_environment() -> str:
    """
    Resolve runtime environment from CLI arg → ENV var → 'dev' default.

    Returns:
        str: One of 'dev', 'uat', 'prod'.
    """
    if len(sys.argv) > 1:
        candidate = sys.argv[1].lower()
        if candidate in _VALID_ENVS:
            return candidate
        # Logger may not be configured yet; use stderr directly
        print(f"WARNING: Invalid environment argument '{candidate}'. Falling back to 'dev'.", file=sys.stderr)

    env = os.getenv('ENV', 'dev').lower()
    if env not in _VALID_ENVS:
        print(f"WARNING: Invalid ENV variable '{env}'. Falling back to 'dev'.", file=sys.stderr)
        return 'dev'
    return env


if __name__ == '__main__':
    env = get_environment()
    os.environ['ENV'] = env

    init_logging()

    from config.config_service import ConfigService
    _server_cfg = ConfigService().get_server_config()

    logger.info("Starting server | env=%s  host=%s  port=%s  debug=%s",
                env,
                _server_cfg.get('host', '0.0.0.0'),
                _server_cfg.get('port', 5006),
                _server_cfg.get('debug', True))

    app.run(
        debug=_server_cfg.get('debug', True),
        host=_server_cfg.get('host', '0.0.0.0'),
        port=_server_cfg.get('port', 5006),
    )

