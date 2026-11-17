"""
Find weapon name strings in binary.

Looking for weapon names from manual: Mk82, Mk84, GBU-10, GBU-12, AGM-65, CBU, etc.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("WEAPON NAME STRING SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Weapon names to search for (from F-16 loadout)
weapon_keywords = [
    "MK", "Mk", "GBU", "AGM", "AIM", "CBU",
    "MAVERICK", "HARM", "SHRIKE", "SIDEWINDER", "AMRAAM",
    "VULCAN", "CANNON",
    "BOMB", "MISSILE", "ROCKET"
]

print(f"Searching for {len(weapon_keywords)} weapon-related keywords")
print(f"Keywords: {', '.join(weapon_keywords)}\n")

results = {}

# Search all strings in the binary
for s in idautils.Strings():
    str_val = str(s)
    str_ea = s.ea
    
    # Check if any keyword matches
    for keyword in weapon_keywords:
        if keyword.upper() in str_val.upper():
            # Find xrefs to this string
            xrefs = []
            for xref in idautils.XrefsTo(str_ea):
                func_name = idc.get_func_name(xref.frm)
                xrefs.append({
                    'address': hex(xref.frm),
                    'function': func_name if func_name else 'unknown'
                })
            
            if keyword not in results:
                results[keyword] = []
            
            results[keyword].append({
                'string': str_val,
                'address': hex(str_ea),
                'xrefs': xrefs
            })
            
            print(f"Found '{keyword}': {str_val} @ {str_ea:#x}")
            if xrefs:
                print(f"  Referenced by {len(xrefs)} locations")
            break

print(f"\n{'=' * 80}")
print(f"Found {sum(len(v) for v in results.values())} weapon-related strings")
print(f"Matching {len(results)} different keywords")

# Save results
output_file = Path(__file__).parent / "weapon_names.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_file}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
