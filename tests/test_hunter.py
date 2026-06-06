"""Tests for HunterService (email enrichment)."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
import responses as responses_lib

from src.services.hunter import HunterService


class TestHunterService:
    def test_is_configured_with_key(self):
        with patch("src.services.hunter.settings") as m:
            m.HUNTER_API_KEY = "test_key_abcdefghij"
            m.REQUEST_TIMEOUT = 30
            svc = HunterService()
            assert svc.is_configured() is True

    def test_is_configured_without_key(self):
        with patch("src.services.hunter.settings") as m:
            m.HUNTER_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = HunterService()
            assert svc.is_configured() is False

    def test_find_email_not_configured(self):
        with patch("src.services.hunter.settings") as m:
            m.HUNTER_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = HunterService()
            result = svc.find_email("John", "Doe", "acme.com")
            assert result is None

    def test_verify_email_not_configured(self):
        with patch("src.services.hunter.settings") as m:
            m.HUNTER_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = HunterService()
            result = svc.verify_email("john@acme.com")
            assert result is None

    def test_domain_search_not_configured(self):
        with patch("src.services.hunter.settings") as m:
            m.HUNTER_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = HunterService()
            result = svc.domain_search("acme.com")
            assert result == []

    def test_find_email_success(self, mock_hunter_response):
        """Mock the HTTP layer to simulate a successful Hunter email find."""
        with patch("src.services.hunter.settings") as m:
            m.HUNTER_API_KEY = "test_key_abcdefghij"
            m.REQUEST_TIMEOUT = 30
            svc = HunterService()
            # Mock the internal _make_request method directly
            svc._make_request = lambda endpoint, params: mock_hunter_response["data"]
            result = svc.find_email("John", "Doe", "acme.com")
            assert result is not None
            assert result.email == "john@acme.com"
            assert result.confidence_score > 0
