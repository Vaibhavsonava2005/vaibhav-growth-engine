"""
Prospect scoring model for VAIBHAV GROWTH ENGINE.

Defines the composite ProspectScore entity that aggregates contact,
company, and intelligence data with multi-dimensional scoring signals
to drive outreach prioritisation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .company import Company, CompanyIntelligence
from .contact import Contact


class ProspectScore(BaseModel):
    """
    Composite scoring record for a single contact + company pair.

    The score is assembled from four independent sub-scores and a final
    ``total_score`` that drives prioritisation (``high`` / ``medium`` /
    ``low``).  A detailed ``scoring_breakdown`` dictionary is stored for
    explainability and debugging.

    Attributes:
        contact:               The prospected contact being scored.
        company:               The company associated with the contact.
        company_intelligence:  Optional enriched company intelligence used
                               during scoring.
        total_score:           Weighted composite score (0.0 – 100.0).
        company_score:         Sub-score reflecting company fit with the ICP
                               (0.0 – 100.0).
        contact_score:         Sub-score reflecting contact seniority and
                               relevance (0.0 – 100.0).
        opportunity_score:     Sub-score derived from growth / hiring signals
                               (0.0 – 100.0).
        email_confidence_score:Sub-score reflecting the quality and confidence
                               of the located email address (0.0 – 100.0).
        scoring_breakdown:     Arbitrary key-value map of intermediate scoring
                               signals for audit and explainability.
        priority:              Final priority bucket: ``'high'``, ``'medium'``,
                               or ``'low'``.
        follow_up_suggested:   Whether automated follow-up is recommended based
                               on the composite score.
        scored_at:             UTC timestamp when scoring was performed.
    """

    model_config = {"populate_by_name": True}

    contact: Contact = Field(..., description="The prospected contact being scored")
    company: Company = Field(
        ..., description="The company associated with the contact"
    )
    company_intelligence: Optional[CompanyIntelligence] = Field(
        default=None,
        description="Enriched company intelligence used during scoring",
    )
    total_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weighted composite score (0–100)",
    )
    company_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="ICP fit sub-score for the company (0–100)",
    )
    contact_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Seniority and relevance sub-score for the contact (0–100)",
    )
    opportunity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Growth / hiring signal sub-score (0–100)",
    )
    email_confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Email address quality sub-score (0–100)",
    )
    scoring_breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="Intermediate scoring signals for audit and explainability",
    )
    priority: str = Field(
        default="medium",
        description="Priority bucket: 'high', 'medium', or 'low'",
    )
    follow_up_suggested: bool = Field(
        default=False,
        description="Whether automated follow-up is recommended",
    )
    scored_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when scoring was performed",
    )
