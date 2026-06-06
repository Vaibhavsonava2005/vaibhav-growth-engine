"""Tests for CompanyResearchEngine."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.models.company import Company, CompanyIntelligence
from src.pipeline.research_engine import CompanyResearchEngine


class TestResearchEngine:
    @pytest.fixture
    def engine(self):
        with patch("src.pipeline.research_engine.WebScraper") as mock_scraper_cls, \
             patch("src.pipeline.research_engine.AIRouter") as mock_ai_cls:
            mock_scraper = MagicMock()
            mock_scraper.scrape_company_pages.return_value = {
                "homepage": "We build enterprise software for scaling businesses. No AI tools yet.",
                "about": "Founded in 2018. Growing team.",
                "services": "Custom software development and consulting.",
                "careers": "We are hiring: Software Engineer, Product Manager, DevOps Lead.",
            }
            mock_scraper.extract_technologies.return_value = ["React", "AWS"]
            mock_scraper.extract_job_titles.return_value = ["Software Engineer", "Product Manager"]
            mock_scraper_cls.return_value = mock_scraper

            mock_ai = MagicMock()
            mock_ai.analyze_company.return_value = {
                "pain_points": ["No AI automation", "Manual reporting"],
                "opportunities": ["AI Solutions", "Workflow Automation"],
                "growth_signals": ["Active hiring"],
                "hiring_signals": ["Software Engineer"],
            }
            mock_ai_cls.return_value = mock_ai

            return CompanyResearchEngine()

    def test_research_company_returns_intelligence(self, engine, sample_company):
        intel = engine.research_company(sample_company)
        assert isinstance(intel, CompanyIntelligence)
        assert intel.company.domain == sample_company.domain

    def test_research_company_has_pain_points(self, engine, sample_company):
        intel = engine.research_company(sample_company)
        assert len(intel.pain_points) > 0

    def test_research_company_has_opportunities(self, engine, sample_company):
        intel = engine.research_company(sample_company)
        assert len(intel.opportunities) > 0

    def test_extract_pain_points_keywords_no_ai(self, engine):
        text = "We manage everything manually with Excel spreadsheets."
        pains = engine._extract_pain_points_keywords(text)
        assert isinstance(pains, list)
        assert len(pains) > 0

    def test_extract_growth_signals_hiring(self, engine):
        text = "We are hiring 50 engineers this quarter as we expand globally."
        signals = engine._extract_growth_signals(text)
        assert any("hiring" in s.lower() or "expand" in s.lower() for s in signals)

    def test_batch_research_handles_failure(self, engine, sample_company):
        engine.research_company = MagicMock(side_effect=Exception("Scrape failed"))
        results = engine.batch_research([sample_company])
        assert len(results) == 1
        assert isinstance(results[0], CompanyIntelligence)
