"""
Company Research Engine for VAIBHAV GROWTH ENGINE.
Scrapes company pages and extracts intelligence signals.

Author: Vaibhav Sonava
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from loguru import logger

from src.agents.ai_router import AIRouter
from src.config.constants import OPPORTUNITY_KEYWORDS, PAIN_POINTS_KEYWORDS
from src.models.company import Company, CompanyIntelligence
from src.services.scraper import WebScraper


class CompanyResearchEngine:
    """Scrape company pages and extract actionable intelligence."""

    def __init__(self) -> None:
        self.scraper = WebScraper()
        self.ai_router = AIRouter()

    def research_company(self, company: Company) -> CompanyIntelligence:
        """Full research pipeline: scrape → extract → AI-enrich → return intelligence."""
        logger.info(f"Researching: {company.name} ({company.domain})")
        try:
            pages = self.scraper.scrape_company_pages(company.domain)
            # Guard: scraper may return None or empty
            if not pages:
                pages = {}
            # Guard: ensure all values are strings (scraper may return None on failure)
            pages = {k: (v or "") for k, v in pages.items()}
            full_text = " ".join(pages.values())
            technologies = self.scraper.extract_technologies(
                pages.get("homepage", "") or pages.get("about", "")
            )
            hiring_signals = self.scraper.extract_job_titles(pages.get("careers", "") or "")

            # Try AI analysis first, fall back to keyword extraction
            ai_result = self.ai_router.analyze_company(company.name, pages) or {}
            if ai_result and ai_result.get("pain_points"):
                pain_points = ai_result.get("pain_points", [])
                opportunities = ai_result.get("opportunities", [])
                growth_signals = ai_result.get("growth_signals", [])
            else:
                pain_points = self._extract_pain_points_keywords(full_text)
                opportunities = self._extract_opportunities(ai_result, company)
                growth_signals = self._extract_growth_signals(full_text)

            # Merge hiring signals from AI
            if ai_result and ai_result.get("hiring_signals"):
                hiring_signals = list(set(hiring_signals + ai_result["hiring_signals"]))

            intel = CompanyIntelligence(
                company=company,
                homepage_text=pages.get("homepage", "")[:1000],
                about_text=pages.get("about", "")[:1000],
                services_text=pages.get("services", "")[:1000],
                careers_text=pages.get("careers", "")[:500],
                technologies=technologies[:10],
                pain_points=pain_points[:5],
                opportunities=opportunities[:5],
                hiring_signals=hiring_signals[:5],
                growth_signals=growth_signals[:5],
            )
            logger.info(
                f"Research complete: {company.name} — "
                f"{len(pain_points)} pain points, {len(opportunities)} opportunities"
            )
            return intel

        except Exception as e:
            logger.error(f"Research failed for {company.domain}: {e}")
            return CompanyIntelligence(
                company=company,
                pain_points=self._default_pain_points(company),
                opportunities=self._default_opportunities(company),
            )

    def _extract_pain_points_keywords(self, text: str) -> List[str]:
        """Keyword-based pain point extraction from scraped text."""
        text_lower = text.lower()
        found = []
        for category, keywords in PAIN_POINTS_KEYWORDS.items():
            matches = [kw for kw in keywords if kw.lower() in text_lower]
            if not matches:
                # If category keywords NOT found, it may be a gap/pain point
                if category == "ai":
                    found.append("No visible AI automation — manual processes likely")
                elif category == "automation":
                    found.append("Workflow automation not evident")
                elif category == "cloud":
                    found.append("Cloud infrastructure signals missing")
            else:
                if category == "scaling":
                    found.append("Scaling challenges — team is growing rapidly")
                elif category == "web":
                    found.append("Active web/product development in progress")
        return found

    def _extract_opportunities(self, ai_result: Dict, company: Company) -> List[str]:
        """Derive service opportunities based on industry and pain points."""
        opportunities = ai_result.get("opportunities", [])
        if opportunities:
            return opportunities

        # Fallback rule-based opportunities
        industry = (company.industry or "").lower()
        opps = []
        if "tech" in industry or "software" in industry or "saas" in industry:
            opps += ["AI Integration & Automation", "Scalable Cloud Infrastructure"]
        if "finance" in industry or "fintech" in industry:
            opps += ["AI-powered Risk Analytics", "Workflow Automation"]
        if "health" in industry or "medical" in industry:
            opps += ["AI Diagnostic Tools", "Data Intelligence Platform"]
        if "retail" in industry or "ecommerce" in industry:
            opps += ["Personalization Engine", "Inventory Intelligence"]

        if not opps:
            opps = ["AI Solutions", "Workflow Automation", "Software Development", "Cloud Infrastructure"]
        return opps[:5]

    def _extract_growth_signals(self, text: str) -> List[str]:
        """Extract growth signals from scraped text."""
        signals = []
        text_lower = text.lower()
        growth_patterns = [
            (r"series [a-d]|seed round|raised \$|funding", "Recent funding round detected"),
            (r"hiring|we.re growing|join our team|open positions", "Active hiring — team expansion"),
            (r"launch|new product|just released|announcing", "New product/feature launch"),
            (r"partner|partnership|integration|acquired", "Strategic partnerships forming"),
            (r"global|international|expand|new market", "Geographic expansion signals"),
        ]
        for pattern, signal in growth_patterns:
            if re.search(pattern, text_lower):
                signals.append(signal)
        return signals

    def _default_pain_points(self, company: Company) -> List[str]:
        """Minimal default pain points when scraping fails."""
        return [
            "AI automation potential not yet realised",
            "Manual processes likely at current scale",
        ]

    def _default_opportunities(self, company: Company) -> List[str]:
        return ["AI Solutions", "Workflow Automation", "Software Development"]

    def batch_research(self, companies: List[Company]) -> List[CompanyIntelligence]:
        """Research multiple companies, continue on failure."""
        results = []
        for i, company in enumerate(companies, 1):
            logger.info(f"Researching company {i}/{len(companies)}: {company.name}")
            try:
                intel = self.research_company(company)
                results.append(intel)
            except Exception as e:
                logger.warning(f"Skipping {company.name}: {e}")
                results.append(CompanyIntelligence(company=company))
        return results
