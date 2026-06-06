"""
validators.py
-------------
Input validation helpers for VAIBHAV GROWTH ENGINE.

Functions
---------
* :func:`validate_domain`       – strip protocol/www and verify domain format.
* :func:`sanitize_domain`       – lightweight wrapper; always returns a string.
* :func:`validate_email`        – regex check + optional DNS MX lookup.
* :func:`validate_api_key`      – non-empty + minimum-length guard.
* :func:`is_valid_linkedin_url` – basic LinkedIn profile/company URL check.

All functions are designed to be safe to call from async contexts (no
blocking I/O beyond an optional DNS lookup).  The DNS check is silently
skipped when *dnspython* is not installed.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Pre-compiled regular expressions
# ---------------------------------------------------------------------------

#: RFC 5321-ish email pattern – strict enough for B2B prospecting use-cases.
_EMAIL_RE: re.Pattern[str] = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

#: Domain pattern: letters, digits, hyphens, dots; TLD ≥ 2 chars.
_DOMAIN_RE: re.Pattern[str] = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

#: LinkedIn profile or company URL pattern.
_LINKEDIN_RE: re.Pattern[str] = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/"
    r"(?:in/[a-zA-Z0-9\-_%]+|company/[a-zA-Z0-9\-_%]+)"
    r"/?$",
    re.IGNORECASE,
)

# Minimum acceptable API-key lengths per provider (characters).
_API_KEY_MIN_LENGTHS: dict[str, int] = {
    "apollo": 20,
    "prospeo": 20,
    "hunter": 30,
    "brevo": 30,
    "gemini": 30,
    "groq": 30,
    "openrouter": 30,
}
_DEFAULT_MIN_KEY_LENGTH: int = 10


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------

def sanitize_domain(domain: str) -> str:
    """
    Return a cleaned domain string without modifying the input.

    Strips leading/trailing whitespace and converts to lower-case.  Unlike
    :func:`validate_domain` this function never raises; it simply returns the
    sanitised string so callers can use it safely as a dict key or cache
    lookup, even before full validation.

    Args:
        domain: Raw domain input (may include protocol, www, paths, …).

    Returns:
        Lower-cased, stripped representation of *domain*.
    """
    return domain.strip().lower()


def validate_domain(domain: str) -> str:
    """
    Validate and normalise a domain name.

    The function strips the protocol (``http://``, ``https://``), the ``www.``
    prefix, trailing slashes, and any path/query components.  It then checks
    the remaining string against a domain-name pattern.

    Args:
        domain: Raw domain string – may include protocol, www prefix, paths.

    Returns:
        The clean, normalised bare domain (e.g. ``"example.com"``).

    Raises:
        ValueError: If *domain* is empty or does not match the domain pattern
                    after stripping.

    Example::

        validate_domain("https://www.example.com/about")
        # → "example.com"
    """
    if not domain or not domain.strip():
        raise ValueError("Domain must not be empty.")

    raw = domain.strip().lower()

    # Prepend a scheme if missing so urlparse works correctly.
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    hostname: str = parsed.hostname or ""

    # Remove the www. prefix if present.
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if not hostname:
        raise ValueError(f"Could not extract a hostname from domain: {domain!r}")

    if not _DOMAIN_RE.match(hostname):
        raise ValueError(
            f"Invalid domain format after normalisation: {hostname!r} "
            f"(original input: {domain!r})"
        )

    logger.debug("validate_domain: {raw!r} → {clean!r}", raw=domain, clean=hostname)
    return hostname


# ---------------------------------------------------------------------------
# Email helpers
# ---------------------------------------------------------------------------

def _check_mx_record(email_domain: str) -> bool:
    """
    Perform a DNS MX record lookup for *email_domain*.

    Returns ``True`` if at least one MX record is found, ``False`` on any
    error (including *dnspython* not being installed or a DNS failure).  This
    keeps :func:`validate_email` resilient in environments without DNS access.
    """
    try:
        import dns.resolver  # type: ignore[import]

        answers = dns.resolver.resolve(email_domain, "MX", lifetime=5.0)
        return bool(answers)
    except ImportError:
        logger.debug(
            "dnspython not installed – skipping MX check for {domain}",
            domain=email_domain,
        )
        return True  # Assume valid when we can't check
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "MX lookup failed for {domain}: {err}",
            domain=email_domain,
            err=exc,
        )
        return False


def validate_email(email: str, check_mx: bool = True) -> bool:
    """
    Validate an email address with a regex check and an optional MX lookup.

    Args:
        email:    The email address to validate.
        check_mx: When ``True`` (default), perform a DNS MX record lookup on
                  the domain part.  Set to ``False`` for fast offline checks.

    Returns:
        ``True`` if the address passes all checks, ``False`` otherwise.

    Example::

        validate_email("alice@example.com")              # → True / False
        validate_email("not-an-email")                   # → False
        validate_email("alice@example.com", check_mx=False)  # regex only
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip().lower()

    if not _EMAIL_RE.match(email):
        logger.debug("validate_email: regex failed for {email!r}", email=email)
        return False

    if check_mx:
        domain_part = email.split("@", maxsplit=1)[1]
        mx_ok = _check_mx_record(domain_part)
        if not mx_ok:
            logger.debug(
                "validate_email: MX check failed for domain {domain}",
                domain=domain_part,
            )
            return False

    return True


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------

def validate_api_key(key: str, provider: str) -> bool:
    """
    Check that an API key is non-empty and meets the minimum length for its
    provider.

    Args:
        key:      The API key string to validate.
        provider: The name of the API provider (case-insensitive), e.g.
                  ``"apollo"``, ``"brevo"``, ``"gemini"``.

    Returns:
        ``True`` when the key is non-empty and at least as long as the
        provider's minimum expected length; ``False`` otherwise.

    Example::

        validate_api_key("sk-abc123…", "groq")  # → True or False
        validate_api_key("",           "apollo") # → False
    """
    if not key or not isinstance(key, str):
        logger.warning(
            "validate_api_key: empty or non-string key for provider {provider!r}",
            provider=provider,
        )
        return False

    min_length = _API_KEY_MIN_LENGTHS.get(provider.lower(), _DEFAULT_MIN_KEY_LENGTH)

    if len(key.strip()) < min_length:
        logger.warning(
            "validate_api_key: key for {provider!r} is too short "
            "(got {got} chars, expected ≥{expected})",
            provider=provider,
            got=len(key.strip()),
            expected=min_length,
        )
        return False

    return True


# ---------------------------------------------------------------------------
# LinkedIn helpers
# ---------------------------------------------------------------------------

def is_valid_linkedin_url(url: str) -> bool:
    """
    Return ``True`` when *url* is a valid LinkedIn profile or company URL.

    Accepted patterns (with or without trailing slash):
    * ``https://www.linkedin.com/in/<handle>``
    * ``https://linkedin.com/in/<handle>``
    * ``https://www.linkedin.com/company/<slug>``
    * ``https://linkedin.com/company/<slug>``

    Args:
        url: The URL string to validate.

    Returns:
        ``True`` if the URL matches a LinkedIn profile/company pattern,
        ``False`` otherwise.

    Example::

        is_valid_linkedin_url("https://www.linkedin.com/in/johndoe")  # → True
        is_valid_linkedin_url("https://twitter.com/johndoe")          # → False
    """
    if not url or not isinstance(url, str):
        return False

    return bool(_LINKEDIN_RE.match(url.strip()))
