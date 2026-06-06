"""
Company data models for VAIBHAV GROWTH ENGINE.

Defines the core Company entity and its enriched intelligence
representation used throughout the prospecting pipeline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CompanySize(str, Enum):
    """Categorical buckets for company headcount."""

    STARTUP = "startup"       # 1–10 employees
    SMALL = "small"           # 11–50 employees
    MEDIUM = "medium"         # 51–200 employees
    LARGE = "large"           # 201–1 000 employees
    ENTERPRISE = "enterprise" # 1 000+ employees


class Company(BaseModel):
    """
    Core company entity discovered during prospecting.

    Attributes:
        id:               Optional external / database identifier.
        name:             Legal or trading name of the company.
        domain:           Primary web domain (e.g. ``acme.com``).
        website:          Full URL of the company homepage.
        industry:         Industry vertical or sector label.
        employee_count:   Approximate headcount.
        company_size:     Bucketed size derived from ``employee_count``.
        linkedin_url:     LinkedIn company page URL.
        description:      Short company description / tagline.
        location:         Headquarters city / country string.
        founded_year:     Year the company was founded.
        funding_stage:    Latest funding round label (e.g. ``Series B``).
        similarity_score: Cosine or heuristic similarity to the target ICP
                          (0.0 – 1.0).
        opportunity_score:Composite opportunity score (0.0 – 1.0).
        discovered_at:    UTC timestamp when this record was created.
        source:           Data provider that returned this record.
    """

    model_config = {"populate_by_name": True}

    id: Optional[str] = Field(default=None, description="External or DB identifier")
    name: str = Field(..., description="Company trading or legal name")
    domain: str = Field(..., description="Primary web domain, e.g. acme.com")
    website: Optional[str] = Field(default=None, description="Full homepage URL")
    industry: Optional[str] = Field(default=None, description="Industry vertical")
    employee_count: Optional[int] = Field(
        default=None, ge=0, description="Approximate headcount"
    )
    company_size: Optional[CompanySize] = Field(
        default=None, description="Bucketed company size"
    )
    linkedin_url: Optional[str] = Field(
        default=None, description="LinkedIn company page URL"
    )
    description: Optional[str] = Field(
        default=None, description="Short company description or tagline"
    )
    location: Optional[str] = Field(
        default=None, description="Headquarters city / country"
    )
    founded_year: Optional[int] = Field(
        default=None, ge=1800, le=2100, description="Year the company was founded"
    )
    funding_stage: Optional[str] = Field(
        default=None, description="Latest funding round label"
    )
    similarity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="ICP similarity score (0–1)"
    )
    opportunity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Composite opportunity score (0–1)"
    )
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this record was first created",
    )
    source: str = Field(
        default="apollo", description="Data provider that returned this record"
    )


class CompanyIntelligence(BaseModel):
    """
    Enriched intelligence gathered from web research on a company.

    This model aggregates scraped website content, AI-extracted signals,
    and structured lists of technologies, pain points, and opportunities.

    Attributes:
        company:           The base company entity this intelligence belongs to.
        homepage_text:     Raw or cleaned text from the company homepage.
        about_text:        Text extracted from the About / Team page.
        services_text:     Text extracted from the Services / Products page.
        careers_text:      Text extracted from the Careers / Jobs page.
        technologies:      List of technology or tool names detected.
        pain_points:       AI-identified pain points the company likely faces.
        opportunities:     Specific engagement opportunities for outreach.
        hiring_signals:    Job titles or roles currently being hired for.
        growth_signals:    Indicators of company growth (funding, headcount, etc.).
        raw_intelligence:  Full LLM response or raw scraped dump for audit.
        researched_at:     UTC timestamp when intelligence was last gathered.
    """

    model_config = {"populate_by_name": True}

    company: Company = Field(..., description="Base company entity")
    homepage_text: Optional[str] = Field(
        default=None, description="Text from the company homepage"
    )
    about_text: Optional[str] = Field(
        default=None, description="Text from the About / Team page"
    )
    services_text: Optional[str] = Field(
        default=None, description="Text from the Services / Products page"
    )
    careers_text: Optional[str] = Field(
        default=None, description="Text from the Careers / Jobs page"
    )
    technologies: List[str] = Field(
        default_factory=list, description="Detected technology or tool names"
    )
    pain_points: List[str] = Field(
        default_factory=list, description="AI-identified pain points"
    )
    opportunities: List[str] = Field(
        default_factory=list, description="Specific outreach opportunity signals"
    )
    hiring_signals: List[str] = Field(
        default_factory=list, description="Job titles or roles being hired"
    )
    growth_signals: List[str] = Field(
        default_factory=list, description="Indicators of company growth"
    )
    raw_intelligence: Optional[str] = Field(
        default=None, description="Full LLM response or raw scraped data for audit"
    )
    researched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when intelligence was last gathered",
    )
