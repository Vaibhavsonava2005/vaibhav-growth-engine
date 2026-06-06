"""
template_agent.py
-----------------
Rule-based personalisation engine for VAIBHAV GROWTH ENGINE.

This agent generates personalised outreach emails using template libraries
and company intelligence — no external AI API key required.  It serves as
the always-available fallback when all LLM providers are unavailable.
"""

from __future__ import annotations

import random
from typing import Optional

from loguru import logger

from src.config.constants import CAMPAIGN_TEMPLATES
from src.models.company import CompanyIntelligence
from src.models.contact import Contact


class TemplateAgent:
    """
    Rule-based personalisation engine.

    Selects and fills email templates using company intelligence signals,
    contact metadata, and a deterministic scoring algorithm.  Always
    available as a fallback — no network calls required.
    """

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_email(
        self,
        contact: Contact,
        intelligence: Optional[CompanyIntelligence],
        sender_product: str = "AI Solutions",
    ) -> dict:
        """
        Generate a personalised email using templates and company intelligence.

        Parameters
        ----------
        contact:
            The target contact record.
        intelligence:
            Enriched company intelligence, or ``None`` if unavailable.
        sender_product:
            The product / service name to reference in the email.

        Returns
        -------
        dict
            Keys: ``subject``, ``body``, ``preview_text``,
            ``personalization_score``, ``follow_ups``, ``ai_provider``.
        """
        logger.debug(
            "TemplateAgent generating email for {} at {}",
            contact.full_name,
            contact.company_name,
        )

        # ── Extract intelligence data ──────────────────────────────────
        pain_points: list[str] = []
        opportunities: list[str] = []
        industry: str = "your industry"

        if intelligence:
            pain_points = intelligence.pain_points[:2]
            opportunities = intelligence.opportunities[:2]
            if intelligence.company.industry:
                industry = intelligence.company.industry

        # ── Derive contact / company labels ───────────────────────────
        company_name: str = contact.company_name
        contact_name: str = (
            contact.first_name
            if contact.first_name
            else contact.full_name.split()[0]
        )
        contact_title: str = contact.title or "Leader"

        # ── Choose the primary pain point and opportunity ──────────────
        primary_pain: str = (
            pain_points[0]
            if pain_points
            else self._default_pain_point(sender_product)
        )
        primary_opportunity: str = (
            opportunities[0]
            if opportunities
            else f"{company_name}'s growth"
        )

        # ── Build email components ─────────────────────────────────────
        subject = self._build_subject(
            contact_name, company_name, pain_points, sender_product
        )
        body = self._build_body(
            contact_name,
            contact_title,
            company_name,
            industry,
            pain_points,
            opportunities,
            sender_product,
        )
        preview_text = self._build_preview(primary_pain, company_name, sender_product)

        # ── Follow-ups ─────────────────────────────────────────────────
        follow_up_1 = self._build_follow_up_1(contact_name, company_name, subject)
        follow_up_2 = self._build_follow_up_2(
            contact_name, company_name, sender_product
        )

        # ── Score ──────────────────────────────────────────────────────
        score = self.calculate_personalization_score(
            pain_points_used=min(len(pain_points), 2),
            opportunities_used=min(len(opportunities), 2),
            has_company_intel=intelligence is not None,
        )

        result = {
            "subject": subject,
            "body": body,
            "preview_text": preview_text,
            "personalization_score": score,
            "follow_ups": [follow_up_1, follow_up_2],
            "ai_provider": "template",
        }

        logger.info(
            "TemplateAgent email generated for {} (score={:.1f})",
            contact.full_name,
            score,
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_subject(
        self,
        contact_name: str,
        company_name: str,
        pain_points: list[str],
        sender_product: str,
    ) -> str:
        """
        Select the most relevant subject-line template and fill its placeholders.

        When pain points are available, prefer templates that reference them;
        otherwise fall back to generic company / product templates.
        """
        pain_point = pain_points[0] if pain_points else "operational efficiency"

        # Weight templates toward pain-point-aware ones when intel is available
        if pain_points:
            candidates = [
                CAMPAIGN_TEMPLATES["subject_lines"][1],  # "Helping {company} with {pain_point}"
                CAMPAIGN_TEMPLATES["subject_lines"][6],  # "How we helped a company like {company}..."
                CAMPAIGN_TEMPLATES["subject_lines"][7],  # "The fastest way {company} can tackle..."
                CAMPAIGN_TEMPLATES["subject_lines"][8],  # "{name}, is {pain_point} slowing..."
            ]
        else:
            candidates = [
                CAMPAIGN_TEMPLATES["subject_lines"][0],  # "Quick question for {name} at {company}"
                CAMPAIGN_TEMPLATES["subject_lines"][3],  # "3 ways {product} could accelerate..."
                CAMPAIGN_TEMPLATES["subject_lines"][4],  # "{company} + {product} — worth a 15-min chat?"
                CAMPAIGN_TEMPLATES["subject_lines"][9],  # "An idea for {company} from Vaibhav"
            ]

        template = random.choice(candidates)
        subject = template.format(
            name=contact_name,
            company=company_name,
            pain_point=pain_point,
            opportunity="recent growth",
            product=sender_product,
        )
        return subject

    def _build_body(
        self,
        contact_name: str,
        contact_title: str,
        company_name: str,
        industry: str,
        pain_points: list[str],
        opportunities: list[str],
        sender_product: str,
    ) -> str:
        """
        Build a professional, personalised email body (150–250 words).

        Selects opening, value proposition, and CTA from the template library,
        filling placeholders with real intelligence data wherever available.
        """
        primary_pain = pain_points[0] if pain_points else "operational efficiency"
        secondary_pain = pain_points[1] if len(pain_points) > 1 else None
        primary_opportunity = (
            opportunities[0] if opportunities else f"{company_name}'s growth trajectory"
        )

        # Pick opening
        if opportunities:
            opening_candidates = [
                CAMPAIGN_TEMPLATES["openings"][0],
                CAMPAIGN_TEMPLATES["openings"][2],
                CAMPAIGN_TEMPLATES["openings"][7],
            ]
        else:
            opening_candidates = [
                CAMPAIGN_TEMPLATES["openings"][1],
                CAMPAIGN_TEMPLATES["openings"][5],
                CAMPAIGN_TEMPLATES["openings"][6],
            ]

        opening = random.choice(opening_candidates).format(
            name=contact_name,
            company=company_name,
            pain_point=primary_pain,
            opportunity=primary_opportunity,
            product=sender_product,
        )

        # Pick value proposition
        value_prop = random.choice(CAMPAIGN_TEMPLATES["value_props"]).format(
            name=contact_name,
            company=company_name,
            pain_point=primary_pain,
            product=sender_product,
        )

        # Optional secondary pain point sentence
        secondary_sentence = ""
        if secondary_pain:
            secondary_sentence = (
                f" We've also seen teams in {industry} tackle "
                f"{secondary_pain} significantly faster once the core pipeline "
                "is streamlined."
            )

        # Pick CTA
        cta = random.choice(CAMPAIGN_TEMPLATES["ctas"]).format(
            name=contact_name,
            company=company_name,
            pain_point=primary_pain,
            product=sender_product,
            opportunity=primary_opportunity,
        )

        body = (
            f"Hi {contact_name},\n\n"
            f"{opening}\n\n"
            f"{value_prop}{secondary_sentence}\n\n"
            f"We work specifically with {industry} companies at {company_name}'s "
            f"stage, so I have a good sense of what actually moves the needle for "
            f"{contact_title.lower()} teams.\n\n"
            f"{cta}\n\n"
            "Best,\n"
            "Vaibhav Sonava\n"
            "Founder, Deknek\n"
            "vaibhav@deknek.com"
        )
        return body

    def _build_follow_up_1(
        self,
        contact_name: str,
        company_name: str,
        original_subject: str,
    ) -> str:
        """
        Build a 3-day follow-up email.

        Short, references the original email, and adds a micro-insight to
        provide incremental value rather than simply bumping the thread.
        """
        insights = [
            (
                "Companies in your space that invest in AI-powered automation "
                "typically report 40–60% reduction in manual overhead within the "
                "first quarter — thought that stat might be relevant."
            ),
            (
                "A quick data point: B2B teams that personalise outreach at scale "
                "see 3× higher reply rates compared to generic blasts — happy to "
                "share the methodology behind this."
            ),
            (
                "One thing I keep hearing from leaders at companies like "
                f"{company_name}: the biggest ROI wins come from automating the "
                "workflows that feel 'small' but eat 10+ hours a week."
            ),
            (
                "A peer of yours at a similar-stage company cut their sales cycle "
                "by 30% after we restructured their outreach pipeline — happy to "
                "walk you through exactly what changed."
            ),
        ]

        insight = random.choice(insights)

        follow_up = (
            f"Hi {contact_name},\n\n"
            f"Following up on my note about {company_name} — I know inboxes get "
            "busy, so just wanted to float this to the top.\n\n"
            f"{insight}\n\n"
            "Would a 15-minute call this week make sense? Happy to work around "
            "your schedule.\n\n"
            "Best,\n"
            "Vaibhav"
        )
        return follow_up

    def _build_follow_up_2(
        self,
        contact_name: str,
        company_name: str,
        sender_product: str,
    ) -> str:
        """
        Build a 7-day final follow-up email.

        Adds a concrete value offer (e.g., a free audit or template),
        uses a soft CTA, and signals this is the last touch to respect
        the prospect's inbox.
        """
        value_offers = [
            (
                f"I put together a short personalised breakdown of three quick wins "
                f"{company_name} could implement with {sender_product} — I can share "
                "it with no strings attached."
            ),
            (
                "Happy to send over a 1-page case study from a company at a similar "
                f"stage that used {sender_product} to solve the same challenge — no "
                "pitch, just the playbook."
            ),
            (
                f"I've sketched a rough 30-day action plan for how {company_name} "
                f"could leverage {sender_product} — it's yours if you want it."
            ),
            (
                "I'll include a free competitive landscape snapshot for "
                f"{company_name}'s niche when we connect — useful context regardless "
                "of whether we work together."
            ),
        ]

        offer = random.choice(value_offers)

        follow_up = (
            f"Hi {contact_name},\n\n"
            f"I'll keep this short — last note from me on this topic.\n\n"
            f"{offer}\n\n"
            "If timing isn't right, no worries at all. And if there's someone "
            f"else at {company_name} I should speak to, I'm happy to reach out "
            "to them instead.\n\n"
            "Either way, wishing you and the team a great quarter ahead.\n\n"
            "Best,\n"
            "Vaibhav"
        )
        return follow_up

    def _build_preview(
        self,
        primary_pain: str,
        company_name: str,
        sender_product: str,
    ) -> str:
        """Generate a concise preview text snippet (≤100 characters)."""
        previews = [
            f"How {sender_product} can help {company_name} tackle {primary_pain}",
            f"A quick idea for {company_name} — worth 2 minutes",
            f"Helping teams like {company_name} solve {primary_pain}",
            f"{company_name} + {sender_product}: a quick thought",
        ]
        preview = random.choice(previews)
        return preview[:100]

    @staticmethod
    def _default_pain_point(sender_product: str) -> str:
        """Return a generic pain point when no intelligence is available."""
        defaults = [
            "scaling efficiently",
            "reducing operational overhead",
            "automating repetitive workflows",
            "accelerating time-to-market",
        ]
        return random.choice(defaults)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def calculate_personalization_score(
        self,
        pain_points_used: int,
        opportunities_used: int,
        has_company_intel: bool,
    ) -> float:
        """
        Compute a 0–100 personalisation score.

        Scoring breakdown
        -----------------
        * Base score for any template email: 20
        * +10 per pain point used (max 2 → up to +20)
        * +10 per opportunity used (max 2 → up to +20)
        * +25 bonus for having company intelligence at all
        * +15 bonus for having both pain points AND opportunities
        * Max score is capped at 100.0
        """
        score: float = 20.0

        # Pain point contribution (cap at 2)
        score += min(pain_points_used, 2) * 10.0

        # Opportunity contribution (cap at 2)
        score += min(opportunities_used, 2) * 10.0

        # Company intelligence bonus
        if has_company_intel:
            score += 25.0

        # Combined intel bonus
        if pain_points_used > 0 and opportunities_used > 0:
            score += 15.0

        return min(score, 100.0)
