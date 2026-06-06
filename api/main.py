"""
VAIBHAV GROWTH ENGINE — REST API Backend
Author: Vaibhav Sonava
GitHub: github.com/Vaibhavsonava2005

FastAPI backend that powers the web dashboard.
Provides endpoints for health checks, campaigns, leads, analytics, and CSV export.
"""

import os
import sys
import csv
import uuid
import threading
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup — ensure repo root is on sys.path
# ---------------------------------------------------------------------------
_API_DIR = Path(__file__).resolve().parent       # .../vaibhav-growth-engine/api
_ROOT_DIR = _API_DIR.parent                      # .../vaibhav-growth-engine
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# Change working directory to repo root so .env is found
os.chdir(str(_ROOT_DIR))

# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
from src.config.settings import settings
from src.config.constants import APP_NAME, APP_VERSION
from src.crm.crm_manager import CRMManager
from src.services.hunter import HunterService
from src.services.prospeo import ProspeoService
from src.services.apollo import ApolloService
from src.services.brevo import BrevoService
from src.agents.ai_router import AIRouter
from src.pipeline.growth_pipeline import GrowthPipeline

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="VAIBHAV GROWTH ENGINE API",
    description="REST backend for the Vaibhav Growth Engine dashboard. Author: Vaibhav Sonava",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store (for background campaign runs)
# ---------------------------------------------------------------------------
_jobs: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class RunCampaignRequest(BaseModel):
    domain: str
    product: str = "AI Solutions"
    dry_run: bool = True


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------
def _run_pipeline_background(job_id: str, domain: str, product: str, dry_run: bool) -> None:
    """Execute GrowthPipeline in a background thread."""
    try:
        pipeline = GrowthPipeline()
        campaign = pipeline.run(
            domain=domain,
            campaign_name=f"api-{domain.split('.')[0]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            sender_product=product,
            dry_run=dry_run,
        )
        _jobs[job_id] = {
            "status": "done",
            "result": {
                "domain": domain,
                "companies_found": campaign.companies_found,
                "contacts_found": campaign.contacts_found,
                "emails_found": campaign.emails_found,
                "emails_sent": campaign.emails_sent,
                "drafts": len(campaign.email_drafts),
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
            },
        }
    except Exception as exc:
        _jobs[job_id] = {"status": "error", "result": {"error": str(exc)}}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Return live connectivity status + credits for every downstream service."""
    response: Dict[str, Any] = {}

    # Hunter
    hunter = HunterService()
    if hunter.is_configured():
        try:
            data = hunter._make_request("/account", params={})
            plan = (data.get("data", {}) or {}).get("plan_name", "free") if data else "free"
            searches = (data.get("data", {}) or {}).get("requests", {}).get("searches", {}) if data else {}
            response["hunter"] = {
                "configured": True,
                "status": "ready",
                "credits_used": searches.get("used", 0),
                "credits_remaining": searches.get("available", 0),
                "plan": plan,
            }
        except Exception as e:
            response["hunter"] = {"configured": True, "status": "key set", "error": str(e)}
    else:
        response["hunter"] = {"configured": False, "status": "no key"}

    # Prospeo
    prospeo = ProspeoService()
    if prospeo.is_configured():
        try:
            data = prospeo.get_account_info()
            resp = (data.get("response") or {}) if data else {}
            response["prospeo"] = {
                "configured": True,
                "status": "ready",
                "credits_remaining": resp.get("remaining_credits", "unknown"),
                "credits_used": resp.get("used_credits", 0),
                "plan": resp.get("current_plan", "FREE"),
                "renewal_date": (resp.get("next_quota_renewal_date") or "")[:10],
            }
        except Exception as e:
            response["prospeo"] = {"configured": True, "status": "key set", "error": str(e)}
    else:
        response["prospeo"] = {"configured": False, "status": "no key"}

    # Apollo
    apollo = ApolloService()
    response["apollo"] = {
        "configured": apollo.is_configured(),
        "status": "ready" if apollo.is_configured() else "no key",
        "note": "master key required for API",
    }

    # Brevo
    brevo = BrevoService()
    response["brevo"] = {
        "configured": brevo.is_configured(),
        "status": "ready" if brevo.is_configured() else "no key",
        "daily_limit": 300,
        "plan": "free",
    }

    # Groq
    groq_key = settings.GROQ_API_KEY if hasattr(settings, "GROQ_API_KEY") else ""
    response["groq"] = {
        "configured": bool(groq_key and len(groq_key) > 10),
        "status": "ready" if (groq_key and len(groq_key) > 10) else "no key",
        "model": "llama-3.1-8b-instant",
    }

    # OpenRouter
    or_key = settings.OPENROUTER_API_KEY if hasattr(settings, "OPENROUTER_API_KEY") else ""
    response["openrouter"] = {
        "configured": bool(or_key and len(or_key) > 10),
        "status": "ready" if (or_key and len(or_key) > 10) else "no key",
        "model": "google/gemma-3-4b-it:free",
    }

    response["last_checked"] = datetime.now(timezone.utc).isoformat()
    response["app"] = APP_NAME
    return response


@app.get("/api/campaigns")
def list_campaigns() -> List[Dict[str, Any]]:
    """Return the full campaign history from CRM."""
    try:
        crm = CRMManager()
        return crm.get_campaign_history() or []
    except Exception:
        return []


@app.post("/api/campaigns/run")
def run_campaign(req: RunCampaignRequest) -> Dict[str, str]:
    """Start a Growth Pipeline run in a background thread."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "result": {}}
    thread = threading.Thread(
        target=_run_pipeline_background,
        args=(job_id, req.domain, req.product, req.dry_run),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id, "status": "started"}


@app.get("/api/campaigns/{job_id}/status")
def campaign_job_status(job_id: str) -> Dict[str, Any]:
    """Poll a background campaign job by ID."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return _jobs[job_id]


@app.get("/api/leads")
def list_leads(
    domain: Optional[str] = Query(default=None, description="Filter by company domain"),
    limit: int = Query(default=100, ge=1, le=10000),
) -> List[Dict[str, Any]]:
    """Return prospect history, optionally filtered by domain."""
    try:
        crm = CRMManager()
        prospects = crm.get_prospect_history() or []
        if domain:
            prospects = [p for p in prospects if domain.lower() in str(p.get("company_domain", "")).lower()]
        return prospects[:limit]
    except Exception:
        return []


@app.get("/api/export/csv")
def export_csv() -> StreamingResponse:
    """Stream all prospect data as a downloadable CSV file."""
    COLUMNS = [
        "company_name", "company_domain", "contact_name", "contact_title",
        "contact_email", "source", "campaign_id", "status", "sent_at",
    ]

    def _generate():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        yield buf.getvalue()
        buf.seek(0); buf.truncate(0)

        csv_path = _ROOT_DIR / "data" / "prospect_history.csv"
        if csv_path.exists():
            try:
                with csv_path.open(newline="", encoding="utf-8") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        filtered = {col: row.get(col, "") for col in COLUMNS}
                        writer.writerow(filtered)
                        yield buf.getvalue()
                        buf.seek(0); buf.truncate(0)
            except Exception:
                pass

    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@app.get("/api/analytics")
def analytics() -> Dict[str, Any]:
    """Aggregate metrics from CRM data."""
    try:
        crm = CRMManager()
        campaigns = crm.get_campaign_history() or []
        prospects = crm.get_prospect_history() or []
    except Exception:
        campaigns, prospects = [], []

    domains = list({c.get("target_domain", "") for c in campaigns if c.get("target_domain", "")})
    total_sent = sum(int(c.get("emails_sent", 0) or 0) for c in campaigns)
    total_contacts = sum(int(c.get("contacts_found", 0) or 0) for c in campaigns)

    # Per-campaign breakdown for charts
    chart_data = [
        {
            "name": c.get("name", c.get("target_domain", ""))[:20],
            "emails_sent": int(c.get("emails_sent", 0) or 0),
            "contacts_found": int(c.get("contacts_found", 0) or 0),
            "date": c.get("created_at", "")[:10],
        }
        for c in campaigns[-10:]  # last 10 for chart
    ]

    return {
        "total_campaigns": len(campaigns),
        "total_emails_sent": total_sent,
        "total_contacts_found": total_contacts,
        "total_prospects": len(prospects),
        "domains_targeted": domains,
        "chart_data": chart_data,
    }


@app.get("/api/config")
def get_config() -> Dict[str, Any]:
    """Return non-sensitive configuration values."""
    return {
        "sender_name": getattr(settings, "SENDER_NAME", None),
        "sender_email": getattr(settings, "SENDER_EMAIL", None),
        "max_companies": getattr(settings, "MAX_COMPANIES", None),
        "max_contacts_per_company": getattr(settings, "MAX_CONTACTS_PER_COMPANY", None),
        "dry_run_mode": getattr(settings, "DRY_RUN", None),
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
    }


@app.get("/api/")
def root():
    return {"message": f"{APP_NAME} API — visit /api/docs for interactive documentation"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
