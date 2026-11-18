"""
Find target/objective system for mission success.

When you bomb a runway or warehouse:
1. How does the game know what the target is?
2. How does it detect a hit on that specific target?
3. How are primary/secondary targets tracked?
4. How is mission success calculated?

Looking for:
- Target designation/marking system
- Hit detection on specific buildings/facilities
- Mission objective tracking
- Primary target vs secondary target logic
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("TARGET/OBJECTIVE SYSTEM SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'target_strings': [],
    'objective_strings': [],
    'target_functions': [],
    'building_entity_refs': []
}

# Search for target/objective related strings
print("Searching for target/objective strings...")
keywords = [
    'TARGET', 'OBJECTIVE', 'PRIMARY', 'SECONDARY',
    'RUNWAY', 'WAREHOUSE', 'BUILDING', 'FACILITY',
    'DESTROYED', 'DAMAGED', 'HIT',
    'MISSION', 'SUCCESS', 'FAIL', 'COMPLETE'
]

for s in idautils.Strings():
    str_val = str(s).upper()
    
    for keyword in keywords:
        if keyword in str_val:
            xrefs = []
            for xref in idautils.XrefsTo(s.ea):
                func_name = idc.get_func_name(xref.frm)
                xrefs.append({
                    'address': hex(xref.frm),
                    'function': func_name if func_name else 'unknown'
                })
            
            # Categorize
            if 'TARGET' in str_val or 'OBJECTIVE' in str_val:
                results['target_strings'].append({
                    'string': str(s),
                    'address': hex(s.ea),
                    'xrefs': xrefs
                })
            elif 'MISSION' in str_val or 'SUCCESS' in str_val or 'FAIL' in str_val:
                results['objective_strings'].append({
                    'string': str(s),
                    'address': hex(s.ea),
                    'xrefs': xrefs
                })
            
            break

print(f"\nFound {len(results['target_strings'])} target-related strings")
print(f"Found {len(results['objective_strings'])} mission-related strings")

# Print key target strings
print(f"\n{'=' * 80}")
print("KEY TARGET STRINGS:")
print("=" * 80)

for item in results['target_strings'][:20]:
    print(f"\n'{item['string']}' @ {item['address']}")
    if item['xrefs']:
        for xref in item['xrefs'][:3]:
            print(f"  -> {xref['function']}")

# Print mission success strings
print(f"\n{'=' * 80}")
print("MISSION SUCCESS/FAILURE STRINGS:")
print("=" * 80)

for item in results['objective_strings'][:15]:
    print(f"\n'{item['string']}' @ {item['address']}")
    if item['xrefs']:
        for xref in item['xrefs'][:3]:
            print(f"  -> {xref['function']}")

# Search for functions with target/objective in name
print(f"\n{'=' * 80}")
print("FUNCTIONS WITH TARGET/OBJECTIVE IN NAME:")
print("=" * 80)

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    
    if func_name:
        name_lower = func_name.lower()
        if any(kw in name_lower for kw in ['target', 'objective', 'mission', 'primary', 'secondary']):
            func = idaapi.get_func(func_ea)
            size = func.end_ea - func.start_ea if func else 0
            
            results['target_functions'].append({
                'name': func_name,
                'address': hex(func_ea),
                'size': size
            })
            
            print(f"  {func_name} @ {func_ea:#x} ({size} bytes)")

# Look for entity type checks for buildings
print(f"\n{'=' * 80}")
print("SEARCHING FOR BUILDING/FACILITY ENTITY TYPES:")
print("=" * 80)

# Entity types for ground structures likely in range 0x08-0x0F or 0x18-0x20
# Search for comparisons in damage or collision code

print("Looking in damage_event_dispatch_handler and related functions...")

# Check damage function for entity type filtering
damage_func = 0x2EAA7
func = idaapi.get_func(damage_func)

if func:
    print(f"\nScanning damage_event_dispatch_handler @ {damage_func:#x}:")
    
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0 and insn.itype == idaapi.NN_cmp:
            # Look for entity type comparisons
            op = insn.ops[1]
            if op.type == idaapi.o_imm:
                val = op.value
                # Likely entity type range
                if 0x08 <= val <= 0x20:
                    disasm = idc.generate_disasm_line(ea, 0)
                    print(f"  {ea:#08x}: {disasm}")
        
        ea = idc.next_head(ea, func.end_ea)

# Save results
output_file = Path(__file__).parent / "target_system_analysis.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print(f"Summary:")
print(f"  Target strings: {len(results['target_strings'])}")
print(f"  Mission strings: {len(results['objective_strings'])}")
print(f"  Target functions: {len(results['target_functions'])}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
