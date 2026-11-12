#!/usr/bin/env python3
"""
Final attempt to map dispatcher segments.

Theory: The segments 0x6E05-0x90B4 might be CS values from overlay records
NOT in the segsplit (which only covers R05/R29).

Let's check all overlay records and see if we can find a pattern.
"""
import json

# Table segments (runtime format suspected)
table_segs_hex = [
    0x6E05, 0x70AD, 0x721D, 0x7389, 0x746E, 0x758A, 0x7618,
    0x7A7D, 0x7AC0, 0x8357, 0x8360, 0x8A87, 0x90B4, 0x900E
]

# Convert assuming runtime: link = runtime - 0x1F5
table_link_segs = [s - 0x1F5 for s in table_segs_hex]

print("Dispatcher table segments analysis")
print("=" * 80)
print(f"\n{'Runtime':<10} {'Link (computed)':<18} {'Decimal'}")
print("-" * 50)
for runtime, link in zip(table_segs_hex, table_link_segs):
    print(f"0x{runtime:04X}    0x{link:04X}                {link}")

# Load overlay placement to see all records
op = json.load(open('../ida_falconcd/overlay_placement.json'))

print(f"\n\nOverlay records in placement (w0 values):")
w0_values = sorted(list(set(r['w0'] for r in op if r['placed'])))
for w0 in w0_values:
    recs = [r for r in op if r['w0'] == w0 and r['placed']]
    print(f"  w0=0x{w0:04X} ({len(recs)} records)")

# Check if any link segments fall in overlay record ranges
print(f"\n\nChecking if computed link segments fall within overlay record ranges...")
print(f"{'Link Seg':<12} {'In Range?':<50}")
print("-" * 70)

for link in table_link_segs:
    matches = []
    for r in op:
        if not r['placed']:
            continue
        # Check if link segment is w0 base OR within record's segment range
        if r['w0'] == link:
            matches.append(f"w0 base match: idx={r['idx']}")
        # Check if it's in the range w0...(w0+length/16)
        seg_end = r['w0'] + (r.get('real_len', 0) // 16)
        if r['w0'] <= link < seg_end:
            matches.append(f"within idx={r['idx']} ({r['w0']:#x}..{seg_end:#x})")
    
    if matches:
        print(f"0x{link:04X}      {', '.join(matches)}")
    else:
        print(f"0x{link:04X}      NO MATCH")

# Alternative theory: maybe these are ABSOLUTE addresses, not segments at all?
print(f"\n\nAlternative: treating as IDA linear addresses directly...")
print(f"{'Value':<10} {'As IDA Addr':<15} {'Function?'}")
print("-" * 50)

fb = json.load(open('../ida_falconcd/function_bytes.json'))

for seg in table_segs_hex[:5]:  # Check first 5
    # Try as linear address
    ida_addr = seg  # Direct use
    
    # Look for function
    found = None
    for fname, fdata in fb.items():
        if fdata['ea'] == ida_addr:
            found = fname
            break
        if fdata['ea'] <= ida_addr < fdata['ea'] + fdata.get('size', 0):
            found = f"{fname}+{ida_addr - fdata['ea']}"
            break
    
    print(f"0x{seg:04X}    0x{ida_addr:05X}        {found if found else 'NO'}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("\nThe segments 0x6E05-0x90B4 don't match:")
print("  - Segsplit link segments (range 0x1E10-0x54AF)")
print("  - Overlay placement w0 bases (range 0x1CF6-0x606E)")
print("  - Runtime segment map (no matches)")
print("  - Direct IDA addresses (mostly out of range)")
print("\nPossible explanations:")
print("  1. These are segment values from overlay records NOT YET PLACED in IDB")
print("  2. The table is corrupt or not actually a dispatch table")
print("  3. Different addressing mode (protected mode? high memory?)")
print("  4. The table format interpretation is wrong")
print("\nRecommendation: Check sub_263F6 bytecode again to verify table format.")
