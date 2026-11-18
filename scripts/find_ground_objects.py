import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\ground_objects_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting ground objects investigation...")
idaapi.auto_wait()

print("=== STRATEGY ===")
print("Ground objects (buildings, tanks, ships) are likely:")
print("1. Separate entity category (not aircraft, not weapons)")
print("2. Have entity status_flags +0x74 bit 6 (AIRCRAFT_TYPE) = 0")
print("3. Checked in target_cycle_scan which filters for aircraft AND ground targets")
print("4. May have different entity type values or separate type field")
print()

# Search for tank/ship/vehicle strings
print("=== Searching for Ground Object Type Strings ===\n")

ground_object_keywords = [
    b"TANK",
    b"VEHICLE",
    b"TRUCK",
    b"SAM",
    b"AAA",
    b"RADAR",
    b"SHIP",
    b"CARRIER",
    b"DESTROYER",
    b"FRIGATE",
    b"CRUISER",
    b"REACTOR",
    b"NUCLEAR",
    b"POWER PLANT",
    b"SAM SITE",
    b"SCUD",
    b"ARMOR",
    b"APC",
    b"BMP",
    b"T-72",
    b"T-80",
]

found_strings = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" not in seg_name:
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            for keyword in ground_object_keywords:
                str_val = idc.get_bytes(ea, len(keyword))
                if str_val and str_val.upper() == keyword:
                    try:
                        full_str = idc.get_strlit_contents(ea)
                        if full_str:
                            decoded = full_str.decode('ascii', errors='ignore')
                            found_strings.append((ea, keyword.decode('ascii'), decoded))
                            ea += len(full_str)
                            break
                    except:
                        pass
            ea += 1

print(f"Found {len(found_strings)} ground object strings:\n")
for addr, keyword, full_text in found_strings:
    print(f"0x{addr:X} [{keyword}]: '{full_text[:60]}'")

# Now check for xrefs to these strings
print("\n\n=== Code References to Ground Object Strings ===\n")

for addr, keyword, full_text in found_strings[:15]:  # First 15
    xrefs = list(idautils.DataRefsTo(addr))
    if xrefs:
        print(f"\n'{keyword}' @ 0x{addr:X}:")
        print(f"  {len(xrefs)} code references:")
        for xref in xrefs[:3]:
            func_name = idc.get_func_name(xref)
            print(f"    0x{xref:X} in {func_name if func_name else 'unknown'}")

# Search for entity type checks that exclude aircraft (NOT bit 6)
print("\n\n=== Searching for Ground Object Entity Type Checks ===\n")
print("Looking for code that checks status_flags +0x74 WITHOUT bit 6 (AIRCRAFT_TYPE)...\n")

ground_entity_checks = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            # Look for test instruction with bit 6 (0x40) on field +0x74
            mnem = idc.print_insn_mnem(ea)
            if mnem == "test":
                op0 = idc.print_operand(ea, 0)
                op1 = idc.print_operand(ea, 1)
                # Check for [reg+74h] AND 0x40 pattern
                if "+74h" in op0 or "+0x74" in op0:
                    try:
                        val = idc.get_operand_value(ea, 1)
                        func_name = idc.get_func_name(ea)
                        ground_entity_checks.append((ea, val, func_name))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(ground_entity_checks)} checks of entity status_flags +0x74:\n")

# Group by test value
value_groups = {}
for ea, val, func_name in ground_entity_checks:
    if val not in value_groups:
        value_groups[val] = []
    value_groups[val].append((ea, func_name))

for val in sorted(value_groups.keys()):
    locs = value_groups[val]
    bit_desc = ""
    if val == 0x40:
        bit_desc = " (bit 6 = AIRCRAFT_TYPE)"
    elif val == 0x01:
        bit_desc = " (bit 0 = ACTIVE)"
    elif val == 0x04:
        bit_desc = " (bit 2 = DESTROYED?)"
    
    print(f"\nTest value 0x{val:02X}{bit_desc}: {len(locs)} checks")
    for ea, func_name in locs[:8]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")

# Look at target_cycle_scan more carefully for ground object handling
print("\n\n=== Detailed Analysis: target_cycle_scan @ 0x48B05 ===\n")
print("This function cycles targets for both aircraft and ground objects\n")

func_start = 0x48B05
func_end = idc.find_func_end(func_start)

# Disassemble looking for branch logic that might separate aircraft/ground
print("Looking for branching logic and type checks:\n")

ea = func_start
branch_count = 0
type_check_count = 0

while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    disasm = idc.generate_disasm_line(ea, 0)
    
    # Look for conditional jumps (branching logic)
    if mnem in ["jz", "jnz", "je", "jne", "jl", "jg", "jle", "jge", "ja", "jb", "jae", "jbe"]:
        branch_count += 1
        if branch_count <= 15:  # Show first 15 branches
            print(f"  0x{ea:X}: {disasm}")
    
    # Look for comparisons that might distinguish object types
    if mnem == "cmp":
        op0 = idc.print_operand(ea, 0)
        if "[" in op0:  # Memory operand (entity field)
            type_check_count += 1
            if type_check_count <= 15:
                print(f"  0x{ea:X}: {disasm}")
    
    ea = idc.next_head(ea, func_end)

print(f"\nTotal: {branch_count} branches, {type_check_count} entity field comparisons")

# Search for entity allocation/initialization functions for ground objects
print("\n\n=== Searching for Ground Object Spawn Functions ===\n")
print("Looking for functions that initialize non-aircraft entities...\n")

# Search for functions that write to status_flags +0x74 WITHOUT setting bit 6
spawn_candidates = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            # Look for mov to [reg+74h]
            if mnem in ["mov", "movb"]:
                op0 = idc.print_operand(ea, 0)
                if "+74h" in op0 or "+0x74" in op0:
                    op1 = idc.print_operand(ea, 1)
                    try:
                        val = idc.get_operand_value(ea, 1)
                        # Look for values that DON'T have bit 6 set
                        if val < 0x100 and (val & 0x40) == 0 and val != 0:
                            func_name = idc.get_func_name(ea)
                            spawn_candidates.append((ea, val, func_name))
                    except:
                        pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(spawn_candidates)} writes to status_flags +0x74 WITHOUT aircraft bit:\n")

# Group by value
spawn_value_groups = {}
for ea, val, func_name in spawn_candidates:
    if val not in spawn_value_groups:
        spawn_value_groups[val] = []
    spawn_value_groups[val].append((ea, func_name))

for val in sorted(spawn_value_groups.keys()):
    locs = spawn_value_groups[val]
    bits = []
    if val & 0x01:
        bits.append("ACTIVE")
    if val & 0x04:
        bits.append("DESTROYED")
    bits_str = "|".join(bits) if bits else "none"
    
    print(f"\nValue 0x{val:02X} ({bits_str}): {len(locs)} writes")
    for ea, func_name in locs[:5]:
        print(f"  0x{ea:X} in {func_name if func_name else 'unknown'}")

# Look for ship/vehicle/tank specific entity types
print("\n\n=== Searching for Non-Weapon, Non-Aircraft Entity Type Values ===\n")
print("Entity +0x75 values: 0x00-0x11 (non-weapons) excluding 0x00...")
print("These might be ground object types\n")

# We already searched for +0x75 comparisons < 0x12 earlier
# Let's search for ANY read of field +0x75 in ground-object-related functions

print("Looking for reads of entity +0x75 field in any context:\n")

type_reads = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for any instruction mentioning +75h
            if "+75h" in disasm or "+0x75" in disasm:
                func_name = idc.get_func_name(ea)
                type_reads.append((ea, func_name, disasm))
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(type_reads)} instructions accessing entity field +0x75:\n")

# Group by function
func_groups = {}
for ea, func_name, disasm in type_reads:
    if func_name:
        if func_name not in func_groups:
            func_groups[func_name] = []
        func_groups[func_name].append((ea, disasm))

print(f"Accessed in {len(func_groups)} different functions:\n")
for func_name in sorted(func_groups.keys())[:20]:  # First 20 functions
    accesses = func_groups[func_name]
    print(f"\n{func_name}: {len(accesses)} accesses")
    for ea, disasm in accesses[:3]:  # First 3 per function
        print(f"  0x{ea:X}: {disasm}")

print("\n\nGround objects investigation complete.")
output_file.close()
idc.qexit(0)
