#!/usr/bin/env python3
from apply_known_names import parse_simple_yaml

data = parse_simple_yaml('../../registry/functions.yaml')
print(f"Parsed {len(data['functions'])} functions")
print("\nFirst 5:")
for f in data['functions'][:5]:
    print(f"  {hex(f['address'])}: {f['name']}")
print("\nLast 5:")
for f in data['functions'][-5:]:
    print(f"  {hex(f['address'])}: {f['name']}")
