"""
Analytics metrics engine for VAIBHAV GROWTH ENGINE.
Computes open rates, reply rates, conversion rates across campaigns.

Author: Vaibhav Sonava
"""
from __future__ import annotations

from typing import Dict, List, Optional

from loguru import logger

from src.crm.crm_manager import CRMManager


class AnalyticsEngine:
    """Compute and surface campaign performance metrics."""

    def __init__(self) -> None:
        self.crm = CRMManager()

    def get_campaign_metrics(self, campaign_id: Optional[str] = None) -> Dict:
        """Return metrics for a specific campaign or all campaigns."""
        campaigns = self.crm.get_campaign_history()
        if campaign_id:
            campaigns = [c for c in campaigns if c.get("id") == campaign_id]

        if not campaigns:
            return self._empty_metrics()

        totals = {
            "leads_generated": 0,
            "emails_sent": 0,
            "emails_opened": 0,
            "emails_clicked": 0,
            "emails_replied": 0,
            "campaigns": len(campaigns),
        }
        for c in campaigns:
            totals["leads_generated"] += int(c.get("emails_found", 0))
            totals["emails_sent"] += int(c.get("emails_sent", 0))
            totals["emails_opened"] += int(c.get("emails_opened", 0))
            totals["emails_clicked"] += int(c.get("emails_clicked", 0))
            totals["emails_replied"] += int(c.get("emails_replied", 0))

        sent = totals["emails_sent"] or 1  # avoid div/0
        totals["open_rate"] = round(totals["emails_opened"] / sent * 100, 1)
        totals["click_rate"] = round(totals["emails_clicked"] / sent * 100, 1)
        totals["reply_rate"] = round(totals["emails_replied"] / sent * 100, 1)
        totals["conversion_rate"] = round(totals["emails_replied"] / (totals["leads_generated"] or 1) * 100, 1)
        return totals

    def get_overall_metrics(self) -> Dict:
        """Aggregate metrics across all campaigns."""
        return self.get_campaign_metrics()

    def get_aggregate_summary(self) -> Dict:
        """Alias for overall metrics — used by CLI."""
        return self.get_overall_metrics()

    def get_all_metrics(self) -> List[Dict]:
        """Per-campaign metrics list for tabular display."""
        campaigns = self.crm.get_campaign_history()
        result = []
        for c in campaigns:
            sent = int(c.get("emails_sent", 0)) or 1
            opened = int(c.get("emails_opened", 0))
            replied = int(c.get("emails_replied", 0))
            result.append({
                "id": c.get("id", "")[:8],
                "name": c.get("name", ""),
                "domain": c.get("target_domain", ""),
                "status": c.get("status", ""),
                "emails_sent": int(c.get("emails_sent", 0)),
                "open_rate": round(opened / sent * 100, 1),
                "reply_rate": round(replied / sent * 100, 1),
                "created_at": c.get("created_at", "")[:10],
            })
        return result

    def get_top_performing_companies(self, limit: int = 5) -> List[Dict]:
        """Return top companies by reply engagement."""
        prospects = self.crm.get_prospect_history()
        company_stats: Dict[str, Dict] = {}
        for p in prospects:
            domain = p.get("company_domain", "unknown")
            if domain not in company_stats:
                company_stats[domain] = {"company": p.get("company_name", domain), "domain": domain, "sent": 0, "replied": 0}
            company_stats[domain]["sent"] += 1
            if p.get("status") in ("replied", "interested", "converted"):
                company_stats[domain]["replied"] += 1

        ranked = sorted(company_stats.values(), key=lambda x: x["replied"], reverse=True)
        return ranked[:limit]

    def generate_performance_report(self) -> str:
        """Return a formatted text performance report."""
        metrics = self.get_overall_metrics()
        lines = [
            "=" * 50,
            "  VAIBHAV GROWTH ENGINE — Performance Report",
            "=" * 50,
            f"  Total Campaigns   : {metrics.get('campaigns', 0)}",
            f"  Leads Generated   : {metrics.get('leads_generated', 0)}",
            f"  Emails Sent       : {metrics.get('emails_sent', 0)}",
            f"  Open Rate         : {metrics.get('open_rate', 0)}%",
            f"  Click Rate        : {metrics.get('click_rate', 0)}%",
            f"  Reply Rate        : {metrics.get('reply_rate', 0)}%",
            f"  Conversion Rate   : {metrics.get('conversion_rate', 0)}%",
            "=" * 50,
        ]
        return "\n".join(lines)

    def _empty_metrics(self) -> Dict:
        return {
            "campaigns": 0, "leads_generated": 0, "emails_sent": 0,
            "emails_opened": 0, "emails_clicked": 0, "emails_replied": 0,
            "open_rate": 0.0, "click_rate": 0.0, "reply_rate": 0.0, "conversion_rate": 0.0,
        }
