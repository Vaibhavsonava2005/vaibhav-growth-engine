"""Tests for AI personalization agents."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.agents.template_agent import TemplateAgent
from src.agents.ai_router import AIRouter


class TestTemplateAgent:
    def test_generate_email_with_intelligence(self, sample_contact, sample_intelligence):
        agent = TemplateAgent()
        result = agent.generate_email(sample_contact, sample_intelligence, "AI Solutions")
        assert "subject" in result
        assert "body" in result
        assert len(result["subject"]) > 0
        assert len(result["body"]) > 50

    def test_generate_email_without_intelligence(self, sample_contact):
        agent = TemplateAgent()
        result = agent.generate_email(sample_contact, None, "AI Solutions")
        assert "subject" in result
        assert "body" in result
        assert len(result["body"]) > 0

    def test_follow_ups_generated(self, sample_contact, sample_intelligence):
        agent = TemplateAgent()
        result = agent.generate_email(sample_contact, sample_intelligence, "AI Solutions")
        assert "follow_ups" in result
        assert len(result["follow_ups"]) >= 2

    def test_personalization_score_with_intel(self, sample_contact, sample_intelligence):
        agent = TemplateAgent()
        result = agent.generate_email(sample_contact, sample_intelligence, "AI Solutions")
        assert result["personalization_score"] > 20  # Should be higher than base

    def test_personalization_score_without_intel(self, sample_contact):
        agent = TemplateAgent()
        result = agent.generate_email(sample_contact, None, "AI Solutions")
        assert 0 <= result["personalization_score"] <= 100

    def test_calculate_score_max(self):
        agent = TemplateAgent()
        score = agent.calculate_personalization_score(5, 5, True)
        assert score <= 100.0

    def test_calculate_score_min(self):
        agent = TemplateAgent()
        score = agent.calculate_personalization_score(0, 0, False)
        assert score >= 0.0


class TestAIRouter:
    def test_get_status_returns_dict(self):
        router = AIRouter()
        status = router.get_status()
        assert "gemini" in status
        assert "groq" in status
        assert "openrouter" in status
        assert "template" in status
        assert status["template"] is True

    def test_falls_back_to_template_when_no_keys(self, sample_contact, sample_intelligence):
        router = AIRouter()
        # With no API keys configured, should fall back to template
        result = router.generate_email(sample_contact, sample_intelligence, "AI Solutions")
        assert result is not None
        assert "subject" in result
        assert "body" in result

    def test_generate_email_never_raises(self, sample_contact):
        router = AIRouter()
        # Should never raise, always return a dict
        result = router.generate_email(sample_contact, None, "Test Product")
        assert isinstance(result, dict)

    def test_analyze_company_returns_dict(self):
        router = AIRouter()
        result = router.analyze_company("Acme Corp", {"homepage": "We build software."})
        assert isinstance(result, dict)
        assert "pain_points" in result or "opportunities" in result
