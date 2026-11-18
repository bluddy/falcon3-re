"""
Find weapon impact and damage system.

Tracing weapon lifecycle:
1. Spawn: ag_weapon_entity_initialize sets initial conditions
2. Flight: Entity update applies physics (gravity, drag, guidance)
3. Impact: Collision detection with ground/targets
4. Damage: Apply damage to target, possible area effect

Looking for:
- Collision detection (entity vs ground, entity vs entity)
- Damage application functions
- Area damage/splash radius
- Target destruction logic
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("WEAPON IMPACT AND DAMAGE SYSTEM SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'collision_strings': [],
    'damage_functions': [],
    'entity_destroy_refs': []
}

# Search for collision/impact/damage related strings
print("Searching for impact/damage strings...")
keywords = [
    'HIT', 'IMPACT', 'COLLISION', 'COLLIDE',
    'DAMAGE', 'DESTROY', 'KILLED', 'DEAD',
    'EXPLODE', 'EXPLOSION', 'BLAST',
    'RADIUS', 'SPLASH', 'AREA'
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
            
            results['collision_strings'].append({
                'string': str(s),
                'address': hex(s.ea),
                'keyword': keyword,
                'xrefs': xrefs
            })
            
            if xrefs:
                print(f"  '{str(s)}' @ {s.ea:#x}")
                for xref in xrefs[:2]:
                    print(f"    -> {xref['function']}")
            break

print(f"\nFound {len(results['collision_strings'])} impact/damage related strings")

# Look for damage field in entity structure
# EntitySlotRecord has fields, looking for damage/health related
print(f"\n{'=' * 80}")
print("Searching for entity health/damage field access...")

# Common entity health offsets to check: +0x20-0x30 range
# Look for decrements, subtracts, compares to zero (destruction check)

text_seg = idaapi.get_segm_by_name(".text")
if text_seg:
    ea = text_seg.start_ea
    health_checks = []
    
    # Limit search to avoid timeout
    max_ea = min(text_seg.start_ea + 0x50000, text_seg.end_ea)
    
    while ea < max_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0:
            # Look for: sub [bx+offset], value (damage application)
            # or: cmp [bx+offset], 0 (death check)
            if insn.itype in [idaapi.NN_sub, idaapi.NN_cmp]:
                dst = insn.ops[0]
                
                # Check for entity field access pattern
                if dst.type == idaapi.o_displ:
                    base_reg = dst.reg
                    # Note: offset access might be in dst.addr or different field
                    
                    if base_reg in [idaapi.R_bx, idaapi.R_si, idaapi.R_di]:
                        disasm = idc.generate_disasm_line(ea, 0)
                        func = idaapi.get_func(ea)
                        
                        if func:
                            func_name = idc.get_func_name(ea)
                            func_start = func.start_ea
                            
                            # Look for promising patterns
                            if 'sub' in disasm.lower() or 'cmp' in disasm.lower():
                                # Avoid duplicates
                                if not any(h['function_addr'] == hex(func_start) for h in health_checks):
                                    health_checks.append({
                                        'address': hex(ea),
                                        'function': func_name,
                                        'function_addr': hex(func_start),
                                        'disasm': disasm
                                    })
                                    
                                    if len(health_checks) <= 20:  # Print first 20
                                        print(f"  {ea:#x} in {func_name}: {disasm}")
        
        ea = idc.next_head(ea, max_ea)
    
    results['entity_destroy_refs'] = health_checks[:50]  # Keep top 50
    print(f"\nFound {len(health_checks)} potential health/damage operations")

# Look for functions with "damage", "destroy", "kill" in name
print(f"\n{'=' * 80}")
print("Searching for damage/destroy functions by name...")

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    
    if func_name:
        name_lower = func_name.lower()
        if any(kw in name_lower for kw in ['damage', 'destroy', 'kill', 'hit', 'collide', 'impact', 'explode']):
            func = idaapi.get_func(func_ea)
            size = func.end_ea - func.start_ea if func else 0
            
            results['damage_functions'].append({
                'name': func_name,
                'address': hex(func_ea),
                'size': size
            })
            
            print(f"  {func_name} @ {func_ea:#x} ({size} bytes)")

print(f"\nFound {len(results['damage_functions'])} damage-related functions")

# Save results
output_file = Path(__file__).parent / "weapon_impact_damage.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print(f"Summary:")
print(f"  Impact strings: {len(results['collision_strings'])}")
print(f"  Health/damage ops: {len(results['entity_destroy_refs'])}")
print(f"  Damage functions: {len(results['damage_functions'])}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
