"""Domain exceptions for the data-validation service layer.

A typed exception hierarchy replaces string-inspection in controller error
handlers (e.g. ``if "closed file" in str(e)``).  Controllers catch by type,
not by message, so they remain closed for modification when new failure modes
are added in the services.

Each class inherits from both a domain base *and* the appropriate stdlib
exception so that callers that still catch the generic type (``ValueError``,
``IOError``, …) continue to work without changes.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class ValidationDomainError(Exception):
    """Base for all domain exceptions raised by the validation service layer."""


# ---------------------------------------------------------------------------
# Exchange / data-source errors
# ---------------------------------------------------------------------------

class ExchangeNotFoundError(ValidationDomainError, ValueError):
    """The requested exchange is not present in the configured exchange map."""

    def __init__(self, exchange: str, available: list[str]) -> None:
        self.exchange = exchange
        self.available = available
        super().__init__(
            f"Exchange '{exchange}' not found. "
            f"Available: {', '.join(sorted(available))}"
        )


class DataFileNotFoundError(ValidationDomainError, FileNotFoundError):
    """The data file configured for an exchange cannot be found on disk."""

    def __init__(self, exchange: str, path: str = "") -> None:
        self.exchange = exchange
        self.path = path
        suffix = f": {path}" if path else ""
        super().__init__(
            f"Data file not found for exchange '{exchange}'{suffix}"
        )


# ---------------------------------------------------------------------------
# Processor / infrastructure errors
# ---------------------------------------------------------------------------

class ProcessorSetupError(ValidationDomainError, IOError):
    """The data processor could not be initialised.

    Typically caused by a closed file handle returned by Great Expectations
    (re-use of a spent iterator) or a missing dependency.
    """

    def __init__(self, product_type: str, cause: Exception) -> None:
        self.product_type = product_type
        self.cause = cause
        super().__init__(
            f"Failed to set up processor for '{product_type}': {cause}"
        )
