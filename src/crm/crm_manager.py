"""
CRM Manager — CSV-based CRM layer for VAIBHAV GROWTH ENGINE.
Tracks campaigns, prospects, and engagement history.

Author: Vaibhav Sonava
"""
from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from src.models.campaign import Campaign
from src.models.contact import Contact

DATA_DIR = Path("data")
CAMPAIGN_HISTORY_FILE = DATA_DIR / "campaign_history.csv"
PROSPECT_HISTORY_FILE = DATA_DIR / "prospect_history.csv"


class CRMManager:
    """CSV-based CRM for tracking campaigns and prospect engagement."""

    CAMPAIGN_COLUMNS = [
        "id", "name", "target_domain", "status",
        "companies_found", "contacts_found", "emails_found",
        "emails_sent", "emails_opened", "emails_clicked", "emails_replied",
        "created_at", "sent_at",
    ]
    PROSPECT_COLUMNS = [
        "contact_email", "contact_name", "contact_title",
        "company_name", "company_domain", "campaign_id",
        "status", "sent_at", "opened_at", "replied_at", "notes",
    ]

    def __init__(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        self._init_files()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def save_campaign(self, campaign: Campaign) -> bool:
        """Append or upsert a campaign record in campaign_history.csv."""
        try:
            rows = self._read_csv(CAMPAIGN_HISTORY_FILE)
            # Remove existing entry for this campaign (upsert)
            rows = [r for r in rows if r.get("id") != campaign.id]
            rows.append({
                "id": campaign.id,
                "name": campaign.name,
                "target_domain": campaign.target_domain,
                "status": campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status),
                "companies_found": campaign.companies_found,
                "contacts_found": campaign.contacts_found,
                "emails_found": campaign.emails_found,
                "emails_sent": campaign.emails_sent,
                "emails_opened": campaign.emails_opened,
                "emails_clicked": campaign.emails_clicked,
                "emails_replied": campaign.emails_replied,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else "",
                "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else "",
            })
            self._write_csv(CAMPAIGN_HISTORY_FILE, rows, self.CAMPAIGN_COLUMNS)
            logger.info(f"Campaign saved to CRM: {campaign.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save campaign to CRM: {e}")
            return False

    def save_prospect(self, contact: Contact, campaign_id: str, status: str = "sent") -> bool:
        """Append a prospect record to prospect_history.csv."""
        try:
            rows = self._read_csv(PROSPECT_HISTORY_FILE)
            rows.append({
                "contact_email": contact.email or "",
                "contact_name": contact.full_name,
                "contact_title": contact.title or "",
                "company_name": contact.company_name,
                "company_domain": contact.company_domain,
                "campaign_id": campaign_id,
                "status": status,
                "sent_at": datetime.utcnow().isoformat(),
                "opened_at": "",
                "replied_at": "",
                "notes": "",
            })
            self._write_csv(PROSPECT_HISTORY_FILE, rows, self.PROSPECT_COLUMNS)
            return True
        except Exception as e:
            logger.error(f"Failed to save prospect: {e}")
            return False

    def get_campaign_history(self) -> List[Dict]:
        """Return all campaign records."""
        return self._read_csv(CAMPAIGN_HISTORY_FILE)

    def get_prospect_history(self, campaign_id: Optional[str] = None) -> List[Dict]:
        """Return prospect records, optionally filtered by campaign."""
        rows = self._read_csv(PROSPECT_HISTORY_FILE)
        if campaign_id:
            rows = [r for r in rows if r.get("campaign_id") == campaign_id]
        return rows

    def update_prospect_status(self, email: str, status: str, notes: str = "") -> bool:
        """Update the status of a prospect (opened, replied, converted, etc.)."""
        try:
            rows = self._read_csv(PROSPECT_HISTORY_FILE)
            updated = False
            ts = datetime.utcnow().isoformat()
            for row in rows:
                if row.get("contact_email", "").lower() == email.lower():
                    row["status"] = status
                    if status == "opened" and not row.get("opened_at"):
                        row["opened_at"] = ts
                    if status in ("replied", "interested", "converted") and not row.get("replied_at"):
                        row["replied_at"] = ts
                    if notes:
                        row["notes"] = notes
                    updated = True
            if updated:
                self._write_csv(PROSPECT_HISTORY_FILE, rows, self.PROSPECT_COLUMNS)
                logger.info(f"Updated prospect status: {email} → {status}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update prospect status: {e}")
            return False

    def get_stats(self) -> Dict:
        """Return aggregate stats across all campaigns."""
        campaigns = self.get_campaign_history()
        prospects = self.get_prospect_history()
        total_sent = sum(int(c.get("emails_sent", 0)) for c in campaigns)
        total_opened = sum(int(c.get("emails_opened", 0)) for c in campaigns)
        total_replied = sum(int(c.get("emails_replied", 0)) for c in campaigns)
        return {
            "total_campaigns": len(campaigns),
            "total_prospects": len(prospects),
            "total_emails_sent": total_sent,
            "total_emails_opened": total_opened,
            "total_emails_replied": total_replied,
            "open_rate": round((total_opened / total_sent * 100) if total_sent else 0, 1),
            "reply_rate": round((total_replied / total_sent * 100) if total_sent else 0, 1),
        }

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _init_files(self) -> None:
        """Create CSV files with headers if they don't exist."""
        for filepath, columns in [
            (CAMPAIGN_HISTORY_FILE, self.CAMPAIGN_COLUMNS),
            (PROSPECT_HISTORY_FILE, self.PROSPECT_COLUMNS),
        ]:
            if not filepath.exists():
                self._write_csv(filepath, [], columns)

    def _read_csv(self, filepath: Path) -> List[Dict]:
        """Read a CSV file and return list of dicts."""
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return []

    def _write_csv(self, filepath: Path, rows: List[Dict], columns: List[str]) -> None:
        """Write rows to a CSV file."""
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
