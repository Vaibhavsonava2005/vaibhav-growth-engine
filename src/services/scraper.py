"""
Web scraping service for company intelligence gathering.

Uses ``requests`` for HTTP and ``BeautifulSoup`` (lxml parser) for
DOM parsing. Handles timeouts, SSL errors, 403/404 pages, and redirect
loops gracefully.
"""

import re
import time
import urllib.parse
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from loguru import logger
from requests.exceptions import (
    ConnectionError,
    ReadTimeout,
    SSLError,
    TooManyRedirects,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT: int = 10  # seconds
_MAX_TEXT_LENGTH: int = 2000

_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Pages appended to the domain when doing a full company scrape
_COMPANY_PAGES: Dict[str, str] = {
    "homepage": "",
    "about": "/about",
    "services": "/services",
    "careers": "/careers",
    "team": "/team",
}

# Technology fingerprints: (regex pattern OR string, human-readable label)
_TECH_SIGNATURES: List[tuple] = [
    # JS frameworks / libraries
    (re.compile(r"react(?:\.min)?\.js", re.I), "React"),
    (re.compile(r"next(?:js)?", re.I), "Next.js"),
    (re.compile(r"vue(?:\.min)?\.js", re.I), "Vue.js"),
    (re.compile(r"angular(?:\.min)?\.js", re.I), "Angular"),
    (re.compile(r"svelte", re.I), "Svelte"),
    (re.compile(r"nuxt", re.I), "Nuxt.js"),
    # CMS / e-commerce
    (re.compile(r"wp-content|wp-includes", re.I), "WordPress"),
    (re.compile(r"shopify", re.I), "Shopify"),
    (re.compile(r"woocommerce", re.I), "WooCommerce"),
    (re.compile(r"squarespace", re.I), "Squarespace"),
    (re.compile(r"wix\.com", re.I), "Wix"),
    (re.compile(r"webflow", re.I), "Webflow"),
    (re.compile(r"ghost", re.I), "Ghost CMS"),
    # Analytics / marketing
    (re.compile(r"google-analytics|gtag|ga\(", re.I), "Google Analytics"),
    (re.compile(r"gtm\.js|googletagmanager", re.I), "Google Tag Manager"),
    (re.compile(r"hotjar", re.I), "Hotjar"),
    (re.compile(r"segment\.com|analytics\.js", re.I), "Segment"),
    (re.compile(r"intercom", re.I), "Intercom"),
    (re.compile(r"hubspot", re.I), "HubSpot"),
    (re.compile(r"zendesk", re.I), "Zendesk"),
    # Infrastructure / cloud
    (re.compile(r"cloudflare", re.I), "Cloudflare"),
    (re.compile(r"netlify", re.I), "Netlify"),
    (re.compile(r"vercel", re.I), "Vercel"),
    (re.compile(r"amazonaws", re.I), "AWS"),
    # Other
    (re.compile(r"stripe", re.I), "Stripe"),
    (re.compile(r"twilio", re.I), "Twilio"),
    (re.compile(r"firebase", re.I), "Firebase"),
    (re.compile(r"supabase", re.I), "Supabase"),
    (re.compile(r"tailwindcss|tailwind", re.I), "Tailwind CSS"),
    (re.compile(r"bootstrap", re.I), "Bootstrap"),
]

# Common job title keywords used when mining a careers page
_JOB_TITLE_PATTERNS: List[re.Pattern] = [
    re.compile(
        r"\b("
        r"(?:senior|lead|principal|junior|mid|staff|associate|founding)?\s*"
        r"(?:software|backend|frontend|full[\s\-]?stack|platform|mobile|ios|android|"
        r"devops|site reliability|machine learning|ml|ai|data|product|growth|"
        r"marketing|sales|customer success|solutions|security|qa|test|"
        r"cloud|infrastructure|network|embedded|firmware)?\s*"
        r"(?:engineer|developer|architect|manager|director|analyst|scientist|"
        r"designer|specialist|consultant|lead|head|vp|vice president|"
        r"recruiter|coordinator|representative|officer|executive)"
        r")\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b("
        r"(?:chief|co-founder|founder|cto|ceo|coo|cmo|cfo|vp|head of|"
        r"director of|president)\s+"
        r"(?:\w+\s*){1,4}"
        r")\b",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class WebScraper:
    """
    Company intelligence web scraper.

    Provides page-level scraping, multi-page company profiling,
    technology detection, and careers-page job-title extraction.
    """

    def __init__(self) -> None:
        self._session: requests.Session = self._build_session()
        logger.info("WebScraper initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape_page(self, url: str) -> str:
        """
        Fetch *url* and return the main textual content.

        Navigational chrome (``<nav>``, ``<header>``, ``<footer>``,
        ``<aside>``), scripts, styles, and ads are stripped before
        extraction. Raises no exceptions – returns an empty string on
        any failure.

        Parameters
        ----------
        url:
            Fully-qualified URL to fetch.

        Returns
        -------
        str
            Cleaned, length-capped plain text.
        """
        html = self._fetch_html(url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        self._remove_boilerplate(soup)
        text = soup.get_text(separator=" ", strip=True)
        return self._clean_text(text)

    def scrape_company_pages(self, domain: str) -> Dict[str, str]:
        """
        Scrape the standard informational pages for a company domain.

        Attempts ``homepage``, ``/about``, ``/services``, ``/careers``,
        and ``/team``. Each page is independently error-handled; a
        failure on one page does not abort the others.

        Parameters
        ----------
        domain:
            Bare domain or full URL prefix, e.g.
            ``"acme.com"`` or ``"https://acme.com"``.

        Returns
        -------
        dict
            ``{page_name: text_content}`` – missing pages have an empty
            string value.
        """
        base = self._normalise_domain(domain)
        results: Dict[str, str] = {}

        for page_name, path in _COMPANY_PAGES.items():
            url = base.rstrip("/") + path
            logger.debug("Scraping {page} → {url}", page=page_name, url=url)
            text = self.scrape_page(url)
            results[page_name] = text
            if text:
                logger.info(
                    "Scraped '{page}' for {domain} ({chars} chars)",
                    page=page_name,
                    domain=domain,
                    chars=len(text),
                )
            else:
                logger.debug("No content for '{page}' at {url}", page=page_name, url=url)
            # Be polite
            time.sleep(0.5)

        return results

    def extract_technologies(self, html: str) -> List[str]:
        """
        Detect frontend/backend technologies mentioned in a page's HTML.

        Inspects ``<script src>``, ``<link href>``, ``<meta>`` tags, and
        the raw HTML text for known technology fingerprints.

        Parameters
        ----------
        html:
            Raw HTML source of the page.

        Returns
        -------
        list[str]
            De-duplicated list of detected technology names.
        """
        if not html:
            return []

        detected: List[str] = []

        # Parse meta tags and element attributes
        try:
            soup = BeautifulSoup(html, "lxml")
            # Combine all attribute values that might reference technologies
            tag_text_parts: List[str] = []
            for tag in soup.find_all(["script", "link", "meta"]):
                for attr in ("src", "href", "content", "data-src"):
                    val = tag.get(attr, "")
                    if val:
                        tag_text_parts.append(val)
        except Exception:  # noqa: BLE001
            tag_text_parts = []

        combined = html + " " + " ".join(tag_text_parts)

        for pattern, label in _TECH_SIGNATURES:
            if isinstance(pattern, re.Pattern):
                if pattern.search(combined):
                    detected.append(label)
            elif isinstance(pattern, str):
                if pattern.lower() in combined.lower():
                    detected.append(label)

        unique = list(dict.fromkeys(detected))  # preserve order, deduplicate
        logger.debug("Technologies detected: {techs}", techs=unique)
        return unique

    def extract_job_titles(self, text: str) -> List[str]:
        """
        Mine job titles from a careers or team page text body.

        Uses a curated set of regex patterns that cover engineering,
        product, leadership, and operational roles.

        Parameters
        ----------
        text:
            Plain text content of the careers / team page.

        Returns
        -------
        list[str]
            De-duplicated, title-cased list of matched job titles.
        """
        if not text:
            return []

        raw_matches: List[str] = []
        for pattern in _JOB_TITLE_PATTERNS:
            for match in pattern.finditer(text):
                raw_matches.append(match.group(0).strip())

        # Normalise: title-case, deduplicate, discard very short fragments
        seen: set = set()
        titles: List[str] = []
        for raw in raw_matches:
            cleaned = re.sub(r"\s+", " ", raw).strip().title()
            key = cleaned.lower()
            if len(cleaned) >= 6 and key not in seen:
                seen.add(key)
                titles.append(cleaned)

        logger.debug("Job titles extracted ({n}): {titles}", n=len(titles), titles=titles[:10])
        return titles

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch *url* and return the raw HTML string.

        Attempts with SSL verification first; falls back to
        ``verify=False`` on :class:`SSLError`. Returns *None* on any
        unrecoverable failure.
        """
        for verify_ssl in (True, False):
            try:
                response = self._session.get(
                    url,
                    timeout=_DEFAULT_TIMEOUT,
                    verify=verify_ssl,
                    allow_redirects=True,
                )
                if response.status_code in (403, 404):
                    logger.debug(
                        "HTTP {code} for {url} – skipping",
                        code=response.status_code,
                        url=url,
                    )
                    return None
                response.raise_for_status()
                return response.text
            except SSLError:
                if verify_ssl:
                    logger.warning(
                        "SSL error for {url} – retrying without verification", url=url
                    )
                    import urllib3  # noqa: PLC0415

                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    continue
                logger.error("SSL error persists for {url} – aborting", url=url)
                return None
            except TooManyRedirects:
                logger.warning("Redirect loop detected for {url}", url=url)
                return None
            except ReadTimeout:
                logger.warning("Timeout after {t}s for {url}", t=_DEFAULT_TIMEOUT, url=url)
                return None
            except ConnectionError as exc:
                logger.warning("Connection error for {url}: {exc}", url=url, exc=exc)
                return None
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unexpected fetch error for {url}: {exc}", url=url, exc=exc)
                return None
        return None  # unreachable but satisfies type checker

    @staticmethod
    def _remove_boilerplate(soup: BeautifulSoup) -> None:
        """
        Destructively remove navigational and non-content elements from *soup*.
        """
        for tag in soup(
            [
                "nav",
                "header",
                "footer",
                "aside",
                "script",
                "style",
                "noscript",
                "iframe",
                "svg",
                "form",
                "button",
                "figure",
                "figcaption",
                "picture",
                "source",
                "template",
                "dialog",
            ]
        ):
            tag.decompose()

        # Also strip elements with telltale class/id patterns
        boilerplate_patterns = re.compile(
            r"\b(nav|navbar|header|footer|sidebar|cookie|banner|ad|promo|"
            r"popup|overlay|modal|breadcrumb|pagination|social|share)\b",
            re.IGNORECASE,
        )
        for tag in soup.find_all(True):
            if tag is None or not hasattr(tag, "get") or getattr(tag, "attrs", None) is None:
                continue
            cls = " ".join(tag.get("class", []) or [])
            tid = tag.get("id", "") or ""
            if boilerplate_patterns.search(cls) or boilerplate_patterns.search(tid):
                try:
                    tag.decompose()
                except Exception:
                    pass

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalise whitespace and cap the text at ``_MAX_TEXT_LENGTH`` chars.

        Parameters
        ----------
        text:
            Raw text after HTML stripping.

        Returns
        -------
        str
            Cleaned, truncated string.
        """
        # Collapse multiple spaces / tabs
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse many consecutive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        if len(text) > _MAX_TEXT_LENGTH:
            text = text[:_MAX_TEXT_LENGTH].rsplit(" ", 1)[0] + "…"
        return text

    @staticmethod
    def _normalise_domain(domain: str) -> str:
        """
        Ensure *domain* is a fully-qualified URL with ``https://`` prefix.

        Parameters
        ----------
        domain:
            Raw domain input, e.g. ``"acme.com"`` or ``"http://acme.com"``.

        Returns
        -------
        str
            URL string with scheme, e.g. ``"https://acme.com"``.
        """
        if not domain:
            raise ValueError("Domain must not be empty")
        if "://" not in domain:
            domain = "https://" + domain.lstrip("/")
        parsed = urllib.parse.urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def _build_session() -> requests.Session:
        """Return a pre-configured :class:`requests.Session`."""
        session = requests.Session()
        session.headers.update(_HEADERS)
        session.max_redirects = 10
        return session
