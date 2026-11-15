#!/usr/bin/env python3
"""
Extract view and input-related functions from top 200 list.
These are candidates for view mode switching code.
"""

import json

# Load the top 200 functions
with open('top_200_functions.json', 'r') as f:
    functions = json.load(f)

# Keywords to search for
view_keywords = ['view', 'camera', 'external', 'cockpit', 'chase']
input_keywords = ['kb_', 'key_', 'input', 'poll']

print("="*80)
print("VIEW-RELATED FUNCTIONS IN TOP 200")
print("="*80)

view_funcs = []
for idx, f in enumerate(functions, 1):
    name_lower = f['name'].lower()
    if any(kw in name_lower for kw in view_keywords):
        f['rank'] = idx  # Add rank for reference
        view_funcs.append(f)
        print(f"\nRank {idx:3d}: {f['name']}")
        print(f"  Address: 0x{f['address']}")
        print(f"  Calls: {f.get('calls', 0)}")
        print(f"  Size: {f.get('size', 0)} bytes")

print(f"\n{len(view_funcs)} view-related functions found")

print("\n" + "="*80)
print("INPUT-RELATED FUNCTIONS IN TOP 200")
print("="*80)

input_funcs = []
for idx, f in enumerate(functions, 1):
    name_lower = f['name'].lower()
    if any(kw in name_lower for kw in input_keywords):
        f['rank'] = idx  # Add rank for reference
        input_funcs.append(f)
        print(f"\nRank {idx:3d}: {f['name']}")
        print(f"  Address: 0x{f['address']}")
        print(f"  Calls: {f.get('calls', 0)}")
        print(f"  Size: {f.get('size', 0)} bytes")

print(f"\n{len(input_funcs)} input-related functions found")

# Save results
results = {
    'view_functions': view_funcs,
    'input_functions': input_funcs
}

with open('view_input_candidates.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "="*80)
print(f"Results saved to view_input_candidates.json")
print("\nNext step: Check if any input functions call view functions or reference 0x107762")
