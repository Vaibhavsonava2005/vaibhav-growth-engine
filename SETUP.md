# Setup Guide — Vaibhav Growth Engine

> Step-by-step instructions to get the engine running locally from zero.

---

## Table of Contents

1. [Python Environment Setup](#1-python-environment-setup)
2. [Node.js Setup (Dashboard Only)](#2-nodejs-setup-dashboard-only)
3. [API Key Setup](#3-api-key-setup)
4. [Environment Configuration (.env)](#4-environment-configuration-env)
5. [Running the CLI Locally](#5-running-the-cli-locally)
6. [Running the Dashboard](#6-running-the-dashboard)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Python Environment Setup

### Clone the Repository

```bash
git clone https://github.com/Vaibhavsonava2005/vaibhav-growth-engine
cd vaibhav-growth-engine
```

### Create a Virtual Environment

Using a virtual environment keeps dependencies isolated from your global Python installation.

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt. All subsequent `pip` and `python` commands should be run inside this activated environment.

### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs all core dependencies: Click, Rich, Pydantic, Loguru, httpx, tenacity, BeautifulSoup4, the Brevo SDK, the Groq SDK, and the Google Genai SDK.

**Expected output:** A list of packages being downloaded and installed. The final line should be `Successfully installed ...`.

**Common issues:**
- `pip: command not found` → ensure Python 3.11+ is installed and your venv is activated
- `ERROR: Could not find a version that satisfies the requirement google-genai>=0.8.0` → upgrade pip with `pip install --upgrade pip` and retry

---

## 2. Node.js Setup (Dashboard Only)

The web dashboard requires Node.js 18 or later. Skip this section if you are only using the CLI.

### Install Node.js

Download and install from [nodejs.org](https://nodejs.org/en/download). Choose the LTS version (18.x or 20.x).

Verify the installation:
```bash
node --version    # should print v18.x.x or higher
npm --version     # should print 9.x.x or higher
```

---

## 3. API Key Setup

You need to register for the following services and obtain API keys. All have free tiers sufficient for development and small campaigns.

### Hunter.io (Required)

1. Go to [hunter.io](https://hunter.io) and create a free account
2. Navigate to **Settings → API** or visit [hunter.io/api-keys](https://hunter.io/api-keys) directly
3. Copy your API key — it looks like `a1b2c3d4e5f6...`

**Free tier:** 25 domain searches/month, 25 email finders/month. Sufficient for testing and small campaigns.

### Brevo / SendinBlue (Required)

1. Go to [brevo.com](https://brevo.com) and create a free account
2. Navigate to **Settings → API Keys** or visit [app.brevo.com/settings/keys/api](https://app.brevo.com/settings/keys/api)
3. Click **Generate a new API key**, give it a name (e.g. "growth-engine"), and copy the key

**Free tier:** 300 transactional emails/day. No credit card required.

**Important:** Also verify your sender email address in Brevo under **Senders & IP → Senders** — emails sent from an unverified address will be rejected.

### Google Gemini (Recommended)

1. Go to [aistudio.google.com](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the key — it starts with `AIza...`

**Free tier:** Generous rate limits for `gemini-2.5-flash`. No credit card required.

### Groq (Recommended)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign in (GitHub or Google OAuth available)
3. Navigate to **API Keys → Create API Key**
4. Copy the key — it starts with `gsk_...`

**Free tier:** Very generous — Llama 3.3 70B is free with high rate limits.

### OpenRouter (Optional)

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up and navigate to **Keys**
3. Create a new key and copy it

**Free tier:** A selection of models (including Mistral 7B) are available with no charge.

### Prospeo (Recommended)

1. Go to [app.prospeo.io](https://app.prospeo.io)
2. Create a free account
3. Navigate to your account settings to find your API key

**Free tier:** 100 enrichment credits. Used as a secondary enrichment source when Hunter doesn't find an email.

### Apollo.io (Optional)

1. Go to [app.apollo.io](https://app.apollo.io)
2. Create a free account
3. Navigate to **Settings → Integrations → API** or visit [app.apollo.io/#/settings/integrations/api](https://app.apollo.io/#/settings/integrations/api)
4. Copy your API key

**Note:** Apollo is optional. Without it, the pipeline will still discover contacts for the target domain using Hunter and Prospeo — it just won't find similar companies in the same industry.

---

## 4. Environment Configuration (.env)

Copy the template:

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in each key. Below is a complete annotated example:

```env
# ── Lead Discovery ────────────────────────────────────────────────
# Optional — needed for similar company discovery
APOLLO_API_KEY=your_apollo_api_key_here

# ── Contact Enrichment ────────────────────────────────────────────
# Recommended
PROSPEO_API_KEY=your_prospeo_api_key_here

# ── Email Enrichment ──────────────────────────────────────────────
# Required
HUNTER_API_KEY=your_hunter_api_key_here

# ── Email Delivery ────────────────────────────────────────────────
# Required
BREVO_API_KEY=your_brevo_api_key_here

# ── AI Providers (at least one recommended) ───────────────────────
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# ── Sender Configuration ──────────────────────────────────────────
# Must match a verified sender in your Brevo account
SENDER_EMAIL=vaibhav@yourdomain.com
SENDER_NAME=Vaibhav Sonava

# ── Pipeline Behaviour ────────────────────────────────────────────
MAX_COMPANIES=10
MAX_CONTACTS_PER_COMPANY=3
MAX_RETRIES=3
REQUEST_TIMEOUT=30
DRY_RUN=false
LOG_LEVEL=INFO
```

> **Security:** `.env` is in `.gitignore` and will never be committed. Never share your `.env` file or paste API keys into GitHub issues.

---

## 5. Running the CLI Locally

### Verify Setup

```bash
python main.py status
```

This command checks all API integrations and prints a status table. Expected output:

```
╔══════════════════════════════════════════════════════════╗
║         VAIBHAV GROWTH ENGINE v1.0.0                    ║
║   AI-Powered Lead Discovery & Outreach Platform         ║
╚══════════════════════════════════════════════════════════╝

ℹ Checking API provider status ...

  AI Providers
  ┌──────────────┬─────────┬──────────┬──────────┐
  │ Provider     │ Status  │ Key Set? │ Priority │
  ├──────────────┼─────────┼──────────┼──────────┤
  │ Gemini       │  READY  │   Yes    │   1st    │
  │ Groq         │  READY  │   Yes    │   2nd    │
  │ OpenRouter   │  NO KEY │   No     │   3rd    │
  │ Template     │  READY  │   Yes    │ Fallback │
  └──────────────┴─────────┴──────────┴──────────┘
```

Missing keys for optional services (Apollo, OpenRouter) will show as **NO KEY** / **Missing** — this is expected and does not prevent the pipeline from running.

### Preview Emails (No Send)

```bash
python main.py preview --domain stripe.com --product "AgentForge"
```

This runs the full pipeline (discovery → enrichment → research → AI generation) but does not send any emails. Each generated email draft is printed to the terminal with subject, recipient, AI provider used, and personalization score.

### Run a Full Campaign

```bash
# Dry run — full pipeline, no emails dispatched
python main.py run --domain hubspot.com --product "Jobby AI" --dry-run

# Live run — prompts for confirmation before sending
python main.py run --domain hubspot.com --product "Jobby AI"
```

When running in live mode, the safety checkpoint will appear:

```
══════════════════ ⚠  MANDATORY SAFETY CHECK  ⚠ ══════════════════

  ╔════════════════════════════════════════╗
  ║         CAMPAIGN SAFETY CHECK         ║
  ╠════════════════════════════════════════╣
  ║  Companies Found:  4                  ║
  ║  Decision Makers:  9                  ║
  ║  Verified Emails:  7                  ║
  ║  Campaign Name:    Hubspot-20260607   ║
  ║  Emails Ready:     7                  ║
  ║  AI Provider:      gemini             ║
  ║  Mode:             LIVE               ║
  ╚════════════════════════════════════════╝

⚠ LIVE mode: approving will dispatch real emails to real contacts.

Proceed with campaign? [y/N]:
```

Type `y` and press Enter to send. The default is `N` — pressing Enter without typing `y` cancels the campaign.

### View Analytics

```bash
python main.py analytics
```

### View History

```bash
python main.py history
python main.py history --limit 50
```

### Export to CSV

```bash
python main.py export --domain hubspot.com
```

---

## 6. Running the Dashboard

The dashboard requires two processes running simultaneously — the FastAPI backend and the Next.js frontend.

### Start the API Backend

```bash
# From the project root
cd api
pip install fastapi uvicorn    # if not already installed
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Test it: open [http://localhost:8000/docs](http://localhost:8000/docs) — you should see the FastAPI auto-generated Swagger UI.

### Start the Next.js Dashboard

Open a **new terminal window** (leave the API running):

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

The dashboard reads campaign and prospect data from the `data/` directory via the FastAPI backend. Run at least one campaign with `python main.py run ...` before opening the dashboard to see populated data.

---

## 7. Troubleshooting

### `ModuleNotFoundError: No module named 'src'`

You are running Python from the wrong directory. Ensure you are in the project root:

```bash
# Should show main.py in the listing
ls          # macOS / Linux
dir         # Windows
```

And that your venv is activated (you should see `(venv)` in your prompt).

### `UnicodeEncodeError` on Windows

The engine handles this internally by wrapping stdout with a UTF-8 encoder. If you see this error, ensure you are using Python 3.11+ and running in PowerShell or Windows Terminal (not the legacy cmd.exe).

### `ValidationError: SENDER_EMAIL is not a valid email`

Your `.env` file has the placeholder value `your-email@domain.com` still set. Replace it with your actual sender email address.

### Emails are not being sent / Brevo rejects

1. Check your Brevo API key is correct: `python main.py status` should show Brevo as **Configured**
2. Verify your sender email in Brevo: go to **Settings → Senders & IP → Senders** and confirm the email is verified
3. Check your Brevo daily sending limit — free tier is 300/day
4. Run with `--dry-run` first to confirm email drafts are being generated before sending

### No contacts found

1. Run `python main.py status` and verify Hunter.io shows **Configured**
2. Check your Hunter.io free tier is not exhausted (25 domain searches/month)
3. Try a different domain — some domains have very few publicly indexed contacts
4. Add an Apollo.io key to enable additional contact discovery strategies

### AI emails look generic / template-like

The `TemplateAgent` fallback produces structurally correct but less personalized emails. To get AI-generated emails:
1. Ensure at least one AI key is set in `.env` (Groq is free and fast)
2. Run `python main.py status` and verify the AI provider shows **READY**
3. Check your API key is not expired or rate-limited

### `python main.py preview` hangs

This usually means the web scraper is waiting on a slow website. Set `REQUEST_TIMEOUT=10` in `.env` to fail faster. The pipeline will still generate emails using whatever data it collected before the timeout.

### Tests failing

```bash
pytest tests/ -v --tb=short
```

Tests mock all external APIs using `responses` and `pytest-mock`, so they should pass without real API keys. If tests fail, ensure you have the latest dependencies:

```bash
pip install -r requirements.txt --upgrade
```
