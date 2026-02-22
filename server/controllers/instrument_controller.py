"""Instrument controller for retrieving instrument data."""

import logging
from flask import Blueprint, request, jsonify, current_app
from services.instrument_service import InstrumentService
from services.loader_factory import LoaderFactory
from config.config_service import ConfigService

logger = logging.getLogger(__name__)
instrument_api = Blueprint('instrument_api', __name__)

# Service factory for lazy initialization
_loader_factory = None
_services_cache = {}

# Cache instance (will be initialized in app.py)
_cache = None

# Cache timeouts — loaded from config on first use
_CACHE_EXCHANGE_LIST_TTL: int | None = None
_CACHE_VALIDATION_TTL: int | None = None


def _get_cache_ttls() -> tuple[int, int]:
    """Return (exchange_list_ttl, validation_ttl) from config, cached after first load."""
    global _CACHE_EXCHANGE_LIST_TTL, _CACHE_VALIDATION_TTL
    if _CACHE_EXCHANGE_LIST_TTL is None:
        try:
            cache_cfg = ConfigService().get_cache_config()
            _CACHE_EXCHANGE_LIST_TTL = cache_cfg.get('exchange_list_timeout_seconds', 300)
            _CACHE_VALIDATION_TTL = cache_cfg.get('validation_timeout_seconds', 60)
        except Exception:
            _CACHE_EXCHANGE_LIST_TTL, _CACHE_VALIDATION_TTL = 300, 60
    return _CACHE_EXCHANGE_LIST_TTL, _CACHE_VALIDATION_TTL

def get_cache():
    """Get the cache instance from Flask app."""
    global _cache
    if _cache is None:
        # Cache should be initialized by init_cache() before use
        # This is a fallback that initializes if called before init_cache
        try:
            from flask_caching import Cache
            _cache = Cache()
            _cache.init_app(current_app._get_current_object())
        except RuntimeError:
            # Outside of request context - cache will be initialized later
            pass
    return _cache


def get_service(product_type='stock'):
    """Get or create instrument service for a product type."""
    global _loader_factory, _services_cache
    
    if product_type not in _services_cache:
        if _loader_factory is None:
            _loader_factory = LoaderFactory()
        
        loader = _loader_factory.create_loader()
        exchange_map = _loader_factory.get_exchange_map(product_type=product_type)
        _services_cache[product_type] = InstrumentService(
            loader, 
            exchange_map=exchange_map, 
            product_type=product_type
        )
        
        # Log connection pool stats if using database loader
        from loaders.database_loader import DatabaseDataLoader
        if isinstance(loader, DatabaseDataLoader):
            pool_stats = loader.get_pool_stats()
            logger.info(f"Database loader initialized for {product_type}: {pool_stats}")
    
    return _services_cache[product_type]


def _handle_instrument_error(e, identifier, identifier_type='RIC', exchange=None):
    """Helper function to format error responses."""
    error_msg = f"{identifier_type} '{identifier}' not found"
    if exchange:
        error_msg += f" in exchange '{exchange}'"
    return jsonify({"error": error_msg}), 404


def _get_instrument_by_ric(ric, product_type='stock', exchange=None):
    """Helper function to get instrument by RIC."""
    service = get_service(product_type)
    results = service.find_by_ric(ric, exchange)
    
    if not results:
        return None, _handle_instrument_error(None, ric, 'Instrument with RIC', exchange)
    
    return (results[0] if len(results) == 1 else results), None


def _get_instrument_by_id(instrument_id, product_type='stock', exchange=None):
    """Helper function to get instrument by ID."""
    service = get_service(product_type)
    result = service.find_by_id(instrument_id, exchange)
    
    if not result:
        return None, _handle_instrument_error(None, instrument_id, 'Instrument with ID', exchange)
    
    return result, None


def _get_instruments_by_exchange(exchange, product_type='stock', limit=None, offset=0):
    """Helper function to get instruments by exchange."""
    service = get_service(product_type)
    return service.get_by_exchange(exchange, limit, offset)


# Unified endpoints with product_type parameter

@instrument_api.route('/ric/<ric>', methods=['GET'])
def get_instrument_by_ric(ric):
    """
    Get instrument by RIC code
    ---
    tags:
      - Instruments
    parameters:
      - name: ric
        in: path
        type: string
        required: true
        description: Reuters Instrument Code (e.g., "0005.HK")
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum:
          - stock
          - option
          - future
          - multileg
        description: Product type (stock, option, or future)
      - name: exchange
        in: query
        type: string
        required: false
        description: Exchange code to limit search
    responses:
      200:
        description: Instrument found
      400:
        description: Invalid product_type parameter
      404:
        description: Instrument not found
    """
    product_type = request.args.get('product_type', 'stock').lower()
    exchange = request.args.get('exchange')
    
    # Validate product_type
    if product_type not in ['stock', 'option', 'future', 'multileg']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    try:
        result, error_response = _get_instrument_by_ric(ric, product_type, exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/id/<instrument_id>', methods=['GET'])
def get_instrument_by_id(instrument_id):
    """
    Get instrument by MasterId
    ---
    tags:
      - Instruments
    parameters:
      - name: instrument_id
        in: path
        type: string
        required: true
        description: MasterId of the instrument
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum:
          - stock
          - option
          - future
          - multileg
        description: Product type (stock, option, or future)
      - name: exchange
        in: query
        type: string
        required: false
        description: Exchange code to limit search
    responses:
      200:
        description: Instrument found
      404:
        description: Instrument not found
    """
    product_type = request.args.get('product_type', 'stock').lower()
    exchange = request.args.get('exchange')
    
    # Validate product_type
    if product_type not in ['stock', 'option', 'future', 'multileg']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    try:
        result, error_response = _get_instrument_by_id(instrument_id, product_type, exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


def init_cache(app, cache_instance):
    """Initialize cache for this blueprint (shares cache instance from app.py)."""
    global _cache
    _cache = cache_instance


@instrument_api.route('/exchanges', methods=['GET'])
def get_all_exchanges():
    """
    Get all configured exchanges for a specific product type
    ---
    tags:
      - Instruments
    parameters:
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum:
          - stock
          - option
          - future
          - multileg
        description: Product type to filter exchanges
    responses:
      200:
        description: List of exchange codes for the specified product type
      400:
        description: Invalid product_type parameter
      404:
        description: No exchanges found for the specified product type
      500:
        description: Error retrieving exchanges
    """
    product_type = request.args.get('product_type', 'stock').lower()
    
    # Validate product_type
    if product_type not in ['stock', 'option', 'future', 'multileg']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    # Try to get from cache
    cache = get_cache()
    cache_key = f"exchanges:{product_type}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Cache HIT for exchanges endpoint: product_type={product_type}")
        return jsonify(cached_result)
    
    logger.info(f"Cache MISS for exchanges endpoint: product_type={product_type}")
    try:
        config_service = ConfigService()
        exchange_map = config_service.get_csv_exchange_map(product_type)
        
        if not exchange_map:
            return jsonify({"error": f"No exchanges found for product_type '{product_type}'"}), 404
        
        # Extract exchange codes (keys) from exchange_map
        exchanges = list(exchange_map.keys())
        
        exchange_list_ttl, _ = _get_cache_ttls()
        cache.set(cache_key, exchanges, timeout=exchange_list_ttl)
        
        return jsonify(exchanges)
    except Exception as e:
        logger.error(f"Error retrieving exchanges: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving exchanges: {str(e)}"}), 500


@instrument_api.route('/exchanges-by-region', methods=['GET'])
def get_exchanges_by_region():
    """
    Get exchanges organized by region and product type (comma-separated format)
    ---
    tags:
      - Instruments
    parameters:
      - name: product_type
        in: query
        type: string
        required: false
        description: Filter by product type (stock, option, future)
        enum: [stock, option, future, multileg]
    responses:
      200:
        description: Exchanges organized by region and product type
    """
    try:
        product_type = request.args.get('product_type')
        config_service = ConfigService()
        regions_config = config_service._config.get('regions', {})
        
        if product_type:
            normalized_type = config_service._normalize_product_type(product_type)
            filtered_regions = {
                region: {normalized_type: products[normalized_type]}
                for region, products in regions_config.items()
                if normalized_type in products
            }
            return jsonify({
                "regions": filtered_regions,
                "product_type": normalized_type
            })
        
        return jsonify({
            "regions": regions_config,
            "count": len(regions_config)
        })
    except Exception as e:
        logger.error(f"Error retrieving exchanges by region: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving exchanges by region: {str(e)}"}), 500


@instrument_api.route('/exchange/<exchange>/filter', methods=['GET'])
def filter_instruments_by_exchange(exchange):
    """
    Return only the instruments from an exchange that match specific column values.
    Much more efficient than fetching all instruments and filtering client-side.
    ---
    tags:
      - Instruments
    parameters:
      - name: exchange
        in: path
        type: string
        required: true
        description: Exchange code (e.g., XHKG, XTKS)
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum:
          - stock
          - option
          - future
          - multileg
        description: Product type
      - name: column
        in: query
        type: string
        required: true
        description: Column name to filter on (e.g., MasterId, Currency)
      - name: values
        in: query
        type: array
        items:
          type: string
        collectionFormat: multi
        required: false
        description: Values to match (repeatable, e.g. values=2001&values=2002)
      - name: missing
        in: query
        type: boolean
        required: false
        default: false
        description: Also include instruments where the column is null/empty
    responses:
      200:
        description: Filtered list of matching instruments
      400:
        description: Missing required parameters
      404:
        description: Exchange not found
    """
    product_type = request.args.get('product_type', 'stock').lower()
    column = request.args.get('column', '').strip()
    values = request.args.getlist('values')
    include_missing = request.args.get('missing', 'false').lower() == 'true'

    if product_type not in ['stock', 'option', 'future', 'multileg']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400

    if not column:
        return jsonify({"error": "column parameter is required"}), 400

    if not values and not include_missing:
        return jsonify({"exchange": exchange, "column": column, "count": 0, "instruments": []}), 200

    try:
        service = get_service(product_type)
        result = service.filter_by_column_values(
            exchange=exchange.upper(),
            column=column,
            values=values,
            include_missing=include_missing,
        )
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error filtering instruments for {exchange}: {e}", exc_info=True)
        return jsonify({"error": f"Error filtering instruments: {str(e)}"}), 500


@instrument_api.route('/exchange/<exchange>', methods=['GET'])
def get_instruments_by_exchange(exchange):
    """
    Get all instruments for a specific exchange
    ---
    tags:
      - Instruments
    parameters:
      - name: exchange
        in: path
        type: string
        required: true
        description: Exchange code
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum:
          - stock
          - option
          - future
          - multileg
        description: Product type (stock, option, or future)
      - name: limit
        in: query
        type: integer
        required: false
        description: Maximum number of results
      - name: offset
        in: query
        type: integer
        required: false
        description: Offset for pagination
        default: 0
    responses:
      200:
        description: List of instruments
      400:
        description: Invalid product_type parameter
      404:
        description: Exchange not found
    """
    product_type = request.args.get('product_type', 'stock').lower()
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # Validate product_type
    if product_type not in ['stock', 'option', 'future', 'multileg']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    # Try to get from cache
    cache = get_cache()
    cache_key = f"instruments:{product_type}:{exchange}:{limit}:{offset}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Cache HIT for instruments endpoint: exchange={exchange}, product_type={product_type}, limit={limit}, offset={offset}")
        return jsonify(cached_result)
    
    logger.info(f"Cache MISS for instruments endpoint: exchange={exchange}, product_type={product_type}, limit={limit}, offset={offset}")
    try:
        result = _get_instruments_by_exchange(exchange, product_type, limit, offset)
        
        _, validation_ttl = _get_cache_ttls()
        cache.set(cache_key, result, timeout=validation_ttl)
        
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
