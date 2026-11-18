import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\mission_objectives_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting mission objectives analysis...")
idaapi.auto_wait()

# Search for target classification and mission success strings
print("=== Searching for Target and Mission Strings ===\n")

target_keywords = [
    b"PRIMARY TARGET",
    b"SECONDARY TARGET",
    b"CLASS A TARGET",
    b"CLASS B TARGET", 
    b"CLASS C TARGET",
    b"CLASS D TARGET",
    b"DESTROYED A PRIMARY",
    b"DAMAGED A PRIMARY",
    b"GROUND TARGETS DESTROYED",
    b"MISSION SUCCESSFUL",
    b"MISSION FAILURE",
    b"RUNWAY",
    b"WAREHOUSE",
    b"HANGAR",
    b"BARRACKS",
    b"BRIDGE",
    b"FACTORY"
]

found_strings = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" not in seg_name:
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            for keyword in target_keywords:
                str_val = idc.get_bytes(ea, len(keyword))
                if str_val == keyword:
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

print(f"Found {len(found_strings)} target/mission strings:\n")
for addr, keyword, full_text in found_strings:
    print(f"0x{addr:X} [{keyword}]: '{full_text}'")
    
    # Find code references to this string
    xrefs = list(idautils.DataRefsTo(addr))
    if xrefs:
        print(f"  Referenced by {len(xrefs)} code locations:")
        for xref in xrefs[:5]:
            func_name = idc.get_func_name(xref)
            if func_name:
                print(f"    0x{xref:X} in {func_name}")
    print()

# Look at ai_target_priority_evaluator - this should tell us how targets are identified
print("\n=== Analysis of ai_target_priority_evaluator @ 0x3E96F ===\n")
func_start = 0x3E96F
func_end = idc.find_func_end(func_start)
print(f"Function size: {func_end - func_start} bytes (0x{func_start:X} - 0x{func_end:X})\n")

# Find entity type comparisons
print("Entity type/field checks:\n")
ea = func_start
type_checks = []
while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    if mnem == "cmp":
        op0 = idc.print_operand(ea, 0)
        op1 = idc.print_operand(ea, 1)
        # Entity field access
        if "[" in op0 and ("si" in op0 or "di" in op0 or "bx" in op0):
            val = idc.get_operand_value(ea, 1)
            if val < 256:
                type_checks.append((ea, op0, op1, val))
    ea = idc.next_head(ea, func_end)

for ea, op0, op1, val in type_checks[:20]:
    print(f"  0x{ea:X}: cmp {op0}, {op1} (value=0x{val:X})")

# Look at mission_state_initializer
print("\n\n=== Analysis of mission_state_initializer @ 0x32D22 ===\n")
func_start = 0x32D22
func_end = idc.find_func_end(func_start)
print(f"Function size: {func_end - func_start} bytes (0x{func_start:X} - 0x{func_end:X})\n")

# Find string references in this function
print("String references:\n")
ea = func_start
while ea < func_end:
    for xref in idautils.DataRefsFrom(ea):
        str_val = idc.get_strlit_contents(xref)
        if str_val:
            try:
                decoded = str_val.decode('ascii', errors='ignore')
                if len(decoded) > 3:
                    print(f"  0x{ea:X} -> '{decoded[:60]}'")
            except:
                pass
    ea = idc.next_head(ea, func_end)

# Look at target_cycle_scan
print("\n\n=== Analysis of target_cycle_scan @ 0x48B05 ===\n")
func_start = 0x48B05
func_end = idc.find_func_end(func_start)
print(f"Function size: {func_end - func_start} bytes (0x{func_start:X} - 0x{func_end:X})\n")

print("First 60 instructions:\n")
ea = func_start
count = 0
while ea < func_end and count < 60:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"  {disasm}")
    ea = idc.next_head(ea, func_end)
    count += 1

# Search for global arrays that might hold target/objective data
print("\n\n=== Searching for target/objective data structures ===\n")
print("Looking for large initialized data arrays that might be target lists...\n")

# Check data segments for arrays
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if seg_name in ["_DATA", ".data", "data"]:
        seg_end = idc.get_segm_end(seg_ea)
        print(f"Segment {seg_name}: 0x{seg_ea:X} - 0x{seg_end:X} ({seg_end-seg_ea} bytes)")

print("\n\nMission objectives analysis complete.")
output_file.close()
idc.qexit(0)
