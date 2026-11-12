"""Show actual call instructions from view_projection."""
import json

with open('view_projection_detailed.json') as f:
    data = json.load(f)

print("=" * 80)
print("CALL INSTRUCTIONS IN view_projection")
print("=" * 80)

# Find call instructions in disassembly
for inst in data['disassembly']:
    if 'call' in inst['instruction'].lower():
        print(f"{inst['address']}: {inst['instruction']}")
