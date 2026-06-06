"""
Report Generator for VAIBHAV GROWTH ENGINE.
Exports campaign data to CSV and JSON formats.

Author: Vaibhav Sonava
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from loguru import logger

from src.analytics.metrics import AnalyticsEngine
from src.crm.crm_manager import CRMManager
from src.models.campaign import Campaign


class ReportGenerator:
    """Generate and export campaign reports in CSV and JSON formats."""

    def __init__(self) -> None:
        self.crm = CRMManager()
        self.analytics = AnalyticsEngine()

    def export_campaign_csv(self, campaign: Campaign, output_dir: str = "data") -> str:
        """Export full campaign metadata to CSV."""
        Path(output_dir).mkdir(exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = str(Path(output_dir) / f"campaign_{campaign.target_domain}_{ts}.csv")
        rows = [{
            "id": campaign.id,
            "name": campaign.name,
            "target_domain": campaign.target_domain,
            "status": str(campaign.status.value if hasattr(campaign.status, "value") else campaign.status),
            "companies_found": campaign.companies_found,
            "contacts_found": campaign.contacts_found,
            "emails_found": campaign.emails_found,
            "emails_sent": campaign.emails_sent,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else "",
        }]
        self._write_csv(filepath, rows, list(rows[0].keys()))
        logger.info(f"Campaign CSV exported: {filepath}")
        return filepath

    def export_leads_csv(self, campaign: Campaign, output_dir: str = "data") -> str:
        """Export all email drafts (leads) to CSV."""
        Path(output_dir).mkdir(exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = str(Path(output_dir) / f"leads_{campaign.target_domain}_{ts}.csv")
        columns = ["contact_name", "contact_title", "contact_email", "company_name",
                   "company_domain", "subject", "personalization_score", "ai_provider"]
        rows = []
        for draft in campaign.email_drafts:
            rows.append({
                "contact_name": draft.contact.full_name,
                "contact_title": draft.contact.title or "",
                "contact_email": draft.contact.email or "",
                "company_name": draft.contact.company_name,
                "company_domain": draft.contact.company_domain,
                "subject": draft.subject,
                "personalization_score": draft.personalization_score,
                "ai_provider": draft.ai_provider_used,
            })
        self._write_csv(filepath, rows, columns)
        logger.info(f"Leads CSV exported: {filepath} ({len(rows)} leads)")
        return filepath

    def export_campaign_json(self, campaign: Campaign, output_dir: str = "data") -> str:
        """Export full campaign as JSON."""
        Path(output_dir).mkdir(exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = str(Path(output_dir) / f"campaign_{campaign.target_domain}_{ts}.json")
        data = {
            "id": campaign.id,
            "name": campaign.name,
            "target_domain": campaign.target_domain,
            "status": str(campaign.status.value if hasattr(campaign.status, "value") else campaign.status),
            "companies_found": campaign.companies_found,
            "contacts_found": campaign.contacts_found,
            "emails_found": campaign.emails_found,
            "emails_sent": campaign.emails_sent,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else "",
            "email_drafts": [
                {
                    "contact": draft.contact.full_name,
                    "email": draft.contact.email or "",
                    "company": draft.contact.company_name,
                    "subject": draft.subject,
                    "body": draft.body[:300] + "..." if len(draft.body) > 300 else draft.body,
                    "ai_provider": draft.ai_provider_used,
                    "personalization_score": draft.personalization_score,
                }
                for draft in campaign.email_drafts
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Campaign JSON exported: {filepath}")
        return filepath

    def generate_campaign_report(self, campaign: Campaign) -> str:
        """Return a formatted text report for display."""
        lines = [
            "=" * 55,
            "  VAIBHAV GROWTH ENGINE — Campaign Report",
            "=" * 55,
            f"  Campaign   : {campaign.name}",
            f"  Domain     : {campaign.target_domain}",
            f"  Status     : {campaign.status}",
            "-" * 55,
            f"  Companies  : {campaign.companies_found}",
            f"  Contacts   : {campaign.contacts_found}",
            f"  Emails     : {campaign.emails_found}",
            f"  Sent       : {campaign.emails_sent}",
            "-" * 55,
            f"  Drafts     : {len(campaign.email_drafts)}",
            "=" * 55,
        ]
        return "\n".join(lines)

    def export_all_reports(self, campaign: Campaign, output_dir: str = "data") -> Dict[str, str]:
        """Export CSV, JSON, and text report. Return filepaths."""
        return {
            "campaign_csv": self.export_campaign_csv(campaign, output_dir),
            "leads_csv": self.export_leads_csv(campaign, output_dir),
            "json": self.export_campaign_json(campaign, output_dir),
            "report": self.generate_campaign_report(campaign),
        }

    def _write_csv(self, filepath: str, rows: List[Dict], columns: List[str]) -> None:
        """Write rows to CSV."""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            logger.error(f"CSV write failed: {e}")
