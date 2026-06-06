"""
Shared pytest fixtures for VAIBHAV GROWTH ENGINE test suite.
Author: Vaibhav Sonava
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from src.models.company import Company, CompanyIntelligence
from src.models.contact import Contact, EmailEnrichment
from src.models.campaign import Campaign, EmailDraft, CampaignStatus


# ---------------------------------------------------------------------------
# Company fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_company() -> Company:
    return Company(name="Acme Corp", domain="acme.com", industry="Technology", employee_count=50)


@pytest.fixture
def sample_company_large() -> Company:
    return Company(name="Mega Enterprise Ltd", domain="mega-enterprise.com", industry="Finance", employee_count=5000)


# ---------------------------------------------------------------------------
# Contact fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_contact() -> Contact:
    return Contact(
        first_name="John", last_name="Doe", full_name="John Doe",
        title="CEO", company_name="Acme Corp", company_domain="acme.com",
        email="john@acme.com", email_confidence=0.9,
    )


@pytest.fixture
def sample_contact_low_confidence() -> Contact:
    return Contact(
        first_name="Jane", last_name="Smith", full_name="Jane Smith",
        title="VP of Marketing", company_name="Acme Corp", company_domain="acme.com",
        email="jane@acme.com", email_confidence=0.35,
    )


# ---------------------------------------------------------------------------
# EmailEnrichment fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_email_enrichment() -> EmailEnrichment:
    return EmailEnrichment(
        email="john@acme.com",
        confidence_score=0.9,
        is_verified=True,
        verification_status="valid",
        first_name="John",
        last_name="Doe",
        company_domain="acme.com",
    )


# ---------------------------------------------------------------------------
# Intelligence fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_intelligence(sample_company: Company) -> CompanyIntelligence:
    return CompanyIntelligence(
        company=sample_company,
        pain_points=["No AI automation", "Manual processes"],
        opportunities=["AI Solutions", "Workflow Automation"],
        growth_signals=["Active hiring"],
        hiring_signals=["Software Engineer"],
    )


# ---------------------------------------------------------------------------
# Campaign / EmailDraft fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_email_draft(sample_contact: Contact, sample_intelligence: CompanyIntelligence) -> EmailDraft:
    return EmailDraft(
        contact=sample_contact,
        company_intelligence=sample_intelligence,
        subject="Automate Acme Corp's manual processes with AI",
        body=(
            f"Hi {sample_contact.first_name},\n\n"
            "I noticed Acme Corp is still handling a lot of workflows manually. "
            "Our AI Solutions platform cuts overhead by up to 60%.\n\n"
            "Would you be open to a 15-minute call this week?\n\nBest,\nVaibhav Sonava"
        ),
        ai_provider_used="template",
        personalization_score=65.0,
    )


@pytest.fixture
def sample_campaign() -> Campaign:
    return Campaign(
        name="Acme Corp Outreach",
        target_domain="acme.com",
        status=CampaignStatus.DRAFT,
    )


# ---------------------------------------------------------------------------
# External API mock-response fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_apollo_response() -> Dict[str, Any]:
    return {
        "organizations": [{
            "id": "123", "name": "Acme Corp", "primary_domain": "acme.com",
            "industry": "Technology", "estimated_num_employees": 50,
            "country": "United States", "city": "San Francisco",
            "linkedin_url": "https://www.linkedin.com/company/acme-corp",
            "website_url": "https://acme.com",
            "short_description": "Acme Corp builds innovative B2B SaaS tools.",
        }],
        "pagination": {"page": 1, "per_page": 25, "total_entries": 1, "total_pages": 1},
    }


@pytest.fixture
def mock_apollo_people_response() -> Dict[str, Any]:
    return {
        "people": [{
            "id": "456", "first_name": "John", "last_name": "Doe", "name": "John Doe",
            "title": "CEO", "email": "john@acme.com", "email_status": "verified",
            "organization_name": "Acme Corp",
        }],
        "pagination": {"page": 1, "per_page": 25, "total_entries": 1, "total_pages": 1},
    }


@pytest.fixture
def mock_hunter_response() -> Dict[str, Any]:
    return {
        "data": {
            "email": "john@acme.com", "score": 90, "status": "valid",
            "first_name": "John", "last_name": "Doe",
            "position": "CEO", "company": "Acme Corp", "domain": "acme.com",
        },
        "meta": {"params": {"full_name": "John Doe", "domain": "acme.com"}},
    }


@pytest.fixture
def mock_prospeo_response() -> Dict[str, Any]:
    return {
        "response": {
            "email": "john@acme.com", "email_status": "VALID",
            "confidence": 92, "first_name": "John", "last_name": "Doe",
        },
        "error": False,
        "message": "success",
    }


@pytest.fixture
def mock_brevo_send_response() -> Dict[str, Any]:
    return {"messageId": "<202601011200.abc123@smtp-relay.mailin.fr>"}


@pytest.fixture
def mock_gemini_response() -> str:
    return (
        "Hi John,\n\nI noticed Acme Corp is still handling workflows manually. "
        "Our AI Solutions platform cuts overhead by up to 60%.\n\n"
        "Would you be open to a 15-minute call?\n\nBest,\nVaibhav"
    )


# ---------------------------------------------------------------------------
# Service mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_growth_pipeline() -> MagicMock:
    pipeline = MagicMock()
    pipeline.run.return_value = Campaign(name="Test Campaign", target_domain="acme.com")
    pipeline.send_campaign.return_value = MagicMock(success=True, message="Sent")
    pipeline.get_email_drafts.return_value = []
    return pipeline


@pytest.fixture
def mock_analytics_engine() -> MagicMock:
    engine = MagicMock()
    engine.get_all_metrics.return_value = [{
        "id": "test-001", "name": "Test Campaign", "domain": "acme.com",
        "status": "sent", "emails_sent": 5, "open_rate": 40.0, "reply_rate": 5.0, "created_at": "2026-01-15",
    }]
    engine.get_aggregate_summary.return_value = {
        "campaigns": 1, "emails_sent": 5, "open_rate": 40.0, "reply_rate": 5.0,
    }
    return engine


@pytest.fixture
def mock_crm_manager() -> MagicMock:
    crm = MagicMock()
    crm.save_campaign.return_value = True
    crm.get_campaign_history.return_value = []
    crm.get_prospect_history.return_value = []
    return crm
