import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\remaining_categories.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Finding remaining category assignments (4-8, 15-17)...")
idaapi.auto_wait()

print("="*70)
print("SEARCHING FOR SPECIFIC CATEGORY VALUES")
print("="*70 + "\n")

# Search for assignments of specific values to [X+0Ch]
target_values = [4, 5, 6, 7, 8, 15, 16, 17]

category_assignments = {}
for val in target_values:
    category_assignments[val] = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    # Only search code segments
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == "mov":
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Check for writes to [X+0Ch]
            if ("[si+0Ch]" in disasm or "[di+0Ch]" in disasm or "[bx+0Ch]" in disasm):
                # Check for specific values
                for val in target_values:
                    hex_val = f"0{val:X}h" if val < 10 else f"{val:X}h"
                    
                    if f", {val}" in disasm or f", {hex_val}" in disasm:
                        func_name = idc.get_func_name(ea)
                        
                        category_assignments[val].append({
                            'addr': ea,
                            'disasm': disasm,
                            'func': func_name
                        })
                        break
        
        ea = idc.next_head(ea, seg.end_ea)

print("Results:\n")

for val in target_values:
    assignments = category_assignments[val]
    print(f"Category {val}: {len(assignments)} assignments")
    
    for a in assignments:
        print(f"  0x{a['addr']:05X} in {a['func']}")
        print(f"    {a['disasm']}")
    
    if assignments:
        print()

print("\n" + "="*70)
print("SEARCHING FOR BUILDING/GROUND OBJECT SPAWNERS")
print("="*70 + "\n")

# Category 4 = BUILDING, so look for building/structure initialization
print("Looking for functions that might spawn buildings (category 4)...\n")

# Check functions with 'building', 'ground', 'structure', 'farobj' in name
building_funcs = []

for seg_ea in idautils.Segments():
    for func_ea in idautils.Functions(seg_ea, idc.get_segm_end(seg_ea)):
        func_name = idc.get_func_name(func_ea)
        
        if any(keyword in func_name.lower() for keyword in 
               ['building', 'ground', 'structure', 'farobj', 'static', 'terrain']):
            
            # Check if function writes to [X+0Ch]
            func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
            
            ea = func_ea
            writes_0c = False
            
            while ea < func_end:
                disasm = idc.generate_disasm_line(ea, 0)
                if "[si+0Ch]" in disasm or "[di+0Ch]" in disasm or "[bx+0Ch]" in disasm:
                    if idc.print_insn_mnem(ea) == "mov":
                        writes_0c = True
                        break
                ea = idc.next_head(ea, func_end)
            
            if writes_0c:
                building_funcs.append((func_ea, func_name))

print(f"Found {len(building_funcs)} potential building spawners:\n")

for func_ea, func_name in building_funcs[:15]:
    print(f"0x{func_ea:05X}: {func_name}")
    
    # Show [X+0Ch] writes in this function
    func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
    
    ea = func_ea
    writes = []
    
    while ea < func_end:
        if idc.print_insn_mnem(ea) == "mov":
            disasm = idc.generate_disasm_line(ea, 0)
            if "[si+0Ch]" in disasm or "[di+0Ch]" in disasm or "[bx+0Ch]" in disasm:
                writes.append((ea, disasm))
        ea = idc.next_head(ea, func_end)
    
    for addr, disasm in writes[:3]:
        print(f"    0x{addr:05X}: {disasm}")
    
    if len(writes) > 3:
        print(f"    ... ({len(writes) - 3} more)")
    print()

print("\n" + "="*70)
print("CHECKING ENTITY INIT FUNCTIONS")
print("="*70 + "\n")

# Search functions that call entity_slot_create
print("Functions that call entity_slot_create and write category:\n")

entity_create_addr = 0x2EBCD

for xref in idautils.XrefsTo(entity_create_addr):
    caller_addr = xref.frm
    caller_func_ea = idc.get_func_attr(caller_addr, idc.FUNCATTR_START)
    
    if caller_func_ea == idc.BADADDR:
        continue
    
    caller_func_name = idc.get_func_name(caller_func_ea)
    caller_func_end = idc.get_func_attr(caller_func_ea, idc.FUNCATTR_END)
    
    # Check if this function writes to [X+0Ch]
    ea = caller_func_ea
    category_writes = []
    
    while ea < caller_func_end:
        if idc.print_insn_mnem(ea) == "mov":
            disasm = idc.generate_disasm_line(ea, 0)
            if "[si+0Ch]" in disasm or "[di+0Ch]" in disasm or "[bx+0Ch]" in disasm:
                category_writes.append((ea, disasm))
        ea = idc.next_head(ea, caller_func_end)
    
    if category_writes:
        print(f"\n{caller_func_name} @ 0x{caller_func_ea:05X}:")
        print(f"  Calls entity_slot_create @ 0x{caller_addr:05X}")
        print(f"  Category writes ({len(category_writes)}):")
        
        for addr, disasm in category_writes[:5]:
            print(f"    0x{addr:05X}: {disasm}")
        
        if len(category_writes) > 5:
            print(f"    ... ({len(category_writes) - 5} more)")

print("\n" + "="*70)
print("ANALYZING PROJECTILE CATEGORIES (9-14, 19)")
print("="*70 + "\n")

# We know weapons use categories 9-14, 19
# Check ag_weapon_entity_initialize for the mapping

print("Checking weapon type to category mapping in ag_weapon_entity_initialize:\n")

ag_func = 0x4C3C7
ag_end = 0x4CAE2

print(f"Function: ag_weapon_entity_initialize @ 0x{ag_func:05X}")
print("Looking for weapon type (BX register) comparisons...\n")

# Find all CMP BX, X instructions
ea = ag_func
weapon_checks = []

while ea < ag_end:
    mnem = idc.print_insn_mnem(ea)
    if mnem == "cmp":
        disasm = idc.generate_disasm_line(ea, 0)
        if "bx," in disasm:
            weapon_checks.append((ea, disasm))
    ea = idc.next_head(ea, ag_end)

print(f"Found {len(weapon_checks)} weapon type checks:\n")

for addr, disasm in weapon_checks[:20]:
    print(f"  0x{addr:05X}: {disasm}")
    
    # Show next few instructions (branch to weapon init code)
    next_ea = idc.next_head(addr, ag_end)
    for i in range(3):
        next_disasm = idc.generate_disasm_line(next_ea, 0)
        print(f"             {next_disasm}")
        next_ea = idc.next_head(next_ea, ag_end)
    print()

if len(weapon_checks) > 20:
    print(f"... ({len(weapon_checks) - 20} more checks)")

print("\nRemaining categories search complete.")
output_file.close()
idc.qexit(0)
