import idc
import idaapi
import sys

# Redirect output to file
output_file = open(r"C:\Users\ybarnoy\projects\falcon3\target_analysis_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting target system analysis...")
idaapi.auto_wait()

# Target-related functions found by find_target_system.py
target_functions = [
    (0x32D22, "mission_state_initializer"),
    (0x3E96F, "ai_target_priority_evaluator"),
    (0x4478D, "farobj_slot_target_search"),
    (0x48B05, "target_cycle_scan"),
    (0x2EAA7, "damage_event_dispatch_handler"),
    (0x397FB, "store_impact_step"),
    (0x47787, "entity_ground_collision_check")
]

print("\n=== Analyzing Target System Functions ===\n")

for addr, name in target_functions:
    print(f"\n--- {name} @ 0x{addr:X} ---")
    func_start = addr
    func_end = idc.find_func_end(func_start)
    if func_end == idc.BADADDR:
        print(f"ERROR: Cannot find function end for {name}")
        continue
    
    func_size = func_end - func_start
    print(f"Size: {func_size} bytes (0x{func_start:X} - 0x{func_end:X})")
    
    # Look for entity type comparisons (target buildings)
    ea = func_start
    type_checks = []
    while ea < func_end:
        mnem = idc.print_insn_mnem(ea)
        if mnem == "cmp":
            op0 = idc.print_operand(ea, 0)
            op1 = idc.print_operand(ea, 1)
            # Look for entity field comparisons
            if "[" in op0 and ("+" in op0 or "si" in op0 or "di" in op0 or "bx" in op0):
                try:
                    val = idc.get_operand_value(ea, 1)
                    if 0 <= val <= 0x40:  # Entity types likely in this range
                        type_checks.append((ea, op0, op1, val))
                except:
                    pass
        ea = idc.next_head(ea, func_end)
    
    if type_checks:
        print(f"Entity type checks found: {len(type_checks)}")
        for check_ea, op0, op1, val in type_checks[:10]:  # Show first 10
            print(f"  0x{check_ea:X}: cmp {op0}, {op1} (value=0x{val:X})")
    
    # Look for string references
    strings = []
    ea = func_start
    while ea < func_end:
        for xref in idautils.DataRefsFrom(ea):
            str_val = idc.get_strlit_contents(xref)
            if str_val:
                try:
                    decoded = str_val.decode('ascii', errors='ignore')
                    if len(decoded) > 3:
                        strings.append((ea, xref, decoded))
                except:
                    pass
        ea = idc.next_head(ea, func_end)
    
    if strings:
        print(f"String references: {len(strings)}")
        for ref_ea, str_addr, text in strings[:5]:
            print(f"  0x{ref_ea:X} -> '{text[:60]}'")
    
    # Look for cross-references to this function
    xrefs = list(idautils.CodeRefsTo(func_start, True))
    print(f"Called from {len(xrefs)} locations")
    if len(xrefs) <= 5:
        for xref in xrefs:
            func_name = idc.get_func_name(xref)
            print(f"  0x{xref:X} (in {func_name if func_name else 'unknown'})")

# Look for entity type enum values in damage_event_dispatch_handler
print("\n\n=== Deep Dive: damage_event_dispatch_handler @ 0x2EAA7 ===")
print("(This function decides what happens when something gets hit)\n")

ea = 0x2EAA7
end = idc.find_func_end(ea)
print(f"Function: 0x{ea:X} - 0x{end:X} ({end-ea} bytes)\n")

# Disassemble first 50 instructions to see structure
print("First 50 instructions:")
count = 0
while ea < end and count < 50:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"0x{ea:X}: {disasm}")
    ea = idc.next_head(ea, end)
    count += 1

# Look for TARGET in all data sections
print("\n\n=== Searching for 'TARGET' strings in data ===\n")
target_strings = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" not in seg_name:  # Skip code segments
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            str_val = idc.get_strlit_contents(ea)
            if str_val:
                try:
                    decoded = str_val.decode('ascii', errors='ignore')
                    if 'TARGET' in decoded.upper():
                        target_strings.append((ea, decoded))
                        ea += len(str_val)
                except:
                    pass
            ea += 1

print(f"Found {len(target_strings)} 'TARGET' strings:")
for addr, text in target_strings:
    print(f"0x{addr:X}: '{text}'")
    # Find xrefs to this string
    xrefs = list(idautils.DataRefsTo(addr))
    if xrefs:
        print(f"  Referenced by {len(xrefs)} locations:")
        for xref in xrefs[:5]:
            func = idc.get_func_name(xref)
            print(f"    0x{xref:X} (in {func if func else 'unknown'})")

print("\nTarget system analysis complete.")
output_file.close()
idc.qexit(0)
