"""Instrument controller — HTTP routing for instrument lookup and exchange listing.

Responsibilities of this module:
  - Declare Flask routes (Blueprint).
  - Parse and validate request parameters.
  - Delegate all data-retrieval to InstrumentService / ConfigService.
  - Serialise service results or errors into JSON responses.

Nothing else.  Service creation, caching, and business logic all live in
the service layer.
"""
from __future__ import annotations

import logging
from flask import Blueprint, request, jsonify
from services.instrument_service import InstrumentService
from services.loader_factory import LoaderFactory
from config.config_service import ConfigService
from controllers.utils import validate_product_type, bad_request, not_found, server_error

logger = logging.getLogger(__name__)
instrument_api = Blueprint('instrument_api', __name__)

# ---------------------------------------------------------------------------
# Module-level singletons — initialised once, reused across requests.
# These are application-scoped resources; a proper DI container would own
# them, but in this Flask blueprint pattern they live here.
# ---------------------------------------------------------------------------

_loader_factory: LoaderFactory | None = None
_services_cache: dict[str, InstrumentService] = {}

# Shared cache instance — injected by app.py via init_cache().
_cache = None

# Cache TTLs — loaded from config on first access.
_CACHE_EXCHANGE_LIST_TTL: int | None = None
_CACHE_VALIDATION_TTL: int | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_cache_ttls() -> tuple[int, int]:
    """Return (exchange_list_ttl, validation_ttl) from config, loaded once."""
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
    """Return the cache instance.  Raises if init_cache() was not called."""
    if _cache is None:
        raise RuntimeError(
            "Cache has not been initialised. "
            "Call controllers.instrument_controller.init_cache(app, cache) during startup."
        )
    return _cache


def init_cache(app, cache_instance) -> None:
    """Inject the application-level cache instance into this blueprint."""
    global _cache
    _cache = cache_instance


def get_service(product_type: str = 'stock') -> InstrumentService:
    """Return a cached InstrumentService for *product_type*, creating it on first use."""
    global _loader_factory, _services_cache

    if product_type not in _services_cache:
        if _loader_factory is None:
            _loader_factory = LoaderFactory()

        loader = _loader_factory.create_loader()
        exchange_map = _loader_factory.get_exchange_map(product_type=product_type)
        _services_cache[product_type] = InstrumentService(
            loader,
            exchange_map=exchange_map,
            product_type=product_type,
        )

        from loaders.database_loader import DatabaseDataLoader
        if isinstance(loader, DatabaseDataLoader):
            logger.info("Database loader initialised for %s: %s",
                        product_type, loader.get_pool_stats())

    return _services_cache[product_type]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

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
        enum: [stock, option, future, multileg]
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
    product_type, err = validate_product_type(request.args.get('product_type'))
    if err:
        return err

    exchange = request.args.get('exchange')

    try:
        service = get_service(product_type)
        results = service.find_by_ric(ric, exchange)
        if not results:
            return not_found(f"Instrument with RIC '{ric}' not found"
                             + (f" in exchange '{exchange}'" if exchange else ""))
        return jsonify(results[0] if len(results) == 1 else results)
    except (ValueError, FileNotFoundError) as e:
        return not_found(str(e))


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
        enum: [stock, option, future, multileg]
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
    product_type, err = validate_product_type(request.args.get('product_type'))
    if err:
        return err

    exchange = request.args.get('exchange')

    try:
        service = get_service(product_type)
        result = service.find_by_id(instrument_id, exchange)
        if not result:
            return not_found(f"Instrument with ID '{instrument_id}' not found"
                             + (f" in exchange '{exchange}'" if exchange else ""))
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return not_found(str(e))


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
        enum: [stock, option, future, multileg]
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
    product_type, err = validate_product_type(request.args.get('product_type'))
    if err:
        return err

    cache = get_cache()
    cache_key = f"exchanges:{product_type}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Cache HIT — exchanges: product_type=%s", product_type)
        return jsonify(cached)

    logger.info("Cache MISS — exchanges: product_type=%s", product_type)
    try:
        exchange_map = ConfigService().get_csv_exchange_map(product_type)
        if not exchange_map:
            return not_found(f"No exchanges found for product_type '{product_type}'")

        exchanges = list(exchange_map.keys())
        exchange_list_ttl, _ = _get_cache_ttls()
        cache.set(cache_key, exchanges, timeout=exchange_list_ttl)
        return jsonify(exchanges)
    except Exception as e:
        logger.error("Error retrieving exchanges: %s", e, exc_info=True)
        return server_error(f"Error retrieving exchanges: {e}")


@instrument_api.route('/exchanges-by-region', methods=['GET'])
def get_exchanges_by_region():
    """
    Get exchanges organised by region and product type
    ---
    tags:
      - Instruments
    parameters:
      - name: product_type
        in: query
        type: string
        required: false
        enum: [stock, option, future, multileg]
    responses:
      200:
        description: Exchanges organised by region and product type
    """
    try:
        raw_product_type = request.args.get('product_type')
        config_service = ConfigService()
        regions_config = config_service.get_regions_config()

        if raw_product_type:
            product_type, err = validate_product_type(raw_product_type)
            if err:
                return err
            # Filter regions to only include the requested product type.
            filtered = {
                region: {product_type: products[product_type]}
                for region, products in regions_config.items()
                if product_type in products
            }
            return jsonify({"regions": filtered, "product_type": product_type})

        return jsonify({"regions": regions_config, "count": len(regions_config)})
    except Exception as e:
        logger.error("Error retrieving exchanges by region: %s", e, exc_info=True)
        return server_error(f"Error retrieving exchanges by region: {e}")


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
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum: [stock, option, future, multileg]
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
    product_type, err = validate_product_type(request.args.get('product_type'))
    if err:
        return err

    column = request.args.get('column', '').strip()
    values = request.args.getlist('values')
    include_missing = request.args.get('missing', 'false').lower() == 'true'

    if not column:
        return bad_request("column parameter is required")

    if not values and not include_missing:
        return jsonify({"exchange": exchange, "column": column, "count": 0, "instruments": []}), 200

    try:
        result = get_service(product_type).filter_by_column_values(
            exchange=exchange.upper(),
            column=column,
            values=values,
            include_missing=include_missing,
        )
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return not_found(str(e))
    except Exception as e:
        logger.error("Error filtering instruments for %s: %s", exchange, e, exc_info=True)
        return server_error(f"Error filtering instruments: {e}")


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
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum: [stock, option, future, multileg]
      - name: limit
        in: query
        type: integer
        required: false
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
    responses:
      200:
        description: List of instruments
      400:
        description: Invalid product_type parameter
      404:
        description: Exchange not found
    """
    product_type, err = validate_product_type(request.args.get('product_type'))
    if err:
        return err

    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)

    cache = get_cache()
    cache_key = f"instruments:{product_type}:{exchange}:{limit}:{offset}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Cache HIT — instruments: exchange=%s product_type=%s", exchange, product_type)
        return jsonify(cached)

    logger.info("Cache MISS — instruments: exchange=%s product_type=%s", exchange, product_type)
    try:
        result = get_service(product_type).get_by_exchange(exchange, limit, offset)
        _, validation_ttl = _get_cache_ttls()
        cache.set(cache_key, result, timeout=validation_ttl)
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return not_found(str(e))
