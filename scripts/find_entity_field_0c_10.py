import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\entity_0c_10_fields.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Searching for EntitySlotRecord fields +0x0C and +0x10...")
idaapi.auto_wait()

print("=== BREAKTHROUGH DISCOVERY ===")
print("r12_farptr_load_thunk @ 0x41B32 reveals:")
print("  DI = EntitySlotRecord array at 0x54AF:0x386Fh")
print("  Stride = 0x5C (92 bytes)")
print("  [si+7Ah] = target entity slot index!")
print()
print("So in store_impact_step:")
print("  SI = weapon entity")
print("  DI = target entity (loaded via SI+0x7A index)")
print("  Both are EntitySlotRecord structures!")
print()
print("[di+0Ch] = target entity object_category (4=building)")
print("[di+10h] = target entity impact_state")
print()

# Search for field +0x10 accesses
print("=== Searching for Entity Field +0x10 (impact_state) ===\n")

field_10_refs = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for +10h with various registers
            if ("+10h]" in disasm or "+0x10]" in disasm or "+16]" in disasm) and "[" in disasm:
                # Make sure it's entity-related (si, di, bx patterns)
                if any(reg in disasm for reg in ["si+10h", "di+10h", "bx+10h", "si+0x10", "di+0x10", "bx+0x10"]):
                    func_name = idc.get_func_name(ea)
                    mnem = idc.print_insn_mnem(ea)
                    field_10_refs.append((ea, func_name, mnem, disasm))
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(field_10_refs)} references to entity field +0x10:\n")

# Group by function and operation
func_groups = {}
for ea, func_name, mnem, disasm in field_10_refs:
    if func_name:
        if func_name not in func_groups:
            func_groups[func_name] = []
        func_groups[func_name].append((ea, mnem, disasm))

print(f"Used in {len(func_groups)} different functions:\n")
for func_name in sorted(func_groups.keys())[:20]:
    refs = func_groups[func_name]
    print(f"\n{func_name}: {len(refs)} references")
    
    # Count operations
    ops = {}
    for ea, mnem, disasm in refs:
        ops[mnem] = ops.get(mnem, 0) + 1
    print(f"  Operations: {ops}")
    
    # Show first few
    for ea, mnem, disasm in refs[:4]:
        print(f"  0x{ea:X}: {disasm}")

# Now search for field +0x0C (object_category) more carefully
print("\n\n=== Searching for Entity Field +0x0C (object_category) ===\n")

field_0c_refs = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for +0Ch patterns
            if ("+0Ch]" in disasm or "+0xC]" in disasm or "+12]" in disasm) and "[" in disasm:
                if any(reg in disasm for reg in ["si+0Ch", "di+0Ch", "bx+0Ch", "si+0xC", "di+0xC", "bx+0xC"]):
                    func_name = idc.get_func_name(ea)
                    mnem = idc.print_insn_mnem(ea)
                    field_0c_refs.append((ea, func_name, mnem, disasm))
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(field_0c_refs)} references to entity field +0x0C:\n")

func_groups_0c = {}
for ea, func_name, mnem, disasm in field_0c_refs:
    if func_name:
        if func_name not in func_groups_0c:
            func_groups_0c[func_name] = []
        func_groups_0c[func_name].append((ea, mnem, disasm))

for func_name in sorted(func_groups_0c.keys())[:20]:
    refs = func_groups_0c[func_name]
    print(f"\n{func_name}: {len(refs)} references")
    
    # Count operations
    ops = {}
    for ea, mnem, disasm in refs:
        ops[mnem] = ops.get(mnem, 0) + 1
    print(f"  Operations: {ops}")
    
    for ea, mnem, disasm in refs[:4]:
        print(f"  0x{ea:X}: {disasm}")

# Search for what VALUES are written to +0x0C
print("\n\n=== Values Written to Entity Field +0x0C ===\n")

writes_0c = []
for ea, func_name, mnem, disasm in field_0c_refs:
    if mnem in ["mov", "movw"]:
        # Try to extract the value being written
        try:
            # Check if this is a write (destination is memory)
            op0 = idc.print_operand(ea, 0)
            if "[" in op0 and "+0Ch" in op0:
                val = idc.get_operand_value(ea, 1)
                if val < 0x100:
                    writes_0c.append((ea, val, func_name, disasm))
        except:
            pass

print(f"Found {len(writes_0c)} writes to field +0x0C:\n")

# Group by value
value_groups = {}
for ea, val, func_name, disasm in writes_0c:
    if val not in value_groups:
        value_groups[val] = []
    value_groups[val].append((ea, func_name, disasm))

for val in sorted(value_groups.keys()):
    locs = value_groups[val]
    print(f"\nValue {val} (0x{val:X}): {len(locs)} writes")
    for ea, func_name, disasm in locs[:5]:
        print(f"  0x{ea:X} in {func_name}: {disasm}")

# Search for values written to +0x10
print("\n\n=== Values Written to Entity Field +0x10 ===\n")

writes_10 = []
for ea, func_name, mnem, disasm in field_10_refs:
    if mnem in ["mov", "movb"]:
        try:
            op0 = idc.print_operand(ea, 0)
            if "[" in op0 and "+10h" in op0:
                val = idc.get_operand_value(ea, 1)
                if val < 0x100:
                    writes_10.append((ea, val, func_name, disasm))
        except:
            pass

print(f"Found {len(writes_10)} writes to field +0x10:\n")

value_groups_10 = {}
for ea, val, func_name, disasm in writes_10:
    if val not in value_groups_10:
        value_groups_10[val] = []
    value_groups_10[val].append((ea, func_name, disasm))

for val in sorted(value_groups_10.keys()):
    locs = value_groups_10[val]
    print(f"\nValue {val} (0x{val:X}): {len(locs)} writes")
    for ea, func_name, disasm in locs[:5]:
        print(f"  0x{ea:X} in {func_name}: {disasm}")

print("\n\nEntity field +0x0C and +0x10 analysis complete.")
output_file.close()
idc.qexit(0)
