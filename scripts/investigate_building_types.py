import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\building_types_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting building type investigation...")
idaapi.auto_wait()

# We know weapons use entity field +0x75 for weapon type (0x12-0x37)
# Buildings might use the same field with different values (0x00-0x11?)
# OR they might use a different field entirely

print("=== STRATEGY ===")
print("1. Search for comparisons with field +0x75 that check values BELOW 0x12 (non-weapons)")
print("2. Check store_impact_step @ 0x397FB for entity type detection")
print("3. Look at [di+0Ch] field which was == 4 for buildings")
print("4. Search for RUNWAY/HANGAR string xrefs to find type assignment code\n")

# Strategy 1: Find low-value comparisons with field +0x75
print("\n=== Searching for entity type +0x75 comparisons with values < 0x12 ===\n")

low_type_checks = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "cmp":
                op0 = idc.print_operand(ea, 0)
                # Look for [reg+75h] patterns
                if "+75h" in op0.lower() or "+0x75" in op0.lower():
                    try:
                        val = idc.get_operand_value(ea, 1)
                        if 0 <= val < 0x12:  # Below weapon range
                            func_name = idc.get_func_name(ea)
                            low_type_checks.append((ea, val, func_name))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(low_type_checks)} comparisons with entity type +0x75 in range 0x00-0x11:\n")
for ea, val, func_name in low_type_checks[:30]:
    print(f"  0x{ea:X}: cmp [?+75h], 0x{val:X} in {func_name if func_name else 'unknown'}")

# Strategy 2: Deep analysis of store_impact_step
print("\n\n=== Deep Analysis: store_impact_step @ 0x397FB ===\n")
print("This function checks [di+0Ch] == 4 for buildings")
print("Let's see what entity type values are checked around that code:\n")

func_start = 0x397FB
func_end = idc.find_func_end(func_start)
ea = func_start

# Find the [di+0Ch] check
print("Looking for [di+0Ch] and nearby type checks:\n")
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    # Look for di+0Ch or di+C
    if ("[di+0Ch]" in disasm or "[di+0xC]" in disasm or "[di+C]" in disasm or 
        "di+75h" in disasm or "di+0x75" in disasm):
        print(f"  0x{ea:X}: {disasm}")
    ea = idc.next_head(ea, func_end)

# Strategy 3: Search for functions that SET field +0x75 (initialization)
print("\n\n=== Searching for code that WRITES to entity field +0x75 ===\n")
print("(This would show entity type assignment during spawn)\n")

type_writers = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ["mov", "movb"]:
                op0 = idc.print_operand(ea, 0)
                # Look for writes to [reg+75h]
                if "+75h" in op0.lower() or "+0x75" in op0.lower():
                    op1 = idc.print_operand(ea, 1)
                    try:
                        val = idc.get_operand_value(ea, 1)
                        if val < 0x100:  # Reasonable type value
                            func_name = idc.get_func_name(ea)
                            type_writers.append((ea, val, func_name))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(type_writers)} writes to entity field +0x75:\n")

# Group by value
value_groups = {}
for ea, val, func_name in type_writers:
    if val not in value_groups:
        value_groups[val] = []
    value_groups[val].append((ea, func_name))

for val in sorted(value_groups.keys()):
    locs = value_groups[val]
    print(f"\nValue 0x{val:02X}: {len(locs)} writes")
    for ea, func_name in locs[:5]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")

# Strategy 4: Check for building name string xrefs
print("\n\n=== Checking Building Name String References ===\n")

building_strings = [
    (0x15020D, "HANGAR"),
    (0x150214, "RUNWAY"),
    (0x15022D, "BRIDGE"),
    (0x150284, "FACTORY"),
    (0x150293, "WAREHOUSE"),
]

for addr, name in building_strings:
    print(f"\n{name} @ 0x{addr:X}:")
    xrefs = list(idautils.DataRefsTo(addr))
    if xrefs:
        print(f"  {len(xrefs)} code references:")
        for xref in xrefs[:5]:
            func_name = idc.get_func_name(xref)
            print(f"    0x{xref:X} in {func_name if func_name else 'unknown'}")
            # Show a few instructions around the reference
            print(f"      {idc.generate_disasm_line(xref, 0)}")
            next_ea = idc.next_head(xref, xref + 20)
            if next_ea != idc.BADADDR:
                print(f"      {idc.generate_disasm_line(next_ea, 0)}")
    else:
        print("  NO CODE REFERENCES (string may be display-only)")

# Strategy 5: Look at field +0x0C which was checked == 4
print("\n\n=== Searching for entity field +0x0C (checked == 4 in store_impact_step) ===\n")

field_0c_checks = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "cmp":
                op0 = idc.print_operand(ea, 0)
                # Look for [reg+0Ch] patterns
                if ("+0Ch]" in op0 or "+0xC]" in op0 or "+12]" in op0 or 
                    "di+0Ch" in op0 or "si+0Ch" in op0 or "bx+0Ch" in op0):
                    try:
                        val = idc.get_operand_value(ea, 1)
                        if 0 <= val <= 10:
                            func_name = idc.get_func_name(ea)
                            field_0c_checks.append((ea, val, func_name, op0))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(field_0c_checks)} comparisons with entity field +0x0C:\n")

# Group by value
value_groups_0c = {}
for ea, val, func_name, op0 in field_0c_checks:
    if val not in value_groups_0c:
        value_groups_0c[val] = []
    value_groups_0c[val].append((ea, func_name))

for val in sorted(value_groups_0c.keys()):
    locs = value_groups_0c[val]
    print(f"\nValue {val}: {len(locs)} checks")
    for ea, func_name in locs[:10]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")

print("\n\nBuilding type investigation complete.")
output_file.close()
idc.qexit(0)
