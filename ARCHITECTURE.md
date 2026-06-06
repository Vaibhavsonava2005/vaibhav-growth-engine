# Architecture — Vaibhav Growth Engine

> Technical reference for the full system design, component interactions, and integration details.

**Author:** Vaibhav Sonava — [github.com/Vaibhavsonava2005](https://github.com/Vaibhavsonava2005)  
**Version:** 1.0.0  
**Stack:** Python 3.11, Click, Rich, Pydantic, Loguru, BeautifulSoup4, Brevo SDK, Groq SDK, google-genai

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow](#data-flow)
4. [Integration Details](#integration-details)
5. [AI Provider Chain](#ai-provider-chain)
6. [Technology Choices and Rationale](#technology-choices-and-rationale)
7. [Deployment Architecture](#deployment-architecture)

---

## System Overview

Vaibhav Growth Engine is structured as a **CLI-first pipeline application**. There is no persistent server process for the core engine — every campaign run is a single process execution that starts, does its work, and exits cleanly. State is persisted to a local JSON-backed CRM in the `data/` directory.

The system has three distinct execution layers:

| Layer | Description |
|-------|-------------|
| **CLI** | Click commands rendered with Rich. Entry point for all operations. |
| **Pipeline** | Orchestrates discovery, enrichment, research, and AI generation in sequence. |
| **Services** | Thin API clients for Apollo, Hunter, Prospeo, Brevo, and the web scraper. |

A separate **web dashboard** (Next.js + FastAPI) reads from the same `data/` directory and provides a browser UI over the same data the CLI writes.

---

## Component Breakdown

### 1. CLI (`main.py`)

The CLI is built with [Click](https://click.palletsprojects.com/) and uses [Rich](https://github.com/Textualize/rich) for all terminal output. It defines the following commands:

| Command | Handler | Description |
|---------|---------|-------------|
| `run` | `run()` | Full pipeline execution with safety checkpoint |
| `preview` | `preview()` | Pipeline in dry-run; renders email drafts to terminal |
| `status` | `status()` | Renders AI provider and external service status tables |
| `analytics` | `analytics()` | Renders aggregate and per-campaign metrics |
| `history` | `history()` | Renders campaign and prospect history from CRM |
| `export` | Calls `CRMManager` | Exports CRM data to CSV |
| `health` | Calls all services | Detailed per-service health check |

The `print_banner()` function renders a UTF-8-safe ANSI banner. Windows compatibility is handled by wrapping `sys.stdout.buffer` with an explicit `utf-8` encoding.

**Safety Checkpoint** (`show_safety_checkpoint`): Before any live send, the CLI renders a summary table — companies found, decision-makers, verified emails, AI provider used, mode (DRY-RUN / LIVE) — and uses `rich.prompt.Confirm` to require explicit user approval. The default is `False`, so an accidental Enter key does not trigger a send.

---

### 2. GrowthPipeline (`src/pipeline/growth_pipeline.py`)

The master orchestrator. Initialized once per CLI invocation, it holds references to all service clients and executes the pipeline in five sequential steps:

```
Step 1 — Company Discovery
  └─ ApolloService.get_similar_companies(domain)
  └─ ApolloService.enrich_company(domain)          # always include target
  └─ Fallback: create minimal Company from domain string

Step 2 — Contact Discovery (per company)
  └─ HunterService.domain_search()                 # Strategy 1
  └─ ProspeoService.enrich_person()                # Strategy 2 (fill gaps)
  └─ ApolloService.search_people()                 # Strategy 3 (fill gaps)

Step 3 — Email Enrichment (per contact)
  └─ Skip if contact already has email with confidence ≥ 0.50
  └─ HunterService.find_email(first, last, domain)

Step 4 — Company Research (per company)
  └─ CompanyResearchEngine.research_company()
      └─ Scraper: homepage, /about, /services, /careers
      └─ AIRouter.analyze_company() → pain_points, opportunities, hiring/growth signals

Step 5 — AI Email Generation (per contact)
  └─ AIRouter.generate_email(contact, intelligence, product)
      └─ Returns: subject, body, preview_text, personalization_score, follow_ups
```

The pipeline renders a `rich.progress.Progress` bar with one task per step so the terminal output is clean even for large campaigns.

Deduplication is handled by `CompanyDeduplicator` and `ContactDeduplicator` — both are in-memory set-based guards that prevent the same company domain or contact email/LinkedIn URL from being processed twice within a single run.

---

### 3. Services (`src/services/`)

Each service is a self-contained API client that:
- Reads its API key from Pydantic settings
- Exposes an `is_configured()` method that returns `False` when no key is set
- Uses `httpx` for async-capable HTTP with `tenacity` retry decorators

| Service | File | Key Method(s) |
|---------|------|---------------|
| Apollo | `apollo.py` | `get_similar_companies`, `enrich_company`, `search_people` |
| Hunter | `hunter.py` | `domain_search`, `find_email` |
| Prospeo | `prospeo.py` | `enrich_person`, `search_people` |
| Brevo | `brevo.py` | `send_campaign_emails`, `send_single_email` |
| Scraper | `scraper.py` | `scrape_company(domain)` → dict of page texts |

All services fail gracefully — exceptions are caught at the pipeline level and logged as warnings, allowing the pipeline to proceed with whatever data is available.

---

### 4. AI Router (`src/agents/ai_router.py`)

The `AIRouter` is a cascading provider orchestrator. It maintains an ordered list of `(agent_instance, provider_name)` tuples and tries each in sequence:

```
Priority 1: GeminiAgent     (google-genai SDK, Gemini 2.5 Flash)
Priority 2: GroqAgent       (groq SDK, Llama 3.3 70B)
Priority 3: OpenRouterAgent (openai SDK pointed at openrouter.ai, Mistral 7B)
Fallback:   TemplateAgent   (deterministic Jinja-style templates, no API needed)
```

Each agent exposes:
- `is_configured()` → bool (checks if API key is set and non-empty)
- `generate_email(contact, intelligence, product)` → dict
- `analyze_company(company_name, scrape_data)` → dict

The router skips unconfigured agents without attempting a network call. If an agent raises any exception, the router logs a warning and tries the next provider. `TemplateAgent` is always the guaranteed last resort and never raises.

`last_used_provider` is a string attribute updated after every successful generation — the CLI reads this to display in the safety checkpoint and summary card.

---

### 5. Research Engine (`src/pipeline/research_engine.py`)

`CompanyResearchEngine` wraps the `Scraper` service and the `AIRouter.analyze_company()` call into a single `research_company(company)` method that returns a `CompanyIntelligence` object.

```python
CompanyIntelligence:
  pain_points: List[str]
  opportunities: List[str]
  hiring_signals: List[str]
  growth_signals: List[str]
  homepage_summary: str
  tech_stack_hints: List[str]
```

When no AI provider is configured, `AIRouter._keyword_analyze()` provides deterministic extraction using `PAIN_POINTS_KEYWORDS` and `OPPORTUNITY_KEYWORDS` constant dictionaries — no network call required.

---

### 6. CRM Manager (`src/crm/crm_manager.py`)

A lightweight JSON file store under `data/`. No external database required.

```
data/
├── campaigns.json     # list of Campaign records
├── prospects.json     # list of Prospect records
└── exports/           # CSV exports
```

Key methods:
- `save_campaign(campaign)` — upserts by campaign ID
- `save_prospect(contact, campaign_id)` — upserts by email
- `get_campaign_history()` → list of dicts
- `get_prospect_history()` → list of dicts

---

### 7. Analytics Engine (`src/analytics/`)

`AnalyticsEngine` reads from `CRMManager` and computes:
- Per-campaign: `emails_sent`, `open_rate`, `click_rate`, `reply_rate`, `bounce_rate`
- Aggregate: totals and averages across all campaigns

`ProspectScorer` assigns a quality score (0–100) to each prospect based on title seniority, email confidence, and company size signals.

---

### 8. Web Dashboard (optional)

The web dashboard is a separate stack that reads from the same `data/` directory:

```
api/          FastAPI backend (serves campaign and prospect data as JSON)
dashboard/    Next.js frontend (leads table, health panel, analytics charts)
```

The dashboard is read-only — it does not trigger pipeline runs. Campaigns are launched exclusively from the CLI.

---

## Data Flow

```
User
  │
  │  python main.py run --domain hubspot.com --product "AgentForge"
  ▼
CLI (main.py)
  │
  │  validate_domain()
  │  GrowthPipeline()
  ▼
Pipeline.run(domain="hubspot.com", ...)
  │
  ├──► ApolloService.get_similar_companies("hubspot.com")
  │       └── Returns: [Company(name="Salesforce", domain="salesforce.com"), ...]
  │
  ├──► HunterService.domain_search("salesforce.com")
  │       └── Returns: [EmailEnrichment(first_name="Marc", email="marc@...", confidence=0.92), ...]
  │
  ├──► HunterService.find_email("Marc", "Benioff", "salesforce.com")
  │       └── Returns: EmailEnrichment(email="marc@salesforce.com", confidence=0.95)
  │
  ├──► Scraper.scrape_company("salesforce.com")
  │       └── Returns: {homepage_text: "...", about_text: "...", careers_text: "..."}
  │
  ├──► AIRouter.analyze_company("Salesforce", scrape_data)
  │       └── Gemini → Returns: {pain_points: [...], opportunities: [...], ...}
  │
  ├──► AIRouter.generate_email(contact, intelligence, "AgentForge")
  │       └── Gemini → Returns: {subject: "...", body: "...", personalization_score: 78.5}
  │
  └──► Campaign(email_drafts=[EmailDraft(...), ...])
         │
CLI  ◄───┘  (renders safety checkpoint)
  │
  │  User confirms → pipeline.send_campaign(campaign, dry_run=False)
  │
  ├──► BrevoService.send_campaign_emails(drafts, campaign)
  │       └── 202 Accepted per email
  │
  └──► CRMManager.save_campaign(campaign)
           └── data/campaigns.json updated
```

---

## Integration Details

### Apollo.io

- **API version:** v1 REST
- **Endpoints used:** `/v1/mixed_companies/search` (similar companies), `/v1/organizations/enrich` (company enrichment), `/v1/mixed_people/search` (people search)
- **Auth:** `X-Api-Key` header
- **Fallback:** If Apollo is unconfigured, the pipeline creates a minimal `Company` object directly from the target domain string. Contact discovery falls back entirely to Hunter + Prospeo.

### Hunter.io

- **Endpoints used:** `/v2/domain-search` (returns people + emails for a domain), `/v2/email-finder` (find email by name + domain)
- **Auth:** `api_key` query parameter
- **Response model:** `EmailEnrichment` (first_name, last_name, email, confidence_score, is_verified)
- **Strategy:** Domain search is tried first; email finder is used only for contacts that came through Apollo/Prospeo without a verified email

### Prospeo

- **Endpoints used:** `/v1/email-finder` (enrich a person by name + domain or LinkedIn URL)
- **Auth:** `X-KEY` header
- **Usage pattern:** Used to re-enrich contacts found via Apollo that don't have a verified email from Hunter

### Brevo (SendinBlue)

- **SDK:** `sib-api-v3-sdk`
- **API used:** Transactional email (`SendSmtpEmail`)
- **Rate limiting:** Brevo's free tier allows 300 emails/day; the pipeline respects this via configurable delays
- **Dry-run:** When `dry_run=True`, `send_campaign_emails` builds the `SendSmtpEmail` objects but does not call the SDK send method

### Google Gemini

- **SDK:** `google-genai` (official Python SDK)
- **Model:** `gemini-2.5-flash` (latest available at time of writing)
- **Prompt structure:** System prompt + structured JSON output schema for `{subject, body, preview_text, personalization_score, follow_ups}`

### Groq

- **SDK:** `groq` (official Python SDK)
- **Model:** `llama-3.3-70b-versatile`
- **Why Groq:** Sub-second inference latency; ideal when generating emails for 30+ contacts in a single pipeline run

### OpenRouter

- **SDK:** `openai` (OpenAI-compatible API)
- **Base URL:** `https://openrouter.ai/api/v1`
- **Model:** `mistralai/mistral-7b-instruct`
- **Why OpenRouter:** Access to 100+ models through a single API key; used as tertiary fallback when Gemini and Groq are unavailable

---

## Technology Choices and Rationale

| Technology | Rationale |
|-----------|-----------|
| **Click** | Composable command groups, automatic `--help` generation, type-safe option parsing |
| **Rich** | Professional terminal output — tables, panels, progress bars, ANSI color — without curses complexity |
| **Pydantic v2** | Settings management reads `.env` into strongly-typed, validated Python objects; model validation prevents bad data from entering the pipeline |
| **Loguru** | Structured logging with `logger.info(...)` and `logger.success(...)` levels; single-line setup vs Python's `logging` module |
| **httpx** | Async-capable HTTP client; `tenacity` decorators wrap calls with exponential backoff retry logic |
| **BeautifulSoup4** | Reliable HTML parsing for company website scraping; `lxml` parser for speed |
| **tenacity** | Retry logic with exponential backoff and jitter for all external API calls |
| **JSON CRM** | Zero infrastructure dependency — no PostgreSQL or Redis required to run the tool locally; data is human-readable and easily inspectable |
| **Cascading AI router** | Resilience — the tool works even if one or two AI providers have outages or rate limits; guaranteed output via `TemplateAgent` |

---

## Deployment Architecture

### Local (default)

```
Developer machine
└── Python venv
    ├── python main.py run ...     (CLI campaigns)
    ├── uvicorn api.main:app       (dashboard backend, optional)
    └── npm run dev                (Next.js frontend, optional)
```

All data is local. No external databases. API keys are stored in `.env` (gitignored).

### Production (future)

For a production deployment handling multiple users, the recommended architecture would be:

```
┌────────────────────────────────────────────────────────┐
│                     Load Balancer                      │
└──────────┬─────────────────────────────────────────────┘
           │
    ┌──────┴───────┐          ┌──────────────────────┐
    │  FastAPI API │◄────────►│  PostgreSQL (CRM)    │
    │  (backend)   │          └──────────────────────┘
    └──────┬───────┘
           │
    ┌──────┴───────┐          ┌──────────────────────┐
    │  Celery      │◄────────►│  Redis (task queue)  │
    │  (pipeline   │          └──────────────────────┘
    │   worker)    │
    └──────────────┘
```

- Pipeline runs become async Celery tasks triggered by API calls
- CRM data moves to PostgreSQL
- Redis queues campaign jobs
- Docker Compose orchestrates all services
- Environment variables become Kubernetes secrets or a secrets manager

This architecture is a natural evolution from the current local-first design — all the service interfaces and pipeline logic remain unchanged.
