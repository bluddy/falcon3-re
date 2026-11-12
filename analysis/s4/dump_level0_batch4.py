#!/usr/bin/env python3
"""
Dump Level-0 batch 4 functions (ranks 36-50, 15 functions) for manual naming.
Extracts from callgraph_partial.json and function_bytes.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CG = ROOT / "analysis" / "traces" / "callgraph_partial.json"
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
CLS = ROOT / "analysis" / "ida_falconcd" / "classification.json"
REG = ROOT / "registry" / "naming.yaml"

# Load data
cg = json.loads(CG.read_text())
fb = json.loads(FB.read_text())
cls = json.loads(CLS.read_text())

# Load named functions from registry
import re
named = set()
for line in REG.read_text().split('\n'):
    if m := re.match(r'^\s*-\s+key:\s+(\w+)', line):
        named.add(m.group(1))

# Build Level-0 candidates: functions with dyn_calls > 0 and no callees
# Get all function keys from classification
all_fns = set(cls.keys())

# Find Level-0: no outgoing edges (or only to self)
level0_candidates = []
for fn in all_fns:
    if fn in named:
        continue  # Skip already named
    
    # Get callees
    callees = [edge[1] for edge in cg["edges"] if edge[0] == fn and edge[1] != fn]
    if len(callees) > 0:
        continue  # Has callees, not Level-0
    
    # Get dyn calls
    dyn = cg["dyn_target_calls"].get(fn, 0)
    static_in = cg["static_in_degree"].get(fn, 0)
    
    # Must have some evidence (dyn > 0 or static_in > 0)
    if dyn == 0 and static_in == 0:
        continue
    
    level0_candidates.append({
        "name": fn,
        "ea": cls[fn]["ea"],
        "size": cls[fn]["size"],
        "dyn": dyn,
        "in": static_in,
    })

# Sort by (dyn DESC, in DESC)
level0_candidates.sort(key=lambda x: (-x["dyn"], -x["in"]))

# Extract batch 4: ranks 36-50
BATCH_START = 35
BATCH_SIZE = 15
batch4 = level0_candidates[BATCH_START:BATCH_START + BATCH_SIZE]

print(f"Level-0 Batch 4 (ranks 36-50, {len(batch4)} functions)")
print("=" * 80)
print()

for i, node in enumerate(batch4, start=BATCH_START+1):
    name = node["name"]
    ea = node["ea"]
    dyn = node["dyn"]
    in_deg = node["in"]
    
    # Get bytecode from function_bytes
    fb_entry = fb.get(name, {})
    bytecode = fb_entry.get("bytes", "")
    size = len(bytes.fromhex(bytecode)) if bytecode else 0
    
    print(f"Rank {i}: {name} (0x{ea:05X})")
    print(f"  dyn={dyn}, in={in_deg}, size={size}B")
    print(f"  bytecode: {bytecode}")
    print()

# Summary
print()
print("Summary:")
print(f"  Total: {len(batch4)} functions")
sizes = [len(bytes.fromhex(fb.get(n['name'], {}).get('bytes', '00'))) for n in batch4]
print(f"  Size range: {min(sizes)}-{max(sizes)}B")
print(f"  Call range: {min(n['dyn'] for n in batch4)}-{max(n['dyn'] for n in batch4)} dyn_calls")
