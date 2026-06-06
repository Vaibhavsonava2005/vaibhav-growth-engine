"""
Contact data models for VAIBHAV GROWTH ENGINE.

Defines individual prospect contacts and the enriched email
verification record attached to each contact.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Contact(BaseModel):
    """
    A prospected individual at a target company.

    Attributes:
        id:                 Optional external / database identifier.
        first_name:         Given name of the contact.
        last_name:          Family name of the contact.
        full_name:          Concatenated display name.
        title:              Job title (e.g. ``Head of Engineering``).
        seniority:          Seniority bucket (e.g. ``director``, ``vp``, ``c_suite``).
        department:         Functional department (e.g. ``engineering``, ``marketing``).
        company_name:       Name of the employer company.
        company_domain:     Primary domain of the employer company.
        linkedin_url:       LinkedIn profile URL.
        email:              Best-guess or verified email address.
        email_confidence:   Provider confidence score for the email (0.0 – 1.0).
        email_verified:     Whether the email has passed verification.
        phone:              Direct or mobile phone number.
        location:           City / country of the contact.
        source:             Data provider that returned this record.
        discovered_at:      UTC timestamp when this record was created.
    """

    model_config = {"populate_by_name": True}

    id: Optional[str] = Field(default=None, description="External or DB identifier")
    first_name: str = Field(..., description="Given name of the contact")
    last_name: str = Field(..., description="Family name of the contact")
    full_name: str = Field(..., description="Concatenated display name")
    title: Optional[str] = Field(
        default=None, description="Job title, e.g. Head of Engineering"
    )
    seniority: Optional[str] = Field(
        default=None,
        description="Seniority bucket, e.g. director / vp / c_suite",
    )
    department: Optional[str] = Field(
        default=None,
        description="Functional department, e.g. engineering / marketing",
    )
    company_name: str = Field(..., description="Name of the employer company")
    company_domain: str = Field(
        ..., description="Primary domain of the employer company"
    )
    linkedin_url: Optional[str] = Field(
        default=None, description="LinkedIn profile URL"
    )
    email: Optional[str] = Field(
        default=None, description="Best-guess or verified email address"
    )
    email_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Provider confidence score for the email (0–1)",
    )
    email_verified: bool = Field(
        default=False, description="Whether the email has passed verification"
    )
    phone: Optional[str] = Field(
        default=None, description="Direct or mobile phone number"
    )
    location: Optional[str] = Field(
        default=None, description="City / country of the contact"
    )
    source: str = Field(
        default="prospeo",
        description="Data provider that returned this record",
    )
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this record was created",
    )


class EmailEnrichment(BaseModel):
    """
    Email verification and enrichment record for a contact.

    Produced by an email verification service (e.g. Hunter.io, Prospeo)
    and attached to a contact to record the full verification audit trail.

    Attributes:
        contact_id:          ID of the parent :class:`Contact` record.
        email:               The email address that was verified.
        confidence_score:    Provider confidence score (0.0 – 1.0).
        is_verified:         Whether the provider confirmed deliverability.
        verification_status: Categorical result from the provider.
        first_name:          First name resolved from the email provider.
        last_name:           Last name resolved from the email provider.
        company_domain:      Domain the email belongs to.
        source:              Verification service used.
        enriched_at:         UTC timestamp when verification was performed.
    """

    model_config = {"populate_by_name": True}

    contact_id: Optional[str] = Field(
        default=None, description="ID of the parent Contact record"
    )
    email: str = Field(..., description="The email address that was verified")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Provider confidence score (0–1)"
    )
    is_verified: bool = Field(
        ..., description="Whether the provider confirmed deliverability"
    )
    verification_status: str = Field(
        ...,
        description=(
            "Categorical verification result: 'valid', 'risky', 'invalid', or 'unknown'"
        ),
    )
    first_name: Optional[str] = Field(
        default=None, description="First name resolved from the email provider"
    )
    last_name: Optional[str] = Field(
        default=None, description="Last name resolved from the email provider"
    )
    company_domain: str = Field(
        ..., description="Domain the verified email belongs to"
    )
    source: str = Field(
        default="hunter", description="Verification service used"
    )
    enriched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when verification was performed",
    )
