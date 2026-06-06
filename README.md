# Vaibhav Growth Engine

> AI-powered B2B lead discovery and outreach automation platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Vaibhav%20Sonava-purple)](https://github.com/Vaibhavsonava2005)

---

## Overview

Vaibhav Growth Engine is a CLI-first B2B outreach automation platform that discovers companies and decision-makers in a target industry, enriches contact data via Hunter.io and Prospeo, and generates hyper-personalized cold emails using a cascading AI provider chain (Gemini → Groq → OpenRouter → deterministic template fallback). Emails are dispatched through Brevo's transactional API with a mandatory pre-send safety checkpoint, and every campaign is persisted to a local CRM for analytics and history tracking.

Built to run real outreach for products like DekNek, Jobby AI, AgentForge, and MindRAG — not as a demo, but as a production tool.

---

## Features

- **Lead Discovery** — Apollo.io company search + similar-company discovery; falls back to target domain when Apollo is unconfigured
- **Contact Enrichment** — Hunter.io domain search → Prospeo person enrichment → Apollo people search (layered fallback strategy)
- **Email Verification** — Hunter.io email finder with confidence scoring; contacts below threshold are filtered out
- **Company Intelligence** — BeautifulSoup web scraper extracts homepage, about, services, and careers page content; AI or keyword fallback extracts pain points, opportunities, hiring signals, and growth signals
- **AI-Personalized Emails** — Cascading AI router: Gemini 2.5 Flash → Groq Llama 3.3 70B → OpenRouter Mistral 7B → Template (guaranteed fallback, always works)
- **Campaign Safety Checkpoint** — Interactive terminal prompt shows exactly how many companies, decision-makers, and verified emails are queued before any email is dispatched
- **Email Delivery via Brevo** — Transactional SMTP with rate limiting; dry-run mode generates emails but never sends
- **Local CRM** — JSON-backed store for campaign history, prospect history, and per-contact status tracking
- **Analytics Engine** — Aggregate open rate, click rate, reply rate, and bounce rate across campaigns
- **CSV Export** — One-command export of all prospect/campaign data
- **Rich Terminal UI** — Colorized progress bars, tables, panels, and a live banner via the `rich` library
- **Dry-Run & Live Modes** — Preview the full pipeline output before committing to real sends

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI  (main.py)                           │
│   run │ preview │ status │ analytics │ history │ export │ health │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GrowthPipeline                                │
│                                                                 │
│  Step 1 ──► Company Discovery   ──► Apollo.io                  │
│  Step 2 ──► Contact Discovery   ──► Hunter → Prospeo → Apollo  │
│  Step 3 ──► Email Enrichment    ──► Hunter.io                  │
│  Step 4 ──► Company Research    ──► Scraper + AI Analysis      │
│  Step 5 ──► AI Email Generation ──► AIRouter                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐  ┌─────────┐  ┌────────────┐
    │ AIRouter │  │  Brevo  │  │ CRMManager │
    │          │  │ (send)  │  │  (persist) │
    │ Gemini   │  └─────────┘  └────────────┘
    │ Groq     │
    │ OpenRtr  │
    │ Template │
    └──────────┘
          │
          ▼
    ┌──────────────────────────────┐
    │   Analytics / Reports / CSV  │
    └──────────────────────────────┘
```

**Data flow in detail:**

1. `main.py` parses CLI args and invokes `GrowthPipeline.run(domain, ...)`
2. Pipeline calls Apollo to discover similar companies in the target industry
3. For each company, Hunter domain search returns people + emails; Prospeo and Apollo fill gaps
4. Hunter email finder verifies or enriches any contacts missing a confident email address
5. `CompanyResearchEngine` scrapes the company website; `AIRouter.analyze_company()` extracts intelligence
6. `AIRouter.generate_email()` tries Gemini, Groq, OpenRouter in order — falls back to `TemplateAgent`
7. `main.py` renders the safety checkpoint; on approval, `GrowthPipeline.send_campaign()` calls Brevo
8. `CRMManager` persists campaign and prospect records; `AnalyticsEngine` aggregates metrics

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| pip | latest |
| Node.js | 18+ (dashboard only) |
| npm | 9+ (dashboard only) |

### Setup

```bash
git clone https://github.com/Vaibhavsonava2005/vaibhav-growth-engine
cd vaibhav-growth-engine

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

# Copy environment template and fill in your keys
cp .env.example .env
```

Open `.env` and replace each `your_*_api_key_here` placeholder with a real key. At minimum you need `HUNTER_API_KEY`, `BREVO_API_KEY`, `SENDER_EMAIL`, and `SENDER_NAME`. At least one AI key (`GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`) is strongly recommended, but the template fallback will still produce emails without any AI key.

Verify the setup:

```bash
python main.py status
```

All configured services will show **READY** / **Configured**. Unconfigured optional services show **NO KEY** / **Missing** — that is fine.

---

### Run a Campaign

```bash
# Preview emails for a domain — no emails are sent
python main.py preview --domain stripe.com --product "YourProduct"

# Full campaign: discovery → enrichment → AI emails → safety check → send
python main.py run --domain hubspot.com --product "YourProduct"

# Dry run — goes through the full pipeline but skips Brevo delivery
python main.py run --domain stripe.com --product "YourProduct" --dry-run
```

When running in live mode the safety checkpoint will display a summary table (companies found, decision-makers, verified emails, AI provider used) and ask for explicit confirmation before any email is sent.

---

### Dashboard

The web dashboard requires the API backend and the Next.js frontend to run concurrently.

```bash
# Terminal 1 — start the FastAPI backend
cd api
uvicorn main:app --reload --port 8000

# Terminal 2 — start the Next.js dashboard
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Keys

| Service | Purpose | Free Tier | Required |
|---------|---------|-----------|----------|
| [Hunter.io](https://hunter.io/api-keys) | Email discovery & verification | 25 searches/month | Yes |
| [Prospeo](https://app.prospeo.io/) | Contact enrichment | 100 credits | Yes |
| [Brevo](https://app.brevo.com/settings/keys/api) | Email delivery (SMTP) | 300 emails/day | Yes |
| [Groq](https://console.groq.com/keys) | AI email generation (fast) | Free | Recommended |
| [Google Gemini](https://aistudio.google.com/app/apikey) | AI email generation (primary) | Free | Recommended |
| [OpenRouter](https://openrouter.ai/keys) | AI email generation (fallback) | Free tier | Optional |
| [Apollo.io](https://app.apollo.io/#/settings/integrations/api) | Company & people search | Limited free | Optional |

> **Note:** The system always has a template-based fallback for email generation — you can run a campaign with zero AI keys and still get structured outreach emails. AI keys improve personalization quality significantly.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `python main.py status` | Check all API integrations and pipeline configuration |
| `python main.py preview --domain X` | Generate and display email drafts without sending |
| `python main.py preview --domain X --product "P"` | Preview with custom product name |
| `python main.py run --domain X` | Full campaign: discover → enrich → generate → safety check → send |
| `python main.py run --domain X --product "P"` | Campaign with custom product/service name |
| `python main.py run --domain X --dry-run` | Full pipeline but skip Brevo delivery |
| `python main.py run --domain X --name "CampaignName"` | Set a custom campaign name |
| `python main.py analytics` | Show aggregate metrics across all campaigns |
| `python main.py analytics --campaign-id ID` | Show metrics for a specific campaign |
| `python main.py history` | Show campaign and prospect history (last 20) |
| `python main.py history --limit 50` | Show last N records |
| `python main.py export --domain X` | Export prospects for a domain to CSV |
| `python main.py health` | Detailed integration health check |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `APOLLO_API_KEY` | Apollo.io API key for company/people search | Optional |
| `PROSPEO_API_KEY` | Prospeo API key for contact enrichment | Recommended |
| `HUNTER_API_KEY` | Hunter.io API key for email discovery | Yes |
| `BREVO_API_KEY` | Brevo (SendinBlue) API key for email delivery | Yes |
| `GEMINI_API_KEY` | Google Gemini API key (primary AI) | Recommended |
| `GROQ_API_KEY` | Groq API key (secondary AI, very fast) | Recommended |
| `OPENROUTER_API_KEY` | OpenRouter API key (tertiary AI fallback) | Optional |
| `SENDER_EMAIL` | From address used in outreach emails | Yes |
| `SENDER_NAME` | From name used in outreach emails | Yes |
| `MAX_COMPANIES` | Max companies to discover per run (default: 10) | No |
| `MAX_CONTACTS_PER_COMPANY` | Max contacts to enrich per company (default: 3) | No |
| `MAX_RETRIES` | HTTP retry attempts before giving up (default: 3) | No |
| `REQUEST_TIMEOUT` | HTTP timeout in seconds (default: 30) | No |
| `DRY_RUN` | Global dry-run override (`true`/`false`, default: false) | No |
| `LOG_LEVEL` | Logging verbosity: `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` | No |

---

## Project Structure

```
vaibhav-growth-engine/
├── main.py                        # CLI entry point (Click + Rich)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .env                           # Your local keys (gitignored)
│
├── src/
│   ├── agents/
│   │   ├── ai_router.py           # Cascading AI provider orchestrator
│   │   ├── gemini_agent.py        # Google Gemini 2.5 Flash integration
│   │   ├── groq_agent.py          # Groq Llama 3.3 70B integration
│   │   ├── openrouter_agent.py    # OpenRouter (Mistral 7B) integration
│   │   └── template_agent.py      # Deterministic template fallback
│   │
│   ├── analytics/
│   │   ├── metrics.py             # Campaign metrics aggregation
│   │   └── scorer.py              # Prospect quality scoring
│   │
│   ├── config/
│   │   ├── settings.py            # Pydantic settings (reads from .env)
│   │   └── constants.py           # Decision-maker titles, keywords, etc.
│   │
│   ├── crm/
│   │   └── crm_manager.py         # Local JSON-backed CRM persistence
│   │
│   ├── models/
│   │   ├── campaign.py            # Campaign, EmailDraft, CampaignResult
│   │   ├── company.py             # Company, CompanyIntelligence
│   │   ├── contact.py             # Contact model
│   │   └── prospect.py            # Prospect model
│   │
│   ├── pipeline/
│   │   ├── growth_pipeline.py     # Master 5-step pipeline orchestrator
│   │   └── research_engine.py     # Company website scraper + intelligence
│   │
│   ├── prompts/                   # AI prompt templates
│   │
│   ├── reports/
│   │   └── report_generator.py    # JSON/CSV report generation
│   │
│   ├── services/
│   │   ├── apollo.py              # Apollo.io company + people search
│   │   ├── brevo.py               # Brevo email delivery
│   │   ├── hunter.py              # Hunter.io email enrichment
│   │   ├── prospeo.py             # Prospeo contact enrichment
│   │   └── scraper.py             # BeautifulSoup web scraper
│   │
│   └── utils/
│       ├── deduplicator.py        # Company and contact deduplication
│       ├── logger.py              # Loguru logger setup
│       └── validators.py          # Domain validation helpers
│
├── data/                          # Campaign output and CRM data (gitignored)
├── logs/                          # Runtime logs (gitignored)
└── tests/                         # pytest test suite
```

---

## Running Tests

```bash
pytest tests/ -v
```

The test suite uses `pytest-mock` and `responses` to mock all external API calls — no live API keys are required to run tests.

---

## Author

**Vaibhav Sonava** — [github.com/Vaibhavsonava2005](https://github.com/Vaibhavsonava2005)

Built as part of the Subspace/Vocallabs Software Engineering assignment and designed for real B2B outreach for [DekNek](https://deknek.com), Jobby AI, AgentForge, and MindRAG.
