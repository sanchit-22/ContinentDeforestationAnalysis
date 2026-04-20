import re
with open('src/AGENT.md', 'r') as f:
    text = f.read()

# Extract scripts
matches = re.finditer(r'```python\n# (scripts/[a-zA-Z0-9_]+\.py)\n(.*?)\n```', text, re.DOTALL)
for m in matches:
    name = m.group(1)
    code = m.group(2)
    with open(name, 'w') as out:
        out.write('# ' + name + '\n' + code + '\n')
    print('Wrote', name)

# Extract app.py
matches = re.finditer(r'```python\n# (app\.py)\n(.*?)\n```', text, re.DOTALL)
for m in matches:
    name = m.group(1)
    code = m.group(2)
    with open(name, 'w') as out:
        out.write('# ' + name + '\n' + code + '\n')
    print('Wrote', name)

