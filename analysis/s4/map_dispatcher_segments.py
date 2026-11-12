#!/usr/bin/env python3
"""
Map sub_263F6 dispatcher table segments to IDA function addresses.

The table uses link-time segment:offset format. We need to convert to IDA addresses.
Key insight: offset 0x1F6C appears in 16/21 entries - likely a common entry point offset.
"""
import json
from pathlib import Path

# Load the parsed table
table = json.load(open('sub_263F6_table.json'))
entries = table['entries']

# Load function_bytes for function lookup
fb = json.load(open('../ida_falconcd/function_bytes.json'))

# Load FALCONCD.EXE.yaml for segment mapping
import yaml
reg_path = Path('../../registry/FALCONCD.EXE.yaml')
with open(reg_path, encoding='utf-8') as f:
    exe_reg = yaml.safe_load(f)

print("="*80)
print("DISPATCHER TABLE SEGMENT MAPPING")
print("="*80)

# The challenge: table entries use LINK segments, not IDA addresses
# Link segment = load-time paragraph address
# IDA address = link_seg * 16 + offset + 0x10000 (load base)

# But some segments might be runtime-relocated overlays
# Strategy: try direct conversion first, then check overlay mapping

valid_entries = [e for e in entries if not e['is_null']]

print(f"\nAnalyzing {len(valid_entries)} valid entries...\n")

print(f"{'Index':<6} {'Seg':<6} {'Offset':<8} {'IDA Addr':<10} {'Function':<20} {'Named?'}")
print("-"*80)

results = []

for e in valid_entries:
    idx = e['index']
    seg = e['segment']
    offset = e['offset']
    
    # Direct IDA address calculation
    ida_addr = seg * 16 + offset + 0x10000
    
    # Look for function at this address
    found_func = None
    is_named = False
    match_type = "none"
    
    # Exact match
    for fname, fdata in fb.items():
        if fdata['ea'] == ida_addr:
            found_func = fname
            match_type = "exact"
            # Check if named (not sub_XXXXX)
            is_named = not fname.startswith('sub_')
            break
    
    # If no exact match, check if inside a function (mid-body)
    if not found_func:
        for fname, fdata in fb.items():
            fstart = fdata['ea']
            fsize = fdata.get('size', 0)
            if fstart <= ida_addr < fstart + fsize:
                offset_in_func = ida_addr - fstart
                found_func = f"{fname}+0x{offset_in_func:X}"
                match_type = "mid-body"
                is_named = not fname.startswith('sub_')
                break
    
    func_str = found_func if found_func else "???"
    named_str = "YES" if is_named else "NO"
    
    results.append({
        'index': idx,
        'segment': seg,
        'offset': offset,
        'ida_address': ida_addr,
        'function': func_str,
        'is_named': is_named,
        'match_type': match_type
    })
    
    print(f"{idx:<6} 0x{seg:04X} 0x{offset:04X}   0x{ida_addr:05X}   {func_str:<20} {named_str}")

# Analysis
print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

exact_matches = [r for r in results if r['match_type'] == 'exact']
mid_body = [r for r in results if r['match_type'] == 'mid-body']
no_match = [r for r in results if r['match_type'] == 'none']

print(f"\nMatch statistics:")
print(f"  Exact function starts: {len(exact_matches)}")
print(f"  Mid-body addresses: {len(mid_body)}")
print(f"  No match: {len(no_match)}")

# Check the 0x1F6C offset pattern
offset_1f6c = [r for r in results if r['offset'] == 0x1F6C]
print(f"\nEntries with offset 0x1F6C: {len(offset_1f6c)} of {len(results)}")
if len(offset_1f6c) > 0:
    print("  These likely use a common entry point at offset +0x1F6C in each segment")

# Named vs unnamed
named = [r for r in results if r['is_named']]
unnamed = [r for r in results if not r['is_named']]
print(f"\nNaming status:")
print(f"  Named functions: {len(named)}")
print(f"  Unnamed functions: {len(unnamed)}")

# Show no-match entries (need segment translation)
if len(no_match) > 0:
    print(f"\nNo-match entries (may need segment translation):")
    for r in no_match:
        print(f"  Entry {r['index']}: seg 0x{r['segment']:04X} offset 0x{r['offset']:04X} -> IDA 0x{r['ida_address']:05X}")

# Check if segments are in overlay range
print(f"\nSegment range analysis:")
seg_min = min(r['segment'] for r in results)
seg_max = max(r['segment'] for r in results)
print(f"  Segment range: 0x{seg_min:04X} - 0x{seg_max:04X}")
print(f"  Resident code ends at IDA 0x2C970 (link seg ~0x1C97)")
print(f"  Overlay code starts at IDA 0x1FBC0 (first overlay record)")

# Check address distribution
addr_min = min(r['ida_address'] for r in results)
addr_max = max(r['ida_address'] for r in results)
print(f"\nIDA address range (if direct conversion):")
print(f"  0x{addr_min:05X} - 0x{addr_max:05X}")

# Save results
output = {
    'dispatcher': 'sub_263F6',
    'table_entries': len(results),
    'exact_matches': len(exact_matches),
    'mid_body_matches': len(mid_body),
    'no_matches': len(no_match),
    'offset_1f6c_count': len(offset_1f6c),
    'named_count': len(named),
    'unnamed_count': len(unnamed),
    'entries': results
}

json.dump(output, open('dispatcher_mapping.json', 'w'), indent=2)
print(f"\n\nSaved mapping to dispatcher_mapping.json")

# If most are no-match, we need to check overlay segment mapping
if len(no_match) > len(exact_matches):
    print("\n" + "="*80)
    print("NEXT STEP: Overlay Segment Translation Needed")
    print("="*80)
    print("\nMost entries don't match IDA addresses directly.")
    print("This means the segments are link-time overlays that need translation.")
    print("\nOptions:")
    print("1. Check overlay_placement.json for segment mapping")
    print("2. Use runtime_seg_map.json to translate runtime->IDA")
    print("3. Parse FALCONCD.EXE.yaml overlay_groups for link->IDA mapping")
else:
    print("\n" + "="*80)
    print("SUCCESS: Most entries mapped directly!")
    print("="*80)
