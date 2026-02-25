"""Shared utilities for all Flask controllers.

Centralises cross-cutting concerns — input validation and error serialisation —
so each controller stays focused on routing only (SRP).

Usage pattern
-------------
    from controllers.utils import validate_product_type, bad_request, not_found

    product_type, err = validate_product_type(request.args.get('product_type'))
    if err:
        return err  # already a (Response, status_code) tuple

    # ... continue with validated product_type
"""
from __future__ import annotations

from typing import Any

from flask import jsonify

# ---------------------------------------------------------------------------
# Product-type constants
# ---------------------------------------------------------------------------

VALID_PRODUCT_TYPES: frozenset[str] = frozenset({"stock", "option", "future", "multileg"})

# Maps common plural / alias forms to their canonical singular form.
_PRODUCT_TYPE_ALIASES: dict[str, str] = {
    "stocks": "stock",
    "options": "option",
    "futures": "future",
    "multilegs": "multileg",
}


def validate_product_type(
    value: str | None, default: str = "stock"
) -> tuple[str, None] | tuple[str, tuple]:
    """Normalise and validate a ``product_type`` request parameter.

    Returns ``(normalised_type, None)`` on success, or
    ``('', error_response_tuple)`` when the value is invalid so callers can
    do an early-return guard:

        product_type, err = validate_product_type(request.args.get('product_type'))
        if err:
            return err
    """
    raw = (value or default).lower().strip()
    normalised = _PRODUCT_TYPE_ALIASES.get(raw, raw)

    if normalised not in VALID_PRODUCT_TYPES:
        valid = ", ".join(f"'{t}'" for t in sorted(VALID_PRODUCT_TYPES))
        return "", bad_request(
            f"Invalid product_type '{value}'. Must be one of: {valid}."
        )

    return normalised, None


# ---------------------------------------------------------------------------
# Consistent JSON error response builders
# ---------------------------------------------------------------------------

def bad_request(message: str, **extra: Any) -> tuple:
    """Return a ``400 Bad Request`` JSON response tuple."""
    return jsonify({"error": message, **extra}), 400


def not_found(message: str, **extra: Any) -> tuple:
    """Return a ``404 Not Found`` JSON response tuple."""
    return jsonify({"error": message, **extra}), 404


def server_error(message: str, **extra: Any) -> tuple:
    """Return a ``500 Internal Server Error`` JSON response tuple."""
    return jsonify({"error": message, **extra}), 500
