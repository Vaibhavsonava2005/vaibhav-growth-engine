"""
prospeo.py
----------
Prospeo.io API service client for VAIBHAV GROWTH ENGINE.

Provides person enrichment and people-search capabilities via the Prospeo
REST API.  All network calls use ``httpx`` with a configurable timeout and
are wrapped by ``tenacity`` for exponential-backoff retries on transient
failures.  Loguru is used for structured logging.

Usage::

    from src.services.prospeo import ProspeoService

    svc = ProspeoService()
    contact = svc.enrich_person("John", "Doe", "acme.com")
    contacts = svc.search_people("CTO", "acme.com", limit=3)
    info = svc.get_account_info()
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
from src.models.contact import Contact

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROSPEO_BASE_URL: str = "https://api.prospeo.io"

_RETRY_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ProspeoService:
    """
    Client for the Prospeo.io REST API.

    Supports:
    - Single-person enrichment (email discovery)
    - Bulk people search by job title + company domain
    - Account credit information retrieval

    All methods gracefully degrade to empty results when the API key is absent
    or invalid, logging appropriate warnings rather than raising exceptions to
    the caller.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.PROSPEO_API_KEY
        self.base_url: str = PROSPEO_BASE_URL
        self.timeout: int = settings.REQUEST_TIMEOUT
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "X-KEY": self.api_key,
        }

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
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute an authenticated HTTP request against the Prospeo API.

        Args:
            method:   HTTP verb (``"GET"`` or ``"POST"``).
            endpoint: Path relative to :attr:`base_url` (e.g. ``/enrich-person``).
            **kwargs: Additional arguments forwarded to :func:`httpx.request`.

        Returns:
            Parsed JSON response as a plain ``dict``.

        Raises:
            httpx.HTTPStatusError: For 4xx/5xx responses (after retry exhaustion).
            httpx.TimeoutException: If the server does not respond within the
                configured timeout.
        """
        url = f"{self.base_url}{endpoint}"
        method_upper = method.upper()

        logger.debug(
            "Prospeo API → {method} {url}", method=method_upper, url=url
        )

        try:
            with httpx.Client(
                timeout=self.timeout, headers=self.headers
            ) as client:
                response = client.request(method_upper, url, **kwargs)

            if response.status_code == 401:
                logger.error(
                    "Prospeo API returned 401 Unauthorized – "
                    "check PROSPEO_API_KEY."
                )
                return {}

            if response.status_code == 403:
                logger.error(
                    "Prospeo API returned 403 Forbidden – "
                    "insufficient permissions or depleted credits."
                )
                return {}

            if response.status_code == 429:
                logger.warning("Prospeo API rate-limit hit (429) – backing off.")
                raise httpx.TimeoutException(
                    "Rate-limited by Prospeo", request=response.request
                )

            if response.status_code == 422:
                logger.warning(
                    "Prospeo API returned 422 Unprocessable – body: {body}",
                    body=response.text[:400],
                )
                return {}

            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            logger.debug(
                "Prospeo API ← {status} ({bytes} bytes)",
                status=response.status_code,
                bytes=len(response.content),
            )
            return data

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Prospeo API HTTP error {status}: {msg}",
                status=exc.response.status_code,
                msg=exc.response.text[:300],
            )
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enrich_person(
        self,
        first_name: str,
        last_name: str,
        company_domain: str,
        linkedin_url: Optional[str] = None,
    ) -> Optional[Contact]:
        """
        Enrich a single person's record using Prospeo's person-enrichment endpoint.

        Queries ``POST /enrich-person`` with only-verified-email mode enabled.

        Args:
            first_name:      Contact's given name.
            last_name:       Contact's family name.
            company_domain:  Employer's primary domain (e.g. ``"stripe.com"``).
            linkedin_url:    Optional LinkedIn profile URL for higher match accuracy.

        Returns:
            A :class:`~src.models.contact.Contact` instance, or ``None`` if
            enrichment fails, returns no data, or the service is not configured.
        """
        if not self.is_configured():
            logger.warning(
                "ProspeoService: PROSPEO_API_KEY not configured – "
                "skipping person enrichment for {name}.",
                name=f"{first_name} {last_name}",
            )
            return None

        payload: Dict[str, Any] = {
            "only_verified_email": True,
            "data": {
                "first_name": first_name,
                "last_name": last_name,
                "company_website": company_domain,
            },
        }
        if linkedin_url:
            payload["data"]["linkedin_url"] = linkedin_url

        logger.info(
            "Prospeo: enriching person {first} {last} @ {domain}",
            first=first_name,
            last=last_name,
            domain=company_domain,
        )

        try:
            data = self._make_request("POST", "/enrich-person", json=payload)
        except Exception as exc:
            logger.error(
                "Prospeo enrich_person failed for {name}: {exc}",
                name=f"{first_name} {last_name}",
                exc=exc,
            )
            return None

        if not data or data.get("error"):
            logger.warning(
                "Prospeo: no enrichment data for {first} {last}: {err}",
                first=first_name,
                last=last_name,
                err=data.get("error", "unknown error"),
            )
            return None

        return self._map_contact(data, company_domain)

    def search_people(
        self,
        title: str,
        company_domain: str,
        limit: int = 5,
    ) -> List[Contact]:
        """
        Search for people at a company by job title, then enrich each result.

        Calls ``POST /search-person`` to obtain a list of person IDs, then
        enriches each one via :meth:`enrich_person`.

        Args:
            title:          Job title keyword (e.g. ``"CTO"``).
            company_domain: Employer's primary domain (e.g. ``"stripe.com"``).
            limit:          Maximum number of contacts to return.

        Returns:
            A list of :class:`~src.models.contact.Contact` instances (may be
            shorter than ``limit`` if fewer results are available).
        """
        if not self.is_configured():
            logger.warning(
                "ProspeoService: PROSPEO_API_KEY not configured – "
                "returning empty contact list."
            )
            return []

        payload: Dict[str, Any] = {
            "job_title": title,
            "company_website": company_domain,
            "limit": limit,
        }

        logger.info(
            "Prospeo: searching people | title={title} domain={domain} limit={limit}",
            title=title,
            domain=company_domain,
            limit=limit,
        )

        try:
            data = self._make_request("POST", "/search-person", json=payload)
        except Exception as exc:
            logger.error(
                "Prospeo search_people failed for {domain}: {exc}",
                domain=company_domain,
                exc=exc,
            )
            return []

        if not data or data.get("error"):
            logger.warning(
                "Prospeo: search_people returned error for {domain}: {err}",
                domain=company_domain,
                err=data.get("error", "unknown error") if data else "empty response",
            )
            return []

        # Prospeo /search-person may return a list of person objects directly
        # or a dict with a ``persons`` key depending on plan / endpoint version.
        raw_persons: List[Dict[str, Any]] = (
            data
            if isinstance(data, list)
            else data.get("persons", data.get("results", []))
        )

        logger.info(
            "Prospeo: received {n} person records for {domain}.",
            n=len(raw_persons),
            domain=company_domain,
        )

        contacts: List[Contact] = []
        for person in raw_persons[:limit]:
            # If the record is already enriched (has email field) map directly;
            # otherwise try a dedicated enrichment call using available identity info.
            if person.get("email") or person.get("professional_email"):
                contact = self._map_contact(person, company_domain)
            else:
                first = person.get("first_name", "")
                last = person.get("last_name", "")
                linkedin = person.get("linkedin_url")
                if first and last:
                    contact = self.enrich_person(
                        first, last, company_domain, linkedin
                    )
                else:
                    contact = self._map_contact(person, company_domain)

            if contact:
                contacts.append(contact)

        logger.info(
            "Prospeo: returning {n} enriched contacts for {domain}.",
            n=len(contacts),
            domain=company_domain,
        )
        return contacts

    def get_account_info(self) -> Dict[str, Any]:
        """
        Retrieve Prospeo account information including remaining credit balance.

        Calls ``GET /account-information``.

        Returns:
            A dict containing account details (e.g. ``credits_remaining``).
            Returns an empty dict if the service is not configured or the
            request fails.
        """
        if not self.is_configured():
            logger.warning(
                "ProspeoService: PROSPEO_API_KEY not configured – "
                "cannot retrieve account info."
            )
            return {}

        logger.info("Prospeo: retrieving account information.")

        try:
            data = self._make_request("GET", "/account-information")
        except Exception as exc:
            logger.error(
                "Prospeo get_account_info failed: {exc}", exc=exc
            )
            return {}

        credits_remaining = data.get("credits_remaining", data.get("credits", "N/A"))
        logger.info(
            "Prospeo account info retrieved. Credits remaining: {credits}",
            credits=credits_remaining,
        )
        return data

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _map_contact(
        self, data: Dict[str, Any], company_domain: str
    ) -> Optional[Contact]:
        """
        Map a Prospeo API person dict to a :class:`~src.models.contact.Contact`.

        Handles multiple nested structures (``data``, ``person``, flat) that
        Prospeo may return depending on the endpoint and plan.

        Args:
            data:           Raw person dict from the Prospeo API response.
            company_domain: Employer domain used as fallback when the response
                            does not include company information.

        Returns:
            A :class:`~src.models.contact.Contact`, or ``None`` if the
            minimum required fields (first and last name) cannot be resolved.
        """
        # Prospeo wraps enrichment results in a ``data`` or ``person`` sub-key
        person: Dict[str, Any] = (
            data.get("data") or data.get("person") or data
        )

        first_name: str = (
            person.get("first_name") or data.get("first_name") or ""
        ).strip()
        last_name: str = (
            person.get("last_name") or data.get("last_name") or ""
        ).strip()

        if not first_name and not last_name:
            logger.debug(
                "Prospeo _map_contact: cannot resolve name from response – skipping."
            )
            return None

        full_name: str = (
            person.get("full_name")
            or data.get("full_name")
            or f"{first_name} {last_name}".strip()
        )

        # Email resolution – prefer professional/work email
        email: Optional[str] = (
            person.get("professional_email")
            or person.get("email")
            or data.get("email")
        )

        # Confidence: Prospeo may express this as a string ("high", "medium") or float
        raw_conf = person.get("confidence") or data.get("email_confidence")
        confidence_map: Dict[str, float] = {
            "high": 0.9,
            "medium": 0.65,
            "low": 0.35,
        }
        if isinstance(raw_conf, str):
            email_confidence: float = confidence_map.get(raw_conf.lower(), 0.5)
        else:
            try:
                email_confidence = float(raw_conf) if raw_conf is not None else 0.0
                email_confidence = min(max(email_confidence, 0.0), 1.0)
            except (TypeError, ValueError):
                email_confidence = 0.0

        email_verified: bool = (
            person.get("email_verified")
            or data.get("email_verified")
            or bool(email and email_confidence >= 0.7)
        )

        # Title / seniority
        title: Optional[str] = person.get("job_title") or person.get("title")
        seniority: Optional[str] = person.get("seniority")
        department: Optional[str] = person.get("department")

        # Company
        comp_name: str = (
            person.get("company_name")
            or person.get("organization")
            or data.get("company_name")
            or "Unknown"
        )
        comp_domain: str = (
            person.get("company_website")
            or person.get("company_domain")
            or data.get("company_domain")
            or company_domain
        )

        # LinkedIn
        linkedin: Optional[str] = (
            person.get("linkedin_url") or data.get("linkedin_url")
        )

        # Location
        location_parts: List[str] = list(
            filter(
                None,
                [
                    person.get("city"),
                    person.get("country"),
                ],
            )
        )
        location: Optional[str] = ", ".join(location_parts) or person.get("location")

        return Contact(
            id=str(person.get("id")) if person.get("id") else None,
            first_name=first_name or "Unknown",
            last_name=last_name,
            full_name=full_name,
            title=title,
            seniority=seniority,
            department=department,
            company_name=comp_name,
            company_domain=comp_domain,
            linkedin_url=linkedin,
            email=email,
            email_confidence=email_confidence,
            email_verified=email_verified,
            phone=person.get("phone") or person.get("direct_phone"),
            location=location,
            source="prospeo",
            discovered_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return ``True`` when a non-trivial API key is available."""
        return bool(self.api_key and len(self.api_key) > 10)
