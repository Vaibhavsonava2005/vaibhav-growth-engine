"""
deduplicator.py
---------------
Deduplication utilities for VAIBHAV GROWTH ENGINE.

Prevents the same company domain or contact (email / LinkedIn URL) from
appearing more than once in prospect lists, ensuring that outreach campaigns
never send duplicate messages.

Classes
-------
* :class:`CompanyDeduplicator`  – tracks seen domains.
* :class:`ContactDeduplicator`  – tracks seen emails and LinkedIn URLs.

Functions
---------
* :func:`deduplicate_companies` – filter a list of company dicts by domain.
* :func:`deduplicate_contacts`  – filter a list of contact dicts by email and
  LinkedIn URL.

Both free functions accept lists of plain ``dict`` objects so they are
compatible with any data model that the rest of the engine uses.
"""

from __future__ import annotations

from typing import Any

from src.utils.logger import logger
from src.utils.validators import sanitize_domain, validate_email, is_valid_linkedin_url

# ---------------------------------------------------------------------------
# Company deduplication
# ---------------------------------------------------------------------------

class CompanyDeduplicator:
    """
    Stateful deduplicator that tracks company domains seen so far in a
    pipeline run.

    Domains are normalised (lower-cased, stripped) before comparison so that
    ``"Example.com"``, ``"example.com  "``, and ``"EXAMPLE.COM"`` are all
    treated as the same entry.

    Example::

        dedup = CompanyDeduplicator()
        dedup.add("example.com")
        dedup.is_duplicate("example.com")  # → True
        dedup.is_duplicate("other.com")    # → False
    """

    def __init__(self) -> None:
        self._seen_domains: set[str] = set()

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def is_duplicate(self, domain: str) -> bool:
        """
        Return ``True`` if *domain* has already been added to this tracker.

        Args:
            domain: The company domain string to check.

        Returns:
            ``True`` when *domain* (normalised) is already in the seen set.
        """
        return sanitize_domain(domain) in self._seen_domains

    def add(self, domain: str) -> None:
        """
        Mark *domain* as seen so future calls to :meth:`is_duplicate` return
        ``True`` for it.

        Args:
            domain: The company domain to register.
        """
        normalised = sanitize_domain(domain)
        if normalised:
            self._seen_domains.add(normalised)
            logger.debug(
                "CompanyDeduplicator: registered domain {domain!r}",
                domain=normalised,
            )

    def reset(self) -> None:
        """Clear all tracked domains (useful between pipeline runs)."""
        self._seen_domains.clear()
        logger.debug("CompanyDeduplicator: reset – all tracked domains cleared.")

    @property
    def count(self) -> int:
        """Number of unique domains currently tracked."""
        return len(self._seen_domains)

    def __contains__(self, domain: str) -> bool:
        return self.is_duplicate(domain)

    def __repr__(self) -> str:
        return f"CompanyDeduplicator(seen={self.count})"


# ---------------------------------------------------------------------------
# Contact deduplication
# ---------------------------------------------------------------------------

class ContactDeduplicator:
    """
    Stateful deduplicator that tracks contacts by both email address and
    LinkedIn profile URL.

    A contact is considered a duplicate if *either* their email or their
    LinkedIn URL has been seen before, preventing the same person from
    appearing twice even if they are listed under two different spellings.

    Example::

        dedup = ContactDeduplicator()
        dedup.add("alice@example.com", "https://linkedin.com/in/alice")
        dedup.is_duplicate("alice@example.com", None)  # → True
        dedup.is_duplicate(None, "https://linkedin.com/in/alice")  # → True
    """

    def __init__(self) -> None:
        self._seen_emails: set[str] = set()
        self._seen_linkedin: set[str] = set()

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def is_duplicate(
        self,
        email: str | None = None,
        linkedin_url: str | None = None,
    ) -> bool:
        """
        Return ``True`` if the contact identified by *email* or *linkedin_url*
        has already been added to this tracker.

        At least one of *email* or *linkedin_url* must be provided; otherwise
        the method returns ``False`` (cannot determine uniqueness).

        Args:
            email:        The contact's email address (optional).
            linkedin_url: The contact's LinkedIn profile URL (optional).

        Returns:
            ``True`` when either identifier has been seen before.
        """
        if email and email.strip().lower() in self._seen_emails:
            return True
        if linkedin_url and linkedin_url.strip().lower() in self._seen_linkedin:
            return True
        return False

    def add(
        self,
        email: str | None = None,
        linkedin_url: str | None = None,
    ) -> None:
        """
        Register a contact's identifiers so they are recognised as duplicates
        in future :meth:`is_duplicate` checks.

        Args:
            email:        The contact's email address (optional).
            linkedin_url: The contact's LinkedIn profile URL (optional).
        """
        if email:
            normalised_email = email.strip().lower()
            self._seen_emails.add(normalised_email)
            logger.debug(
                "ContactDeduplicator: registered email {email!r}",
                email=normalised_email,
            )

        if linkedin_url:
            normalised_li = linkedin_url.strip().lower()
            self._seen_linkedin.add(normalised_li)
            logger.debug(
                "ContactDeduplicator: registered linkedin {url!r}",
                url=normalised_li,
            )

    def reset(self) -> None:
        """Clear all tracked contacts (useful between pipeline runs)."""
        self._seen_emails.clear()
        self._seen_linkedin.clear()
        logger.debug("ContactDeduplicator: reset – all tracked contacts cleared.")

    @property
    def email_count(self) -> int:
        """Number of unique email addresses currently tracked."""
        return len(self._seen_emails)

    @property
    def linkedin_count(self) -> int:
        """Number of unique LinkedIn URLs currently tracked."""
        return len(self._seen_linkedin)

    def __repr__(self) -> str:
        return (
            f"ContactDeduplicator("
            f"emails={self.email_count}, "
            f"linkedin={self.linkedin_count})"
        )


# ---------------------------------------------------------------------------
# Free functions for one-shot list deduplication
# ---------------------------------------------------------------------------

def deduplicate_companies(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return a new list containing only the first occurrence of each unique
    company domain found in *companies*.

    Each dict in *companies* should contain a ``"domain"`` key.  Entries
    missing that key (or with a falsy domain) are included once in the result
    to avoid silently dropping data; a warning is emitted for each such entry.

    Args:
        companies: List of company dicts, each expected to have a ``"domain"``
                   key.

    Returns:
        A deduplicated list preserving the original ordering.

    Example::

        raw = [
            {"domain": "example.com", "name": "Example"},
            {"domain": "Example.com", "name": "Example (dup)"},
            {"domain": "other.com",   "name": "Other"},
        ]
        deduplicate_companies(raw)
        # → [{"domain": "example.com", …}, {"domain": "other.com", …}]
    """
    dedup = CompanyDeduplicator()
    unique: list[dict[str, Any]] = []
    dropped = 0

    for company in companies:
        domain: str = company.get("domain", "") or ""

        if not domain:
            logger.warning(
                "deduplicate_companies: company entry has no 'domain' key – "
                "including as-is: {company}",
                company=company,
            )
            unique.append(company)
            continue

        if dedup.is_duplicate(domain):
            logger.debug(
                "deduplicate_companies: dropping duplicate domain {domain!r}",
                domain=domain,
            )
            dropped += 1
            continue

        dedup.add(domain)
        unique.append(company)

    logger.info(
        "deduplicate_companies: {total} input → {unique} unique, {dropped} dropped",
        total=len(companies),
        unique=len(unique),
        dropped=dropped,
    )
    return unique


def deduplicate_contacts(contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return a new list containing only the first occurrence of each unique
    contact, identified by email address and/or LinkedIn URL.

    Each dict in *contacts* may contain ``"email"`` and/or ``"linkedin_url"``
    keys.  A contact is considered a duplicate if *either* identifier has been
    seen before.  Entries with neither key are included once with a warning.

    Args:
        contacts: List of contact dicts, each expected to contain ``"email"``
                  and/or ``"linkedin_url"`` keys.

    Returns:
        A deduplicated list preserving the original ordering.

    Example::

        raw = [
            {"email": "alice@ex.com", "linkedin_url": "…/in/alice"},
            {"email": "alice@ex.com", "linkedin_url": "…/in/alice2"},  # dup email
            {"email": "bob@ex.com",   "linkedin_url": "…/in/bob"},
        ]
        deduplicate_contacts(raw)
        # → first + third entry only
    """
    dedup = ContactDeduplicator()
    unique: list[dict[str, Any]] = []
    dropped = 0

    for contact in contacts:
        email: str | None = contact.get("email") or None
        linkedin_url: str | None = contact.get("linkedin_url") or None

        if not email and not linkedin_url:
            logger.warning(
                "deduplicate_contacts: contact entry has neither 'email' nor "
                "'linkedin_url' – including as-is: {contact}",
                contact=contact,
            )
            unique.append(contact)
            continue

        if dedup.is_duplicate(email=email, linkedin_url=linkedin_url):
            logger.debug(
                "deduplicate_contacts: dropping duplicate contact "
                "(email={email!r}, linkedin={li!r})",
                email=email,
                li=linkedin_url,
            )
            dropped += 1
            continue

        dedup.add(email=email, linkedin_url=linkedin_url)
        unique.append(contact)

    logger.info(
        "deduplicate_contacts: {total} input → {unique} unique, {dropped} dropped",
        total=len(contacts),
        unique=len(unique),
        dropped=dropped,
    )
    return unique
