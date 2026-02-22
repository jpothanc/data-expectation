"""Report controller — HTTP endpoints for downloadable reports.

Routing only: all generation logic lives in ReportService.
New report formats (PDF, CSV, etc.) belong here, not in validation_controller.
"""

import logging
import threading

from flask import Blueprint, request, send_file
from services.report_service import ReportService

logger = logging.getLogger(__name__)
report_api = Blueprint('report_api', __name__)

_thread_local = threading.local()


def _get_report_service() -> ReportService:
    """Return a thread-local ReportService instance (created on first use)."""
    if not hasattr(_thread_local, 'report_service'):
        _thread_local.report_service = ReportService()
    return _thread_local.report_service


def _error(message: str, status: int = 500):
    from flask import jsonify
    return jsonify({'error': message}), status


@report_api.route('/excel/<region>/<date>', methods=['GET'])
def download_excel_report(region, date):
    """
    Download a consolidated Excel failure report for a region and date.
    ---
    tags:
      - Reports
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
        description: Date in YYYY-MM-DD format
      - name: days
        in: query
        type: integer
        default: 90
        description: How many days back to search for the run
    produces:
      - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    responses:
      200:
        description: Excel file download
      400:
        description: Missing or invalid parameters
      500:
        description: Error generating report
    """
    if not region or not date:
        return _error('region and date are required', 400)

    try:
        days = request.args.get('days', 90, type=int)
        buf  = _get_report_service().generate_excel_report(region, date, days)
        return send_file(
            buf,
            as_attachment=True,
            download_name=f'validation_report_{region.upper()}_{date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except Exception as exc:
        logger.error('Error generating Excel report for %s / %s: %s',
                     region, date, exc, exc_info=True)
        return _error(f'Error generating report: {exc}')
