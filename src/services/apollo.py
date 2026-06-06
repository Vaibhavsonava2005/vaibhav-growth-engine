"""
apollo.py
---------
Apollo.io API service client for VAIBHAV GROWTH ENGINE.

Provides company search, company enrichment, people search, and similar-company
discovery via the Apollo.io REST API v1.  All network calls use ``httpx`` with
a configurable timeout and are wrapped by ``tenacity`` for exponential-backoff
retries.  Loguru is used for all logging.

Usage::

    from src.services.apollo import ApolloService

    svc = ApolloService()
    companies = svc.search_companies(industry="SaaS", per_page=5)
    contacts  = svc.search_people("acme.com", titles=["CTO", "VP Engineering"])
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
from src.models.company import Company, CompanySize
from src.models.contact import Contact

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APOLLO_BASE_URL: str = "https://api.apollo.io"

_RETRY_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)

# Headcount → CompanySize mapping (upper-bound inclusive)
_SIZE_BUCKETS: List[tuple[int, CompanySize]] = [
    (10, CompanySize.STARTUP),
    (50, CompanySize.SMALL),
    (200, CompanySize.MEDIUM),
    (1_000, CompanySize.LARGE),
]


# ---------------------------------------------------------------------------
# Helper – derive CompanySize from raw headcount
# ---------------------------------------------------------------------------

def _headcount_to_size(count: Optional[int]) -> Optional[CompanySize]:
    """Map a raw employee count integer to a :class:`CompanySize` bucket."""
    if count is None:
        return None
    for threshold, size in _SIZE_BUCKETS:
        if count <= threshold:
            return size
    return CompanySize.ENTERPRISE


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ApolloService:
    """
    Client for the Apollo.io REST API.

    Supports:
    - Company search by domain / industry
    - Company enrichment by domain
    - People (contact) search by domain + title filters
    - Similar-company discovery

    All methods gracefully degrade to empty results when the API key is absent
    or invalid, logging appropriate warnings rather than raising exceptions to
    the caller.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.APOLLO_API_KEY
        self.base_url: str = APOLLO_BASE_URL
        self.timeout: int = settings.REQUEST_TIMEOUT
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
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
        Execute an HTTP request against the Apollo API.

        For POST requests the ``api_key`` is injected into the JSON body.
        For GET requests it is appended as a query parameter.  Both approaches
        satisfy Apollo's authentication requirements.

        Args:
            method:   HTTP verb (``"GET"`` or ``"POST"``).
            endpoint: Path relative to :attr:`base_url` (e.g. ``/api/v1/…``).
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

        # Inject API key into the appropriate location
        if method_upper == "POST":
            body: Dict[str, Any] = kwargs.pop("json", {})
            body["api_key"] = self.api_key
            kwargs["json"] = body
        else:
            params: Dict[str, Any] = kwargs.pop("params", {})
            params["api_key"] = self.api_key
            kwargs["params"] = params

        logger.debug(
            "Apollo API → {method} {url}",
            method=method_upper,
            url=url,
        )

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.request(method_upper, url, **kwargs)

            if response.status_code == 401:
                logger.error(
                    "Apollo API returned 401 Unauthorized – check APOLLO_API_KEY."
                )
                return {}

            if response.status_code == 422:
                logger.warning(
                    "Apollo API returned 422 Unprocessable – payload: {body}",
                    body=response.text[:400],
                )
                return {}

            if response.status_code == 429:
                logger.warning("Apollo API rate-limit hit (429) – backing off.")
                raise httpx.TimeoutException(
                    "Rate-limited by Apollo", request=response.request
                )

            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            logger.debug(
                "Apollo API ← {status} ({bytes} bytes)",
                status=response.status_code,
                bytes=len(response.content),
            )
            return data

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Apollo API HTTP error {status}: {msg}",
                status=exc.response.status_code,
                msg=exc.response.text[:300],
            )
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_companies(
        self,
        domain: Optional[str] = None,
        industry: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[Company]:
        """
        Search Apollo for companies matching the given filters.

        Args:
            domain:    Optional domain filter (e.g. ``"acme.com"``).
            industry:  Optional industry keyword / tag.
            page:      Results page number (1-indexed).
            per_page:  Number of results per page (max 100).

        Returns:
            A list of :class:`~src.models.company.Company` instances.
            Returns an empty list if the service is not configured or if the
            API returns no results.
        """
        if not self.is_configured():
            logger.warning(
                "ApolloService: APOLLO_API_KEY not configured – "
                "returning empty company list."
            )
            return []

        payload: Dict[str, Any] = {"page": page, "per_page": per_page}
        if domain:
            payload["q_organization_domains"] = [domain]
        if industry:
            payload["q_keywords"] = industry

        logger.info(
            "Apollo: searching companies | domain={domain} industry={industry} "
            "page={page}",
            domain=domain,
            industry=industry,
            page=page,
        )

        try:
            data = self._make_request(
                "POST", "/api/v1/mixed_companies/search", json=payload
            )
        except Exception as exc:
            logger.error("Apollo company search failed: {exc}", exc=exc)
            return []

        organizations: List[Dict[str, Any]] = data.get("organizations", [])
        logger.info(
            "Apollo: received {n} organizations.", n=len(organizations)
        )
        return [self._map_company(org) for org in organizations if org]

    def enrich_company(self, domain: str) -> Optional[Company]:
        """
        Enrich a single company by domain using Apollo's organisation endpoint.

        Args:
            domain: The company's primary web domain (e.g. ``"stripe.com"``).

        Returns:
            An enriched :class:`~src.models.company.Company` or ``None`` if
            enrichment fails or the service is not configured.
        """
        if not self.is_configured():
            logger.warning(
                "ApolloService: APOLLO_API_KEY not configured – "
                "skipping company enrichment for {domain}.",
                domain=domain,
            )
            return None

        logger.info("Apollo: enriching company domain={domain}", domain=domain)
        try:
            data = self._make_request(
                "GET",
                "/api/v1/organizations/enrich",
                params={"domain": domain},
            )
        except Exception as exc:
            logger.error(
                "Apollo company enrichment failed for {domain}: {exc}",
                domain=domain,
                exc=exc,
            )
            return None

        org: Optional[Dict[str, Any]] = data.get("organization")
        if not org:
            logger.warning(
                "Apollo: no organisation data returned for domain={domain}.",
                domain=domain,
            )
            return None

        return self._map_company(org)

    def search_people(
        self,
        company_domain: str,
        titles: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 5,
    ) -> List[Contact]:
        """
        Search for people at a specific company, optionally filtered by title.

        Args:
            company_domain: The employer's primary domain (e.g. ``"stripe.com"``).
            titles:         Optional list of job-title keywords to filter by.
            page:           Results page number (1-indexed).
            per_page:       Number of results per page.

        Returns:
            A list of :class:`~src.models.contact.Contact` instances.
        """
        if not self.is_configured():
            logger.warning(
                "ApolloService: APOLLO_API_KEY not configured – "
                "returning empty contact list."
            )
            return []

        # Per Apollo docs: /mixed_people/api_search is POST with QUERY params
        # (not JSON body) — field names use [] suffix for arrays
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        if company_domain:
            params["q_organization_domains_list[]"] = company_domain
        if titles:
            # Pass multiple titles as repeated query params
            params["person_titles[]"] = titles
        # Also filter by seniority to get decision makers
        params["person_seniorities[]"] = ["owner", "founder", "c_suite", "vp", "head", "director"]

        logger.info(
            "Apollo: searching people | domain={domain} titles={titles} page={page}",
            domain=company_domain,
            titles=titles,
            page=page,
        )

        try:
            # POST with query params — per API spec
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                url = f"{self.base_url}/api/v1/mixed_people/api_search"
                response = client.post(url, params=params)
                if response.status_code == 401:
                    logger.error("Apollo 401 – check API key")
                    return []
                if response.status_code == 403:
                    body = response.json()
                    logger.warning("Apollo 403 – {err}", err=body.get("error", ""))
                    return []
                if response.status_code == 429:
                    logger.warning("Apollo 429 rate limit hit")
                    return []
                if response.status_code == 422:
                    logger.warning("Apollo 422 – invalid params: {}", response.text[:200])
                    return []
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.error(
                "Apollo people search failed for {domain}: {exc}",
                domain=company_domain,
                exc=exc,
            )
            return []

        people: List[Dict[str, Any]] = data.get("people", [])
        logger.info("Apollo: received {n} people.", n=len(people))
        return [self._map_contact(person) for person in people if person]

    def get_similar_companies(
        self,
        domain: str,
        limit: int = 10,
    ) -> List[Company]:
        """
        Discover companies similar to the given domain.

        The implementation first enriches the seed domain to obtain its
        industry tag, then performs a broad industry search and filters out
        the seed itself.

        Args:
            domain: Seed company domain (e.g. ``"hubspot.com"``).
            limit:  Maximum number of similar companies to return.

        Returns:
            A list of similar :class:`~src.models.company.Company` instances.
        """
        if not self.is_configured():
            logger.warning(
                "ApolloService: APOLLO_API_KEY not configured – "
                "returning empty similar-companies list."
            )
            return []

        logger.info(
            "Apollo: finding similar companies for domain={domain}", domain=domain
        )

        seed = self.enrich_company(domain)
        if not seed:
            logger.warning(
                "Apollo: could not enrich seed domain {domain} – "
                "cannot find similar companies.",
                domain=domain,
            )
            return []

        industry = seed.industry
        similar = self.search_companies(
            industry=industry, per_page=min(limit + 5, 25)
        )
        # Exclude the seed domain from results
        filtered = [
            c for c in similar if c.domain and c.domain.lower() != domain.lower()
        ][:limit]

        logger.info(
            "Apollo: returning {n} similar companies for {domain}.",
            n=len(filtered),
            domain=domain,
        )
        return filtered

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _map_company(self, org: Dict[str, Any]) -> Company:
        """
        Map an Apollo ``organization`` dict to a :class:`~src.models.company.Company`.

        Handles missing or ``None`` values on every field to avoid validation
        errors when Apollo returns partial data.

        Args:
            org: Raw organization dictionary from the Apollo API response.

        Returns:
            A populated :class:`~src.models.company.Company` instance.
        """
        raw_count: Optional[int] = org.get("estimated_num_employees") or org.get(
            "num_employees"
        )
        try:
            employee_count: Optional[int] = int(raw_count) if raw_count else None
        except (TypeError, ValueError):
            employee_count = None

        # Build a best-effort location string
        location_parts: List[str] = list(
            filter(
                None,
                [
                    org.get("city"),
                    org.get("state"),
                    org.get("country"),
                ],
            )
        )
        location: Optional[str] = ", ".join(location_parts) or None

        # Founded year
        raw_year = org.get("founded_year")
        try:
            founded_year: Optional[int] = int(raw_year) if raw_year else None
        except (TypeError, ValueError):
            founded_year = None

        # Primary domain: prefer primary_domain field, fall back to website_url parsing
        domain_val: str = (
            org.get("primary_domain")
            or org.get("domain")
            or _extract_domain(org.get("website_url", ""))
            or "unknown.com"
        )

        return Company(
            id=str(org.get("id")) if org.get("id") else None,
            name=org.get("name") or "Unknown",
            domain=domain_val,
            website=org.get("website_url"),
            industry=org.get("industry"),
            employee_count=employee_count,
            company_size=_headcount_to_size(employee_count),
            linkedin_url=org.get("linkedin_url"),
            description=org.get("short_description") or org.get("seo_description"),
            location=location,
            founded_year=founded_year,
            funding_stage=org.get("latest_funding_stage"),
            source="apollo",
            discovered_at=datetime.utcnow(),
        )

    def _map_contact(self, person: Dict[str, Any]) -> Contact:
        """
        Map an Apollo ``person`` dict to a :class:`~src.models.contact.Contact`.

        Args:
            person: Raw person dictionary from the Apollo API response.

        Returns:
            A populated :class:`~src.models.contact.Contact` instance.
        """
        # Apollo people/api_search returns obfuscated last_name_obfuscated
        # and no email/phone (need enrichment for those)
        first_name: str = person.get("first_name") or "Unknown"
        last_name_raw: str = person.get("last_name") or person.get("last_name_obfuscated") or ""
        # Strip obfuscation markers if present (e.g. "Do***e" → keep as-is for display)
        full_name: str = person.get("name") or f"{first_name} {last_name_raw}".strip()

        # Email not returned by api_search — will be enriched by Hunter
        email: Optional[str] = person.get("email")
        raw_confidence = person.get("email_confidence") or person.get(
            "email_status_confidence"
        )
        try:
            email_confidence: float = float(raw_confidence) / 100.0 if raw_confidence else 0.0
            email_confidence = min(max(email_confidence, 0.0), 1.0)
        except (TypeError, ValueError):
            email_confidence = 0.0

        # Company info — api_search returns nested organization object
        org: Dict[str, Any] = person.get("organization") or {}
        company_name: str = (
            person.get("organization_name")
            or org.get("name")
            or "Unknown"
        )
        company_domain: str = (
            person.get("organization_domain")
            or org.get("primary_domain")
            or org.get("domain")
            or _extract_domain(org.get("website_url", ""))
            or "unknown.com"
        )

        # Location
        location_parts: List[str] = list(
            filter(None, [person.get("city"), person.get("country")])
        )
        location: Optional[str] = ", ".join(location_parts) or None

        return Contact(
            id=str(person.get("id")) if person.get("id") else None,
            first_name=first_name,
            last_name=last_name_raw,
            full_name=full_name,
            title=person.get("title"),
            seniority=person.get("seniority"),
            department=person.get("departments", [None])[0]
            if isinstance(person.get("departments"), list)
            else person.get("department"),
            company_name=company_name,
            company_domain=company_domain,
            linkedin_url=person.get("linkedin_url"),
            email=email,
            email_confidence=email_confidence,
            email_verified=person.get("email_status") == "verified",
            phone=person.get("phone") or person.get("direct_phone_number"),
            location=location,
            source="apollo",
            discovered_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return ``True`` when a non-trivial API key is available."""
        return bool(self.api_key and len(self.api_key) > 10)


# ---------------------------------------------------------------------------
# Module-level utility
# ---------------------------------------------------------------------------

def _extract_domain(url: Optional[str]) -> Optional[str]:
    """
    Naively extract the netloc from a URL string without importing ``urllib``.

    Examples::

        _extract_domain("https://www.acme.com/about")  # → "acme.com"
        _extract_domain(None)                           # → None
    """
    if not url:
        return None
    # Strip scheme
    stripped = url.split("//", 1)[-1]
    # Strip path, query, fragment
    netloc = stripped.split("/")[0].split("?")[0].split("#")[0]
    # Strip www.
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc or None
