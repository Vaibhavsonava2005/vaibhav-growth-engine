# 🚀 Deployment Guide — Vaibhav Growth Engine

> **Author:** Vaibhav Sonava | [github.com/Vaibhavsonava2005](https://github.com/Vaibhavsonava2005)  
> **Stack:** Python CLI · Next.js Dashboard · Vercel Hosting

---

## Table of Contents

1. [Local Development](#1-local-development)
2. [Vercel Deployment (Dashboard)](#2-vercel-deployment-dashboard)
3. [GitHub Setup](#3-github-setup)
4. [Vercel CLI Deploy](#4-vercel-cli-deploy)
5. [Environment Variables Reference](#5-environment-variables-reference)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

---

### 1.1 Python CLI Setup

```bash
# Clone or enter the project directory
cd vaibhav-growth-engine

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and fill in your keys
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux

# Run the growth engine pipeline
python main.py
```

---

### 1.2 Dashboard Dev Server

```bash
# Navigate to dashboard directory
cd dashboard

# Install Node dependencies
npm install

# Start development server (hot reload enabled)
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

### 1.3 FastAPI Backend (Optional Local API)

> **Note:** The FastAPI backend is for local use only. On Vercel, API routes are handled by Next.js serverless functions.

```bash
# From project root (with venv activated)
uvicorn api.main:app --reload --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 2. Vercel Deployment (Dashboard)

### Prerequisites

- A [GitHub](https://github.com) account
- A [Vercel](https://vercel.com) account (free tier is sufficient)
- Repository pushed to GitHub (see [Section 3](#3-github-setup))

---

### 2.1 Import Repository to Vercel

1. Log in to [vercel.com](https://vercel.com)
2. Click **"Add New… → Project"**
3. Under **"Import Git Repository"**, select your GitHub account
4. Find and select **`vaibhav-growth-engine`**
5. Click **"Import"**

---

### 2.2 Configure the Project

Vercel will auto-detect the `vercel.json` settings. Verify the following on the configuration screen:

| Setting | Value |
|---|---|
| **Framework Preset** | Next.js |
| **Root Directory** | `dashboard` |
| **Build Command** | `npm run build` |
| **Output Directory** | `.next` |
| **Install Command** | `npm install` |

---

### 2.3 Set Environment Variables

In the Vercel project configuration screen, expand **"Environment Variables"** and add:

| Variable | Value | Required |
|---|---|---|
| `NEXT_PUBLIC_APP_NAME` | `Vaibhav Growth Engine` | Yes |
| `NEXT_PUBLIC_GITHUB` | `https://github.com/Vaibhavsonava2005` | Yes |

> These are already set in `vercel.json`. Add any additional secrets (API keys) here if your Next.js API routes need them — they will **not** be exposed to the browser.

---

### 2.4 Deploy

Click **"Deploy"**. Vercel will:

1. Clone your repository
2. Run `npm install` inside `dashboard/`
3. Run `npm run build`
4. Publish the `.next` output to the global CDN

Your dashboard will be live at:  
`https://vaibhav-growth-engine.vercel.app` (or a custom domain)

---

### 2.5 Auto-Deploy on Push

Every `git push` to the `main` branch automatically triggers a new production deployment. Pull requests get their own **preview URLs** automatically.

```
main branch push → Production deployment
PR opened        → Preview deployment (unique URL per PR)
```

---

### 2.6 Custom Domain (Optional)

1. In your Vercel project, go to **Settings → Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `growth.vaibhav.dev`)
4. Follow the DNS configuration instructions shown by Vercel
5. Vercel provisions an SSL certificate automatically

---

## 3. GitHub Setup

### 3.1 Initialize and Push Repository

```bash
# From the project root
git init
git add .
git commit -m "Initial commit: Vaibhav Growth Engine v1.0.0"

# Create the remote repository on GitHub first, then:
git remote add origin https://github.com/Vaibhavsonava2005/vaibhav-growth-engine.git
git branch -M main
git push -u origin main
```

### 3.2 Recommended .gitignore entries

Ensure the following are in your `.gitignore`:

```
# Secrets — NEVER commit these
.env
*.env

# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# Next.js
dashboard/.next/
dashboard/node_modules/
dashboard/out/

# Logs & output
logs/
*.log
output/
data/leads_*.json
data/emails_*.json
```

---

## 4. Vercel CLI Deploy

For faster iterations, deploy directly from your terminal:

```bash
# Install Vercel CLI globally
npm i -g vercel

# Authenticate (one-time setup)
vercel login

# Deploy to production from project root
vercel --prod
```

The CLI reads `vercel.json` automatically and deploys to your linked project.

---

## 5. Environment Variables Reference

### Where to Set Each Variable

| Variable | Local (`.env`) | Vercel Dashboard | Notes |
|---|:---:|:---:|---|
| `APOLLO_API_KEY` | ✅ | ❌ | CLI only |
| `HUNTER_API_KEY` | ✅ | ❌ | CLI only |
| `PROSPEO_API_KEY` | ✅ | ❌ | CLI only |
| `BREVO_API_KEY` | ✅ | ❌ | CLI only |
| `SENDER_EMAIL` | ✅ | ❌ | CLI only |
| `SENDER_NAME` | ✅ | ❌ | CLI only |
| `GEMINI_API_KEY` | ✅ | ⚠️ Optional | If used in Next.js API routes |
| `GROQ_API_KEY` | ✅ | ⚠️ Optional | If used in Next.js API routes |
| `OPENROUTER_API_KEY` | ✅ | ⚠️ Optional | If used in Next.js API routes |
| `NEXT_PUBLIC_APP_NAME` | ✅ | ✅ | Pre-set in vercel.json |
| `NEXT_PUBLIC_GITHUB` | ✅ | ✅ | Pre-set in vercel.json |
| `MAX_COMPANIES` | ✅ | ❌ | CLI pipeline config |
| `MAX_CONTACTS_PER_COMPANY` | ✅ | ❌ | CLI pipeline config |
| `MAX_RETRIES` | ✅ | ❌ | CLI pipeline config |
| `REQUEST_TIMEOUT` | ✅ | ❌ | CLI pipeline config |
| `DRY_RUN` | ✅ | ❌ | CLI pipeline config |
| `LOG_LEVEL` | ✅ | ❌ | CLI pipeline config |

> **`NEXT_PUBLIC_*` variables** are embedded into the browser bundle — never put secrets in them.

---

## 6. Troubleshooting

### ❌ Build fails: "Cannot find module"

**Cause:** Missing Node dependencies.  
**Fix:**
```bash
cd dashboard
rm -rf node_modules package-lock.json
npm install
```

---

### ❌ Build fails: "rootDirectory not found"

**Cause:** Vercel can't find the `dashboard` directory.  
**Fix:** Ensure `rootDirectory: "dashboard"` is set in `vercel.json` and that `dashboard/package.json` exists.

---

### ❌ Environment variable not available at runtime

**Cause:** Secret added locally but not in Vercel dashboard.  
**Fix:** Go to **Vercel → Project → Settings → Environment Variables** and add the missing variable. Then redeploy:
```bash
vercel --prod
```

---

### ❌ Python CLI: "ModuleNotFoundError"

**Cause:** Virtual environment not activated, or dependencies not installed.  
**Fix:**
```bash
# Activate venv first
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# Reinstall requirements
pip install -r requirements.txt
```

---

### ❌ Emails not sending (Brevo)

**Cause:** Sender email not verified in Brevo, or wrong API key.  
**Fix:**
1. Log in to [app.brevo.com](https://app.brevo.com)
2. Go to **Senders & IP** → verify your sender email
3. Confirm `BREVO_API_KEY` in `.env` matches your Brevo API key
4. Set `DRY_RUN=True` to test without sending real emails

---

### ❌ 404 on Vercel deployment

**Cause:** Output directory misconfigured.  
**Fix:** Confirm `outputDirectory` in `vercel.json` is `.next` (relative to `rootDirectory: "dashboard"`).

---

### ❌ `git push` rejected

**Cause:** Remote already has commits (e.g., initialized with a README on GitHub).  
**Fix:**
```bash
git pull origin main --rebase
git push -u origin main
```

---

## Quick Reference

```
Local CLI:         python main.py
Local Dashboard:   cd dashboard && npm run dev  →  localhost:3000
Local API:         uvicorn api.main:app --reload  →  localhost:8000/docs
Deploy Dashboard:  vercel --prod
GitHub push:       git push origin main  (auto-deploys via Vercel)
```

---

*Last updated: June 2026 · Vaibhav Growth Engine v1.0.0*
