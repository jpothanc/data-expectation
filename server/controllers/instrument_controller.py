"""Instrument controller for retrieving instrument data."""

import logging
from flask import Blueprint, request, jsonify
from services.instrument_service import InstrumentService
from services.loader_factory import LoaderFactory
from config.config_service import ConfigService

logger = logging.getLogger(__name__)
instrument_api = Blueprint('instrument_api', __name__)

# Service factory for lazy initialization
_loader_factory = None
_services_cache = {}


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


# Stock endpoints
@instrument_api.route('/ric/<ric>', methods=['GET'])
def get_stock_by_ric(ric):
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
    exchange = request.args.get('exchange')
    
    try:
        result, error_response = _get_instrument_by_ric(ric, 'stock', exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/id/<instrument_id>', methods=['GET'])
def get_stock_by_id(instrument_id):
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
    exchange = request.args.get('exchange')
    
    try:
        result, error_response = _get_instrument_by_id(instrument_id, 'stock', exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/exchanges', methods=['GET'])
def get_all_exchanges():
    """
    Get all configured exchanges
    ---
    tags:
      - Instruments
    responses:
      200:
        description: List of all configured exchanges
    """
    try:
        result = get_service('stock').get_all_exchanges()
        return jsonify(result)
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
        enum: [stock, option, future]
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


@instrument_api.route('/exchange/<exchange>', methods=['GET'])
def get_stocks_by_exchange(exchange):
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
      404:
        description: Exchange not found
    """
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    try:
        result = _get_instruments_by_exchange(exchange, 'stock', limit, offset)
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


# Futures endpoints
@instrument_api.route('/future/ric/<ric>', methods=['GET'])
def get_future_by_ric(ric):
    """
    Get future instrument by RIC code
    ---
    tags:
      - Instruments
    parameters:
      - name: ric
        in: path
        type: string
        required: true
        description: Reuters Instrument Code
      - name: exchange
        in: query
        type: string
        required: false
        description: Exchange code to limit search
    responses:
      200:
        description: Future instrument found
      404:
        description: Future instrument not found
    """
    exchange = request.args.get('exchange')
    
    try:
        result, error_response = _get_instrument_by_ric(ric, 'future', exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/future/id/<instrument_id>', methods=['GET'])
def get_future_by_id(instrument_id):
    """
    Get future instrument by MasterId
    ---
    tags:
      - Instruments
    parameters:
      - name: instrument_id
        in: path
        type: string
        required: true
        description: MasterId of the future instrument
      - name: exchange
        in: query
        type: string
        required: false
        description: Exchange code to limit search
    responses:
      200:
        description: Future instrument found
      404:
        description: Future instrument not found
    """
    exchange = request.args.get('exchange')
    
    try:
        result, error_response = _get_instrument_by_id(instrument_id, 'future', exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/future/exchange/<exchange>', methods=['GET'])
def get_futures_by_exchange(exchange):
    """
    Get all future instruments for a specific exchange
    ---
    tags:
      - Instruments
    parameters:
      - name: exchange
        in: path
        type: string
        required: true
        description: Exchange code
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
        description: List of future instruments
      404:
        description: Exchange not found
    """
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    try:
        result = _get_instruments_by_exchange(exchange, 'future', limit, offset)
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


# Options endpoints
@instrument_api.route('/option/ric/<ric>', methods=['GET'])
def get_option_by_ric(ric):
    """
    Get option instrument by RIC code
    ---
    tags:
      - Instruments
    parameters:
      - name: ric
        in: path
        type: string
        required: true
        description: Reuters Instrument Code
      - name: exchange
        in: query
        type: string
        required: false
        description: Exchange code to limit search
    responses:
      200:
        description: Option instrument found
      404:
        description: Option instrument not found
    """
    exchange = request.args.get('exchange')
    
    try:
        result, error_response = _get_instrument_by_ric(ric, 'option', exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/option/id/<instrument_id>', methods=['GET'])
def get_option_by_id(instrument_id):
    """
    Get option instrument by MasterId
    ---
    tags:
      - Instruments
    parameters:
      - name: instrument_id
        in: path
        type: string
        required: true
        description: MasterId of the option instrument
      - name: exchange
        in: query
        type: string
        required: false
        description: Exchange code to limit search
    responses:
      200:
        description: Option instrument found
      404:
        description: Option instrument not found
    """
    exchange = request.args.get('exchange')
    
    try:
        result, error_response = _get_instrument_by_id(instrument_id, 'option', exchange)
        if error_response:
            return error_response
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404


@instrument_api.route('/option/exchange/<exchange>', methods=['GET'])
def get_options_by_exchange(exchange):
    """
    Get all option instruments for a specific exchange
    ---
    tags:
      - Instruments
    parameters:
      - name: exchange
        in: path
        type: string
        required: true
        description: Exchange code
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
        description: List of option instruments
      404:
        description: Exchange not found
    """
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    try:
        result = _get_instruments_by_exchange(exchange, 'option', limit, offset)
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
