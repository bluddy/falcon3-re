#!/usr/bin/env python3
"""Count and list all flight_physics system functions."""
import re

content = open('../../registry/functions.yaml', 'r', encoding='utf-8').read()

# Find all flight_physics functions
pattern = r'-\s+address:\s+(0x[0-9a-fA-F]+)\s+name:\s+([^\n]+)\s+system:\s+flight_physics'
matches = re.findall(pattern, content)

print(f"Current flight_physics functions: {len(matches)}\n")
print("First 20 flight_physics functions:")
for i, (addr, name) in enumerate(matches[:20], 1):
    print(f"  {i:2}. {addr}: {name.strip()}")

if len(matches) > 20:
    print(f"\n... and {len(matches) - 20} more")
