"""
hunter.py
---------
Hunter.io API service client for VAIBHAV GROWTH ENGINE.

Provides email discovery, email verification, and domain-level email search
via the Hunter.io REST API v2.  All network calls use ``httpx`` with a
configurable timeout and are wrapped by ``tenacity`` for exponential-backoff
retries on transient failures.  Loguru is used for structured logging.

Usage::

    from src.services.hunter import HunterService

    svc = HunterService()
    enrichment = svc.find_email("John", "Doe", "acme.com")
    verified   = svc.verify_email("john@acme.com")
    emails     = svc.domain_search("acme.com", limit=5)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import settings
from src.models.contact import EmailEnrichment

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HUNTER_BASE_URL: str = "https://api.hunter.io/v2"

_RETRY_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)

# Hunter verification status strings → normalised status
_STATUS_MAP: Dict[str, str] = {
    "valid": "valid",
    "accept_all": "risky",
    "webmail": "risky",
    "disposable": "invalid",
    "unknown": "unknown",
    "invalid": "invalid",
    "risky": "risky",
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class HunterService:
    """
    Client for the Hunter.io REST API v2.

    Supports:
    - Email finder (first name + last name + domain → email address)
    - Email verifier (email address → deliverability status)
    - Domain search (domain → list of email addresses)

    All methods gracefully degrade to ``None`` / empty list when the API key
    is absent or invalid, logging warnings rather than raising to the caller.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.HUNTER_API_KEY
        self.base_url: str = HUNTER_BASE_URL
        self.timeout: int = settings.REQUEST_TIMEOUT

    # ------------------------------------------------------------------
    # Low-level transport
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(_RETRY_EXCEPTIONS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an authenticated GET request against the Hunter API.

        Hunter authenticates exclusively via an ``api_key`` query parameter;
        no request body or header auth is needed.

        Args:
            endpoint: Path relative to :attr:`base_url`
                      (e.g. ``/email-finder``).
            params:   Additional query parameters merged with ``api_key``.

        Returns:
            The ``data`` sub-dict from the parsed JSON response, or the full
            response dict when no ``data`` key is present.

        Raises:
            httpx.HTTPStatusError: For 4xx/5xx responses (after retry exhaustion).
            httpx.TimeoutException: If the server does not respond within the
                configured timeout.
        """
        url = f"{self.base_url}{endpoint}"
        merged_params: Dict[str, Any] = {"api_key": self.api_key}
        if params:
            merged_params.update(params)

        logger.debug("Hunter API → GET {url}", url=url)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=merged_params)

            if response.status_code == 401:
                logger.error(
                    "Hunter API returned 401 Unauthorized – check HUNTER_API_KEY."
                )
                return {}

            if response.status_code == 403:
                logger.error(
                    "Hunter API returned 403 Forbidden – plan limit or invalid key."
                )
                return {}

            if response.status_code == 429:
                logger.warning("Hunter API rate-limit hit (429) – backing off.")
                raise httpx.TimeoutException(
                    "Rate-limited by Hunter", request=response.request
                )

            if response.status_code == 422:
                logger.warning(
                    "Hunter API returned 422 Unprocessable – body: {body}",
                    body=response.text[:400],
                )
                return {}

            response.raise_for_status()
            body: Dict[str, Any] = response.json()
            logger.debug(
                "Hunter API ← {status} ({bytes} bytes)",
                status=response.status_code,
                bytes=len(response.content),
            )
            # Hunter wraps all useful content inside a ``data`` key
            return body.get("data") or body

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Hunter API HTTP error {status}: {msg}",
                status=exc.response.status_code,
                msg=exc.response.text[:300],
            )
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
    ) -> Optional[EmailEnrichment]:
        """
        Discover a professional email address for a named individual.

        Calls ``GET /email-finder``.

        Args:
            first_name: Contact's given name.
            last_name:  Contact's family name.
            domain:     Employer's primary domain (e.g. ``"acme.com"``).

        Returns:
            An :class:`~src.models.contact.EmailEnrichment` with the
            discovered address and confidence score, or ``None`` if the
            request fails or the service is not configured.
        """
        if not self.is_configured():
            logger.warning(
                "HunterService: HUNTER_API_KEY not configured – "
                "skipping email finder for {first} {last} @ {domain}.",
                first=first_name,
                last=last_name,
                domain=domain,
            )
            return None

        logger.info(
            "Hunter: finding email | {first} {last} @ {domain}",
            first=first_name,
            last=last_name,
            domain=domain,
        )

        try:
            data = self._make_request(
                "/email-finder",
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
        except Exception as exc:
            logger.error(
                "Hunter find_email failed for {first} {last} @ {domain}: {exc}",
                first=first_name,
                last=last_name,
                domain=domain,
                exc=exc,
            )
            return None

        if not data or not data.get("email"):
            logger.warning(
                "Hunter: no email found for {first} {last} @ {domain}.",
                first=first_name,
                last=last_name,
                domain=domain,
            )
            return None

        enrichment = self._map_enrichment(data, domain)
        logger.info(
            "Hunter: found {email} (confidence={conf:.0%}).",
            email=enrichment.email,
            conf=enrichment.confidence_score,
        )
        return enrichment

    def verify_email(self, email: str) -> Optional[EmailEnrichment]:
        """
        Verify deliverability of a known email address.

        Calls ``GET /email-verifier``.

        Args:
            email: The email address to verify.

        Returns:
            An :class:`~src.models.contact.EmailEnrichment` with
            verification status, or ``None`` if the request fails or the
            service is not configured.
        """
        if not self.is_configured():
            logger.warning(
                "HunterService: HUNTER_API_KEY not configured – "
                "skipping verification for {email}.",
                email=email,
            )
            return None

        logger.info("Hunter: verifying email {email}", email=email)

        try:
            data = self._make_request(
                "/email-verifier",
                params={"email": email},
            )
        except Exception as exc:
            logger.error(
                "Hunter verify_email failed for {email}: {exc}",
                email=email,
                exc=exc,
            )
            return None

        if not data or not data.get("email"):
            logger.warning(
                "Hunter: no verification result for {email}.", email=email
            )
            return None

        # derive domain from email
        domain_part = email.split("@")[-1] if "@" in email else "unknown.com"
        enrichment = self._map_enrichment(data, domain_part)
        logger.info(
            "Hunter: {email} verification status={status}.",
            email=email,
            status=enrichment.verification_status,
        )
        return enrichment

    def domain_search(
        self,
        domain: str,
        limit: int = 5,
    ) -> List[EmailEnrichment]:
        """
        Retrieve all email addresses Hunter knows for a given domain.

        Calls ``GET /domain-search``.

        Args:
            domain: Employer's primary domain (e.g. ``"acme.com"``).
            limit:  Maximum number of email records to return.

        Returns:
            A list of :class:`~src.models.contact.EmailEnrichment` instances.
            Returns an empty list if the request fails or the service is not
            configured.
        """
        if not self.is_configured():
            logger.warning(
                "HunterService: HUNTER_API_KEY not configured – "
                "returning empty domain search results."
            )
            return []

        logger.info(
            "Hunter: domain search for {domain} (limit={limit})",
            domain=domain,
            limit=limit,
        )

        try:
            data = self._make_request(
                "/domain-search",
                params={"domain": domain, "limit": limit},
            )
        except Exception as exc:
            logger.error(
                "Hunter domain_search failed for {domain}: {exc}",
                domain=domain,
                exc=exc,
            )
            return []

        if not data:
            logger.warning(
                "Hunter: no results for domain search {domain}.", domain=domain
            )
            return []

        raw_emails: List[Dict[str, Any]] = data.get("emails", [])
        logger.info(
            "Hunter: domain search returned {n} email(s) for {domain}.",
            n=len(raw_emails),
            domain=domain,
        )

        results: List[EmailEnrichment] = []
        for raw in raw_emails[:limit]:
            # Domain-search response nests the address in ``value``
            # and exposes first/last under the email-level object.
            synthetic: Dict[str, Any] = {
                "email": raw.get("value"),
                "score": raw.get("confidence", 0),
                "result": raw.get("verification", {}).get("result", "unknown"),
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
            }
            if synthetic["email"]:
                results.append(self._map_enrichment(synthetic, domain))

        return results

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _map_enrichment(
        self, data: Dict[str, Any], domain: str
    ) -> EmailEnrichment:
        """
        Map a raw Hunter API response dict to an
        :class:`~src.models.contact.EmailEnrichment`.

        Handles both the ``/email-finder`` and ``/email-verifier`` response
        shapes, as well as the individual items from ``/domain-search``.

        Args:
            data:   Parsed response dict (or a single email item from a list).
            domain: Employer domain to attach to the enrichment record.

        Returns:
            A populated :class:`~src.models.contact.EmailEnrichment` instance.
        """
        email: str = data.get("email") or "unknown@unknown.com"

        # Confidence score: Hunter returns 0–100 integer
        raw_score = data.get("score") or data.get("confidence") or 0
        try:
            confidence: float = float(raw_score) / 100.0
            confidence = min(max(confidence, 0.0), 1.0)
        except (TypeError, ValueError):
            confidence = 0.0

        # Verification status normalisation
        raw_status: str = (
            data.get("result")
            or data.get("status")
            or data.get("verification_status")
            or "unknown"
        )
        status: str = _STATUS_MAP.get(raw_status.lower(), "unknown")
        is_verified: bool = status == "valid"

        return EmailEnrichment(
            email=email,
            confidence_score=confidence,
            is_verified=is_verified,
            verification_status=status,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            company_domain=domain,
            source="hunter",
            enriched_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return ``True`` when a non-trivial API key is available."""
        return bool(self.api_key and len(self.api_key) > 10)
