import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\farobj_types_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting FarObj entity type investigation...")
idaapi.auto_wait()

print("=== NEW THEORY ===")
print("We've been looking at EntitySlotRecord (16 slots @ 0x54AF:0x386F)")
print("But there's also FarObj structure (main game object at R05_400C:0x34)")
print()
print("From registry/structs.yaml FarObj structure:")
print("  +0x12: render_flags")
print("  +0x13: type_flags")
print("  +0x14: entity_class (0x12=aircraft, 0x14=?, 0x33=?, 0x38=?)")
print("  +0x22: object_kind (index to type descriptor)")
print()
print("Ground objects (tanks, ships, SAMs) likely use FarObj.entity_class field!")
print()

# Search for entity_class field +0x14 comparisons
print("=== Searching for FarObj entity_class (+0x14) Comparisons ===\n")

entity_class_checks = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "cmp":
                op0 = idc.print_operand(ea, 0)
                # Look for [reg+14h] patterns
                if "+14h" in op0 or "+0x14" in op0 or "+20]" in op0:
                    try:
                        val = idc.get_operand_value(ea, 1)
                        if 0 <= val < 0x100:
                            func_name = idc.get_func_name(ea)
                            entity_class_checks.append((ea, val, func_name, op0))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(entity_class_checks)} comparisons with field +0x14:\n")

# Group by value
value_groups = {}
for ea, val, func_name, op0 in entity_class_checks:
    if val not in value_groups:
        value_groups[val] = []
    value_groups[val].append((ea, func_name))

for val in sorted(value_groups.keys())[:25]:  # First 25 distinct values
    locs = value_groups[val]
    desc = ""
    if val == 0x12:
        desc = " (AIRCRAFT - known from registry)"
    elif val == 0x14:
        desc = " (unknown entity type)"
    elif val == 0x33:
        desc = " (unknown entity type)"
    elif val == 0x38:
        desc = " (unknown entity type)"
    
    print(f"\nValue 0x{val:02X}{desc}: {len(locs)} checks")
    for ea, func_name in locs[:6]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")

# Search for object_kind field +0x22 - this indexes type descriptors
print("\n\n=== Searching for FarObj object_kind (+0x22) Usage ===\n")

object_kind_refs = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for +22h or +0x22 or +34 (decimal)
            if ("+22h" in disasm or "+0x22" in disasm or "+34]" in disasm) and "[" in disasm:
                func_name = idc.get_func_name(ea)
                object_kind_refs.append((ea, func_name, disasm))
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(object_kind_refs)} references to field +0x22 (object_kind):\n")

# Group by function
func_groups = {}
for ea, func_name, disasm in object_kind_refs:
    if func_name:
        if func_name not in func_groups:
            func_groups[func_name] = []
        func_groups[func_name].append((ea, disasm))

print(f"Used in {len(func_groups)} different functions:\n")
for func_name in sorted(func_groups.keys())[:15]:
    refs = func_groups[func_name]
    print(f"\n{func_name}: {len(refs)} references")
    for ea, disasm in refs[:3]:
        print(f"  0x{ea:X}: {disasm}")

# Look at farobj_entity_attr_setup which initializes entity attributes
print("\n\n=== Checking farobj_entity_attr_setup (known entity initializer) ===\n")

# This function is mentioned in registry - search for it
farobj_setup_addr = idc.get_name_ea_simple("farobj_entity_attr_setup")
if farobj_setup_addr != idc.BADADDR:
    print(f"Found farobj_entity_attr_setup @ 0x{farobj_setup_addr:X}")
    func_end = idc.find_func_end(farobj_setup_addr)
    
    print("\nLooking for entity_class assignments:\n")
    ea = farobj_setup_addr
    count = 0
    while ea < func_end and count < 50:
        disasm = idc.generate_disasm_line(ea, 0)
        # Look for writes to +0x14 or reads from +0x14
        if ("+14h" in disasm or "+0x14" in disasm) and "mov" in disasm:
            print(f"  0x{ea:X}: {disasm}")
        ea = idc.next_head(ea, func_end)
        count += 1
else:
    print("farobj_entity_attr_setup not found by name, searching for it...")

# Search for writes to entity_class field +0x14
print("\n\n=== Searching for Writes to entity_class Field (+0x14) ===\n")

entity_class_writes = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ["mov", "movb"]:
                op0 = idc.print_operand(ea, 0)
                if ("+14h" in op0 or "+0x14" in op0) and "[" in op0:
                    try:
                        val = idc.get_operand_value(ea, 1)
                        if val < 0x100:
                            func_name = idc.get_func_name(ea)
                            entity_class_writes.append((ea, val, func_name))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(entity_class_writes)} writes to entity_class field:\n")

# Group by value
write_value_groups = {}
for ea, val, func_name in entity_class_writes:
    if val not in write_value_groups:
        write_value_groups[val] = []
    write_value_groups[val].append((ea, func_name))

for val in sorted(write_value_groups.keys())[:20]:
    locs = write_value_groups[val]
    print(f"\nValue 0x{val:02X}: {len(locs)} writes")
    for ea, func_name in locs[:5]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")

# Search for the type descriptor table at 0x7B0E:0x3052
print("\n\n=== Analyzing Type Descriptor Table @ 0x7B0E:0x3052 ===\n")
print("FarObj.object_kind indexes this table (4-byte far pointers)\n")

# Calculate linear address: segment 0x7B0E, offset 0x3052
type_table_seg = 0x7B0E
type_table_off = 0x3052
type_table_addr = (type_table_seg << 4) + type_table_off

print(f"Type descriptor table at linear address: 0x{type_table_addr:X}")
print("\nReading first 32 type descriptor pointers (4 bytes each):\n")

for i in range(32):
    ptr_addr = type_table_addr + (i * 4)
    # Read 4 bytes (seg:off far pointer)
    try:
        offset = idc.get_wide_word(ptr_addr)
        segment = idc.get_wide_word(ptr_addr + 2)
        if offset != 0 or segment != 0:
            print(f"  Type {i:2d}: seg:off = 0x{segment:04X}:0x{offset:04X}")
    except:
        pass

# Look for SAM/AAA/Tank spawn functions
print("\n\n=== Searching for Ground Unit Spawn Pattern ===\n")
print("Looking for functions that reference both:")
print("- Ground object strings (TANK/SAM/AAA)")
print("- Entity initialization (field +0x14 or +0x22 writes)\n")

# Get functions that reference ground object strings
ground_string_funcs = set()
ground_strings = [
    (0x150277, "TANK"),
    (0x15024E, "SAM SITE"),
    (0x1503AC, "AAA"),
    (0x14EB06, "SHIP"),
    (0x150240, "NUCLEAR PLANT"),
    (0x14FF88, "RADAR SITE"),
]

for addr, name in ground_strings:
    xrefs = list(idautils.DataRefsTo(addr))
    for xref in xrefs:
        func = idc.get_func_name(xref)
        if func:
            ground_string_funcs.add(func)
            print(f"'{name}' referenced in: {func}")

print(f"\n{len(ground_string_funcs)} unique functions reference ground object strings")

print("\n\nFarObj entity type investigation complete.")
output_file.close()
idc.qexit(0)
