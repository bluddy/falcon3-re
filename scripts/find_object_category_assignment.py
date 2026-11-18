import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\object_category_init.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Searching for object_category assignment code...")
idaapi.auto_wait()

print("=== STRATEGY ===")
print("Find where EntitySlotRecord +0x0C (object_category) is initialized")
print("Look for MOV instructions that write constant values to [reg+0Ch]")
print()

# Search for all writes to offset +0Ch in entity context
print("=== Searching for Writes to [entity+0Ch] ===\n")

# We need to search more broadly - look for mov with memory dest
category_writes = []

for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for mov/movw to memory
            if mnem in ["mov", "movw"]:
                disasm = idc.generate_disasm_line(ea, 0)
                
                # Check if destination looks like entity offset +0Ch
                # Patterns: [si+0Ch], [di+0Ch], [bx+0Ch], word ptr [...]
                if ("word ptr [" in disasm or "word [" in disasm) and \
                   ("+0Ch" in disasm or "+12]" in disasm or "+0xC" in disasm):
                    
                    # Try to get the source value
                    try:
                        src_val = idc.get_operand_value(ea, 1)
                        if src_val < 20:  # Reasonable category value
                            func_name = idc.get_func_name(ea)
                            category_writes.append((ea, src_val, func_name, disasm))
                    except:
                        # Might be register source, not immediate
                        op1 = idc.print_operand(ea, 1)
                        if not "[" in op1:  # Not memory-to-memory
                            func_name = idc.get_func_name(ea)
                            category_writes.append((ea, -1, func_name, disasm))
            
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(category_writes)} potential writes to object_category:\n")

# Group by value
value_groups = {}
reg_writes = []

for ea, val, func_name, disasm in category_writes:
    if val == -1:
        reg_writes.append((ea, func_name, disasm))
    else:
        if val not in value_groups:
            value_groups[val] = []
        value_groups[val].append((ea, func_name, disasm))

print("Immediate value writes:\n")
for val in sorted(value_groups.keys()):
    writes = value_groups[val]
    print(f"\nValue {val}: {len(writes)} writes")
    for ea, func_name, disasm in writes[:5]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")
        print(f"    {disasm}")

if reg_writes:
    print(f"\n\nRegister/indirect writes: {len(reg_writes)}")
    for ea, func_name, disasm in reg_writes[:15]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}: {disasm}")

# Look for entity initialization/spawn functions
print("\n\n=== Looking for Entity Spawn Functions ===\n")
print("Functions with 'spawn', 'create', 'init', 'alloc' in name:\n")

spawn_funcs = []
for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    if func_name:
        name_lower = func_name.lower()
        if any(keyword in name_lower for keyword in ['spawn', 'create', 'init', 'alloc', 'entity', 'farobj']):
            func_end = idc.find_func_end(func_ea)
            spawn_funcs.append((func_ea, func_name, func_end - func_ea))

print(f"Found {len(spawn_funcs)} potential entity initialization functions:\n")

for addr, name, size in sorted(spawn_funcs, key=lambda x: x[2], reverse=True)[:30]:
    print(f"  0x{addr:X}: {name} ({size}B)")

# Analyze ag_weapon_entity_initialize for how it sets up weapons
print("\n\n=== Analyzing ag_weapon_entity_initialize @ 0x4C3C7 ===\n")
print("This function initializes A-G weapons - let's see if it sets object_category\n")

func_start = 0x4C3C7
func_end = idc.find_func_end(func_start)

# Look for offset +0Ch writes
ea = func_start
found_0c = []
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    if "+0Ch" in disasm or "+0xC" in disasm or "+12]" in disasm:
        found_0c.append((ea, disasm))
    ea = idc.next_head(ea, func_end)

if found_0c:
    print(f"Found {len(found_0c)} references to offset +0Ch:")
    for ea, disasm in found_0c:
        print(f"  0x{ea:X}: {disasm}")
else:
    print("No references to +0Ch found - weapon init might not set category")
    print("OR weapons use different initialization path")

# Check entity_slot_create or similar
print("\n\n=== Looking for entity_slot_create or similar ===\n")

entity_create_funcs = []
for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    if func_name and 'slot' in func_name.lower() and ('create' in func_name.lower() or 'alloc' in func_name.lower()):
        entity_create_funcs.append((func_ea, func_name))

if entity_create_funcs:
    print(f"Found {len(entity_create_funcs)} entity slot functions:\n")
    for addr, name in entity_create_funcs:
        print(f"0x{addr:X}: {name}")
        
        # Analyze first one
        if addr == entity_create_funcs[0][0]:
            print(f"\nAnalyzing {name}:")
            func_end = idc.find_func_end(addr)
            
            ea = addr
            count = 0
            while ea < func_end and count < 40:
                disasm = idc.generate_disasm_line(ea, 0)
                if "mov" in disasm or "lea" in disasm:
                    print(f"  {disasm}")
                    count += 1
                ea = idc.next_head(ea, func_end)
else:
    print("No entity_slot_create functions found")

# Look at target_cycle_scan to see how it checks categories
print("\n\n=== Checking target_cycle_scan @ 0x48B05 ===\n")
print("Does it read object_category to filter targets?\n")

func_start = 0x48B05
func_end = idc.find_func_end(func_start)

ea = func_start
cat_refs = []
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    if "+0Ch" in disasm or "+0xC" in disasm:
        cat_refs.append((ea, disasm))
    ea = idc.next_head(ea, func_end)

if cat_refs:
    print(f"Found {len(cat_refs)} references to +0Ch:")
    for ea, disasm in cat_refs:
        print(f"  0x{ea:X}: {disasm}")
else:
    print("No direct category checks in target_cycle_scan")
    print("Category filtering might happen in called functions")

print("\n\nObject category assignment search complete.")
output_file.close()
idc.qexit(0)
