import glob
for f in glob.glob('src/agents/*_agent.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if 'EMAIL_GENERATION_PROMPT.format(' in content and 'cta=' not in content:
        content = content.replace(
            'sender_name=settings.SENDER_NAME,',
            'sender_name=settings.SENDER_NAME,\n            cta="Would you be open to a brief chat?",'
        )
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Patched {f}')
