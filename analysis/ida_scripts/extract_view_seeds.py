#!/usr/bin/env python3
"""Extract all view system functions as seeds."""
import re
import json

content = open('../../registry/functions.yaml', 'r', encoding='utf-8').read()

# Find all view functions
pattern = r'-\s+address:\s+(0x[0-9a-fA-F]+)\s+name:\s+([^\n]+)\s+system:\s+view'
matches = re.findall(pattern, content)

seeds = {}
for addr, name in matches:
    seeds[name.strip()] = addr

print(f"Found {len(seeds)} view seed functions")

# Write seeds file
with open('../view_seeds.json', 'w') as f:
    json.dump(seeds, f, indent=2)

print(f"Wrote view_seeds.json")
print(f"\nAll view seeds:")
for i, (name, addr) in enumerate(sorted(seeds.items(), key=lambda x: int(x[1], 16))):
    print(f"  {i+1:2}. {addr}: {name}")
