#!/usr/bin/env python3
"""Extract HUD system functions as seeds."""
import re
import json

content = open('../../registry/functions.yaml', 'r', encoding='utf-8').read()

# Find all HUD functions
pattern = r'-\s+address:\s+(0x[0-9a-fA-F]+)\s+name:\s+([^\n]+)\s+system:\s+hud'
matches = re.findall(pattern, content)

seeds = {}
for addr, name in matches:
    seeds[name.strip()] = addr

print(f"Found {len(seeds)} HUD seed functions")

# Write seeds file
with open('../hud_seeds.json', 'w') as f:
    json.dump(seeds, f, indent=2)

print(f"Wrote hud_seeds.json")
print(f"\nAll HUD seeds:")
for i, (name, addr) in enumerate(sorted(seeds.items(), key=lambda x: int(x[1], 16))):
    print(f"  {i+1:2}. {addr}: {name}")
