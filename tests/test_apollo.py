"""Tests for ApolloService."""
from __future__ import annotations

import pytest
import responses as responses_lib
from unittest.mock import MagicMock, patch

from src.services.apollo import ApolloService


class TestApolloService:
    def test_is_configured_with_key(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = "test_key_abcdefghij"
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            assert svc.is_configured() is True

    def test_is_configured_without_key(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            assert svc.is_configured() is False

    def test_is_configured_short_key(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = "short"
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            assert svc.is_configured() is False

    def test_search_companies_not_configured_returns_empty(self, sample_company):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            result = svc.search_companies(domain="acme.com")
            assert result == []

    def test_search_people_not_configured_returns_empty(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            result = svc.search_people(company_domain="acme.com")
            assert result == []

    def test_enrich_company_not_configured_returns_none(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = ""
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            result = svc.enrich_company("acme.com")
            assert result is None

    def test_map_company_full_data(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = "test_key_abcdefghij"
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            org = {
                "id": "abc123", "name": "Acme Corp",
                "primary_domain": "acme.com", "website_url": "https://acme.com",
                "industry": "Technology", "estimated_num_employees": 150,
                "linkedin_url": "https://linkedin.com/company/acme",
                "short_description": "A test company",
                "city": "San Francisco", "state": "CA", "country": "USA",
            }
            company = svc._map_company(org)
            assert company.name == "Acme Corp"
            assert company.domain == "acme.com"
            assert company.industry == "Technology"
            assert company.employee_count == 150

    def test_map_company_missing_fields(self):
        with patch("src.services.apollo.settings") as m:
            m.APOLLO_API_KEY = "test_key_abcdefghij"
            m.REQUEST_TIMEOUT = 30
            svc = ApolloService()
            org = {"name": "Minimal Corp", "primary_domain": "minimal.com"}
            company = svc._map_company(org)
            assert company.name == "Minimal Corp"
            assert company.domain == "minimal.com"
            assert company.industry is None
