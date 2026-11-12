#!/usr/bin/env python3
"""
Analyze overlay target frequencies from trace data to find high-value overlay functions.
"""
import json
from collections import defaultdict
from pathlib import Path

# Read function_bytes to get all overlay functions (runtime CS != 0x1AA3)
fb_path = Path("../ida_falconcd/function_bytes.json")
fb = json.load(open(fb_path))

# Identify overlay functions: those with start_ea >= 0x1FBC0 (first overlay segment R01)
# Per FALCONCD.EXE.yaml: resident ends at 0x1FBB6, R01 starts at 0x1FBC0
overlay_funcs = {name: data for name, data in fb.items() if data['ea'] >= 0x1FBC0}

print(f"Total functions: {len(fb)}")
print(f"Overlay functions: {len(overlay_funcs)}")
print(f"Resident functions: {len(fb) - len(overlay_funcs)}")

# Load callgraph data to get dynamic call counts
cg_path = Path("../traces/callgraph_partial.json")
if not cg_path.exists():
    print("\nERROR: callgraph_partial.json not found")
    exit(1)

# Callgraph format: need to check structure first
cg = json.load(open(cg_path))
print(f"\nCallgraph keys: {list(cg.keys())}")

# Check if we have function-level data
if 'functions' in cg:
    func_data = cg['functions']
    print(f"Function entries: {len(func_data)}")
elif isinstance(cg, dict) and 'edge_counts' in cg:
    print("Callgraph is edge-based, not node-based")
    print("Need to parse trace files directly for overlay IP frequencies")

# Try loading naming registry to see which overlays are already named
naming_path = Path("../../registry/naming.yaml")
import yaml
naming = yaml.safe_load(open(naming_path))
named_set = {entry['ida'] for entry in naming}

# Count overlay functions by naming status
named_overlay = [name for name in overlay_funcs if name in named_set]
unnamed_overlay = [name for name in overlay_funcs if name not in named_set]

print(f"\nOverlay naming status:")
print(f"  Named: {len(named_overlay)} ({100*len(named_overlay)/len(overlay_funcs):.1f}%)")
print(f"  Unnamed: {len(unnamed_overlay)} ({100*len(unnamed_overlay)/len(overlay_funcs):.1f}%)")

# Show address range distribution
ranges = defaultdict(int)
for name, data in overlay_funcs.items():
    ea = data['ea']
    # Group by 0x10000 blocks (roughly by overlay record)
    block = (ea // 0x10000) * 0x10000
    ranges[block] += 1

print(f"\nOverlay functions by address range:")
for block in sorted(ranges.keys()):
    print(f"  0x{block:05X}+: {ranges[block]} functions")

print("\n=== Need trace data with IP frequencies ===")
print("Callgraph_partial.json has edge data, not IP frequencies")
print("Options:")
print("1. Parse memdump/*.jsonl trace files for overlay CS segments")
print("2. Use existing analysis/s4/level*.json files with dyn counts")
print("3. Check if there's already an overlay IP frequency file")
