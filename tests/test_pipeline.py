"""Integration tests for the full pipeline."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.utils.validators import validate_domain
from src.models.campaign import Campaign, CampaignStatus
from src.crm.crm_manager import CRMManager
from src.analytics.metrics import AnalyticsEngine
from src.analytics.scorer import ProspectScorer


class TestDomainValidation:
    def test_valid_domain(self):
        assert validate_domain("hubspot.com") == "hubspot.com"

    def test_strips_http(self):
        assert validate_domain("http://hubspot.com") == "hubspot.com"

    def test_strips_https(self):
        assert validate_domain("https://hubspot.com") == "hubspot.com"

    def test_strips_www(self):
        assert validate_domain("www.hubspot.com") == "hubspot.com"

    def test_strips_all(self):
        assert validate_domain("https://www.hubspot.com/path") == "hubspot.com"

    def test_invalid_domain_raises(self):
        with pytest.raises((ValueError, Exception)):
            validate_domain("not_a_domain")


class TestCampaignCreation:
    def test_campaign_has_id(self, sample_campaign):
        assert len(sample_campaign.id) > 0

    def test_campaign_default_status(self, sample_campaign):
        assert sample_campaign.status == CampaignStatus.DRAFT

    def test_campaign_counters_default_zero(self, sample_campaign):
        assert sample_campaign.companies_found == 0
        assert sample_campaign.contacts_found == 0


class TestCRMManager:
    def test_save_and_retrieve_campaign(self, sample_campaign, tmp_path, monkeypatch):
        """CRM saves and retrieves campaign correctly."""
        monkeypatch.setattr("src.crm.crm_manager.DATA_DIR", tmp_path)
        monkeypatch.setattr("src.crm.crm_manager.CAMPAIGN_HISTORY_FILE", tmp_path / "campaigns.csv")
        monkeypatch.setattr("src.crm.crm_manager.PROSPECT_HISTORY_FILE", tmp_path / "prospects.csv")
        crm = CRMManager()
        crm.save_campaign(sample_campaign)
        history = crm.get_campaign_history()
        assert len(history) >= 1
        ids = [r["id"] for r in history]
        assert sample_campaign.id in ids

    def test_save_and_retrieve_prospect(self, sample_contact, sample_campaign, tmp_path, monkeypatch):
        monkeypatch.setattr("src.crm.crm_manager.DATA_DIR", tmp_path)
        monkeypatch.setattr("src.crm.crm_manager.CAMPAIGN_HISTORY_FILE", tmp_path / "campaigns.csv")
        monkeypatch.setattr("src.crm.crm_manager.PROSPECT_HISTORY_FILE", tmp_path / "prospects.csv")
        crm = CRMManager()
        crm.save_prospect(sample_contact, sample_campaign.id)
        prospects = crm.get_prospect_history()
        assert len(prospects) >= 1


class TestProspectScorer:
    def test_score_returns_prosect_score(self, sample_contact, sample_company):
        scorer = ProspectScorer()
        score = scorer.score_prospect(sample_contact, sample_company)
        assert 0 <= score.total_score <= 100

    def test_high_priority_ceo(self, sample_contact, sample_company):
        sample_contact.title = "CEO"
        scorer = ProspectScorer()
        score = scorer.score_prospect(sample_contact, sample_company)
        assert score.contact_score >= 28

    def test_priority_assignment(self, sample_contact, sample_company):
        scorer = ProspectScorer()
        score = scorer.score_prospect(sample_contact, sample_company)
        assert score.priority in ("high", "medium", "low")

    def test_analytics_empty_state(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.crm.crm_manager.DATA_DIR", tmp_path)
        monkeypatch.setattr("src.crm.crm_manager.CAMPAIGN_HISTORY_FILE", tmp_path / "c.csv")
        monkeypatch.setattr("src.crm.crm_manager.PROSPECT_HISTORY_FILE", tmp_path / "p.csv")
        analytics = AnalyticsEngine()
        metrics = analytics.get_overall_metrics()
        assert metrics["emails_sent"] == 0
        assert metrics["open_rate"] == 0.0
