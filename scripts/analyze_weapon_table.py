"""
Analyze weapon name table structure.

Weapon names found at 0x55c55-0x55cc7. Check if this is a table with
weapon type IDs, names, and parameters.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("WEAPON TABLE STRUCTURE ANALYSIS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Weapon name string addresses (from previous search)
weapon_strings = [
    (0x55c55, "AIM9P"),
    (0x55c5b, "AIM9M"),
    (0x55c61, "AIM120"),
    (0x55c68, "unknown1"),  # gap
    (0x55c71, "AGM88"),
    (0x55c77, "AGM65B"),
    (0x55c7e, "AGM65D"),
    (0x55c85, "AGM45"),
    (0x55c94, "MK82HD"),
    (0x55ca5, "CBU84"),
    (0x55cb0, "GBU15"),
    (0x55cc7, "AGM84"),
]

print("Analyzing data around weapon name strings...")
print()

results = []

for addr, name in weapon_strings:
    print(f"\n{name} @ {addr:#x}:")
    
    # Get the string
    str_val = idc.get_strlit_contents(addr)
    if str_val:
        str_val = str_val.decode('ascii', errors='ignore')
        print(f"  String: '{str_val}'")
    
    # Check bytes before the string (might be weapon type ID or index)
    print(f"  Bytes before string:")
    for offset in range(-8, 0):
        byte_val = idc.get_wide_byte(addr + offset)
        print(f"    [{addr + offset:#x}] = {byte_val:#04x} ({byte_val}d)")
    
    # Check bytes after the string
    str_len = len(str_val) if str_val else 6
    print(f"  Bytes after string (offset +{str_len}):")
    for offset in range(str_len, str_len + 8):
        byte_val = idc.get_wide_byte(addr + offset)
        print(f"    [{addr + offset:#x}] = {byte_val:#04x} ({byte_val}d)")
    
    # Look for xrefs
    xref_count = 0
    for xref in idautils.XrefsTo(addr):
        xref_count += 1
        func_name = idc.get_func_name(xref.frm)
        print(f"  Xref from {xref.frm:#x} in {func_name}")
    
    if xref_count == 0:
        print(f"  No xrefs (might be part of table accessed by offset)")
    
    results.append({
        'name': name,
        'address': hex(addr),
        'string': str_val if str_val else None,
        'xref_count': xref_count
    })

# Check if there's a pattern - look at start of table
table_start = 0x55c55 - 0x20  # Check 32 bytes before first string
print(f"\n{'=' * 80}")
print(f"Data dump from {table_start:#x} to {0x55cd0:#x}:")
print()

ea = table_start
while ea < 0x55cd0:
    # Print 16 bytes per line
    line_bytes = []
    line_ascii = []
    for i in range(16):
        if ea + i < 0x55cd0:
            b = idc.get_wide_byte(ea + i)
            line_bytes.append(f"{b:02x}")
            line_ascii.append(chr(b) if 32 <= b < 127 else '.')
        else:
            line_bytes.append("  ")
            line_ascii.append(" ")
    
    print(f"{ea:#08x}:  {' '.join(line_bytes[:8])}  {' '.join(line_bytes[8:])}  {''.join(line_ascii)}")
    ea += 16

# Save results
output_file = Path(__file__).parent / "weapon_table_analysis.json"
with open(output_file, 'w') as f:
    json.dump({'weapons': results}, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
