"""
Analyze the menu system expansion results to find key functions.
"""
import json
from collections import defaultdict, Counter

with open('ida_scripts/menu_system_expansion.json', 'r') as f:
    data = json.load(f)

print("MENU SYSTEM CALL GRAPH ANALYSIS")
print("=" * 80)

# Show basic stats for each seed
print("\nSEED FUNCTIONS:")
print("-" * 80)
for seed_name, info in data.items():
    print(f"\n{seed_name}:")
    print(f"  Address: 0x{info['address']:05X}")
    print(f"  Name: {info['name']}")
    print(f"  Size: {info['size']} bytes")
    print(f"  Callers: {len(info['callers'])}")
    print(f"  Callees: {len(info['callees'])}")

# Find common callees
print("\n" + "=" * 80)
print("COMMON INFRASTRUCTURE (called by multiple seeds)")
print("=" * 80)

all_callees = defaultdict(lambda: {'name': '', 'called_by': []})
for seed_name, info in data.items():
    for callee in info.get('callees', []):
        addr = callee['address']
        all_callees[addr]['name'] = callee['name']
        all_callees[addr]['called_by'].append(seed_name)

common = [(addr, data) for addr, data in all_callees.items() 
          if len(data['called_by']) > 1]
common.sort(key=lambda x: len(x[1]['called_by']), reverse=True)

print(f"\nFound {len(common)} functions called by multiple seeds:\n")
for addr, cdata in common[:30]:
    callers = ', '.join(cdata['called_by'])
    print(f"0x{addr:05X} {cdata['name']:50} [{len(cdata['called_by'])}] <- {callers}")

# Find graphics/file/rendering related functions
print("\n" + "=" * 80)
print("GRAPHICS/FILE/RENDERING FUNCTIONS")
print("=" * 80)

keywords = {
    'graphics': ['vga', 'graph', 'palette', 'blit', 'draw', 'render', 'display', 'pixel'],
    'file': ['file', 'load', 'idx', 'dat', 'read', 'open'],
    'ui': ['ui_', 'menu_', 'text', 'cursor', 'panel', 'page', 'layout'],
}

categorized = defaultdict(list)

for seed_name, info in data.items():
    for callee in info.get('callees', []):
        name = callee['name'].lower()
        addr = callee['address']
        
        for category, kws in keywords.items():
            if any(kw in name for kw in kws):
                categorized[category].append({
                    'addr': addr,
                    'name': callee['name'],
                    'called_from': seed_name
                })
                break

for category, funcs in sorted(categorized.items()):
    print(f"\n{category.upper()}:")
    # Deduplicate by address
    seen = set()
    for func in funcs:
        if func['addr'] not in seen:
            print(f"  0x{func['addr']:05X} {func['name']}")
            seen.add(func['addr'])

# Find functions with interesting names
print("\n" + "=" * 80)
print("INTERESTING FUNCTIONS (potential next targets)")
print("=" * 80)

interesting_patterns = [
    'loadout', 'weapon', 'slot', 'record', 'list', 'selection',
    'transition', 'animation', 'coordinate', 'transform',
    'validation', 'calculator', 'highlight', 'field'
]

interesting = []
for seed_name, info in data.items():
    for callee in info.get('callees', []):
        name = callee['name'].lower()
        if any(pat in name for pat in interesting_patterns):
            interesting.append({
                'addr': callee['address'],
                'name': callee['name'],
                'called_from': seed_name
            })

# Deduplicate
seen = {}
for func in interesting:
    if func['addr'] not in seen:
        seen[func['addr']] = func

for addr in sorted(seen.keys()):
    func = seen[addr]
    print(f"0x{addr:05X} {func['name']:50} <- {func['called_from']}")

print("\n" + "=" * 80)
print(f"Total unique callees across all seeds: {len(all_callees)}")
