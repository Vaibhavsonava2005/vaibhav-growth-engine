"""
Public API of the ``models`` package for VAIBHAV GROWTH ENGINE.

Import every model from this package to keep consumer imports clean::

    from src.models import Company, Contact, Campaign, ProspectScore
"""

from .campaign import Campaign, CampaignResult, CampaignStatus, EmailDraft
from .company import Company, CompanyIntelligence, CompanySize
from .contact import Contact, EmailEnrichment
from .prospect import ProspectScore

__all__: list[str] = [
    # campaign
    "Campaign",
    "CampaignResult",
    "CampaignStatus",
    "EmailDraft",
    # company
    "Company",
    "CompanyIntelligence",
    "CompanySize",
    # contact
    "Contact",
    "EmailEnrichment",
    # prospect
    "ProspectScore",
]
