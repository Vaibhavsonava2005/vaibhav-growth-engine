"""
logger.py
---------
Centralised logging configuration for VAIBHAV GROWTH ENGINE using Loguru.

Usage::

    from src.utils.logger import logger, get_logger

    logger.info("Application started")
    module_log = get_logger("my_module")
    module_log.debug("Debug message from my_module")

The module sets up two handlers on import:

1. **File handler** – writes to ``logs/growth_engine_<YYYY-MM-DD>.log`` with
   daily rotation, 7-day retention, and DEBUG-level granularity.
2. **Stderr handler** – writes human-readable coloured output at the level
   specified by ``settings.LOG_LEVEL`` (default ``INFO``).
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as _loguru_logger

from src.config.settings import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_LOGS_DIR: Path = Path("logs")
_LOG_FILE_PATTERN: str = "growth_engine_{time:YYYY-MM-DD}.log"
_FILE_FORMAT: str = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} | {message}"
)
_STDERR_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def _configure_logger() -> None:
    """Remove Loguru's default handler and attach file + stderr handlers."""
    # Remove the default handler that Loguru adds automatically.
    _loguru_logger.remove()

    # ── File handler ──────────────────────────────────────────────────── #
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _loguru_logger.add(
        sink=str(_LOGS_DIR / _LOG_FILE_PATTERN),
        level="DEBUG",
        format=_FILE_FORMAT,
        rotation="00:00",          # rotate at midnight every day
        retention="7 days",        # keep the last 7 daily log files
        compression="zip",         # compress rotated logs to save space
        encoding="utf-8",
        enqueue=True,              # thread-safe async writes
        backtrace=True,            # full traceback on exceptions
        diagnose=True,             # variable values in tracebacks (dev)
    )

    # ── Stderr handler ────────────────────────────────────────────────── #
    _loguru_logger.add(
        sink=sys.stderr,
        level=settings.LOG_LEVEL.upper(),
        format=_STDERR_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=False,            # hide variable values in production stderr
    )


_configure_logger()

# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

#: The shared Loguru logger instance.  Import directly for convenience.
logger = _loguru_logger


def get_logger(name: str):
    """
    Return a Loguru logger bound with an extra ``name`` context field.

    This is a lightweight alternative to Python's ``logging.getLogger``; it
    returns the same underlying Loguru instance but with the given name bound
    so that log records show a meaningful module identifier.

    Args:
        name: A human-readable label for the calling module, e.g.
              ``"apollo_client"`` or ``"email_sender"``.

    Returns:
        A Loguru ``BoundLogger`` with ``name`` set in the extra context.

    Example::

        log = get_logger("apollo_client")
        log.info("Fetching companies from Apollo …")
    """
    return _loguru_logger.bind(module_name=name)
