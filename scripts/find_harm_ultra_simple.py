"""
Ultra-simple HARM search - just scan known function.
"""

import idc
import idaapi
import json
from pathlib import Path

print("Starting HARM search...")

# Wait for auto-analysis
idaapi.auto_wait()

results = []

# Known function that handles A-G weapons: farobj_utility_1819 @ 0x4C3C7
func_ea = 0x4C3C7
func = idaapi.get_func(func_ea)

if func:
    print(f"Analyzing function at {func_ea:#x}")
    
    ea = func.start_ea
    while ea < func.end_ea:
        # Get disassembly
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for "19h" or similar in disassembly string
        if "19h" in disasm or "0x19" in disasm:
            results.append({
                'address': hex(ea),
                'disasm': disasm
            })
            print(f"  {ea:#x}: {disasm}")
        
        ea = idc.next_head(ea, func.end_ea)
else:
    print("ERROR: Function not found")

print(f"\nFound {len(results)} potential HARM references")

# Save
output_file = Path(__file__).parent / "harm_ultra_simple.json"
with open(output_file, 'w') as f:
    json.dump({'references': results}, f, indent=2)

print(f"Saved to {output_file}")

# Exit
idc.qexit(0)
