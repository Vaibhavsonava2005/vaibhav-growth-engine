"""
Prospect & Company Scorer for VAIBHAV GROWTH ENGINE.
Scores leads 0-100 based on seniority, company size, and intelligence signals.

Author: Vaibhav Sonava
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from src.models.company import Company, CompanyIntelligence
from src.models.contact import Contact
from src.models.prospect import ProspectScore


class ProspectScorer:
    """Score prospects on a 0-100 scale and assign priority tiers."""

    SENIORITY_SCORES: Dict[str, float] = {
        "founder": 30, "co-founder": 30, "ceo": 30, "chief executive": 30,
        "cto": 28, "chief technology": 28, "cpo": 27, "chief product": 27,
        "coo": 26, "chief operating": 26,
        "vp": 22, "vice president": 22,
        "head of": 18, "director": 18,
        "lead": 12, "principal": 12,
        "manager": 10, "senior manager": 12,
    }

    def score_prospect(
        self,
        contact: Contact,
        company: Company,
        intelligence: Optional[CompanyIntelligence] = None,
    ) -> ProspectScore:
        """Score a prospect and return a ProspectScore object."""
        company_score = self._score_company_size(company)
        contact_score = self._score_seniority(contact.title or "")
        intel_score = self._score_intelligence(intelligence)
        email_score = round(contact.email_confidence * 20, 1)  # 0-20

        total = min(100.0, company_score + contact_score + intel_score + email_score)
        priority = "high" if total >= 70 else ("medium" if total >= 40 else "low")

        breakdown = {
            "company_size": company_score,
            "seniority": contact_score,
            "intelligence": intel_score,
            "email_confidence": email_score,
        }
        logger.debug(f"Scored {contact.full_name} @ {company.name}: {total:.1f} ({priority})")

        return ProspectScore(
            contact=contact,
            company=company,
            company_intelligence=intelligence,
            total_score=total,
            company_score=company_score,
            contact_score=contact_score,
            opportunity_score=intel_score,
            email_confidence_score=email_score,
            scoring_breakdown=breakdown,
            priority=priority,
            follow_up_suggested=(total >= 50),
        )

    def score_companies(
        self,
        companies: List[Company],
        intelligences: Optional[Dict[str, CompanyIntelligence]] = None,
    ) -> List[Company]:
        """Sort companies by opportunity score descending."""
        intelligences = intelligences or {}
        for company in companies:
            intel = intelligences.get(company.domain)
            company.opportunity_score = self._score_intelligence(intel) + self._score_company_size(company)
        return sorted(companies, key=lambda c: c.opportunity_score, reverse=True)

    def _score_seniority(self, title: str) -> float:
        """Score contact seniority from title string."""
        title_lower = title.lower()
        for keyword, score in self.SENIORITY_SCORES.items():
            if keyword in title_lower:
                return score
        return 5.0

    def _score_company_size(self, company: Company) -> float:
        """Score based on employee count: startup(5) → enterprise(30)."""
        count = company.employee_count or 0
        if count >= 1000:
            return 30.0
        elif count >= 200:
            return 25.0
        elif count >= 50:
            return 20.0
        elif count >= 10:
            return 15.0
        elif count >= 1:
            return 10.0
        return 5.0

    def _score_intelligence(self, intelligence: Optional[CompanyIntelligence]) -> float:
        """Score based on number of pain points + opportunities identified."""
        if not intelligence:
            return 0.0
        pain_score = min(15.0, len(intelligence.pain_points) * 3.0)
        opp_score = min(10.0, len(intelligence.opportunities) * 2.0)
        signal_score = min(5.0, (len(intelligence.growth_signals) + len(intelligence.hiring_signals)))
        return pain_score + opp_score + signal_score
