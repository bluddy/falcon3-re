"""
Find entity physics update functions.

Bombs/missiles need per-frame updates:
- Position integration (velocity -> position)
- Velocity updates (gravity, drag, guidance)
- Collision detection (ground, targets)
- Damage application on impact

Looking for main entity update loop that processes all active entities.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("ENTITY PHYSICS UPDATE SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'update_functions': [],
    'farobj_functions': []
}

# Search for functions with "update", "step", "tick", "frame" in name
print("Searching for entity update functions by name...")

keywords = ['update', 'step', 'tick', 'frame', 'integrate', 'advance']

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    
    if func_name:
        name_lower = func_name.lower()
        
        # Look for update-related names
        if any(kw in name_lower for kw in keywords):
            # Filter for entity/farobj related
            if any(sys in name_lower for sys in ['entity', 'farobj', 'slot', 'object']):
                func = idaapi.get_func(func_ea)
                size = func.end_ea - func.start_ea if func else 0
                
                results['update_functions'].append({
                    'name': func_name,
                    'address': hex(func_ea),
                    'size': size
                })
                
                print(f"  {func_name} @ {func_ea:#x} ({size} bytes)")

print(f"\nFound {len(results['update_functions'])} entity update functions")

# Look for farobj_slot_update or similar (entity slot processing)
print(f"\n{'=' * 80}")
print("Searching for farobj/entity slot processing functions...")

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    
    if func_name and 'farobj' in func_name.lower():
        func = idaapi.get_func(func_ea)
        size = func.end_ea - func.start_ea if func else 0
        
        # Look for larger functions (main loops are bigger)
        if size > 200:
            results['farobj_functions'].append({
                'name': func_name,
                'address': hex(func_ea),
                'size': size
            })
            
            print(f"  {func_name} @ {func_ea:#x} ({size} bytes)")

print(f"\nFound {len(results['farobj_functions'])} large farobj functions")

# Look for gravity constant application
# Gravity adds downward velocity: velocity_z += gravity_constant
print(f"\n{'=' * 80}")
print("Searching for velocity modification patterns (gravity application)...")

# Look for add/sub to velocity fields
# Pattern: add [entity+velocity_offset], value
text_seg = idaapi.get_segm_by_name(".text")
if text_seg:
    ea = text_seg.start_ea
    velocity_updates = []
    
    # Limit search
    max_ea = min(text_seg.start_ea + 0x80000, text_seg.end_ea)
    
    while ea < max_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0:
            # Look for add/sub to memory (velocity update)
            if insn.itype in [idaapi.NN_add, idaapi.NN_sub]:
                dst = insn.ops[0]
                
                # Memory destination
                if dst.type == idaapi.o_displ:
                    disasm = idc.generate_disasm_line(ea, 0)
                    
                    # Look for promising patterns
                    if any(pat in disasm for pat in ['[bx+', '[si+', '[di+']):
                        func = idaapi.get_func(ea)
                        if func:
                            func_name = idc.get_func_name(ea)
                            
                            # Check if function looks like physics update
                            if any(kw in func_name.lower() for kw in ['update', 'step', 'integrate', 'farobj', 'entity']):
                                func_start = func.start_ea
                                
                                if not any(v['function_addr'] == hex(func_start) for v in velocity_updates):
                                    velocity_updates.append({
                                        'address': hex(ea),
                                        'function': func_name,
                                        'function_addr': hex(func_start),
                                        'disasm': disasm
                                    })
                                    
                                    if len(velocity_updates) <= 15:
                                        print(f"  {ea:#x} in {func_name}: {disasm}")
        
        ea = idc.next_head(ea, max_ea)
    
    results['velocity_updates'] = velocity_updates[:30]
    print(f"\nFound {len(velocity_updates)} velocity update operations")

# Save results
output_file = Path(__file__).parent / "entity_physics_update.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print(f"Summary:")
print(f"  Entity update functions: {len(results['update_functions'])}")
print(f"  Large farobj functions: {len(results['farobj_functions'])}")
print(f"  Velocity updates found: {len(results.get('velocity_updates', []))}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
