"""Tests for ProspeoService."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


class TestProspeoService:
    def test_is_configured_with_key(self):
        with patch("src.services.prospeo.settings") as m:
            m.PROSPEO_API_KEY = "test_key_abcdefghij"
            m.REQUEST_TIMEOUT = 30
            from src.services.prospeo import ProspeoService
            svc = ProspeoService()
            assert svc.is_configured() is True

    def test_is_configured_without_key(self):
        with patch("src.services.prospeo.settings") as m:
            m.PROSPEO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            from src.services.prospeo import ProspeoService
            svc = ProspeoService()
            assert svc.is_configured() is False

    def test_enrich_person_not_configured(self):
        with patch("src.services.prospeo.settings") as m:
            m.PROSPEO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            from src.services.prospeo import ProspeoService
            svc = ProspeoService()
            result = svc.enrich_person("John", "Doe", "acme.com")
            assert result is None

    def test_search_people_not_configured(self):
        with patch("src.services.prospeo.settings") as m:
            m.PROSPEO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            from src.services.prospeo import ProspeoService
            svc = ProspeoService()
            result = svc.search_people("CEO", "acme.com")
            assert result == []

    def test_get_account_info_not_configured(self):
        with patch("src.services.prospeo.settings") as m:
            m.PROSPEO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            from src.services.prospeo import ProspeoService
            svc = ProspeoService()
            result = svc.get_account_info()
            assert result == {}
