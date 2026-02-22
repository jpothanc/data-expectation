"""Timing utilities for performance logging throughout the application."""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional


def timed(operation: Optional[str] = None, logger: Optional[logging.Logger] = None, level: int = logging.INFO):
    """
    Decorator that logs the execution time of a function.

    Usage::

        @timed("load exchange data")
        def load_exchange(exchange: str) -> pd.DataFrame: ...

        @timed(logger=my_logger, level=logging.DEBUG)
        def heavy_computation(): ...
    """
    def decorator(func: Callable) -> Callable:
        _label = operation or func.__qualname__
        _logger = logger or logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                _logger.log(level, "[TIMING] %s completed in %.1f ms", _label, elapsed_ms)
                return result
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000
                _logger.log(level, "[TIMING] %s failed after %.1f ms | %s", _label, elapsed_ms, exc)
                raise
        return wrapper

    # Support both @timed and @timed("label") usage
    if callable(operation):
        func, operation = operation, None
        return decorator(func)
    return decorator


@contextmanager
def timer(label: str, logger: Optional[logging.Logger] = None, level: int = logging.INFO):
    """
    Context manager that logs elapsed time for a block of code.

    Usage::

        with timer("validate XHKG", logger=logger):
            result = validator.validate(df, exchange="XHKG")

        with timer(f"DB query {exchange}", logger=logger, level=logging.DEBUG):
            rows = cursor.fetchall()
    """
    _logger = logger or logging.getLogger(__name__)
    start = time.perf_counter()
    try:
        yield
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _logger.log(level, "[TIMING] %s failed after %.1f ms | %s", label, elapsed_ms, exc)
        raise
    else:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _logger.log(level, "[TIMING] %s completed in %.1f ms", label, elapsed_ms)


class RequestTimer:
    """
    Collects per-request timing spans and emits a summary log at the end.

    Usage in a Flask before/after request context::

        rt = RequestTimer("POST /api/v1/rules/validate/stock/XHKG")
        with rt.span("load data"):
            df = loader.load(exchange)
        with rt.span("run GE validation"):
            result = validator.validate(df)
        rt.log_summary(logger)
    """

    def __init__(self, request_label: str) -> None:
        self.request_label = request_label
        self._spans: list[tuple[str, float]] = []
        self._total_start = time.perf_counter()

    @contextmanager
    def span(self, label: str):
        """Record a named sub-span."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._spans.append((label, elapsed_ms))

    @property
    def total_ms(self) -> float:
        return (time.perf_counter() - self._total_start) * 1000

    def log_summary(self, logger: Optional[logging.Logger] = None, level: int = logging.INFO) -> None:
        _logger = logger or logging.getLogger(__name__)
        spans_str = " | ".join(f"{name}={ms:.1f}ms" for name, ms in self._spans)
        _logger.log(
            level,
            "[REQUEST TIMING] %s | total=%.1f ms  [%s]",
            self.request_label,
            self.total_ms,
            spans_str,
        )
