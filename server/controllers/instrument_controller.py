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
    if product_type not in ['stock', 'option', 'future']:
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
    if product_type not in ['stock', 'option', 'future']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    try:
        result, error_response = _get_instrument_by_id(instrument_id, product_type, exchange)
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
    if product_type not in ['stock', 'option', 'future']:
        return jsonify({"error": f"Invalid product_type '{product_type}'. Must be 'stock', 'option', or 'future'."}), 400
    
    try:
        result = _get_instruments_by_exchange(exchange, product_type, limit, offset)
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
