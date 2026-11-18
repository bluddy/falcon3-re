import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\target_hit_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting target hit detection analysis...")
idaapi.auto_wait()

# Key function: damage_event_dispatch_handler @ 0x2EAA7
# This is called when something gets hit - let's see what it checks

print("\n=== Analysis of damage_event_dispatch_handler @ 0x2EAA7 ===\n")
func_start = 0x2EAA7
func_end = idc.find_func_end(func_start)
print(f"Function size: {func_end - func_start} bytes (0x{func_start:X} - 0x{func_end:X})\n")

# Disassemble the function to see the logic
print("Disassembly (first 80 instructions):\n")
ea = func_start
count = 0
while ea < func_end and count < 80:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"  {disasm}")
    ea = idc.next_head(ea, func_end)
    count += 1

print("\n=== Looking for entity type checks in damage handler ===\n")
# Find all CMP instructions that check entity fields
ea = func_start
while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    if mnem == "cmp":
        op0 = idc.print_operand(ea, 0)
        op1 = idc.print_operand(ea, 1)
        # Entity field access patterns: [si+XX], [bx+XX], [di+XX]
        if "[" in op0 and "+" in op0:
            val = idc.get_operand_value(ea, 1)
            if 0 <= val <= 0x50:
                print(f"0x{ea:X}: cmp {op0}, {op1} (checking field against 0x{val:X})")
    ea = idc.next_head(ea, func_end)

# Look at entity_ground_collision_check @ 0x47787
# This is called when a bomb/missile hits the ground
print("\n\n=== Analysis of entity_ground_collision_check @ 0x47787 ===\n")
func_start = 0x47787
func_end = idc.find_func_end(func_start)
print(f"Function size: {func_end - func_start} bytes (0x{func_start:X} - 0x{func_end:X})\n")

print("Disassembly:\n")
ea = func_start
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"  {disasm}")
    ea = idc.next_head(ea, func_end)

# Find what calls entity_ground_collision_check
print("\n=== Functions that call entity_ground_collision_check ===\n")
xrefs = list(idautils.CodeRefsTo(0x47787, True))
print(f"Called from {len(xrefs)} locations:\n")
for xref in xrefs:
    func_name = idc.get_func_name(xref)
    print(f"  0x{xref:X} in {func_name if func_name else 'unknown'}")

# Look at store_impact_step @ 0x397FB
# This records where weapons hit
print("\n\n=== Analysis of store_impact_step @ 0x397FB ===\n")
func_start = 0x397FB
func_end = idc.find_func_end(func_start)
print(f"Function size: {func_end - func_start} bytes (0x{func_start:X} - 0x{func_end:X})\n")

print("Disassembly:\n")
ea = func_start
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"  {disasm}")
    ea = idc.next_head(ea, func_end)

print("\n\n=== Looking for building/facility entity types ===\n")
# Search for comparisons with entity type values in 0x08-0x20 range
# (weapons are 0x12-0x37, so buildings likely lower)
print("Searching all code for entity type checks in range 0x08-0x20...\n")

building_type_checks = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "cmp":
                op0 = idc.print_operand(ea, 0)
                op1 = idc.print_operand(ea, 1)
                # Look for entity field +0x75 (weapon_type/entity_type)
                if "[" in op0 and "+75h" in op0.lower():
                    val = idc.get_operand_value(ea, 1)
                    if 0x08 <= val <= 0x20:
                        func_name = idc.get_func_name(ea)
                        building_type_checks.append((ea, val, func_name))
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(building_type_checks)} checks for entity types 0x08-0x20:\n")
for ea, val, func_name in building_type_checks[:20]:
    print(f"  0x{ea:X}: type check 0x{val:X} in {func_name if func_name else 'unknown'}")

print("\n\nTarget hit detection analysis complete.")
output_file.close()
idc.qexit(0)
