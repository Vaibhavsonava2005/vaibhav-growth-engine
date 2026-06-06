"""
Master Growth Pipeline for VAIBHAV GROWTH ENGINE.
Orchestrates the full domain → campaign flow.

Author: Vaibhav Sonava
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
import io
import sys
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from src.agents.ai_router import AIRouter
from src.analytics.scorer import ProspectScorer
from src.config.constants import DECISION_MAKER_TITLES
from src.config.settings import settings
from src.crm.crm_manager import CRMManager
from src.models.campaign import Campaign, CampaignResult, CampaignStatus, EmailDraft
from src.pipeline.research_engine import CompanyResearchEngine
from src.services.apollo import ApolloService
from src.services.brevo import BrevoService
from src.services.hunter import HunterService
from src.services.prospeo import ProspeoService
from src.utils.deduplicator import CompanyDeduplicator, ContactDeduplicator
from src.utils.validators import validate_domain

# Force UTF-8 on Windows to prevent charmap encode errors with unicode chars
console = Console(
    file=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stdout, "buffer")
    else sys.stdout,
    force_terminal=True,
    legacy_windows=False,
)


class GrowthPipeline:
    """Master pipeline: domain → companies → contacts → emails → research → AI → Brevo."""

    def __init__(self) -> None:
        self.apollo = ApolloService()
        self.prospeo = ProspeoService()
        self.hunter = HunterService()
        self.brevo = BrevoService()
        self.research_engine = CompanyResearchEngine()
        self.ai_router = AIRouter()
        self.scorer = ProspectScorer()
        self.crm = CRMManager()
        self.company_dedup = CompanyDeduplicator()
        self.contact_dedup = ContactDeduplicator()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def run(
        self,
        domain: str,
        campaign_name: Optional[str] = None,
        sender_product: str = "AI Solutions",
        dry_run: bool = False,
    ) -> Campaign:
        """
        Full pipeline execution.

        Steps:
          1. Company discovery (Apollo)
          2. Contact discovery (Prospeo + Apollo)
          3. Email enrichment (Hunter)
          4. Company research (Scraper + AI)
          5. AI personalization (Gemini/Groq/OpenRouter/Template)
        """
        domain = validate_domain(domain)
        campaign = Campaign(
            name=campaign_name or f"Campaign_{domain}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            target_domain=domain,
            id=str(uuid.uuid4()),
        )
        logger.info(f"Starting pipeline for domain: {domain}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # ── Step 1: Company Discovery ──────────────────────────────
            task1 = progress.add_task("[cyan]🔍 Discovering companies...", total=100)
            companies = self._discover_companies(domain)
            campaign.companies_found = len(companies)
            progress.update(task1, completed=100, description=f"[cyan]✓ {len(companies)} companies found")
            logger.info(f"Companies discovered: {len(companies)}")

            if not companies:
                logger.warning("No companies found. Pipeline will still generate email for the target domain.")

            # ── Step 2: Contact Discovery ──────────────────────────────
            task2 = progress.add_task(
                "[green]👥 Finding decision makers...", total=max(len(companies), 1)
            )
            all_contacts = []
            for company in companies:
                contacts = self._discover_contacts(company)
                all_contacts.extend(contacts)
                progress.advance(task2)
            campaign.contacts_found = len(all_contacts)
            progress.update(task2, description=f"[green]✓ {len(all_contacts)} decision makers found")

            # ── Step 3: Email Enrichment ───────────────────────────────
            task3 = progress.add_task(
                "[yellow]📧 Enriching emails...", total=max(len(all_contacts), 1)
            )
            enriched_contacts = []
            for contact in all_contacts:
                enriched = self._enrich_email(contact)
                if enriched and enriched.email:
                    enriched_contacts.append(enriched)
                progress.advance(task3)
            campaign.emails_found = len(enriched_contacts)
            progress.update(task3, description=f"[yellow]✓ {len(enriched_contacts)} emails verified")

            # ── Step 4: Company Research ───────────────────────────────
            task4 = progress.add_task(
                "[blue]🔬 Researching companies...", total=max(len(companies), 1)
            )
            intelligences: Dict[str, object] = {}
            for company in companies:
                try:
                    intel = self.research_engine.research_company(company)
                    intelligences[company.domain] = intel
                except Exception as e:
                    logger.warning(f"Research failed for {company.domain}: {e}")
                progress.advance(task4)
            progress.update(task4, description=f"[blue]✓ {len(intelligences)} companies researched")

            # ── Step 5: AI Personalization ─────────────────────────────
            task5 = progress.add_task(
                "[magenta]✨ Generating personalized emails...",
                total=max(len(enriched_contacts), 1),
            )
            email_drafts = []
            for contact in enriched_contacts:
                intel = intelligences.get(contact.company_domain)
                draft = self._generate_email(contact, intel, sender_product)
                email_drafts.append(draft)
                progress.advance(task5)
            campaign.email_drafts = email_drafts
            progress.update(
                task5,
                description=f"[magenta]✓ {len(email_drafts)} emails personalized "
                f"(via {self.ai_router.last_used_provider})",
            )

        logger.success(f"Pipeline complete: {len(email_drafts)} emails ready for {domain}")
        return campaign

    def send_campaign(self, campaign: Campaign, dry_run: bool = False) -> CampaignResult:
        """Send campaign emails via Brevo and save to CRM."""
        result = self.brevo.send_campaign_emails(campaign.email_drafts, campaign, dry_run=dry_run)
        campaign.status = CampaignStatus.SENT if not dry_run else CampaignStatus.DRAFT
        campaign.sent_at = datetime.utcnow() if not dry_run else None

        # Save to CRM
        self.crm.save_campaign(campaign)
        for draft in campaign.email_drafts:
            if draft.contact.email:
                self.crm.save_prospect(draft.contact, campaign.id)

        logger.success(f"Campaign '{campaign.name}' saved to CRM")
        return result

    def get_email_drafts(self, domain: str, sender_product: str = "AI Solutions") -> List[EmailDraft]:
        """Run pipeline and return email drafts without sending (preview mode)."""
        campaign = self.run(domain, sender_product=sender_product, dry_run=True)
        return campaign.email_drafts

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _discover_companies(self, domain: str) -> list:
        """Discover similar companies via Apollo, fall back to target domain only."""
        companies = []

        if self.apollo.is_configured():
            try:
                # Get similar companies in same industry
                similar = self.apollo.get_similar_companies(domain, limit=settings.MAX_COMPANIES)
                for c in similar:
                    if not self.company_dedup.is_duplicate(c.domain):
                        self.company_dedup.add(c.domain)
                        companies.append(c)
                logger.info(f"Apollo: {len(companies)} similar companies found")
            except Exception as e:
                logger.warning(f"Apollo company search failed: {e}")

        # Always include the target domain company
        if not any(c.domain == domain for c in companies):
            try:
                if self.apollo.is_configured():
                    target = self.apollo.enrich_company(domain)
                    if target:
                        companies.insert(0, target)
                        self.company_dedup.add(domain)
                else:
                    # Create basic company from domain
                    from src.models.company import Company
                    companies.insert(0, Company(
                        name=domain.split(".")[0].title(),
                        domain=domain,
                        website=f"https://{domain}",
                    ))
            except Exception as e:
                logger.warning(f"Could not enrich target domain {domain}: {e}")
                from src.models.company import Company
                companies.insert(0, Company(name=domain.split(".")[0].title(), domain=domain))

        return companies[: settings.MAX_COMPANIES]

    def _discover_contacts(self, company) -> list:
        """Find decision makers at a company via Hunter domain search → Prospeo → Apollo."""
        contacts = []
        from src.models.contact import Contact

        # ── Strategy 1: Hunter domain_search (returns people + emails directly) ──
        if self.hunter.is_configured():
            try:
                enrichments = self.hunter.domain_search(
                    company.domain,
                    limit=settings.MAX_CONTACTS_PER_COMPANY * 3,  # get more to filter
                )
                # Filter to decision-maker seniority levels
                SENIORITY_KEEP = {"executive", "senior", "director", "vp", "manager", "c-level", "owner"}
                for enr in enrichments:
                    if len(contacts) >= settings.MAX_CONTACTS_PER_COMPANY:
                        break
                    # Hunter EmailEnrichment has first_name, last_name, email
                    first = enr.first_name or ""
                    last = enr.last_name or ""
                    if not first and not last:
                        continue
                    # Accept all — we'll rank them later
                    contact = Contact(
                        first_name=first,
                        last_name=last,
                        full_name=f"{first} {last}".strip(),
                        title=None,  # Hunter domain_search doesn't always return title
                        company_name=company.name,
                        company_domain=company.domain,
                        email=enr.email,
                        email_confidence=enr.confidence_score,
                        email_verified=enr.is_verified,
                        source="hunter",
                    )
                    if not self.contact_dedup.is_duplicate(
                        email=contact.email or "", linkedin_url=""
                    ):
                        self.contact_dedup.add(email=contact.email or "", linkedin_url="")
                        contacts.append(contact)
                logger.info(f"Hunter domain search: {len(contacts)} contacts for {company.domain}")
            except Exception as e:
                logger.warning(f"Hunter domain search failed for {company.domain}: {e}")

        # ── Strategy 2: Prospeo enrich_person (by name) — skip search_people (needs LinkedIn URL) ──
        if len(contacts) < settings.MAX_CONTACTS_PER_COMPANY and self.prospeo.is_configured():
            try:
                for c in list(contacts):  # Try to enrich already-found contacts
                    if c.email and not c.email_verified:
                        enriched = self.prospeo.enrich_person(
                            c.first_name, c.last_name, c.company_domain, c.linkedin_url
                        )
                        if enriched and enriched.email:
                            c.email = enriched.email
                            c.email_confidence = enriched.email_confidence
                logger.debug(f"Prospeo enrich: done for {company.domain}")
            except Exception as e:
                logger.warning(f"Prospeo failed for {company.domain}: {e}")

        # ── Strategy 3: Apollo people search ──
        if len(contacts) < settings.MAX_CONTACTS_PER_COMPANY and self.apollo.is_configured():
            try:
                found = self.apollo.search_people(
                    company.domain,
                    titles=DECISION_MAKER_TITLES[:8],
                    per_page=settings.MAX_CONTACTS_PER_COMPANY,
                )
                for c in found:
                    if not self.contact_dedup.is_duplicate(email=c.email or "", linkedin_url=c.linkedin_url or ""):
                        self.contact_dedup.add(email=c.email or "", linkedin_url=c.linkedin_url or "")
                        contacts.append(c)
            except Exception as e:
                logger.warning(f"Apollo people search failed for {company.domain}: {e}")

        return contacts[: settings.MAX_CONTACTS_PER_COMPANY]

    def _enrich_email(self, contact) -> Optional[object]:
        """Find email via Hunter.io, return contact with email filled in."""
        # Already has email
        if contact.email and contact.email_confidence >= 0.5:
            return contact

        if self.hunter.is_configured():
            try:
                enrichment = self.hunter.find_email(
                    contact.first_name, contact.last_name, contact.company_domain
                )
                if enrichment and enrichment.email:
                    contact.email = enrichment.email
                    contact.email_confidence = enrichment.confidence_score
                    contact.email_verified = enrichment.is_verified
                    logger.debug(f"Email found: {enrichment.email} (confidence: {enrichment.confidence_score:.0%})")
                    return contact
            except Exception as e:
                logger.warning(f"Hunter enrichment failed for {contact.full_name}: {e}")

        # Return contact even without email if it came with one from the service
        if contact.email:
            return contact
        return None

    def _generate_email(self, contact, intel, sender_product: str) -> EmailDraft:
        """Generate personalized email via AI router."""
        try:
            result = self.ai_router.generate_email(contact, intel, sender_product)
            return EmailDraft(
                contact=contact,
                company_intelligence=intel,
                subject=result.get("subject", f"Quick question about {contact.company_name}"),
                body=result.get("body", ""),
                preview_text=result.get("preview_text", ""),
                ai_provider_used=result.get("ai_provider", "template"),
                personalization_score=result.get("personalization_score", 20.0),
                follow_up_sequence=result.get("follow_ups", []),
            )
        except Exception as e:
            logger.error(f"Email generation failed for {contact.full_name}: {e}")
            return EmailDraft(
                contact=contact,
                company_intelligence=intel,
                subject=f"Partnership opportunity with {contact.company_name}",
                body=f"Hi {contact.first_name},\n\nI'd love to connect about how we can help {contact.company_name}.\n\nBest,\n{settings.SENDER_NAME}",
                ai_provider_used="fallback",
                personalization_score=10.0,
            )
