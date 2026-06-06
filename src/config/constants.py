"""
constants.py
------------
Application-wide constants for VAIBHAV GROWTH ENGINE.

Centralising these values in one place makes it trivial to tune scoring
weights, add new industries, expand keyword dictionaries, or modify
outreach templates without hunting through multiple files.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME: str = "VAIBHAV GROWTH ENGINE"
APP_VERSION: str = "1.0.0"
APP_AUTHOR: str = "Vaibhav Sonava"
APP_GITHUB: str = "https://github.com/Vaibhavsonava2005"

# ---------------------------------------------------------------------------
# Decision-maker titles to target during contact discovery
# ---------------------------------------------------------------------------
DECISION_MAKER_TITLES: list[str] = [
    "CEO",
    "CTO",
    "Co-Founder",
    "Founder",
    "VP Engineering",
    "VP Product",
    "VP Sales",
    "Head of Growth",
    "Director of Engineering",
    "Director of Product",
    "Chief Technology Officer",
    "Chief Executive Officer",
    "Head of Product",
    "VP of Engineering",
    "Engineering Manager",
    "Product Manager",
    "Chief Product Officer",
    "Chief Operating Officer",
    "VP of Product",
    "VP of Sales",
    "Head of Engineering",
    "Technical Co-Founder",
    "Managing Director",
    "General Manager",
    "President",
]

# ---------------------------------------------------------------------------
# Major B2B tech industries to target
# ---------------------------------------------------------------------------
INDUSTRIES: list[str] = [
    "Software as a Service (SaaS)",
    "Artificial Intelligence & Machine Learning",
    "FinTech",
    "HealthTech",
    "EdTech",
    "PropTech",
    "LegalTech",
    "HRTech",
    "MarTech",
    "AdTech",
    "Cybersecurity",
    "Cloud Computing",
    "DevOps & Platform Engineering",
    "Data Analytics & Business Intelligence",
    "E-Commerce & Retail Tech",
    "Supply Chain & Logistics Tech",
    "InsurTech",
    "RegTech",
    "IoT & Connected Devices",
    "Blockchain & Web3",
    "Digital Media & Content Tech",
    "Sales Enablement",
    "Customer Success & CX Platforms",
    "Automation & RPA",
    "Enterprise Software",
]

# ---------------------------------------------------------------------------
# Company size → scoring weight mapping
# Used to prioritise outreach: larger weight = higher priority
# ---------------------------------------------------------------------------
COMPANY_SIZE_MAP: dict[str, float] = {
    "1-10": 0.4,
    "11-50": 0.7,
    "51-200": 1.0,
    "201-500": 0.9,
    "501-1000": 0.75,
    "1001-5000": 0.6,
    "5001-10000": 0.4,
    "10001+": 0.2,
}

# ---------------------------------------------------------------------------
# Pain-point keywords (used to score and categorise prospect pain signals)
# ---------------------------------------------------------------------------
PAIN_POINTS_KEYWORDS: dict[str, list[str]] = {
    "ai_adoption": [
        "ai integration",
        "machine learning",
        "llm",
        "generative ai",
        "chatgpt",
        "openai",
        "ai-powered",
        "natural language processing",
        "nlp",
        "computer vision",
        "ai strategy",
        "ai roadmap",
        "adopting ai",
        "ai implementation",
    ],
    "automation": [
        "manual process",
        "repetitive tasks",
        "workflow automation",
        "rpa",
        "robotic process automation",
        "process improvement",
        "efficiency",
        "bottleneck",
        "slow pipeline",
        "operational overhead",
        "automate",
        "no-code automation",
        "low-code",
        "zapier",
        "n8n",
        "make.com",
    ],
    "scaling": [
        "scaling issues",
        "growth challenges",
        "series a",
        "series b",
        "hypergrowth",
        "rapid expansion",
        "hiring engineers",
        "scaling team",
        "technical debt",
        "infrastructure scaling",
        "load balancing",
        "distributed systems",
        "microservices migration",
    ],
    "web_development": [
        "legacy system",
        "outdated website",
        "slow website",
        "poor ux",
        "redesign",
        "replatform",
        "mobile-first",
        "web app",
        "saas product",
        "frontend performance",
        "core web vitals",
        "nextjs",
        "react",
        "vue",
        "angular",
        "full-stack development",
    ],
    "cloud": [
        "cloud migration",
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "serverless",
        "cost optimisation",
        "cloud cost",
        "multi-cloud",
        "hybrid cloud",
        "cloud security",
        "devops",
        "cicd",
        "infrastructure as code",
        "terraform",
    ],
}

# ---------------------------------------------------------------------------
# Opportunity keywords – signals that a company is ripe for outreach
# ---------------------------------------------------------------------------
OPPORTUNITY_KEYWORDS: list[str] = [
    "recently funded",
    "series a",
    "series b",
    "seed round",
    "pre-seed",
    "launched",
    "new product",
    "expanding",
    "hiring",
    "growing team",
    "digital transformation",
    "modernisation",
    "revamp",
    "new cto",
    "new vp engineering",
    "open source",
    "product launch",
    "beta launch",
    "waitlist",
    "early access",
    "pivot",
    "rebranding",
    "acquisition",
    "partnership",
    "integrations",
    "platform upgrade",
    "new market",
    "international expansion",
]

# ---------------------------------------------------------------------------
# Outreach campaign templates
# Placeholders: {name}, {company}, {pain_point}, {opportunity}, {product}
# ---------------------------------------------------------------------------
CAMPAIGN_TEMPLATES: dict[str, list[str]] = {
    "subject_lines": [
        "Quick question for {name} at {company}",
        "Helping {company} with {pain_point}",
        "{name}, saw your {opportunity} — had to reach out",
        "3 ways {product} could accelerate {company}'s growth",
        "{company} + {product} — worth a 15-min chat?",
        "Congrats on {opportunity}, {name} — here's an idea",
        "How we helped a company like {company} solve {pain_point}",
        "The fastest way {company} can tackle {pain_point}",
        "{name}, is {pain_point} slowing {company} down?",
        "An idea for {company} from Vaibhav",
    ],
    "openings": [
        "Hi {name}, I came across {company} and was impressed by {opportunity}.",
        "Hey {name}, I noticed {company} is working through {pain_point} — something we see a lot.",
        "Hi {name}, congrats on the {opportunity} at {company}! Exciting milestone.",
        "Hello {name}, a colleague mentioned {company}'s work and I had to reach out.",
        "Hey {name}, I've been following {company}'s journey and love what you're building.",
        "Hi {name}, I came across {company} while researching teams tackling {pain_point}.",
        "Hello {name}, I work with companies at {company}'s stage to solve exactly {pain_point}.",
        "Hi {name}, saw {company}'s {opportunity} and thought of a few ideas that might help.",
    ],
    "value_props": [
        "{product} helps teams like {company} eliminate {pain_point} in days, not months.",
        "We've helped similar companies reduce {pain_point} by up to 60% using {product}.",
        "{product} integrates with your existing stack and directly addresses {pain_point}.",
        "With {product}, {company} can turn {pain_point} into a competitive advantage.",
        "Our clients use {product} to automate {pain_point}, freeing engineers for higher-value work.",
        "{product} is purpose-built for companies experiencing {pain_point} at your scale.",
        "Teams like yours use {product} to go from {pain_point} to smooth operations in weeks.",
        "Instead of fighting {pain_point}, {company} can leverage {product} to leapfrog competitors.",
    ],
    "ctas": [
        "Would you be open to a 15-minute call this week to explore if {product} is a fit?",
        "Happy to send over a quick case study — would that be useful, {name}?",
        "Can I grab 20 minutes on your calendar to walk through how {product} could help {company}?",
        "Would it make sense to connect for a no-pressure demo of {product}?",
        "Are you the right person at {company} to chat about {pain_point}, or should I reach out to someone else?",
        "I'd love to share a few ideas tailored to {company} — keen for a quick call?",
        "If {pain_point} is on your radar, a 15-min chat could be well worth it. Interested?",
        "Want me to put together a short personalised plan for {company} based on {opportunity}?",
    ],
}
