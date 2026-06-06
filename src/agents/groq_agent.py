"""
groq_agent.py
-------------
Groq AI agent for VAIBHAV GROWTH ENGINE.

Wraps the ``groq`` Python SDK to provide email generation and company
analysis using the Llama 3.3 70B Versatile model via Groq's ultra-low-latency
inference API.  Returns ``None`` gracefully on any error so the
:class:`AIRouter` can fall through to the next provider.
"""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger

from src.config.settings import settings
from src.models.company import CompanyIntelligence
from src.models.contact import Contact
from src.prompts.outreach_prompts import (
    COMPANY_ANALYSIS_PROMPT,
    EMAIL_GENERATION_PROMPT,
    FOLLOW_UP_PROMPT,
)


class GroqAgent:
    """
    AI email and company-analysis agent backed by Groq (Llama 3.3 70B).

    The Groq client is only initialised when a valid API key is present.
    All public methods catch exceptions and return ``None`` / empty dicts
    so that callers can implement seamless fallback logic.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.GROQ_API_KEY
        self.client = None
        # llama-3.1-8b-instant is on Groq free tier with higher rate limits
        self.model: str = "llama-3.1-8b-instant"

        if self.is_configured():
            try:
                from groq import Groq  # type: ignore

                self.client = Groq(api_key=self.api_key)
                logger.debug("GroqAgent initialised with model {}", self.model)
            except Exception as exc:
                logger.warning("GroqAgent: failed to initialise client — {}", exc)
                self.client = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_email(
        self,
        contact: Contact,
        intelligence: Optional[CompanyIntelligence],
        sender_product: str = "AI Solutions",
    ) -> Optional[dict]:
        """
        Generate a personalised cold email via Groq / Llama 3.3.

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
        dict | None
            Keys: ``subject``, ``body``, ``preview_text``,
            ``personalization_score``, ``follow_ups``, ``ai_provider``.
            Returns ``None`` on any error.
        """
        if not self.is_configured() or self.client is None:
            logger.debug("GroqAgent: not configured, skipping")
            return None

        pain_points_str = (
            ", ".join(intelligence.pain_points[:3]) if intelligence else "not available"
        )
        opportunities_str = (
            ", ".join(intelligence.opportunities[:3]) if intelligence else "not available"
        )
        industry = (
            intelligence.company.industry if intelligence else "Technology"
        )
        contact_name = (
            contact.first_name
            if contact.first_name
            else contact.full_name.split()[0]
        )

        prompt = EMAIL_GENERATION_PROMPT.format(
            contact_name=contact_name,
            contact_title=contact.title or "Leader",
            company_name=contact.company_name,
            industry=industry or "Technology",
            pain_points=pain_points_str,
            opportunities=opportunities_str,
            sender_product=sender_product,
            sender_name=settings.SENDER_NAME,
            cta="Would you be open to a brief chat?",
        )

        follow_up_prompt_3d = FOLLOW_UP_PROMPT.format(
            contact_name=contact_name,
            company_name=contact.company_name,
            original_subject="[original subject]",
            days_since_first=3,
            sender_product=sender_product,
            sender_name=settings.SENDER_NAME,
            cta="Would you be open to a brief chat?",
        )
        follow_up_prompt_7d = FOLLOW_UP_PROMPT.format(
            contact_name=contact_name,
            company_name=contact.company_name,
            original_subject="[original subject]",
            days_since_first=7,
            sender_product=sender_product,
            sender_name=settings.SENDER_NAME,
            cta="Would you be open to a brief chat?",
        )

        try:
            logger.debug(
                "GroqAgent: calling {} for {}", self.model, contact.full_name
            )

            main_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert B2B sales development representative. "
                            "Follow the output format instructions precisely."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            raw_text: str = main_response.choices[0].message.content or ""
            parsed = self._parse_email_response(raw_text)

            if not parsed.get("subject") or not parsed.get("body"):
                logger.warning(
                    "GroqAgent: could not parse structured response for {}",
                    contact.full_name,
                )
                return None

            # Follow-up 1 (3 days)
            fu1_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a B2B SDR writing concise follow-up emails.",
                    },
                    {"role": "user", "content": follow_up_prompt_3d},
                ],
                temperature=0.7,
                max_tokens=512,
            )
            follow_up_1 = self._extract_body(
                fu1_response.choices[0].message.content or ""
            )

            # Follow-up 2 (7 days)
            fu2_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a B2B SDR writing concise follow-up emails.",
                    },
                    {"role": "user", "content": follow_up_prompt_7d},
                ],
                temperature=0.7,
                max_tokens=512,
            )
            follow_up_2 = self._extract_body(
                fu2_response.choices[0].message.content or ""
            )

            n_pain = len(intelligence.pain_points) if intelligence else 0
            n_opp = len(intelligence.opportunities) if intelligence else 0
            score = min(50.0 + n_pain * 8.0 + n_opp * 7.0, 100.0)

            result = {
                "subject": parsed["subject"],
                "body": parsed["body"],
                "preview_text": parsed.get("preview_text", ""),
                "personalization_score": score,
                "follow_ups": [follow_up_1, follow_up_2],
                "ai_provider": "groq",
            }
            logger.info(
                "GroqAgent: email generated for {} (score={:.1f})",
                contact.full_name,
                score,
            )
            return result

        except Exception as exc:
            logger.error(
                "GroqAgent: generate_email failed for {} — {}", contact.full_name, exc
            )
            return None

    def analyze_company(
        self, company_name: str, scrape_data: dict
    ) -> dict:
        """
        Extract structured intelligence from scraped website content via Groq.

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
        """
        empty: dict = {
            "pain_points": [],
            "opportunities": [],
            "hiring_signals": [],
            "growth_signals": [],
        }

        if not self.is_configured() or self.client is None:
            logger.debug("GroqAgent: not configured for company analysis")
            return empty

        prompt = COMPANY_ANALYSIS_PROMPT.format(
            company_name=company_name,
            industry="Technology",
            homepage_text=scrape_data.get("homepage_text", "N/A")[:3000],
            about_text=scrape_data.get("about_text", "N/A")[:2000],
            services_text=scrape_data.get("services_text", "N/A")[:2000],
            careers_text=scrape_data.get("careers_text", "N/A")[:2000],
        )

        try:
            logger.debug("GroqAgent: analysing company '{}'", company_name)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a business analyst extracting structured sales "
                            "intelligence from website content. Follow the output format "
                            "instructions precisely."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            raw_text = response.choices[0].message.content or ""
            parsed = self._parse_analysis_response(raw_text)
            logger.info(
                "GroqAgent: analysis complete for '{}' — {} pain points, {} opportunities",
                company_name,
                len(parsed["pain_points"]),
                len(parsed["opportunities"]),
            )
            return parsed

        except Exception as exc:
            logger.error(
                "GroqAgent: analyze_company failed for '{}' — {}", company_name, exc
            )
            return empty

    # ------------------------------------------------------------------
    # Private parsers
    # ------------------------------------------------------------------

    def _parse_email_response(self, text: str) -> dict:
        """
        Parse a structured LLM email response into subject / body / preview.

        Expected format produced by EMAIL_GENERATION_PROMPT::

            SUBJECT: <line>
            BODY:
            <multi-line body>
            PREVIEW: <line>
        """
        result: dict = {"subject": "", "body": "", "preview_text": ""}

        if not text:
            return result

        # Extract SUBJECT
        subject_match = re.search(r"SUBJECT:\s*(.+)", text, re.IGNORECASE)
        if subject_match:
            result["subject"] = subject_match.group(1).strip()

        # Extract PREVIEW
        preview_match = re.search(r"PREVIEW:\s*(.+)", text, re.IGNORECASE)
        if preview_match:
            result["preview_text"] = preview_match.group(1).strip()[:100]

        # Extract BODY
        body_match = re.search(
            r"BODY:\s*\n(.*?)(?=PREVIEW:|$)", text, re.IGNORECASE | re.DOTALL
        )
        if body_match:
            result["body"] = body_match.group(1).strip()
        else:
            lines = text.splitlines()
            body_lines: list[str] = []
            in_body = False
            for line in lines:
                if re.match(r"^BODY:", line, re.IGNORECASE):
                    in_body = True
                    continue
                if re.match(r"^PREVIEW:", line, re.IGNORECASE):
                    break
                if in_body:
                    body_lines.append(line)
            if body_lines:
                result["body"] = "\n".join(body_lines).strip()

        if not result["body"] and result["subject"]:
            result["body"] = text.replace(
                f"SUBJECT: {result['subject']}", ""
            ).strip()

        return result

    def _extract_body(self, text: str) -> str:
        """Extract just the body section from a follow-up LLM response."""
        body_match = re.search(
            r"BODY:\s*\n(.*)", text, re.IGNORECASE | re.DOTALL
        )
        if body_match:
            return body_match.group(1).strip()
        return text.strip()

    def _parse_analysis_response(self, text: str) -> dict:
        """
        Parse a structured company analysis LLM response into lists.

        Expected format produced by COMPANY_ANALYSIS_PROMPT::

            PAIN_POINTS:
            - item
            OPPORTUNITIES:
            - item
            HIRING_SIGNALS:
            - item
            GROWTH_SIGNALS:
            - item
        """
        sections = {
            "pain_points": "PAIN_POINTS",
            "opportunities": "OPPORTUNITIES",
            "hiring_signals": "HIRING_SIGNALS",
            "growth_signals": "GROWTH_SIGNALS",
        }
        result: dict = {k: [] for k in sections}

        for field, header in sections.items():
            pattern = rf"{header}:\s*\n(.*?)(?=\n[A-Z_]+:|$)"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                block = match.group(1)
                items = re.findall(r"[-*]\s*(.+)", block)
                result[field] = [item.strip() for item in items if item.strip()]

        return result

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return ``True`` when a usable API key is present."""
        return bool(self.api_key and len(self.api_key) > 10)

    def get_name(self) -> str:
        """Return provider identifier."""
        return "groq"
