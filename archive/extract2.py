import re
with open('src/AGENT.md', 'r') as f: text=f.read()
import os
for x in re.findall(r'# scripts/.*\.py', text):
    print(x)
for m in re.finditer(r'# (scripts/[0-9a-zA-Z_]+\.py)\n(.*?)```', text, re.DOTALL):
    name = m.group(1)
    with open(name, 'w') as out:
        out.write(m.group(0).replace('```', ''))
    print('Wrote', name)
for m in re.finditer(r'# (app\.py)\n(.*?)```', text, re.DOTALL):
    name = m.group(1)
    with open(name, 'w') as out:
        out.write(m.group(0).replace('```', ''))
    print('Wrote', name)
