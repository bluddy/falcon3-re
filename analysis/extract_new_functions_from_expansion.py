"""
Extract all functions from expansion analysis and prepare them for registry.
Compare with existing registry to find NEW functions.
"""
import json
import yaml

# Load expansion results
with open('expansion_analysis_results.json', 'r') as f:
    expansion = json.load(f)

# Load existing registry
with open('../registry/functions.yaml', 'r') as f:
    # Just read as text to check addresses
    registry_text = f.read()

print(f"Total functions in expansion: {len(expansion['all_functions'])}")

# Extract new functions
new_functions = []
existing_count = 0

for addr_str, info in expansion['all_functions'].items():
    addr = int(addr_str, 16)
    
    # Check if already in registry
    addr_pattern = f"address: 0x{addr:06x}"
    if addr_pattern.lower() in registry_text.lower():
        existing_count += 1
        continue
    
    # New function!
    new_functions.append({
        'address': addr,
        'name': info['name'],
        'size': info['size'],
        'depth': info['depth'],
        'score': info['score'],
        'stats': info['stats']
    })

print(f"Already in registry: {existing_count}")
print(f"NEW functions found: {len(new_functions)}")

# Sort by address
new_functions.sort(key=lambda x: x['address'])

# Create YAML entries
print(f"\nGenerating YAML entries for {len(new_functions)} new functions...")

yaml_entries = []

for func in new_functions:
    # Generate documentation string
    doc_parts = []
    doc_parts.append(f"{func['size']}B")
    
    stats = func['stats']
    if stats['bit_ops'] > 0:
        doc_parts.append(f"bit_ops={stats['bit_ops']}")
    if stats['buffer_writes'] > 0:
        doc_parts.append(f"buf_wr={stats['buffer_writes']}")
    if stats['loops'] > 0:
        doc_parts.append(f"loops={stats['loops']}")
    if stats['calls'] > 0:
        doc_parts.append(f"calls={stats['calls']}")
    
    doc_parts.append(f"depth={func['depth']}")
    doc_parts.append(f"score={func['score']}")
    doc_parts.append("Found via systematic expansion from font loaders")
    
    doc = ", ".join(doc_parts)
    
    entry = {
        'address': f"0x{func['address']:06x}",
        'name': func['name'],
        'size': func['size'],
        'doc': doc,
        'source': 'expansion_analysis_2026-11-15'
    }
    
    yaml_entries.append(entry)

# Save to a temporary file for review
output = """# New Functions from Expansion Analysis
# Found by systematically expanding from font loaders
# Total: {} new functions
# Session: 2026-11-15

""".format(len(yaml_entries))

for entry in yaml_entries:
    output += f"  - address: {entry['address']}\n"
    output += f"    name: {entry['name']}\n"
    output += f"    size: {entry['size']}\n"
    output += f"    doc: '{entry['doc']}'\n"
    output += f"    source: '{entry['source']}'\n"
    output += "\n"

with open('new_functions_expansion.yaml', 'w') as f:
    f.write(output)

print(f"\nNew functions saved to new_functions_expansion.yaml")

# Also create a summary by depth
print(f"\nBreakdown by expansion depth:")
from collections import defaultdict
by_depth = defaultdict(list)
for func in new_functions:
    by_depth[func['depth']].append(func)

for depth in sorted(by_depth.keys()):
    funcs = by_depth[depth]
    avg_score = sum(f['score'] for f in funcs) / len(funcs) if funcs else 0
    print(f"  Depth {depth}: {len(funcs)} functions (avg score: {avg_score:.1f})")

# High-scoring new functions
print(f"\nTop 20 NEW functions by score:")
new_functions_sorted = sorted(new_functions, key=lambda x: x['score'], reverse=True)
for i, func in enumerate(new_functions_sorted[:20], 1):
    print(f"  {i:2}. {func['name'][:40]:40} @ 0x{func['address']:06X} "
          f"(score: {func['score']:2}, depth: {func['depth']})")

print("\nDone!")
