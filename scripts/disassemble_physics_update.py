"""
Deep dive into entity_physics_and_ai_update @ 0x3D37F (1319 bytes).

Looking for:
- Gravity constant (subtract from velocity_z)
- Weapon guidance logic (Maverick, HARM, missile tracking)
- Bomb ballistics (trajectory integration)
- Entity type dispatching
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("ENTITY PHYSICS AND AI UPDATE - DEEP ANALYSIS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

func_ea = 0x3D37F
func = idaapi.get_func(func_ea)

if not func:
    print(f"ERROR: Function not found at {func_ea:#x}")
    idc.qexit(1)

func_name = idc.get_func_name(func_ea)
print(f"Analyzing: {func_name}")
print(f"Address: {func_ea:#x}")
print(f"Size: {func.end_ea - func.start_ea} bytes\n")

results = {
    'function': func_name,
    'address': hex(func_ea),
    'size': func.end_ea - func.start_ea,
    'full_disassembly': [],
    'function_calls': [],
    'constants': [],
    'entity_field_accesses': [],
    'branches': []
}

# Get complete disassembly
print("Extracting complete disassembly...")
ea = func.start_ea
insn_count = 0

while ea < func.end_ea:
    disasm = idc.generate_disasm_line(ea, 0)
    results['full_disassembly'].append({
        'address': hex(ea),
        'disasm': disasm
    })
    
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0:
        # Track function calls
        if insn.itype == idaapi.NN_call:
            target = insn.ops[0]
            if target.type == idaapi.o_near:
                target_ea = target.addr
                target_name = idc.get_func_name(target_ea)
                if target_name:
                    results['function_calls'].append({
                        'address': hex(ea),
                        'target': hex(target_ea),
                        'name': target_name
                    })
        
        # Track constants (potential gravity, velocities)
        for i, op in enumerate(insn.ops):
            if op.type == idaapi.o_imm:
                value = op.value
                # Interesting constants: small values (gravity), large values (velocities)
                if (0 < value < 100) or (1000 < value < 10000):
                    results['constants'].append({
                        'address': hex(ea),
                        'value': value,
                        'hex': hex(value),
                        'disasm': disasm
                    })
        
        # Track entity field accesses [si+offset]
        for i, op in enumerate(insn.ops):
            if op.type == idaapi.o_displ:
                # Entity field access
                results['entity_field_accesses'].append({
                    'address': hex(ea),
                    'disasm': disasm
                })
        
        # Track conditional branches (state machine, type checking)
        if insn.itype in [idaapi.NN_jz, idaapi.NN_jnz, idaapi.NN_jl, idaapi.NN_jg, 
                          idaapi.NN_jle, idaapi.NN_jge, idaapi.NN_ja, idaapi.NN_jb,
                          idaapi.NN_je, idaapi.NN_jne]:
            results['branches'].append({
                'address': hex(ea),
                'type': idc.GetMnem(ea),
                'target': hex(insn.ops[0].addr) if insn.ops[0].type == idaapi.o_near else 'unknown',
                'disasm': disasm
            })
    
    ea = idc.next_head(ea, func.end_ea)
    insn_count += 1

print(f"Extracted {insn_count} instructions")
print(f"  Function calls: {len(results['function_calls'])}")
print(f"  Interesting constants: {len(results['constants'])}")
print(f"  Entity field accesses: {len(results['entity_field_accesses'])}")
print(f"  Branches: {len(results['branches'])}")

# Print function calls (shows structure)
print(f"\n{'=' * 80}")
print("FUNCTION CALLS (shows what this function does):")
print("=" * 80)

call_groups = {}
for call in results['function_calls']:
    name = call['name']
    if name not in call_groups:
        call_groups[name] = []
    call_groups[name].append(call['address'])

for name, addresses in sorted(call_groups.items()):
    print(f"{name} - called {len(addresses)} times")
    for addr in addresses[:3]:  # Show first 3
        print(f"  @ {addr}")
    if len(addresses) > 3:
        print(f"  ... and {len(addresses) - 3} more")

# Print interesting constants (potential gravity, velocities)
print(f"\n{'=' * 80}")
print("INTERESTING CONSTANTS (potential gravity/velocity values):")
print("=" * 80)

# Group constants by value
const_groups = {}
for const in results['constants']:
    val = const['value']
    if val not in const_groups:
        const_groups[val] = []
    const_groups[val].append(const)

for val in sorted(const_groups.keys()):
    consts = const_groups[val]
    print(f"\nValue {val} (0x{val:x}) - appears {len(consts)} times:")
    for c in consts[:5]:  # Show first 5
        print(f"  {c['address']}: {c['disasm']}")
    if len(consts) > 5:
        print(f"  ... and {len(consts) - 5} more")

# Look for subtract patterns (gravity application: velocity_z -= constant)
print(f"\n{'=' * 80}")
print("SUBTRACT OPERATIONS (potential gravity application):")
print("=" * 80)

subtract_count = 0
for line in results['full_disassembly']:
    if 'sub' in line['disasm'].lower() and '[si+' in line['disasm']:
        print(f"{line['address']}: {line['disasm']}")
        subtract_count += 1
        if subtract_count >= 20:  # Limit output
            break

if subtract_count == 0:
    print("(No subtract operations found to entity fields)")

# Look for add patterns (velocity integration: position += velocity)
print(f"\n{'=' * 80}")
print("ADD OPERATIONS (potential position integration):")
print("=" * 80)

add_count = 0
for line in results['full_disassembly']:
    if 'add' in line['disasm'].lower() and '[si+' in line['disasm']:
        print(f"{line['address']}: {line['disasm']}")
        add_count += 1
        if add_count >= 20:  # Limit output
            break

if add_count == 0:
    print("(No add operations found to entity fields)")

# Save full results
output_file = Path(__file__).parent / "physics_update_deep_dive.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Full analysis saved to: {output_file}")
print(f"Disassembly: {insn_count} instructions")
print("Exiting IDA...")

# Exit
idc.qexit(0)
