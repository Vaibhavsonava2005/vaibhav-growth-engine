"""Tests for BrevoService (email delivery)."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


class TestBrevoService:
    def test_is_configured_with_key(self):
        with patch("src.services.brevo.settings") as m:
            m.BREVO_API_KEY = "xkeysib-test_key_abcdefghij"
            m.SENDER_EMAIL = "test@example.com"
            m.SENDER_NAME = "Test User"
            from src.services.brevo import BrevoService
            svc = BrevoService()
            assert svc.is_configured() is True

    def test_is_configured_without_key(self):
        with patch("src.services.brevo.settings") as m:
            m.BREVO_API_KEY = ""
            m.SENDER_EMAIL = "test@example.com"
            m.SENDER_NAME = "Test"
            from src.services.brevo import BrevoService
            svc = BrevoService()
            assert svc.is_configured() is False

    def test_format_email_body_plain_text(self):
        with patch("src.services.brevo.settings") as m:
            m.BREVO_API_KEY = ""
            m.SENDER_EMAIL = "test@example.com"
            m.SENDER_NAME = "Test"
            from src.services.brevo import BrevoService
            svc = BrevoService()
            html = svc._format_email_body("Hello World\n\nThis is a test.")
            assert "<html" in html.lower() or "Hello World" in html

    def test_send_campaign_emails_dry_run(self, sample_campaign, sample_email_draft):
        """Dry run should not call Brevo API — just return mock result."""
        with patch("src.services.brevo.settings") as m:
            m.BREVO_API_KEY = ""
            m.SENDER_EMAIL = "test@example.com"
            m.SENDER_NAME = "Test"
            from src.services.brevo import BrevoService
            svc = BrevoService()
            result = svc.send_campaign_emails([], sample_campaign, dry_run=True)
            assert result is not None
            assert result.campaign.id == sample_campaign.id
