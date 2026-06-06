import re

with open('src/prompts/outreach_prompts.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace COMPANY_ANALYSIS_PROMPT JSON instruction
old_json_instruction = r'''Based solely on the content above, return a JSON object with these exact keys:

\{
  "company_summary": "<2-3 sentence summary of what the company does and who it serves>",
  "core_products_services": \["<product or service 1>", "<product or service 2>", ...\],
  "target_customers": "<who they sell to>",
  "growth_signals": \["<signal 1 indicating growth or investment>", ...\],
  "tech_stack_hints": \["<inferred technology or stack hint>", ...\],
  "hiring_signals": \["<role or department they are actively hiring for>", ...\],
  "pain_points": \[
    "<specific operational, technical, or business pain point observable from the content>",
    ...
  \],
  "opportunities": \[
    "<specific opportunity where an external product or service could add value>",
    ...
  \],
  "tone_and_culture": "<professional tone of the company: formal / startup / technical / creative>",
  "recommended_angle": "<the single strongest angle for a cold-email outreach – one sentence>"
\}

Rules:
- Be specific; avoid generic platitudes.
- If a section of content is empty or missing, infer from other sections or use \
  an empty list / "Unknown".
- Return only valid JSON. No markdown fences, no commentary.'''

new_format_instruction = '''Based solely on the content above, return your response in this exact format (no extra text or markdown):

PAIN_POINTS:
- <pain point 1>
- <pain point 2>
OPPORTUNITIES:
- <opportunity 1>
- <opportunity 2>
HIRING_SIGNALS:
- <signal 1>
GROWTH_SIGNALS:
- <signal 1>'''

content = re.sub(old_json_instruction, new_format_instruction, content, flags=re.MULTILINE)


# Replace EMAIL_GENERATION_PROMPT format instruction
old_email_instruction = r'''Return your response in this exact format (no extra text):

SUBJECT: <subject line>
---
<email body>'''

new_email_instruction = '''Return your response in this exact format (no extra text):

SUBJECT: <subject line>
PREVIEW: <short preview under 100 chars>
BODY:
<email body>'''

content = re.sub(old_email_instruction, new_email_instruction, content)

with open('src/prompts/outreach_prompts.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Prompts patched successfully.")
