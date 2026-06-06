"""
Prompt templates for AI-driven outreach email generation.

All templates use Python str.format() / f-string compatible
``{placeholder}`` syntax. They are designed to be passed directly to
an LLM (e.g. OpenAI or Gemini) to produce personalised cold-outreach
content.

Usage
-----
>>> from src.prompts.outreach_prompts import EMAIL_GENERATION_PROMPT
>>> prompt = EMAIL_GENERATION_PROMPT.format(
...     contact_name="Jane Doe",
...     contact_title="CTO",
...     company_name="Acme Corp",
...     industry="FinTech",
...     pain_points="Legacy infrastructure limits deployment velocity",
...     opportunities="AI-assisted CI/CD could cut release cycles by 40 %",
...     sender_name="Vaibhav",
...     sender_product="AgentForge",
...     cta="15-minute call this week",
... )
"""

from typing import Dict

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = """\
You are an elite B2B outreach specialist and copywriter with deep expertise in \
crafting personalised cold-email campaigns that convert. You have written \
thousands of emails for SaaS, AI, and developer-tools companies with open rates \
above 40 % and reply rates above 12 %.

Your guiding principles:
1. **Hyper-personalisation** – every sentence should feel like it was written \
exclusively for this one recipient. Reference specific details about their company, \
role, or public initiatives.
2. **Value first** – lead with a concrete insight or observed pain point, never \
with a product pitch.
3. **Brevity** – keep emails under 150 words. Busy executives do not read long \
emails.
4. **Soft CTA** – end with a single, low-friction call to action (e.g. a question, \
a short calendar link request).
5. **Human tone** – write like a thoughtful peer, not a salesperson. Avoid corporate \
buzzwords, emoji, and exclamation marks.
6. **No fluff** – eliminate filler phrases like "I hope this email finds you well" \
or "I wanted to reach out".

Always respond in the exact output format requested. Do not include meta-commentary \
or explanations outside the requested output structure.
"""

# ---------------------------------------------------------------------------
# Company analysis prompt
# ---------------------------------------------------------------------------

COMPANY_ANALYSIS_PROMPT: str = """\
You are a business analyst specialising in technology companies. Analyse the \
scraped website content for **{company_name}** (industry: **{industry}**) and \
produce a structured intelligence report.

=== SCRAPED CONTENT ===

**Homepage:**
{homepage_text}

**About Page:**
{about_text}

**Services / Products Page:**
{services_text}

**Careers Page:**
{careers_text}

=== INSTRUCTIONS ===

Based solely on the content above, return your response in this exact format (no extra text or markdown):

PAIN_POINTS:
- <pain point 1>
- <pain point 2>
OPPORTUNITIES:
- <opportunity 1>
- <opportunity 2>
HIRING_SIGNALS:
- <signal 1>
GROWTH_SIGNALS:
- <signal 1>
"""

# ---------------------------------------------------------------------------
# Email generation prompt
# ---------------------------------------------------------------------------

EMAIL_GENERATION_PROMPT: str = """\
You are writing a personalised cold-outreach email on behalf of **{sender_name}**, \
who is introducing **{sender_product}** to a prospect.

=== PROSPECT CONTEXT ===
- Name: {contact_name}
- Title: {contact_title}
- Company: {company_name}
- Industry: {industry}
- Key pain points: {pain_points}
- Key opportunities: {opportunities}

=== PRODUCT CONTEXT ===
Product/Service being pitched: **{sender_product}**
Desired call-to-action: {cta}

=== INSTRUCTIONS ===

Write a cold-outreach email that:
1. Opens with a hyper-specific observation about {company_name} or {contact_name}'s \
   work (NOT a compliment – an insight).
2. Bridges that observation to one concrete pain point from the list above.
3. In one sentence, explains how {sender_product} addresses that pain point with \
   a measurable outcome or specific mechanism.
4. Ends with the CTA: "{cta}".
5. Is between 80 and 140 words total (excluding subject line).
6. Sounds human, peer-to-peer, and confident – not salesy.

Return your response in this exact format (no extra text):

SUBJECT: <subject line>
PREVIEW: <short preview under 100 chars>
BODY:
<email body>
"""

# ---------------------------------------------------------------------------
# Subject line prompt
# ---------------------------------------------------------------------------

SUBJECT_LINE_PROMPT: str = """\
You are a cold-email subject-line specialist. Your subject lines achieve \
open rates above 45 % because they are curious, specific, and never \
sound like marketing.

=== EMAIL BODY ===
{email_body}

=== RECIPIENT CONTEXT ===
- Name: {contact_name}
- Title: {contact_title}
- Company: {company_name}
- Industry: {industry}
- Main pain point: {pain_point}

=== INSTRUCTIONS ===

Generate exactly **3** subject line options for the email above.

Rules:
- Each subject line must be under 50 characters.
- Do NOT use the words "intro", "partnership", "synergy", "leverage", \
  "touching base", "following up", "quick question", or "opportunity".
- At least one subject line must reference something specific about {company_name}.
- At least one subject line must hint at a measurable outcome or risk.
- None should use emoji or punctuation other than a single comma or dash.

Return only a JSON array of 3 strings. Example:
["Subject line one", "Subject line two", "Subject line three"]
"""

# ---------------------------------------------------------------------------
# Follow-up prompt
# ---------------------------------------------------------------------------

FOLLOW_UP_PROMPT: str = """\
You are a cold-email follow-up specialist. You write follow-up emails that \
feel natural, add new value, and never feel pushy or desperate.

=== ORIGINAL EMAIL ===
Subject: {original_subject}

=== RECIPIENT CONTEXT ===
- Name: {contact_name}
- Company: {company_name}
- Days since original email was sent: {days_since_first}

=== INSTRUCTIONS ===

Write a **2-email follow-up sequence**. Each follow-up should:
- Reference the previous email without copying it.
- Add a new piece of value, data point, relevant case study, or different angle.
- Be shorter than the original (under 80 words each).
- Use a different hook / opening than the original.
- End with a gentle CTA (a different one each time).

Return your response in this exact format:

FOLLOW_UP_1_SUBJECT: <subject line for follow-up 1>
FOLLOW_UP_1_DAYS: <number of days after original to send>
---
<follow-up 1 body>
===
FOLLOW_UP_2_SUBJECT: <subject line for follow-up 2>
FOLLOW_UP_2_DAYS: <number of days after original to send>
---
<follow-up 2 body>
"""

# ---------------------------------------------------------------------------
# Sender products registry
# ---------------------------------------------------------------------------

SENDER_PRODUCTS: Dict[str, Dict[str, str]] = {
    "deknek": {
        "name": "DekNek",
        "tagline": "AI-powered deck and pitch builder for founders and sales teams",
        "description": (
            "DekNek turns raw notes, briefs, or bullet points into polished "
            "investor decks and sales presentations in minutes. It uses GPT-4 "
            "to structure narrative flow, generate slide content, and apply "
            "professional design templates – cutting deck creation time from "
            "days to under an hour."
        ),
        "ideal_customer": (
            "Early-stage founders preparing investor pitch decks, "
            "sales teams that need customised proposal decks at scale, "
            "and consultancies producing client deliverables."
        ),
        "key_outcomes": [
            "10× faster deck creation",
            "Consistent on-brand slides across the team",
            "Higher close rates with data-backed story structures",
        ],
        "cta_default": "Would a 15-minute demo make sense this week?",
    },
    "jobby_ai": {
        "name": "Jobby AI",
        "tagline": "AI copilot that automates high-volume hiring workflows",
        "description": (
            "Jobby AI plugs into existing ATS platforms and automates resume "
            "screening, interview scheduling, and candidate communication. It "
            "uses fine-tuned LLMs to rank candidates against role-specific "
            "rubrics, reducing time-to-hire by up to 60 % while improving "
            "quality-of-hire scores."
        ),
        "ideal_customer": (
            "HR and talent acquisition teams at companies hiring 20+ roles "
            "per quarter, staffing agencies, and fast-growing startups that "
            "cannot afford a large recruiting team."
        ),
        "key_outcomes": [
            "60 % reduction in time-to-hire",
            "80 % less manual screening effort",
            "Bias-reduced shortlisting via structured rubrics",
        ],
        "cta_default": "Happy to show you a live workflow – does Thursday work?",
    },
    "agentforge": {
        "name": "AgentForge",
        "tagline": "No-code platform for building and deploying AI agents",
        "description": (
            "AgentForge lets engineering and product teams visually compose "
            "multi-step AI agent workflows without writing infrastructure code. "
            "It includes a library of pre-built tool integrations (Slack, "
            "Notion, GitHub, Salesforce, etc.), an agent orchestration runtime, "
            "and a one-click deployment pipeline to any cloud."
        ),
        "ideal_customer": (
            "Product and engineering teams at mid-market SaaS companies looking "
            "to automate internal operations or build AI-native product features "
            "without months of custom development."
        ),
        "key_outcomes": [
            "Ship AI agent features in days, not months",
            "Reduce engineering overhead with reusable tool blocks",
            "Production-ready agents with built-in monitoring and retries",
        ],
        "cta_default": "Want to see a 10-minute build walkthrough?",
    },
    "mindrag": {
        "name": "MindRAG",
        "tagline": "Retrieval-augmented generation engine for enterprise knowledge bases",
        "description": (
            "MindRAG connects to a company's existing documents, wikis, PDFs, "
            "and databases to build a semantically searchable knowledge layer. "
            "Teams can then query that knowledge via a chat interface or API, "
            "getting cited, accurate answers grounded in internal data – not "
            "hallucinated general knowledge."
        ),
        "ideal_customer": (
            "Operations, legal, compliance, and customer support teams at "
            "mid-to-enterprise companies with large unstructured document "
            "repositories that are difficult to search or surface insights from."
        ),
        "key_outcomes": [
            "90 % reduction in time spent searching internal docs",
            "Cited, auditable answers for compliance-sensitive workflows",
            "Zero hallucination risk – answers are grounded in your own data",
        ],
        "cta_default": "Could I show you a 10-minute proof-of-concept on your own docs?",
    },
}
