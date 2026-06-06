"""
Campaign data models for VAIBHAV GROWTH ENGINE.

Defines email draft, campaign lifecycle, and campaign result
entities used to orchestrate outbound email sequences.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .company import CompanyIntelligence
from .contact import Contact


class EmailDraft(BaseModel):
    """
    A personalised outbound email draft generated for a specific contact.

    Attributes:
        contact:               The target contact this email is addressed to.
        company_intelligence:  Optional enriched company context used during
                               AI personalisation.
        subject:               Email subject line.
        body:                  Full HTML or plain-text email body.
        preview_text:          Optional email preview / pre-header text.
        ai_provider_used:      Identifier of the LLM or template engine that
                               generated this draft (e.g. ``openai``, ``gemini``,
                               ``template``).
        personalization_score: Quality score measuring how personalised the
                               email is (0 – 100).
        follow_up_sequence:    Ordered list of follow-up email body strings to
                               be sent if the initial email goes unanswered.
        created_at:            UTC timestamp when the draft was generated.
    """

    model_config = {"populate_by_name": True}

    contact: Contact = Field(..., description="Target contact for this email draft")
    company_intelligence: Optional[CompanyIntelligence] = Field(
        default=None,
        description="Enriched company context used during AI personalisation",
    )
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Full email body (HTML or plain text)")
    preview_text: Optional[str] = Field(
        default=None, description="Email preview / pre-header text"
    )
    ai_provider_used: str = Field(
        default="template",
        description="LLM or template engine that generated this draft",
    )
    personalization_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Personalisation quality score (0–100)",
    )
    follow_up_sequence: List[str] = Field(
        default_factory=list,
        description="Ordered follow-up email body strings",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the draft was generated",
    )


class CampaignStatus(str, Enum):
    """Lifecycle state of an outbound email campaign."""

    DRAFT = "draft"
    APPROVED = "approved"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    COMPLETED = "completed"


class Campaign(BaseModel):
    """
    Top-level campaign entity that tracks the full outbound pipeline run.

    A campaign targets a single domain (the seed competitor / partner) and
    accumulates all discovered companies, contacts, email drafts, and send
    metrics associated with that prospecting run.

    Attributes:
        id:               UUID assigned at creation time.
        name:             Human-readable campaign label.
        target_domain:    Seed domain used to find look-alike companies.
        status:           Current lifecycle state of the campaign.
        companies_found:  Total companies discovered in the ICP search.
        contacts_found:   Total contacts discovered across all companies.
        emails_found:     Contacts for whom a valid email was located.
        emails_sent:      Emails successfully dispatched via Brevo.
        emails_opened:    Unique email opens tracked.
        emails_clicked:   Unique link clicks tracked.
        emails_replied:   Replies received (manual or webhook-tracked).
        email_drafts:     All generated :class:`EmailDraft` objects.
        created_at:       UTC timestamp when the campaign was created.
        sent_at:          UTC timestamp when bulk-sending began.
        completed_at:     UTC timestamp when the campaign finished.
    """

    model_config = {"populate_by_name": True}

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID assigned at campaign creation",
    )
    name: str = Field(..., description="Human-readable campaign label")
    target_domain: str = Field(
        ..., description="Seed domain used for look-alike prospecting"
    )
    status: CampaignStatus = Field(
        default=CampaignStatus.DRAFT, description="Current lifecycle state"
    )
    companies_found: int = Field(
        default=0, ge=0, description="Total companies discovered"
    )
    contacts_found: int = Field(
        default=0, ge=0, description="Total contacts discovered"
    )
    emails_found: int = Field(
        default=0, ge=0, description="Contacts with a located email address"
    )
    emails_sent: int = Field(
        default=0, ge=0, description="Emails dispatched via Brevo"
    )
    emails_opened: int = Field(
        default=0, ge=0, description="Unique email opens tracked"
    )
    emails_clicked: int = Field(
        default=0, ge=0, description="Unique link clicks tracked"
    )
    emails_replied: int = Field(
        default=0, ge=0, description="Replies received"
    )
    email_drafts: List[EmailDraft] = Field(
        default_factory=list, description="Generated EmailDraft objects"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the campaign was created",
    )
    sent_at: Optional[datetime] = Field(
        default=None, description="UTC timestamp when bulk-sending began"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="UTC timestamp when the campaign finished"
    )


class CampaignResult(BaseModel):
    """
    Summary result returned after a campaign send attempt.

    Attributes:
        campaign:           The :class:`Campaign` that was executed.
        success:            Whether the overall send operation succeeded.
        message:            Human-readable status or error summary.
        brevo_message_ids:  Brevo message IDs for successfully dispatched emails.
        errors:             List of per-contact or system error messages.
    """

    model_config = {"populate_by_name": True}

    campaign: Campaign = Field(..., description="The campaign that was executed")
    success: bool = Field(..., description="Whether the send operation succeeded")
    message: str = Field(..., description="Human-readable status or error summary")
    brevo_message_ids: List[str] = Field(
        default_factory=list,
        description="Brevo message IDs for successfully dispatched emails",
    )
    errors: List[str] = Field(
        default_factory=list, description="Per-contact or system error messages"
    )
