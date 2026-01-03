"""Rule controller for running validation rules per exchange."""

import logging
import traceback
import threading
from flask import Blueprint, request, jsonify, Response
from services.validation_service import ValidationService
from services.loader_factory import LoaderFactory
import yaml

logger = logging.getLogger(__name__)
rule_api = Blueprint('rule_api', __name__)

# Thread-local storage for services to avoid conflicts in concurrent requests
_thread_local = threading.local()


def get_validation_service(product_type='stock'):
    """Get or create a validation service instance for the current thread/request.
    
    This ensures each request gets its own service instance, preventing
    file handle conflicts and race conditions in parallel processing.
    
    Args:
        product_type: Product type ('stock', 'option', 'future'). Defaults to 'stock'.
    """
    cache_key = f'validation_service_{product_type}'
    
    if not hasattr(_thread_local, cache_key):
        loader_factory = LoaderFactory()
        loader = loader_factory.create_loader()
        exchange_map = loader_factory.get_exchange_map(product_type=product_type)
        setattr(_thread_local, cache_key, ValidationService(
            loader, 
            exchange_map=exchange_map, 
            product_type=product_type
        ))
    
    return getattr(_thread_local, cache_key)


def _parse_custom_rules():
    """Parse custom rules from request (GET or POST)."""
    if request.method == 'POST':
        data = request.get_json() or {}
        return data.get('custom_rule_names'), data.get('custom_rules')
    else:
        custom_rule_names_param = request.args.get('custom_rule_names')
        if custom_rule_names_param:
            return [name.strip() for name in custom_rule_names_param.split(",")], None
        return None, None


def _parse_custom_rule_names_from_query():
    """Parse comma-separated custom rule names from query parameter."""
    custom_rule_names_param = request.args.get('custom_rule_names')
    if custom_rule_names_param:
        return [name.strip() for name in custom_rule_names_param.split(",")]
    return None


def _handle_validation_error(e, exchange, product_type):
    """Handle validation errors with consistent error responses."""
    error_type = type(e).__name__
    error_msg = str(e)
    
    if isinstance(e, ValueError):
        logger.error(f"ValueError for {exchange}: {error_msg}")
        if "Exchange" in error_msg and "not found" in error_msg:
            validation_service = get_validation_service(product_type=product_type)
            return jsonify({
                "error": error_msg,
                "error_type": error_type,
                "available_exchanges": list(validation_service.exchange_map.keys()),
                "exchange_map": validation_service.exchange_map
            }), 404
        return jsonify({
            "error": error_msg,
            "error_type": error_type,
            "exchange": exchange,
            "product_type": product_type
        }), 404
    
    elif isinstance(e, FileNotFoundError):
        logger.error(f"FileNotFoundError for {exchange}: {error_msg}")
        validation_service = get_validation_service(product_type=product_type)
        return jsonify({
            "error": error_msg,
            "error_type": "FileNotFoundError",
            "exchange": exchange,
            "expected_file": validation_service.exchange_map.get(exchange, "unknown"),
            "exchange_map": validation_service.exchange_map
        }), 404
    
    else:
        logger.error(f"Unexpected error for {exchange} ({error_type}): {error_msg}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Validation error: {error_msg}",
            "error_type": error_type,
            "exchange": exchange,
            "product_type": product_type,
            "traceback": traceback.format_exc() if __debug__ else None
        }), 500


def _to_yaml_response(data, status_code=200):
    """Convert data to YAML response."""
    yaml_output = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return Response(yaml_output, mimetype='text/plain; charset=utf-8'), status_code


@rule_api.route('/validate/<product_type>/<exchange>', methods=['POST', 'GET'])
def validate_exchange(product_type, exchange):
    """
    Validate exchange data with base + exchange + custom rules
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, future, option]
      - name: exchange
        in: path
        type: string
        required: true
      - name: custom_rule_names
        in: query
        type: string
        required: false
        description: Comma-separated list of custom rule names (for GET requests)
    responses:
      200:
        description: Validation results
      404:
        description: Exchange not found or validation failed
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Validation request: product_type={product_type}, exchange={exchange}")
        custom_rule_names, custom_rules = _parse_custom_rules()
        
        validation_service = get_validation_service(product_type=product_type)
        results = validation_service.validate_exchange(
            exchange,
            custom_rule_names=custom_rule_names,
            custom_rules=custom_rules,
            product_type=product_type
        )
        
        logger.info(f"Validation successful for {exchange}")
        return jsonify(results)
    except (ValueError, FileNotFoundError, Exception) as e:
        return _handle_validation_error(e, exchange, product_type)


@rule_api.route('/validate-custom/<product_type>/<exchange>', methods=['POST', 'GET'])
def validate_exchange_custom(product_type, exchange):
    """
    Validate exchange data with ONLY custom rules (skips base and exchange rules)
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, future, option]
      - name: exchange
        in: path
        type: string
        required: true
    responses:
      200:
        description: Validation results (custom rules only)
      400:
        description: No custom rules provided
      404:
        description: Exchange not found
      500:
        description: Validation error
    """
    try:
        custom_rule_names, custom_rules = _parse_custom_rules()
        validation_service = get_validation_service(product_type=product_type)
        results = validation_service.validate_custom_only(
            exchange,
            custom_rule_names=custom_rule_names,
            custom_rules=custom_rules,
            product_type=product_type
        )
        return jsonify(results)
    except ValueError as e:
        status_code = 400 if "At least one custom rule" in str(e) else 404
        return jsonify({"error": str(e)}), status_code
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return jsonify({"error": f"Validation error: {str(e)}"}), 500


@rule_api.route('/rules/<product_type>/<exchange>', methods=['GET'])
def get_rules_for_exchange(product_type, exchange):
    """
    Get all rules that would be applied for a specific exchange and product type
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, future, option]
      - name: exchange
        in: path
        type: string
        required: true
      - name: custom_rule_names
        in: query
        type: string
        required: false
        description: Comma-separated list of custom rule names to include
    responses:
      200:
        description: List of rules
      404:
        description: Exchange not found
      500:
        description: Error retrieving rules
    """
    try:
        custom_rule_names = _parse_custom_rule_names_from_query()
        validation_service = get_validation_service(product_type=product_type)
        rules = validation_service.get_rules_for_exchange(
            exchange,
            product_type=product_type,
            custom_rule_names=custom_rule_names
        )
        return jsonify(rules)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error retrieving rules: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving rules: {str(e)}"}), 500


@rule_api.route('/rules-yaml/<product_type>/<exchange>', methods=['GET'])
def get_rules_for_exchange_yaml(product_type, exchange):
    """
    Get all rules that would be applied for a specific exchange and product type in YAML format
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, future, option]
      - name: exchange
        in: path
        type: string
        required: true
      - name: custom_rule_names
        in: query
        type: string
        required: false
        description: Comma-separated list of custom rule names to include
    responses:
      200:
        description: Rules in YAML format
      404:
        description: Exchange not found
      500:
        description: Error retrieving rules
    """
    try:
        custom_rule_names = _parse_custom_rule_names_from_query()
        validation_service = get_validation_service(product_type=product_type)
        rules = validation_service.get_rules_for_exchange(
            exchange,
            product_type=product_type,
            custom_rule_names=custom_rule_names
        )
        return _to_yaml_response(rules)
    except ValueError as e:
        return _to_yaml_response({"error": str(e)}, 404)
    except Exception as e:
        logger.error(f"Error retrieving rules: {e}", exc_info=True)
        return _to_yaml_response({"error": f"Error retrieving rules: {str(e)}"}, 500)


@rule_api.route('/combined-rules/<product_type>/<exchange>', methods=['GET'])
def get_combined_rule_names(product_type, exchange):
    """
    Get available combined rule names for a specific product type and exchange
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, stocks, future, option, options]
      - name: exchange
        in: path
        type: string
        required: true
    responses:
      200:
        description: List of available combined rule names
      500:
        description: Error retrieving combined rule names
    """
    try:
        validation_service = get_validation_service(product_type=product_type)
        result = validation_service.get_combined_rule_names(
            product_type=product_type,
            exchange=exchange
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error retrieving combined rule names: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving combined rule names: {str(e)}"}), 500


@rule_api.route('/combined-rules-details/<product_type>/<exchange>', methods=['GET'])
def get_combined_rule_details(product_type, exchange):
    """
    Get detailed information about combined rules for a specific product type and exchange
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, stocks, future, option, options]
      - name: exchange
        in: path
        type: string
        required: true
    responses:
      200:
        description: Detailed information about combined rules
      404:
        description: Exchange not found
      500:
        description: Error retrieving combined rule details
    """
    try:
        validation_service = get_validation_service(product_type=product_type)
        result = validation_service.get_combined_rule_details(
            product_type=product_type,
            exchange=exchange
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error retrieving combined rule details: {e}", exc_info=True)
        return jsonify({"error": f"Error retrieving combined rule details: {str(e)}"}), 500


@rule_api.route('/combined-rules-details-yaml/<product_type>/<exchange>', methods=['GET'])
def get_combined_rule_details_yaml(product_type, exchange):
    """
    Get detailed information about combined rules in YAML format
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, stocks, future, option, options]
      - name: exchange
        in: path
        type: string
        required: true
      - name: rule_name
        in: query
        type: string
        required: false
        description: Optional specific combined rule name to get details for
    responses:
      200:
        description: Combined rule details in YAML format
      404:
        description: Exchange not found or rule not found
      500:
        description: Error retrieving combined rule details
    """
    try:
        rule_name = request.args.get('rule_name')
        validation_service = get_validation_service(product_type=product_type)
        
        if rule_name:
            all_details = validation_service.get_combined_rule_details(
                product_type=product_type,
                exchange=exchange
            )
            
            combined_rules = all_details.get('combined_rules', [])
            specific_rule = next(
                (rule for rule in combined_rules if rule.get('name') == rule_name),
                None
            )
            
            if not specific_rule:
                return _to_yaml_response(
                    {"error": f"Combined rule '{rule_name}' not found"}, 
                    404
                )
            
            result = {
                "product_type": product_type,
                "exchange": exchange,
                "combined_rule": specific_rule
            }
        else:
            result = validation_service.get_combined_rule_details(
                product_type=product_type,
                exchange=exchange
            )
        
        return _to_yaml_response(result)
    except ValueError as e:
        return _to_yaml_response({"error": str(e)}, 404)
    except Exception as e:
        logger.error(f"Error retrieving combined rule details: {e}", exc_info=True)
        return _to_yaml_response(
            {"error": f"Error retrieving combined rule details: {str(e)}"}, 
            500
        )


@rule_api.route('/validate-by-masterid/<master_id>/<combined_rule_name>', methods=['GET'])
def validate_by_masterid(master_id, combined_rule_name):
    """
    Validate a single record by MasterId using a combined rule name
    ---
    tags:
      - Rules
    parameters:
      - name: master_id
        in: path
        type: string
        required: true
        description: MasterId of the record to validate
      - name: combined_rule_name
        in: path
        type: string
        required: true
        description: Name of the combined rule set to use for validation
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum: [stock, future, option]
    responses:
      200:
        description: Validation results for the record
      404:
        description: Record not found or rule not found
      500:
        description: Validation error
    """
    try:
        product_type = request.args.get('product_type', 'stock')
        validation_service = get_validation_service(product_type=product_type)
        result = validation_service.validate_record_by_masterid(
            master_id=master_id,
            combined_rule_name=combined_rule_name,
            product_type=product_type
        )
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return jsonify({"error": f"Validation error: {str(e)}"}), 500
