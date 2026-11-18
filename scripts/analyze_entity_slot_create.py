import idc
import idaapi
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\entity_slot_create_analysis.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Analyzing entity_slot_create @ 0x2EBCD...")
idaapi.auto_wait()

func_start = 0x2EBCD
func_end = idc.find_func_end(func_start)

print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")
print("This is the main entity slot creation function - should set object_category\n")
print("Complete disassembly:\n")

ea = func_start
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"{disasm}")
    ea = idc.next_head(ea, func_end)

print("\n\nCalled by:\n")
callers = list(idautils.CodeRefsTo(func_start, True))
for caller in callers[:15]:
    caller_func = idc.get_func_name(caller)
    print(f"0x{caller:X} in {caller_func if caller_func else 'unknown'}")

# Now look at ag_weapon_entity_initialize writes to +0Ch
print("\n\n=== Analyzing ag_weapon_entity_initialize @ 0x4C3C7 ===\n")
print("Found 22 writes to [si+0Ch] - these set object_category for weapons!\n")

func_start = 0x4C3C7
func_end = idc.find_func_end(func_start)

# Show context around first few +0Ch writes
writes_to_analyze = [
    0x4C3F1,  # mov [si+0Ch], cx - first write
    0x4C43D,  # mov [si+0Ch], cx - second write
    0x4CA26,  # mov word ptr [si+0Ch], 0 - explicit 0
]

for write_ea in writes_to_analyze:
    print(f"\nContext around 0x{write_ea:X}:")
    
    # Show 5 instructions before and after
    context_start = write_ea - 20
    ea = context_start
    count = 0
    while ea < write_ea + 20 and count < 10:
        disasm = idc.generate_disasm_line(ea, 0)
        marker = " ← HERE" if ea == write_ea else ""
        print(f"  0x{ea:X}: {disasm}{marker}")
        ea = idc.next_head(ea, write_ea + 20)
        count += 1

# Check what CX register contains before writes
print("\n\n=== Analysis of CX Register Before Writes ===\n")
print("All writes use 'mov [si+0Ch], cx' - need to find where CX is set\n")

# Look backward from first write to find CX assignment
ea = 0x4C3F1
search_start = ea - 100
print(f"Searching backwards from 0x{ea:X} for CX assignment:\n")

search_ea = ea
count = 0
while search_ea > search_start and count < 30:
    search_ea = idc.prev_head(search_ea, search_start)
    disasm = idc.generate_disasm_line(search_ea, 0)
    if "cx" in disasm.lower() and ("mov" in disasm.lower() or "xor" in disasm.lower()):
        print(f"  0x{search_ea:X}: {disasm}")
        count += 1

print("\n\nEntity slot create analysis complete.")
output_file.close()
idc.qexit(0)
