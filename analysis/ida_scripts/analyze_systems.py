#!/usr/bin/env python3
"""Analyze system distribution in the registry."""
import re
from collections import Counter

content = open('../../registry/functions.yaml', 'r', encoding='utf-8').read()

# Find all systems
pattern = r'system:\s+(\w+)'
systems = re.findall(pattern, content)

counts = Counter(systems)

print('Current systems by function count:\n')
for sys, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
    print(f'  {sys:25} {count:4} functions')

print(f'\nTotal systems: {len(counts)}')
print(f'Total functions: {sum(counts.values())}')
