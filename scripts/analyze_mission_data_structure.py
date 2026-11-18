import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\mission_data_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting mission data structure analysis...")
idaapi.auto_wait()

print("=== THEORY ===")
print("Buildings might not be entities at all - they could be:")
print("1. Static map data referenced by coordinates")
print("2. Mission objective records with position + type")
print("3. Separate building/facility array distinct from entity system")
print()
print("The [di+0Ch] == 4 check in store_impact_step might check:")
print("- Mission objective record type")
print("- Damage event type (4 = building hit)")
print("- Something else entirely\n")

# Analyze mission_state_initializer @ 0x32D22 (850 bytes!)
print("=== Analyzing mission_state_initializer @ 0x32D22 (850B) ===\n")

func_start = 0x32D22
func_end = idc.find_func_end(func_start)
print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")

# Look for large data structures being initialized
print("Looking for large memory allocations/initializations:\n")

ea = func_start
large_loops = []
call_count = 0

while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    
    # Look for calls (might call mission data loaders)
    if mnem in ["call", "lcall"]:
        target = idc.get_operand_value(ea, 0)
        target_name = idc.get_name(target) if target != idc.BADADDR else "unknown"
        call_count += 1
        if call_count <= 20:  # Show first 20 calls
            print(f"  0x{ea:X}: call {target_name}")
    
    # Look for loop initialization (large cx values)
    if mnem == "mov" and "cx" in idc.print_operand(ea, 0).lower():
        try:
            val = idc.get_operand_value(ea, 1)
            if val > 10:  # Loops larger than 10
                large_loops.append((ea, val))
        except:
            pass
    
    ea = idc.next_head(ea, func_end)

print(f"\nTotal calls in function: {call_count}")

if large_loops:
    print(f"\nLarge loop initializations ({len(large_loops)}):")
    for addr, count in large_loops[:10]:
        print(f"  0x{addr:X}: mov cx, 0x{count:X} ({count} iterations)")

# Look for data segment references (mission data tables)
print("\n\nSearching for global data references in mission_state_initializer:\n")

ea = func_start
data_refs = set()

while ea < func_end:
    for xref in idautils.DataRefsFrom(ea):
        seg_name = idc.get_segm_name(xref)
        if seg_name and "DATA" in seg_name.upper():
            data_refs.add(xref)
    ea = idc.next_head(ea, func_end)

print(f"Found {len(data_refs)} unique data segment references:")
for ref in sorted(data_refs)[:30]:
    seg = idc.get_segm_name(ref)
    name = idc.get_name(ref)
    print(f"  0x{ref:X} ({seg}): {name if name else 'unnamed'}")

# Now look at the ai_target_priority_evaluator structure
print("\n\n=== Analyzing ai_target_priority_evaluator @ 0x3E96F ===\n")
print("This checks 11 byte fields at [di+0xB3h] through [di+0xBFh]")
print("These are probably target count arrays\n")

# Let's see what DI points to (find where DI is loaded)
func_start = 0x3E96F
func_end = idc.find_func_end(func_start)

print("Looking for DI initialization:\n")
ea = func_start
di_loads = []

count = 0
while ea < func_end and count < 40:  # First 40 instructions
    disasm = idc.generate_disasm_line(ea, 0)
    if "di" in disasm.lower():
        print(f"  0x{ea:X}: {disasm}")
        di_loads.append(ea)
    ea = idc.next_head(ea, func_end)
    count += 1

# Search for the structure that contains the target count fields
print("\n\n=== Searching for target count structure (fields at +0xB3 onwards) ===\n")
print("Looking for global arrays/structures ~200 bytes in size...\n")

# Check data segments for suitably sized allocations
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if seg_name and "DATA" in seg_name.upper():
        print(f"Segment: {seg_name} at 0x{seg_ea:X}")
        # We'd need to analyze allocation patterns here
        # For now, just note the segment exists

# Look at damage_event_dispatch_handler more carefully
print("\n\n=== Re-analyzing damage_event_dispatch_handler @ 0x2EAA7 ===\n")
print("This is abstract - uses op_dispatch calls")
print("Let's trace the first 100 instructions to understand data flow:\n")

func_start = 0x2EAA7
func_end = idc.find_func_end(func_start)

ea = func_start
count = 0
while ea < func_end and count < 100:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"  0x{ea:X}: {disasm}")
    ea = idc.next_head(ea, func_end)
    count += 1

# Search for "objective" related strings
print("\n\n=== Searching for OBJECTIVE related strings ===\n")

objective_strings = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if seg_name and "CODE" not in seg_name:
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        while ea < seg_end:
            str_val = idc.get_strlit_contents(ea)
            if str_val:
                try:
                    decoded = str_val.decode('ascii', errors='ignore')
                    if 'OBJECTIVE' in decoded.upper() or 'TARGET' in decoded.upper():
                        objective_strings.append((ea, decoded))
                        ea += len(str_val)
                except:
                    pass
            ea += 1

print(f"Found {len(objective_strings)} objective/target strings:")
for addr, text in objective_strings[:20]:
    print(f"  0x{addr:X}: '{text}'")

print("\n\nMission data structure analysis complete.")
output_file.close()
idc.qexit(0)
