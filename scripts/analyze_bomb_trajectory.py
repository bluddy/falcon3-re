"""
Analyze bomb trajectory and release code.

Starting from farobj_utility_1819 @ 0x4C3C7 which handles A-G weapons.
Looking for:
- Initial velocity setup
- Gravity/acceleration application
- Entity update for bombs
- Release conditions
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("BOMB TRAJECTORY ANALYSIS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'farobj_utility_1819': {},
    'bomb_types': {},
    'entity_updates': []
}

# Analyze farobj_utility_1819 @ 0x4C3C7
func_ea = 0x4C3C7
func = idaapi.get_func(func_ea)

if not func:
    print(f"ERROR: Function not found at {func_ea:#x}")
    idc.qexit(1)

func_name = idc.get_func_name(func_ea)
print(f"Analyzing {func_name} @ {func_ea:#x}")
print(f"Size: {func.end_ea - func.start_ea} bytes\n")

# Get complete disassembly
disasm_lines = []
ea = func.start_ea
while ea < func.end_ea:
    disasm = idc.generate_disasm_line(ea, 0)
    disasm_lines.append({
        'address': hex(ea),
        'disasm': disasm
    })
    ea = idc.next_head(ea, func.end_ea)

results['farobj_utility_1819'] = {
    'address': hex(func_ea),
    'size': func.end_ea - func.start_ea,
    'disassembly': disasm_lines
}

print(f"Extracted {len(disasm_lines)} instructions from farobj_utility_1819")

# Look for calls to other functions (entity setup, physics integration)
print(f"\nCalls from farobj_utility_1819:")
calls_found = []

ea = func.start_ea
while ea < func.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0 and insn.itype == idaapi.NN_call:
        # Get call target
        target = insn.ops[0]
        if target.type == idaapi.o_near:
            target_ea = target.addr
            target_name = idc.get_func_name(target_ea)
            if target_name:
                calls_found.append({
                    'address': hex(ea),
                    'target': hex(target_ea),
                    'function': target_name
                })
                print(f"  Call @ {ea:#x} -> {target_name} @ {target_ea:#x}")
    
    ea = idc.next_head(ea, func.end_ea)

results['farobj_utility_1819']['calls'] = calls_found
print(f"\nFound {len(calls_found)} function calls")

# Look for entity field writes in this function
# Pattern: mov [bp+offset], value or mov [bx+si+offset], value
print(f"\n{'=' * 80}")
print("Entity field writes in farobj_utility_1819:")

field_writes = []
ea = func.start_ea

while ea < func.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0 and insn.itype == idaapi.NN_mov:
        # Check destination operand
        dst = insn.ops[0]
        src = insn.ops[1]
        
        # Look for memory writes with offset (entity field access)
        if dst.type in [idaapi.o_displ, idaapi.o_phrase]:
            disasm = idc.generate_disasm_line(ea, 0)
            field_writes.append({
                'address': hex(ea),
                'disasm': disasm
            })
            print(f"  {ea:#x}: {disasm}")
    
    ea = idc.next_head(ea, func.end_ea)

results['entity_field_writes'] = field_writes
print(f"\nFound {len(field_writes)} entity field writes")

# Save full analysis
output_file = Path(__file__).parent / "bomb_trajectory_analysis.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print(f"Next: Analyze called functions for physics integration")
print("Exiting IDA...")

# Exit
idc.qexit(0)
