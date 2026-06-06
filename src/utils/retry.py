"""
retry.py
--------
Tenacity-based retry decorator factories for VAIBHAV GROWTH ENGINE.

Three ready-made decorators are provided:

* :func:`retry_with_backoff` – generic exponential back-off, configurable
  max attempts and wait bounds.
* :func:`retry_on_rate_limit` – specialised for HTTP 429 responses; detects
  ``httpx``, ``requests``, and plain ``Exception`` messages.
* :func:`retry_on_network_error` – handles transient connection / timeout
  failures.

All retry events are logged through the project's Loguru logger so failures
are always visible in the log files.

Usage::

    from src.utils.retry import retry_with_backoff, retry_on_rate_limit

    @retry_with_backoff(max_attempts=4, min_wait=2, max_wait=30)
    def call_external_api() -> dict:
        ...

    @retry_on_rate_limit(max_attempts=6)
    def fetch_contacts() -> list:
        ...
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)

from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Type variable for generic decorator typing
# ---------------------------------------------------------------------------
_F = TypeVar("_F", bound=Callable[..., Any])

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_rate_limit_error(exc: BaseException) -> bool:
    """
    Return ``True`` when *exc* represents an HTTP 429 Too Many Requests error.

    Checks:
    * ``httpx.HTTPStatusError`` with status code 429.
    * ``requests.HTTPError`` with status code 429.
    * Any exception whose string representation contains "429".
    """
    # httpx
    try:
        import httpx  # noqa: PLC0415
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
            return True
    except ImportError:
        pass

    # requests
    try:
        import requests  # noqa: PLC0415
        if (
            isinstance(exc, requests.HTTPError)
            and exc.response is not None
            and exc.response.status_code == 429
        ):
            return True
    except ImportError:
        pass

    # Fallback: check the exception message
    return "429" in str(exc)


def _is_network_error(exc: BaseException) -> bool:
    """
    Return ``True`` when *exc* represents a transient network problem.

    Covers:
    * ``httpx.ConnectError``, ``httpx.TimeoutException``
    * ``requests.ConnectionError``, ``requests.Timeout``
    * ``ConnectionError``, ``TimeoutError`` (built-ins)
    * ``OSError`` / ``IOError``
    """
    # Built-in network exceptions
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, IOError)):
        return True

    # httpx
    try:
        import httpx  # noqa: PLC0415
        if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
            return True
    except ImportError:
        pass

    # requests
    try:
        import requests  # noqa: PLC0415
        if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
            return True
    except ImportError:
        pass

    return False


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Loguru callback invoked by Tenacity before each sleep between retries."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    attempt = retry_state.attempt_number
    fn_name = getattr(retry_state.fn, "__qualname__", str(retry_state.fn))
    wait_time = retry_state.next_action.sleep if retry_state.next_action else 0.0  # type: ignore[union-attr]

    logger.warning(
        "Retry attempt {attempt} for '{fn}' | "
        "exception: {exc_type}: {exc_msg} | "
        "sleeping {wait:.2f}s before next try",
        attempt=attempt,
        fn=fn_name,
        exc_type=type(exc).__name__ if exc else "unknown",
        exc_msg=str(exc) if exc else "",
        wait=wait_time,
    )


# ---------------------------------------------------------------------------
# Public decorator factories
# ---------------------------------------------------------------------------

def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
) -> Callable[[_F], _F]:
    """
    Generic exponential back-off retry decorator factory.

    Wraps the decorated callable with Tenacity's exponential wait strategy.
    Every retry attempt is logged via Loguru before the sleep period begins.

    Args:
        max_attempts: Maximum total number of call attempts (including the
                      first).  Defaults to ``3``.
        min_wait: Minimum number of seconds to wait between retries.
                  Defaults to ``1.0``.
        max_wait: Maximum number of seconds to wait between retries.
                  Defaults to ``60.0``.

    Returns:
        A decorator that, when applied to a callable, makes it retry on any
        ``Exception`` with exponential back-off.

    Example::

        @retry_with_backoff(max_attempts=5, min_wait=2, max_wait=30)
        def fragile_call() -> dict:
            return requests.get("https://api.example.com/data").json()
    """
    return retry(  # type: ignore[return-value]
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        before_sleep=_log_retry_attempt,
        reraise=True,
    )


def retry_on_rate_limit(max_attempts: int = 5) -> Callable[[_F], _F]:
    """
    Retry decorator factory specialised for HTTP 429 Too Many Requests errors.

    Uses a randomised exponential wait (jitter) to avoid thundering-herd
    problems when multiple threads hit the same rate-limited endpoint.

    Args:
        max_attempts: Maximum total number of call attempts.  Defaults to
                      ``5``.

    Returns:
        A decorator that retries on rate-limit errors with jitter back-off.

    Example::

        @retry_on_rate_limit(max_attempts=6)
        def fetch_from_apollo(domain: str) -> dict:
            ...
    """
    return retry(  # type: ignore[return-value]
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=2, min=1, max=120),
        retry=retry_if_exception(_is_rate_limit_error),
        before_sleep=_log_retry_attempt,
        reraise=True,
    )


def retry_on_network_error(max_attempts: int = 3) -> Callable[[_F], _F]:
    """
    Retry decorator factory for transient network / connection failures.

    Uses a standard exponential back-off.  After *max_attempts* the original
    exception is re-raised so the caller can handle the permanent failure.

    Args:
        max_attempts: Maximum total number of call attempts.  Defaults to
                      ``3``.

    Returns:
        A decorator that retries on connection and timeout errors.

    Example::

        @retry_on_network_error(max_attempts=4)
        def ping_endpoint(url: str) -> bool:
            ...
    """
    return retry(  # type: ignore[return-value]
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception(_is_network_error),
        before_sleep=_log_retry_attempt,
        reraise=True,
    )
