import re

with open('src/AGENT.md', 'r') as f:
    text = f.read()

# Extract script blocks
# We know the specific names for Phase 9
for m in re.finditer(r'```python\n# (scripts/09_prepare_map_tiles\.py)\n(.*?)\n```', text, re.DOTALL):
    with open(m.group(1), 'w') as out:
        out.write('# ' + m.group(1) + '\n' + m.group(2) + '\n')
    print('Wrote', m.group(1))

for m in re.finditer(r'```python\n# (map_component\.py)\n(.*?)\n```', text, re.DOTALL):
    with open(m.group(1), 'w') as out:
        out.write('# ' + m.group(1) + '\n' + m.group(2) + '\n')
    print('Wrote', m.group(1))

for m in re.finditer(r'```python\n# (scripts/09_verify_tiles\.py)\n(.*?)\n```', text, re.DOTALL):
    with open(m.group(1), 'w') as out:
        out.write('# ' + m.group(1) + '\n' + m.group(2) + '\n')
    print('Wrote', m.group(1))
