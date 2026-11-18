import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\farptr_load_analysis.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Analyzing far pointer load functions...")
idaapi.auto_wait()

# store_impact_step calls r12_farptr_load_thunk with AX = [si+7Ah]
# This loads DI with a far pointer to some structure
# DI then has fields at +0x0C and +0x10

print("=== store_impact_step Analysis ===\n")
print("At 0x39833: mov ax, [si+7Ah]")
print("At 0x39836: call r12_farptr_load_thunk")
print("Result: ES:DI points to some structure")
print()
print("DI structure fields accessed:")
print("  [di+0Ch] - compared with 4 (type field?)")
print("  [di+10h] - impact state (0xFF=pristine, 0xA0=impacted)")
print()
print("SI is EntitySlotRecord, so [si+7Ah] at offset 0x7A is:")
print("  According to our registry: data_7A_95 (unknown bytes)")
print()

# Find r12_farptr_load_thunk
print("=== Analyzing r12_farptr_load_thunk ===\n")

thunk_addr = idc.get_name_ea_simple("r12_farptr_load_thunk")
if thunk_addr != idc.BADADDR:
    print(f"Found at 0x{thunk_addr:X}\n")
    func_end = idc.find_func_end(thunk_addr)
    
    print("Disassembly:\n")
    ea = thunk_addr
    count = 0
    while ea < func_end and count < 30:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"  {disasm}")
        ea = idc.next_head(ea, func_end)
        count += 1
else:
    print("r12_farptr_load_thunk not found, searching...")

# Search for all functions with "farptr_load" in name
print("\n\n=== All farptr_load Functions ===\n")

farptr_funcs = []
for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    if func_name and "farptr" in func_name.lower() and "load" in func_name.lower():
        func_end = idc.find_func_end(func_ea)
        farptr_funcs.append((func_ea, func_name, func_end - func_ea))

for addr, name, size in farptr_funcs:
    print(f"0x{addr:X}: {name} ({size}B)")

# Analyze what r08_farptr_load_thunk does (used elsewhere)
print("\n\n=== Analyzing r08_farptr_load_thunk Pattern ===\n")

r08_addr = idc.get_name_ea_simple("r08_farptr_load_thunk")
if r08_addr != idc.BADADDR:
    print(f"Found at 0x{r08_addr:X}\n")
    func_end = idc.find_func_end(r08_addr)
    
    print("Disassembly:\n")
    ea = r08_addr
    count = 0
    while ea < func_end and count < 30:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"  {disasm}")
        ea = idc.next_head(ea, func_end)
        count += 1

# Search for references to entity field +0x7A
print("\n\n=== Searching for Entity Field +0x7A Usage ===\n")
print("This field is used as index to load far pointer in store_impact_step\n")

field_7a_refs = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for +7Ah or +0x7A
            if ("+7Ah" in disasm or "+0x7A" in disasm or "+122]" in disasm) and "[" in disasm:
                func_name = idc.get_func_name(ea)
                field_7a_refs.append((ea, func_name, disasm))
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(field_7a_refs)} references to field +0x7A:\n")

# Group by function
func_groups = {}
for ea, func_name, disasm in field_7a_refs:
    if func_name:
        if func_name not in func_groups:
            func_groups[func_name] = []
        func_groups[func_name].append((ea, disasm))

print(f"Used in {len(func_groups)} different functions:\n")
for func_name in sorted(func_groups.keys())[:20]:
    refs = func_groups[func_name]
    print(f"\n{func_name}: {len(refs)} references")
    for ea, disasm in refs[:3]:
        print(f"  0x{ea:X}: {disasm}")

# Look for the structure that DI points to
print("\n\n=== Investigating DI Structure (with +0x0C and +0x10 fields) ===\n")
print("This structure has:")
print("  +0x0C: word (type field, checked == 4)")
print("  +0x10: byte (impact state: 0xFF, 0xA0)")
print()
print("Searching for other accesses to these fields...")

# Search for [di+0Ch] accesses
di_0c_refs = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            if "di+0Ch" in disasm or "di+0xC" in disasm or ("di+12]" in disasm and "[" in disasm):
                func_name = idc.get_func_name(ea)
                di_0c_refs.append((ea, func_name, disasm))
            ea = idc.next_head(ea, seg_end)

print(f"\nFound {len(di_0c_refs)} references to [di+0Ch]:\n")

# Group by function
func_groups_0c = {}
for ea, func_name, disasm in di_0c_refs:
    if func_name:
        if func_name not in func_groups_0c:
            func_groups_0c[func_name] = []
        func_groups_0c[func_name].append((ea, disasm))

for func_name in sorted(func_groups_0c.keys())[:15]:
    refs = func_groups_0c[func_name]
    print(f"\n{func_name}: {len(refs)} references")
    for ea, disasm in refs[:3]:
        print(f"  0x{ea:X}: {disasm}")

print("\n\nFar pointer load analysis complete.")
output_file.close()
idc.qexit(0)
