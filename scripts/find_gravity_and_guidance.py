"""
Find gravity constant and weapon guidance in entity_physics_and_ai_update.

Focused search for:
1. Gravity: sub [si+velocity_z_offset], constant
2. Weapon guidance: comparisons with weapon type values (0x12-0x32)
3. Target tracking: reads of target entity position
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("GRAVITY AND GUIDANCE SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

func_ea = 0x3D37F
func = idaapi.get_func(func_ea)

if not func:
    print(f"ERROR: Function not found")
    idc.qexit(1)

print(f"Analyzing entity_physics_and_ai_update @ {func_ea:#x}")
print(f"Size: {func.end_ea - func.start_ea} bytes\n")

results = {
    'gravity_candidates': [],
    'weapon_type_checks': [],
    'target_tracking': [],
    'function_calls': {}
}

# Pass 1: Find all function calls (to understand structure)
print("Pass 1: Analyzing function calls...")
ea = func.start_ea
while ea < func.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0 and insn.itype == idaapi.NN_call:
        target = insn.ops[0]
        if target.type == idaapi.o_near:
            target_ea = target.addr
            target_name = idc.get_func_name(target_ea)
            if target_name:
                if target_name not in results['function_calls']:
                    results['function_calls'][target_name] = 0
                results['function_calls'][target_name] += 1
    
    ea = idc.next_head(ea, func.end_ea)

print(f"Found {len(results['function_calls'])} unique function calls")
for name, count in sorted(results['function_calls'].items(), key=lambda x: -x[1])[:15]:
    print(f"  {name}: {count}x")

# Helper function for weapon names
def get_weapon_name(type_val):
    names = {
        0x12: 'AIM9_SIDEWINDER',
        0x13: 'AIM120_AMRAAM',
        0x15: 'AGM65_MAVERICK_TV',
        0x16: 'AGM65_MAVERICK_IR',
        0x19: 'AGM88_HARM',
        0x1A: 'AGM45_SHRIKE',
        0x28: 'MK82_BOMB',
        0x2D: 'CBU84_CLUSTER',
        0x2E: 'GBU15_GUIDED',
        0x30: 'AGM84_HARPOON',
        0x33: 'M61A1_VULCAN'
    }
    return names.get(type_val, f'WEAPON_TYPE_{type_val:02X}')

# Pass 2: Find weapon type checks (cmp with 0x12-0x32)
print(f"\n{'=' * 80}")
print("Pass 2: Finding weapon type checks...")

ea = func.start_ea
while ea < func.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0 and insn.itype == idaapi.NN_cmp:
        # Check second operand for weapon type values
        op = insn.ops[1]
        if op.type == idaapi.o_imm:
            val = op.value
            # Weapon types: 0x12-0x13 (A-A), 0x14-0x32 (A-G), 0x33-0x37 (guns)
            if 0x12 <= val <= 0x37:
                disasm = idc.generate_disasm_line(ea, 0)
                results['weapon_type_checks'].append({
                    'address': hex(ea),
                    'type': hex(val),
                    'type_name': get_weapon_name(val),
                    'disasm': disasm
                })
    
    ea = idc.next_head(ea, func.end_ea)

print(f"\nFound {len(results['weapon_type_checks'])} weapon type checks")
for check in results['weapon_type_checks']:
    print(f"  {check['address']}: {check['disasm']}")

# Pass 3: Look for subtract to entity fields (gravity/drag)
print(f"\n{'=' * 80}")
print("Pass 3: Finding subtract operations (gravity candidates)...")

ea = func.start_ea
sub_count = 0

while ea < func.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0 and insn.itype == idaapi.NN_sub:
        dst = insn.ops[0]
        src = insn.ops[1]
        
        # Look for: sub [si+offset], constant or register
        if dst.type == idaapi.o_displ:
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Get the constant if it's an immediate
            const_val = None
            if src.type == idaapi.o_imm:
                const_val = src.value
            
            results['gravity_candidates'].append({
                'address': hex(ea),
                'disasm': disasm,
                'constant': const_val
            })
            
            print(f"  {ea:#08x}: {disasm}")
            sub_count += 1
            
            if sub_count >= 30:  # Limit output
                print(f"  ... (stopping at 30, total continues)")
                break
    
    ea = idc.next_head(ea, func.end_ea)

print(f"\nFound {len(results['gravity_candidates'])} subtract operations")

# Pass 4: Look for add to entity fields (position integration)
print(f"\n{'=' * 80}")
print("Pass 4: Finding add operations (position integration)...")

ea = func.start_ea
add_count = 0

while ea < func.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0 and insn.itype == idaapi.NN_add:
        dst = insn.ops[0]
        
        # Look for: add [si+offset], ...
        if dst.type == idaapi.o_displ:
            disasm = idc.generate_disasm_line(ea, 0)
            
            print(f"  {ea:#08x}: {disasm}")
            add_count += 1
            
            if add_count >= 20:  # Limit output
                print(f"  ... (stopping at 20)")
                break
    
    ea = idc.next_head(ea, func.end_ea)

print(f"\nFound add operations to entity fields")

# Save results
output_file = Path(__file__).parent / "gravity_guidance_analysis.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
