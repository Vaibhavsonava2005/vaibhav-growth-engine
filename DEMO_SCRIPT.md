# Demo Script — Vaibhav Growth Engine
## Explainer Video Recording Guide

**Total runtime:** ~9 minutes  
**Author:** Vaibhav Sonava — [github.com/Vaibhavsonava2005](https://github.com/Vaibhavsonava2005)  
**Recording setup:** Terminal maximized, font size 16+, PowerShell or Windows Terminal with UTF-8 support

---

## Pre-Recording Checklist

Before you hit record:

- [ ] All API keys configured in `.env` (Gemini + Groq + Hunter + Brevo at minimum)
- [ ] Virtual environment activated: `venv\Scripts\activate`
- [ ] Terminal font size set to 16 or larger (legible in video)
- [ ] Run `python main.py status` once beforehand to warm up — confirm all services show green
- [ ] Run `python main.py preview --domain hubspot.com --product "AgentForge"` once beforehand to confirm it generates emails (warm up any rate limits)
- [ ] Dashboard running: `cd api && uvicorn main:app --reload` + `cd dashboard && npm run dev`
- [ ] Browser open at `http://localhost:3000`
- [ ] Screen recording software ready (OBS, Loom, etc.)

---

## Segment 1 — Opening (30 seconds)

**What to say:**

> "This is the Vaibhav Growth Engine — a B2B outreach automation system I built that takes a company domain, discovers decision-makers at similar companies, researches those companies using AI, and writes hyper-personalized cold emails — then sends them through Brevo's transactional API.
>
> The whole thing runs from the terminal. Let me show you."

**What to show on screen:**
- Your code editor with `main.py` open briefly — just to establish that this is real code
- Then switch to the terminal

**Tip:** Keep this tight. Viewers want to see the demo, not hear a long intro.

---

## Segment 2 — Integration Health Check (2 minutes)

**What to type:**

```bash
python main.py status
```

**What to say while it runs:**

> "First — let me check that all integrations are healthy. The `status` command queries the AIRouter and checks every external service for a configured API key."

**Wait for output, then walk through the tables:**

> "Here you can see my AI providers: Gemini is my primary — it's Google's latest flash model. Groq is the secondary, using Llama 3.3 70B — it's insanely fast, sub-second inference. OpenRouter is the tertiary fallback. And Template is the guaranteed last resort — even if every AI provider goes down, the engine still produces structured outreach emails.
>
> Below that — external services. Hunter.io for email discovery and verification. Prospeo for contact enrichment. Brevo for email delivery. Apollo for company and people search.
>
> And the pipeline configuration: max 10 companies per run, up to 3 contacts per company, 3 retries on failed API calls."

**Pause on the green status table for 3–4 seconds so viewers can read it.**

> "Everything is green. We're ready to run a campaign."

---

## Segment 3 — Email Preview (3 minutes)

**What to type:**

```bash
python main.py preview --domain hubspot.com --product "AgentForge"
```

**What to say as the progress bars run:**

> "I'm targeting HubSpot's domain. The `preview` command runs the full pipeline — company discovery, contact enrichment, web scraping, AI analysis, and email generation — but doesn't send anything. Think of it as a dry run that shows you exactly what would go out.
>
> Watch the progress steps: discovering companies in the same industry as HubSpot, finding decision-makers via Hunter domain search, verifying email addresses, scraping company websites for pain points and growth signals, then generating personalized emails via Gemini."

**When the email drafts render:**

> "Here's the first draft. You can see: the recipient — their name and verified email address. The subject line — Gemini wrote this based on the company's specific context. The personalization score — this one is 76 out of 100. And the AI provider that generated it.
>
> And here's the full email body. Notice it's not a generic template — it references [read a specific detail from the actual output, e.g., 'HubSpot's recent expansion into AI-powered CRM']. That came from the web scraper and the AI analysis step."

**Scroll through 2–3 drafts.**

> "Each email is unique — different pain points, different opening hooks — because the AI analyzed each company's website separately.
>
> This is what I'd use for real outreach for AgentForge — or Jobby AI, or any product I'm pitching to SaaS companies."

---

## Segment 4 — Full Campaign with Safety Checkpoint (2 minutes)

> **Note:** Record this segment with `--dry-run` so you don't actually send emails during the recording. The safety checkpoint behavior is identical.

**What to type:**

```bash
python main.py run --domain stripe.com --product "MindRAG" --dry-run
```

**What to say:**

> "Now let me show the full campaign flow. I'm targeting Stripe's industry — so the engine will find companies similar to Stripe and reach out on behalf of MindRAG.
>
> I'm using `--dry-run` here — which means the pipeline runs completely, including the safety checkpoint, but Brevo doesn't dispatch anything."

**When the safety checkpoint appears:**

> "Here's the mandatory safety checkpoint. Before any email is sent, the engine stops and shows you exactly what's queued: four companies found, nine decision-makers, seven verified emails ready. The AI provider it used. The mode — dry-run in this case.
>
> You have to type 'y' to proceed. The default is 'N' — so if I just hit Enter right now, the campaign is cancelled. This is deliberate. I never want a typo to trigger a real send."

**Type `y` to confirm, then show the summary card.**

> "And here's the campaign summary: companies discovered, contacts found, emails generated — and since this is dry-run, emails sent is zero. In live mode, that number would show the actual Brevo delivery count.
>
> The campaign is automatically saved to the local CRM."

---

## Segment 5 — Dashboard Walkthrough (2 minutes)

**Switch to browser at `http://localhost:3000`**

**What to say:**

> "The web dashboard gives you a visual interface over the same data the CLI writes. Let me walk through it."

**Walk through each section:**

**Leads table:**
> "This is the prospect table — every contact the engine has ever enriched, across all campaigns. Name, title, company, email, status, which campaign they were part of. You can filter by domain or campaign."

**Integration health panel:**
> "The health panel mirrors what `python main.py status` shows in the terminal — but you can leave this browser tab open as a live reference."

**Analytics / metrics:**
> "Analytics pulls open rates, click rates, reply rates, and bounce rates from Brevo's reporting. Aggregate view at the top, per-campaign breakdown below. Industry benchmarks are shown alongside for context — 20–30% open rate is typical for cold B2B, 1–3% reply rate."

**Campaign history:**
> "Campaign history shows every run: domain, campaign name, number of emails sent, status, timestamp. You can see the dry-run campaigns I just ran show up here too — nothing is lost."

---

## Segment 6 — CSV Export (1 minute)

**Switch back to terminal.**

**What to type:**

```bash
python main.py export --domain hubspot.com
```

**What to say:**

> "One command exports all prospect data for a domain to CSV — ready to import into a spreadsheet, a proper CRM like HubSpot or Notion, or pass to a sales team."

**Show the output file path printed in the terminal.**

> "The CSV includes contact name, title, company, email, personalization score, campaign ID, and sent timestamp. Everything you'd need to track follow-ups manually or in another tool."

---

## Segment 7 — Closing (30 seconds)

**Stay on the terminal or switch to a split view showing code + terminal.**

**What to say:**

> "So that's the Vaibhav Growth Engine: automated lead discovery via Apollo and Hunter, AI-personalized outreach via Gemini and Groq, safe delivery via Brevo — all from a single command.
>
> I built this for real use — to run outreach for DekNek, Jobby AI, AgentForge, and MindRAG. The pipeline is production-ready: retry logic on every API call, graceful fallbacks at every step, a mandatory safety checkpoint before any email goes out.
>
> All the code is on GitHub at github.com/Vaibhavsonava2005. Thanks for watching."

---

## Recording Tips

- **Keep your hands off the keyboard** while the progress bars are animating — let viewers read the output
- **Read actual output values** from your terminal rather than scripted numbers — it sounds more natural and is more credible
- **Pause after each command** for 1–2 seconds before speaking — gives viewers time to process what appeared
- **If something fails during recording** — stop, fix the issue (usually an API key or rate limit), and re-record that segment; don't try to talk around errors
- **Font size:** Aim for 16px minimum in your terminal so text is legible at 1080p
- **Resolution:** Record at 1920×1080 minimum
- **Microphone:** Use a headset or dedicated mic — built-in laptop mics pick up too much ambient noise

---

## Fallback Commands (if live APIs fail during recording)

If Hunter or Apollo rate limits kick in mid-recording, these flags help:

```bash
# Increase timeout for slow API responses
REQUEST_TIMEOUT=60 python main.py preview --domain hubspot.com --product "AgentForge"

# Use a less-popular domain that Hunter is more likely to return results for
python main.py preview --domain salesforce.com --product "AgentForge"

# Force template fallback (skips all AI providers — fastest, always works)
GEMINI_API_KEY="" GROQ_API_KEY="" OPENROUTER_API_KEY="" python main.py preview --domain stripe.com --product "DekNek"
```
