"""API client for the validation endpoints.

Uses a persistent requests.Session (connection pooling at the HTTP layer),
configurable timeouts, and automatic retry with exponential backoff for
transient failures (timeouts, 5xx errors).
"""

import time
import logging

import requests

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 120      # seconds — generous for large exchanges
_DEFAULT_RETRIES = 3
_RETRY_BACKOFF = [1, 2, 4]  # sleep seconds between successive retries

# HTTP status codes that are safe to retry
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ValidationAPIClient:
    """Call validation API endpoints with retry and backoff."""

    def __init__(self, base_url="http://127.0.0.1:5006"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_exchange(self, product_type, exchange, custom_rule_names=None,
                          timeout=_DEFAULT_TIMEOUT, max_retries=_DEFAULT_RETRIES):
        """Call validate endpoint for *product_type* / *exchange*.

        Args:
            product_type: 'stock', 'option', or 'future'.
            exchange: Exchange code e.g. 'XHKG'.
            custom_rule_names: Optional list of rule names to pass as query param.
            timeout: Per-attempt request timeout in seconds.
            max_retries: Total attempts (first attempt + retries).

        Returns:
            dict — parsed JSON response body.

        Raises:
            Exception — after all retries exhausted, or on non-retryable errors.
        """
        url = f"{self.base_url}/api/v1/rules/validate/{product_type}/{exchange}"
        params = {}
        if custom_rule_names:
            params['custom_rule_names'] = ','.join(custom_rule_names)

        return self._get_with_retry(url, params, timeout, max_retries,
                                    context=f"{product_type}/{exchange}")

    def health_check(self, timeout=5):
        """Return True if the API is up."""
        url = f"{self.base_url}/health"
        try:
            resp = self.session.get(url, timeout=timeout)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_with_retry(self, url, params, timeout, max_retries, context=""):
        last_exc = None

        for attempt in range(max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=timeout)

                if resp.status_code in _RETRYABLE_STATUS and attempt < max_retries - 1:
                    delay = _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]
                    logger.warning(
                        "HTTP %s for %s (attempt %d/%d) — retrying in %ds",
                        resp.status_code, context, attempt + 1, max_retries, delay
                    )
                    time.sleep(delay)
                    continue

                resp.raise_for_status()
                return self._parse_json(resp, context)

            except requests.exceptions.Timeout as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    delay = _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]
                    logger.warning(
                        "Timeout for %s (attempt %d/%d) — retrying in %ds",
                        context, attempt + 1, max_retries, delay
                    )
                    time.sleep(delay)
                else:
                    raise Exception(
                        f"Request timed out after {max_retries} attempts: {url}"
                    ) from exc

            except requests.exceptions.HTTPError as exc:
                resp = exc.response
                body = resp.text[:200] if resp is not None else ""
                raise Exception(
                    f"HTTP {resp.status_code if resp is not None else '?'}: {body}"
                ) from exc

            except requests.exceptions.ConnectionError as exc:
                raise Exception(
                    f"Connection error — cannot reach {url}"
                ) from exc

            except requests.exceptions.RequestException as exc:
                raise Exception(str(exc)) from exc

        # Should only be reached if the retry loop exits without returning
        raise Exception(
            f"Failed after {max_retries} attempts: {url}"
        ) from last_exc

    @staticmethod
    def _parse_json(response, context=""):
        """Parse the response body as JSON; raise on malformed content."""
        try:
            return response.json()
        except ValueError as exc:
            preview = response.text[:300]
            raise Exception(
                f"Invalid JSON response for {context}. Preview: {preview}"
            ) from exc
