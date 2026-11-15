#!/usr/bin/env python3
"""
Extract campaign-related functions as seeds.
Includes: file_io, ui, menu systems
"""
import re
import json

content = open('../../registry/functions.yaml', 'r', encoding='utf-8').read()

# Find all campaign-related functions
systems = ['file_io', 'ui', 'menu', 'uibounds']
pattern = r'-\s+address:\s+(0x[0-9a-fA-F]+)\s+name:\s+([^\n]+)\s+system:\s+(' + '|'.join(systems) + ')'
matches = re.findall(pattern, content)

seeds = {}
by_system = {sys: [] for sys in systems}

for addr, name, system in matches:
    seeds[name.strip()] = addr
    by_system[system].append((addr, name.strip()))

print(f"Found {len(seeds)} campaign-related seed functions\n")
for system in systems:
    print(f"  {system}: {len(by_system[system])} functions")

# Write seeds file
with open('../campaign_seeds.json', 'w') as f:
    json.dump(seeds, f, indent=2)

print(f"\nWrote campaign_seeds.json")
print(f"\nFirst 15 seeds:")
for i, (name, addr) in enumerate(list(seeds.items())[:15]):
    print(f"  {addr}: {name}")
