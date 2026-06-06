import glob
for f in glob.glob('src/agents/*_agent.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    start_idx = content.find('COMPANY_ANALYSIS_PROMPT.format(')
    if start_idx != -1 and 'industry=' not in content[start_idx:start_idx+500]:
        content = content.replace(
            'company_name=company_name,',
            'company_name=company_name,\n            industry="Technology",'
        )
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Patched {f}')
