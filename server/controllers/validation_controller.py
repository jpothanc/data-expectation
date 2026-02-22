"""Validation analytics controller for chart data endpoints.

This module contains only HTTP routing and request/response handling.
All business logic lives in the service layer (services/).
"""

import logging
import threading
from flask import Blueprint, request, jsonify
from services.validation_analytics_service import ValidationAnalyticsService

logger = logging.getLogger(__name__)
validation_api = Blueprint('validation_api', __name__)

# Thread-local storage for services
_thread_local = threading.local()


def get_analytics_service():
    """Get or create an analytics service instance for the current thread."""
    if not hasattr(_thread_local, 'analytics_service'):
        _thread_local.analytics_service = ValidationAnalyticsService()
    return _thread_local.analytics_service


def _get_int_param(param_name, default_value):
    """Helper to get integer parameter from request with default."""
    try:
        return int(request.args.get(param_name, default_value))
    except (ValueError, TypeError):
        return default_value


def _add_chart_metadata(data, chart_type, chart_title):
    """Add chart metadata to response."""
    return {
        "data": data,
        "chart_type": chart_type,
        "chart_title": chart_title
    }


def _handle_analytics_error(e, operation_name):
    """Handle analytics errors consistently."""
    logger.error(f"Error in {operation_name}: {e}", exc_info=True)
    return jsonify({"error": f"Error retrieving {operation_name}: {str(e)}"}), 500


@validation_api.route('/global-view', methods=['GET'])
def get_global_view():
    """
    Get pass vs fail statistics by region for stacked bar chart
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
    responses:
      200:
        description: Pass vs fail statistics by region
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        service = get_analytics_service()
        data = service.get_pass_fail_by_region(days=days)
        return jsonify(_add_chart_metadata(data, "stacked_bar", "Pass vs Fail by Region"))
    except Exception as e:
        return _handle_analytics_error(e, "global view data")


@validation_api.route('/heatmap', methods=['GET'])
def get_heatmap():
    """
    Get success rates by region and product type for heatmap
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
    responses:
      200:
        description: Success rates by region and product type
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        service = get_analytics_service()
        data = service.get_heatmap_region_product(days=days)
        return jsonify(_add_chart_metadata(data, "heatmap", "Region x Product Success Rates"))
    except Exception as e:
        return _handle_analytics_error(e, "heatmap data")


@validation_api.route('/treemap', methods=['GET'])
def get_treemap():
    """
    Get regional exchange breakdown for treemap visualization
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
    responses:
      200:
        description: Exchange breakdown by region and product type
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        service = get_analytics_service()
        data = service.get_regional_exchange_breakdown(days=days)
        return jsonify(_add_chart_metadata(data, "treemap", "Regional Exchange Breakdown"))
    except Exception as e:
        return _handle_analytics_error(e, "treemap data")


@validation_api.route('/rule-failures', methods=['GET'])
def get_rule_failures():
    """
    Get rule failure statistics for bar chart
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of rules to return
    responses:
      200:
        description: Rule failure statistics
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        limit = _get_int_param('limit', 20)
        service = get_analytics_service()
        data = service.get_rule_failure_stats(days=days, limit=limit)
        return jsonify(_add_chart_metadata(data, "bar", "Rule Failure Statistics"))
    except Exception as e:
        return _handle_analytics_error(e, "rule failure data")


@validation_api.route('/rule-failures-by-region', methods=['GET'])
def get_rule_failures_by_region():
    """
    Get rule failure statistics grouped by region
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of rules to return per region
      - name: product_type
        in: query
        type: string
        required: false
        enum:
          - stock
          - option
          - future
        description: Filter by product type (stock, option, or future)
    responses:
      200:
        description: Rule failure statistics grouped by region
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        limit = _get_int_param('limit', 20)
        product_type = request.args.get('product_type')
        service = get_analytics_service()
        data = service.get_rule_failures_by_region(days=days, limit=limit, product_type=product_type)
        return jsonify(_add_chart_metadata(data, "grouped_bar", "Rule Failures by Region"))
    except Exception as e:
        return _handle_analytics_error(e, "rule failures by region data")


@validation_api.route('/expectation-failures-by-region', methods=['GET'])
def get_expectation_failures_by_region():
    """
    Get expectation failure statistics grouped by region, column name, and expectation type
    Shows which specific expectations (e.g., Currency + ExpectColumnValuesToBeInSet) failed per region
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of expectations to return per region
      - name: product_type
        in: query
        type: string
        required: false
        enum:
          - stock
          - option
          - future
        description: Filter by product type (stock, option, or future)
    responses:
      200:
        description: Expectation failure statistics grouped by region
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        limit = _get_int_param('limit', 20)
        product_type = request.args.get('product_type')
        service = get_analytics_service()
        data = service.get_expectation_failures_by_region(days=days, limit=limit, product_type=product_type)
        return jsonify(_add_chart_metadata(data, "grouped_bar", "Expectation Failures by Region"))
    except Exception as e:
        return _handle_analytics_error(e, "expectation failures by region data")


@validation_api.route('/exchange/<exchange>', methods=['GET'])
def get_validation_results_by_exchange(exchange):
    """
    Get validation results for a specific exchange
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: exchange
        in: path
        type: string
        required: true
        description: Exchange code (e.g., XHKG, XNSE, XTKS)
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
      - name: limit
        in: query
        type: integer
        description: Optional limit on number of runs to return
    responses:
      200:
        description: Validation results for the exchange
      400:
        description: Invalid exchange parameter
      500:
        description: Error retrieving validation results
    """
    try:
        if not exchange:
            return jsonify({"error": "Exchange parameter is required"}), 400
        
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', None, type=int)
        
        service = get_analytics_service()
        results = service.get_validation_results_by_exchange(
            exchange=exchange.upper(),
            days=days,
            limit=limit
        )
        return jsonify(results)
    except Exception as e:
        return _handle_analytics_error(e, "validation results by exchange")


@validation_api.route('/combined-rule/<combined_rule_name>', methods=['GET'])
def get_combined_rule_stats(combined_rule_name):
    """
    Get statistics for a specific combined rule (e.g., IsTradableStock)
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: combined_rule_name
        in: path
        type: string
        required: true
        description: Name of the combined rule
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
    responses:
      200:
        description: Combined rule statistics
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 7)
        service = get_analytics_service()
        data = service.get_combined_rule_stats(combined_rule_name, days=days)
        
        data["chart_type"] = "pie"
        data["chart_title"] = f"{combined_rule_name} Breakdown"
        
        return jsonify(data)
    except Exception as e:
        return _handle_analytics_error(e, f"combined rule stats for {combined_rule_name}")


@validation_api.route('/run-sessions/<region>/<date>', methods=['GET'])
def get_run_sessions(region, date):
    """
    Return distinct run batches (5-minute windows) for a region and date.
    Lightweight — no joins, used to populate the session picker in the UI.
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: region
        in: path
        type: string
        required: true
      - name: date
        in: path
        type: string
        required: true
        description: Date in YYYY-MM-DD format
      - name: days
        in: query
        type: integer
        default: 90
        description: How many days back to search
    responses:
      200:
        description: List of run sessions with pass/fail counts
      400:
        description: Missing parameters
      500:
        description: Server error
    """
    if not region or not date:
        return jsonify({'error': 'region and date are required'}), 400
    try:
        days = request.args.get('days', 90, type=int)
        service = get_analytics_service()
        result = service.get_run_sessions_by_region_date(region=region, date=date, days=days)
        return jsonify(result)
    except Exception as e:
        return _handle_analytics_error(e, 'run sessions by region and date')


@validation_api.route('/region-date/<region>/<date>', methods=['GET'])
def get_validation_results_by_region_date(region, date):
    """
    Get validation results for a specific region and date.
    Pass session_time (ISO-8601) to restrict results to a single run batch.
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: region
        in: path
        type: string
        required: true
        description: Region name (e.g., APAC, US, EMEA)
      - name: date
        in: path
        type: string
        required: true
        description: Date in format YYYY-MM-DD
      - name: days
        in: query
        type: integer
        default: 7
        description: Number of days to look back
      - name: limit
        in: query
        type: integer
        description: Optional limit on number of runs to return
      - name: session_time
        in: query
        type: string
        description: ISO-8601 session bucket from /run-sessions — filters to that batch only
    responses:
      200:
        description: Validation results for the region and date
      400:
        description: Invalid parameters
      500:
        description: Error retrieving validation results
    """
    try:
        if not region:
            return jsonify({"error": "Region parameter is required"}), 400
        if not date:
            return jsonify({"error": "Date parameter is required"}), 400

        days         = request.args.get('days', 7, type=int)
        limit        = request.args.get('limit', None, type=int)
        session_time = request.args.get('session_time', None, type=str)

        service = get_analytics_service()
        results = service.get_validation_results_by_region_date(
            region=region,
            date=date,
            days=days,
            limit=limit,
            session_time=session_time,
        )
        return jsonify(results)
    except Exception as e:
        return _handle_analytics_error(e, "validation results by region and date")


@validation_api.route('/regional-trends', methods=['GET'])
def get_regional_trends():
    """
    Get validation trend data by region over time
    ---
    tags:
      - Validation Analytics
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
        description: Number of days to look back
      - name: product_type
        in: query
        type: string
        required: false
        enum:
          - stock
          - option
          - future
        description: Filter by product type (stock, option, or future)
    responses:
      200:
        description: Regional trend data grouped by region
      500:
        description: Error retrieving data
    """
    try:
        days = _get_int_param('days', 30)
        product_type = request.args.get('product_type')
        service = get_analytics_service()
        data = service.get_regional_trends(days=days, product_type=product_type)
        return jsonify(_add_chart_metadata(data, "line", "Validation Trends by Region"))
    except Exception as e:
        return _handle_analytics_error(e, "regional trends")
