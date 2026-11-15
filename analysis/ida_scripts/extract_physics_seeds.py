#!/usr/bin/env python3
"""Extract all flight_physics functions as seeds."""
import re
import json

content = open('../../registry/functions.yaml', 'r', encoding='utf-8').read()

# Find all flight_physics functions
pattern = r'-\s+address:\s+(0x[0-9a-fA-F]+)\s+name:\s+([^\n]+)\s+system:\s+flight_physics'
matches = re.findall(pattern, content)

seeds = {}
for addr, name in matches:
    seeds[name.strip()] = addr

print(f"Found {len(seeds)} flight_physics seed functions")

# Write seeds file
with open('../physics_seeds.json', 'w') as f:
    json.dump(seeds, f, indent=2)

print(f"Wrote physics_seeds.json")
print(f"\nFirst 10 seeds:")
for i, (name, addr) in enumerate(list(seeds.items())[:10]):
    print(f"  {addr}: {name}")
