"""
ai_router.py
------------
Master AI Router with automatic provider failover for VAIBHAV GROWTH ENGINE.

Priority order for email generation:
    Gemini 2.5 Flash → Groq Llama 3.3 70B → OpenRouter Mistral 7B → Template

The router also provides keyword-based company intelligence extraction as a
fallback when no AI provider is available for :meth:`analyze_company`.
"""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger

from src.agents.gemini_agent import GeminiAgent
from src.agents.groq_agent import GroqAgent
from src.agents.openrouter_agent import OpenRouterAgent
from src.agents.template_agent import TemplateAgent
from src.config.constants import OPPORTUNITY_KEYWORDS, PAIN_POINTS_KEYWORDS
from src.models.company import CompanyIntelligence
from src.models.contact import Contact


class AIRouter:
    """
    Orchestrates AI providers with automatic failover and tracking.

    Tries AI providers in priority order: Gemini → Groq → OpenRouter →
    TemplateAgent.  Automatically falls back when a provider is unconfigured,
    raises an exception, or returns ``None`` (e.g. parse failure).

    Attributes
    ----------
    last_used_provider:
        Name of the provider that successfully handled the most recent
        ``generate_email`` call.
    """

    def __init__(self) -> None:
        self.gemini = GeminiAgent()
        self.groq = GroqAgent()
        self.openrouter = OpenRouterAgent()
        self.template = TemplateAgent()

        # Ordered list of (agent_instance, provider_name) tuples
        self.providers: list[tuple] = [
            (self.gemini, "gemini"),
            (self.groq, "groq"),
            (self.openrouter, "openrouter"),
        ]

        self.last_used_provider: str = "template"

        configured = [name for _, name in self.providers if _.is_configured()]
        logger.info(
            "AIRouter initialised — configured AI providers: {} | fallback: template",
            configured if configured else "none",
        )

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
        Generate a personalised cold email using the best available provider.

        Iterates through configured AI providers in priority order.  On the
        first successful result the result dict is augmented with an
        ``ai_provider`` key and returned.  If every AI provider fails or is
        unconfigured, the :class:`TemplateAgent` is used as a guaranteed
        fallback.

        Parameters
        ----------
        contact:
            Target contact record.
        intelligence:
            Enriched company intelligence (may be ``None``).
        sender_product:
            Product / service name to reference in the email.

        Returns
        -------
        dict
            Keys: ``subject``, ``body``, ``preview_text``,
            ``personalization_score``, ``follow_ups``, ``ai_provider``.
            Never raises — always returns a valid dict.
        """
        # ── Try each AI provider in priority order ─────────────────────
        for agent, provider_name in self.providers:
            if not agent.is_configured():
                logger.debug(
                    "AIRouter: {} not configured, skipping", provider_name
                )
                continue

            try:
                logger.info(
                    "AIRouter: attempting email generation via {}", provider_name
                )
                result: Optional[dict] = agent.generate_email(
                    contact, intelligence, sender_product
                )

                if result and result.get("subject") and result.get("body"):
                    result["ai_provider"] = provider_name
                    self.last_used_provider = provider_name
                    logger.info(
                        "AIRouter: email generated via {} for {}",
                        provider_name,
                        contact.full_name,
                    )
                    return result

                logger.warning(
                    "AIRouter: {} returned empty result, trying next provider",
                    provider_name,
                )

            except Exception as exc:
                logger.warning(
                    "AIRouter: {} raised exception '{}', trying next provider",
                    provider_name,
                    exc,
                )
                continue

        # ── Guaranteed fallback: TemplateAgent ─────────────────────────
        logger.info(
            "AIRouter: all AI providers exhausted — using TemplateAgent for {}",
            contact.full_name,
        )
        result = self.template.generate_email(contact, intelligence, sender_product)
        result["ai_provider"] = "template"
        self.last_used_provider = "template"
        return result

    def analyze_company(
        self, company_name: str, scrape_data: dict
    ) -> dict:
        """
        Extract structured intelligence from scraped website content.

        Tries AI providers in priority order.  Falls back to a deterministic
        keyword-extraction algorithm when no AI provider is available.

        Parameters
        ----------
        company_name:
            Human-readable company name.
        scrape_data:
            Dict with optional keys: ``homepage_text``, ``about_text``,
            ``services_text``, ``careers_text``.

        Returns
        -------
        dict
            Keys: ``pain_points``, ``opportunities``, ``hiring_signals``,
            ``growth_signals`` — each a ``list[str]``.
            Never raises — always returns a valid dict.
        """
        for agent, provider_name in self.providers:
            if not agent.is_configured():
                continue

            try:
                logger.info(
                    "AIRouter: attempting company analysis via {}", provider_name
                )
                result = agent.analyze_company(company_name, scrape_data)

                if result and any(result.values()):
                    logger.info(
                        "AIRouter: company analysis completed via {} for '{}'",
                        provider_name,
                        company_name,
                    )
                    return result

                logger.warning(
                    "AIRouter: {} returned empty analysis for '{}', trying next",
                    provider_name,
                    company_name,
                )

            except Exception as exc:
                logger.warning(
                    "AIRouter: {} raised exception during analysis of '{}' — {}",
                    provider_name,
                    company_name,
                    exc,
                )
                continue

        # ── Keyword-based fallback analysis ────────────────────────────
        logger.info(
            "AIRouter: using keyword-based analysis fallback for '{}'", company_name
        )
        return self._keyword_analyze(scrape_data)

    def get_status(self) -> dict:
        """
        Return the configuration status of all providers.

        Returns
        -------
        dict
            Keys: ``gemini``, ``groq``, ``openrouter``, ``template``,
            ``last_used`` — values are ``bool`` (or provider name string
            for ``last_used``).
        """
        status = {
            "gemini": self.gemini.is_configured(),
            "groq": self.groq.is_configured(),
            "openrouter": self.openrouter.is_configured(),
            "template": True,
            "last_used": self.last_used_provider,
        }
        logger.debug("AIRouter status: {}", status)
        return status

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _keyword_analyze(self, scrape_data: dict) -> dict:
        """
        Deterministic keyword-based intelligence extraction fallback.

        Scans all scraped text against ``PAIN_POINTS_KEYWORDS`` and
        ``OPPORTUNITY_KEYWORDS`` from constants and returns matched items
        as structured intelligence.  No network calls required.

        Parameters
        ----------
        scrape_data:
            Dict with optional text fields from scraped pages.

        Returns
        -------
        dict
            Keys: ``pain_points``, ``opportunities``, ``hiring_signals``,
            ``growth_signals``.
        """
        # Combine all text into a single lowercased corpus
        all_text: str = " ".join(
            [
                scrape_data.get("homepage_text", ""),
                scrape_data.get("about_text", ""),
                scrape_data.get("services_text", ""),
                scrape_data.get("careers_text", ""),
            ]
        ).lower()

        # ── Pain points ────────────────────────────────────────────────
        pain_points: list[str] = []
        for category, keywords in PAIN_POINTS_KEYWORDS.items():
            matched_kws = [kw for kw in keywords if kw in all_text]
            if matched_kws:
                # Produce a human-readable pain point label from the category
                label = category.replace("_", " ").title()
                pain_points.append(
                    f"{label} challenges (signals: {', '.join(matched_kws[:2])})"
                )
        pain_points = pain_points[:5]

        # ── Opportunities ──────────────────────────────────────────────
        opportunities: list[str] = []
        for keyword in OPPORTUNITY_KEYWORDS:
            if keyword in all_text:
                opportunities.append(keyword.title())
        opportunities = list(dict.fromkeys(opportunities))[:5]  # deduplicate, cap

        # ── Hiring signals ─────────────────────────────────────────────
        hiring_patterns = [
            r"we(?:'re| are) hiring\s+([a-z\s]+?)(?:\.|,|$)",
            r"open(?:ing)? for\s+([a-z\s]+?)(?:\.|,|$)",
            r"join(?:ing)? us as\s+([a-z\s]+?)(?:\.|,|$)",
            r"looking for\s+(?:a\s+)?([a-z\s]+?)(?:\.|,|$)",
        ]
        hiring_signals: list[str] = []
        careers_text = scrape_data.get("careers_text", "").lower()
        for pattern in hiring_patterns:
            matches = re.findall(pattern, careers_text)
            for match in matches:
                role = match.strip().title()
                if role and len(role) > 3:
                    hiring_signals.append(role)
        hiring_signals = list(dict.fromkeys(hiring_signals))[:5]

        # ── Growth signals ─────────────────────────────────────────────
        growth_keywords = [
            "series a",
            "series b",
            "seed round",
            "recently funded",
            "expanding",
            "new market",
            "international expansion",
            "acquisition",
            "partnership",
            "product launch",
        ]
        growth_signals: list[str] = []
        for kw in growth_keywords:
            if kw in all_text:
                growth_signals.append(kw.title())
        growth_signals = list(dict.fromkeys(growth_signals))[:5]

        result = {
            "pain_points": pain_points,
            "opportunities": opportunities,
            "hiring_signals": hiring_signals,
            "growth_signals": growth_signals,
        }
        logger.debug(
            "AIRouter keyword analysis: {} pain points, {} opportunities, "
            "{} hiring signals, {} growth signals",
            len(pain_points),
            len(opportunities),
            len(hiring_signals),
            len(growth_signals),
        )
        return result
