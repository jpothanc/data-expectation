"""Rule controller — HTTP endpoints for rule inspection and exchange validation.

Responsibilities of this module:
  - Declare Flask routes (Blueprint).
  - Parse and validate request parameters.
  - Delegate to ValidationService.
  - Translate domain exceptions into consistent HTTP responses.

Nothing else.
"""

import logging
import threading
from flask import Blueprint, request, jsonify, Response
from services.validation_service import ValidationService
from services.loader_factory import LoaderFactory
from services.exceptions import ExchangeNotFoundError, ProcessorSetupError, DataFileNotFoundError
from controllers.utils import bad_request, not_found, server_error
import yaml

logger = logging.getLogger(__name__)
rule_api = Blueprint('rule_api', __name__)

# Thread-local storage ensures each worker thread gets its own service instance,
# preventing file-handle conflicts when GE validators are used concurrently.
_thread_local = threading.local()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_validation_service(product_type: str = 'stock') -> ValidationService:
    """Return a thread-local ValidationService, creating it on first use per thread."""
    cache_key = f'validation_service_{product_type}'
    if not hasattr(_thread_local, cache_key):
        factory = LoaderFactory()
        setattr(_thread_local, cache_key, ValidationService(
            factory.create_loader(),
            exchange_map=factory.get_exchange_map(product_type=product_type),
            product_type=product_type,
        ))
    return getattr(_thread_local, cache_key)


def _parse_custom_rules() -> tuple[list[str] | None, list | None]:
    """Extract custom rule names and definitions from GET query params or POST body."""
    if request.method == 'POST':
        body = request.get_json() or {}
        return body.get('custom_rule_names'), body.get('custom_rules')

    raw = request.args.get('custom_rule_names')
    if raw:
        return [name.strip() for name in raw.split(',')], None
    return None, None


def _parse_custom_rule_names_from_query() -> list[str] | None:
    """Extract comma-separated custom rule names from the query string."""
    raw = request.args.get('custom_rule_names')
    return [name.strip() for name in raw.split(',')] if raw else None


def _handle_validation_error(e: Exception, exchange: str, product_type: str) -> tuple:
    """Translate a service-layer exception into a consistent HTTP error response.

    Uses the typed exception hierarchy from ``services.exceptions`` — no
    string-inspection of error messages required.
    """
    if isinstance(e, ExchangeNotFoundError):
        return not_found(str(e), available_exchanges=e.available, exchange=exchange)

    if isinstance(e, ProcessorSetupError):
        logger.error("Processor setup failure for %s/%s: %s", product_type, exchange, e)
        return server_error(str(e), exchange=exchange, product_type=product_type)

    if isinstance(e, DataFileNotFoundError):
        logger.error("Data file missing for %s/%s: %s", product_type, exchange, e)
        return not_found(str(e), exchange=exchange)

    if isinstance(e, (IOError, OSError)):
        logger.error("I/O error for %s/%s: %s", product_type, exchange, e)
        return server_error(str(e), exchange=exchange, product_type=product_type)

    if isinstance(e, FileNotFoundError):
        logger.error("FileNotFoundError for %s/%s: %s", product_type, exchange, e)
        return not_found(str(e), exchange=exchange)

    if isinstance(e, ValueError):
        logger.error("ValueError for %s/%s: %s", product_type, exchange, e)
        return not_found(str(e), exchange=exchange, product_type=product_type)

    logger.error("Unexpected error for %s/%s (%s): %s",
                 product_type, exchange, type(e).__name__, e, exc_info=True)
    return server_error(
        f"Unexpected validation error: {e}",
        exchange=exchange,
        product_type=product_type,
        error_type=type(e).__name__,
    )


def _to_yaml_response(data: dict, status_code: int = 200) -> tuple:
    """Serialise *data* to a plain-text YAML response."""
    yaml_output = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return Response(yaml_output, mimetype='text/plain; charset=utf-8'), status_code


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

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
        enum: [stock, future, option, multileg]
      - name: exchange
        in: path
        type: string
        required: true
      - name: custom_rule_names
        in: query
        type: string
        required: false
        description: Comma-separated list of custom rule names (GET requests)
    responses:
      200:
        description: Validation results
      404:
        description: Exchange not found
      500:
        description: Internal server error
    """
    try:
        logger.info("Validation request: product_type=%s, exchange=%s", product_type, exchange)
        custom_rule_names, custom_rules = _parse_custom_rules()
        results = _get_validation_service(product_type).validate_exchange(
            exchange,
            custom_rule_names=custom_rule_names,
            custom_rules=custom_rules,
            product_type=product_type,
        )
        logger.info("Validation successful for %s/%s", product_type, exchange)
        return jsonify(results)
    except Exception as e:
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
        enum: [stock, future, option, multileg]
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
        results = _get_validation_service(product_type).validate_custom_only(
            exchange,
            custom_rule_names=custom_rule_names,
            custom_rules=custom_rules,
            product_type=product_type,
        )
        return jsonify(results)
    except ValueError as e:
        status = 400 if "At least one custom rule" in str(e) else 404
        return jsonify({"error": str(e)}), status
    except FileNotFoundError as e:
        return not_found(str(e))
    except Exception as e:
        logger.error("Custom validation error for %s/%s: %s", product_type, exchange, e, exc_info=True)
        return server_error(f"Validation error: {e}")


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
        enum: [stock, future, option, multileg]
      - name: exchange
        in: path
        type: string
        required: true
      - name: custom_rule_names
        in: query
        type: string
        required: false
    responses:
      200:
        description: List of rules
      404:
        description: Exchange not found
      500:
        description: Error retrieving rules
    """
    try:
        rules = _get_validation_service(product_type).get_rules_for_exchange(
            exchange,
            product_type=product_type,
            custom_rule_names=_parse_custom_rule_names_from_query(),
        )
        return jsonify(rules)
    except ValueError as e:
        return not_found(str(e))
    except Exception as e:
        logger.error("Error retrieving rules for %s/%s: %s", product_type, exchange, e, exc_info=True)
        return server_error(f"Error retrieving rules: {e}")


@rule_api.route('/rules-yaml/<product_type>/<exchange>', methods=['GET'])
def get_rules_for_exchange_yaml(product_type, exchange):
    """
    Get all rules for a specific exchange and product type in YAML format
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, future, option, multileg]
      - name: exchange
        in: path
        type: string
        required: true
      - name: custom_rule_names
        in: query
        type: string
        required: false
    responses:
      200:
        description: Rules in YAML format
      404:
        description: Exchange not found
      500:
        description: Error retrieving rules
    """
    try:
        rules = _get_validation_service(product_type).get_rules_for_exchange(
            exchange,
            product_type=product_type,
            custom_rule_names=_parse_custom_rule_names_from_query(),
        )
        return _to_yaml_response(rules)
    except ValueError as e:
        return _to_yaml_response({"error": str(e)}, 404)
    except Exception as e:
        logger.error("Error retrieving rules (YAML) for %s/%s: %s",
                     product_type, exchange, e, exc_info=True)
        return _to_yaml_response({"error": f"Error retrieving rules: {e}"}, 500)


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
        enum: [stock, stocks, future, option, options, multileg, multilegs]
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
        result = _get_validation_service(product_type).get_combined_rule_names(
            product_type=product_type,
            exchange=exchange,
        )
        return jsonify(result)
    except Exception as e:
        logger.error("Error retrieving combined rule names for %s/%s: %s",
                     product_type, exchange, e, exc_info=True)
        return server_error(f"Error retrieving combined rule names: {e}")


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
        enum: [stock, stocks, future, option, options, multileg, multilegs]
      - name: exchange
        in: path
        type: string
        required: true
    responses:
      200:
        description: Detailed combined rule information
      404:
        description: Exchange not found
      500:
        description: Error retrieving combined rule details
    """
    try:
        result = _get_validation_service(product_type).get_combined_rule_details(
            product_type=product_type,
            exchange=exchange,
        )
        return jsonify(result)
    except ValueError as e:
        return not_found(str(e))
    except Exception as e:
        logger.error("Error retrieving combined rule details for %s/%s: %s",
                     product_type, exchange, e, exc_info=True)
        return server_error(f"Error retrieving combined rule details: {e}")


@rule_api.route('/combined-rules-details-yaml/<product_type>/<exchange>', methods=['GET'])
def get_combined_rule_details_yaml(product_type, exchange):
    """
    Get detailed combined rule information in YAML format
    ---
    tags:
      - Rules
    parameters:
      - name: product_type
        in: path
        type: string
        required: true
        enum: [stock, stocks, future, option, options, multileg, multilegs]
      - name: exchange
        in: path
        type: string
        required: true
      - name: rule_name
        in: query
        type: string
        required: false
        description: Optional specific combined rule name to filter
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
        all_details = _get_validation_service(product_type).get_combined_rule_details(
            product_type=product_type,
            exchange=exchange,
        )

        if rule_name:
            specific = next(
                (r for r in all_details.get('combined_rules', []) if r.get('name') == rule_name),
                None,
            )
            if not specific:
                return _to_yaml_response(
                    {"error": f"Combined rule '{rule_name}' not found"}, 404
                )
            result = {"product_type": product_type, "exchange": exchange, "combined_rule": specific}
        else:
            result = all_details

        return _to_yaml_response(result)
    except ValueError as e:
        return _to_yaml_response({"error": str(e)}, 404)
    except Exception as e:
        logger.error("Error retrieving combined rule details (YAML) for %s/%s: %s",
                     product_type, exchange, e, exc_info=True)
        return _to_yaml_response({"error": f"Error retrieving combined rule details: {e}"}, 500)


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
      - name: combined_rule_name
        in: path
        type: string
        required: true
      - name: product_type
        in: query
        type: string
        required: false
        default: stock
        enum: [stock, future, option, multileg]
    responses:
      200:
        description: Validation results for the record
      404:
        description: Record not found or rule not found
      500:
        description: Validation error
    """
    product_type = request.args.get('product_type', 'stock')
    try:
        result = _get_validation_service(product_type).validate_record_by_masterid(
            master_id=master_id,
            combined_rule_name=combined_rule_name,
            product_type=product_type,
        )
        return jsonify(result)
    except (ValueError, FileNotFoundError) as e:
        return not_found(str(e))
    except Exception as e:
        logger.error("Validation error for master_id=%s rule=%s: %s",
                     master_id, combined_rule_name, e, exc_info=True)
        return server_error(f"Validation error: {e}")
