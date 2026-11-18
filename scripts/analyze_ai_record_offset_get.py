import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\ai_record_offset_get.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Analyzing ai_record_offset_get function...")
idaapi.auto_wait()

# Search for function by name pattern
print("="*70)
print("SEARCHING FOR ai_record_offset_get FUNCTION")
print("="*70 + "\n")

# Try to find the function
func_addr = idc.get_name_ea_simple("ai_record_offset_get")

if func_addr == idc.BADADDR:
    print("Function 'ai_record_offset_get' not found by name.")
    print("Searching for references in ai_state_calculate_helper...\n")
    
    # We know it's called from ai_state_calculate_helper @ 0x3F45B
    call_site = 0x3F45B
    
    # Get the call target
    disasm = idc.generate_disasm_line(call_site, 0)
    print(f"Call site @ 0x{call_site:05X}: {disasm}")
    
    # Get operand (call target)
    target = idc.get_operand_value(call_site, 0)
    
    if target != idc.BADADDR:
        print(f"Call target: 0x{target:05X}")
        func_addr = target
    else:
        print("Could not resolve call target")
        output_file.close()
        idc.qexit(0)

print(f"\nAnalyzing function @ 0x{func_addr:05X}")

# Get function bounds
func = idaapi.get_func(func_addr)
if not func:
    print("Not a valid function")
    output_file.close()
    idc.qexit(0)

func_start = func.start_ea
func_end = func.end_ea
func_size = func_end - func_start
func_name = idc.get_func_name(func_addr)

print(f"Function: {func_name}")
print(f"Address: 0x{func_start:05X}-0x{func_end:05X}")
print(f"Size: {func_size} bytes\n")

print("="*70)
print("COMPLETE DISASSEMBLY")
print("="*70 + "\n")

# Disassemble entire function
ea = func_start
inst_count = 0

while ea < func_end and ea != idc.BADADDR:
    disasm = idc.generate_disasm_line(ea, 0)
    mnem = idc.print_insn_mnem(ea)
    
    # Get instruction bytes
    size = idc.get_item_size(ea)
    byte_list = [idc.get_wide_byte(ea + i) for i in range(min(size, 6))]
    byte_str = " ".join(f"{b:02X}" for b in byte_list)
    
    # Mark interesting instructions
    marker = ""
    if mnem == "ret" or mnem == "retf":
        marker = " <-- RETURN (DX contains result?)"
    elif mnem in ["mov", "add", "sub", "shl", "shr"] and "dx" in disasm.lower():
        marker = " <-- DX OPERATION"
    elif mnem == "cmp" and "dx" in disasm.lower():
        marker = " <-- DX COMPARISON"
    elif mnem == "call":
        marker = " (CALL)"
    
    print(f"0x{ea:05X}: {byte_str:18s} {disasm:50s}{marker}")
    
    ea = idc.next_head(ea, func_end)
    inst_count += 1

print(f"\n\nTotal instructions: {inst_count}")

print("\n" + "="*70)
print("RETURN VALUE ANALYSIS")
print("="*70 + "\n")

# Check what's in DX at return
print("Looking for DX assignments before return:\n")

ea = func_start
dx_assignments = []

while ea < func_end and ea != idc.BADADDR:
    mnem = idc.print_insn_mnem(ea)
    disasm = idc.generate_disasm_line(ea, 0)
    
    # Look for MOV DX, X or operations that set DX
    if mnem in ["mov", "xor", "or", "add", "sub", "shl", "shr"] and "dx," in disasm:
        dx_assignments.append((ea, disasm))
    
    ea = idc.next_head(ea, func_end)

print(f"Found {len(dx_assignments)} DX assignments:\n")

for addr, disasm in dx_assignments:
    print(f"  0x{addr:05X}: {disasm}")

print("\n" + "="*70)
print("CALLERS AND USAGE")
print("="*70 + "\n")

# Find all callers
callers = []
for xref in idautils.XrefsTo(func_start):
    caller_addr = xref.frm
    caller_func = idc.get_func_name(caller_addr)
    callers.append((caller_addr, caller_func))

print(f"Found {len(callers)} callers:\n")

for caller_addr, caller_func in callers[:10]:
    print(f"0x{caller_addr:05X} in {caller_func}")
    
    # Show how DX is used after the call
    print(f"  Context after call:")
    
    ctx_ea = caller_addr
    for i in range(10):
        ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
        
        marker = ""
        if ctx_ea == caller_addr:
            marker = " <-- CALL HERE"
        elif "dx" in ctx_disasm.lower():
            marker = " <-- DX USAGE"
        
        print(f"    0x{ctx_ea:05X}: {ctx_disasm}{marker}")
        ctx_ea = idc.next_head(ctx_ea, caller_addr + 30)
    print()

if len(callers) > 10:
    print(f"... ({len(callers) - 10} more callers)")

print("\n" + "="*70)
print("KEY CALLER: ai_state_calculate_helper @ 0x3F45B")
print("="*70 + "\n")

# Analyze the specific usage in category assignment
key_call = 0x3F45B

print(f"Call to ai_record_offset_get @ 0x{key_call:05X}:")
print(f"Context:\n")

ctx_ea = key_call - 20
for i in range(15):
    ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
    
    marker = ""
    if ctx_ea == key_call:
        marker = " <-- CALL ai_record_offset_get"
    elif ctx_ea == 0x3F45E:
        marker = " <-- CMP DX, 4 (distance check!)"
    elif ctx_ea == 0x3F461:
        marker = " <-- JB (if DX < 4)"
    elif ctx_ea == 0x3F463:
        marker = " <-- JMP sub_3F525 (category 0)"
    elif ctx_ea == 0x3F466:
        marker = " <-- CMP [si+0Ch], 2"
    elif ctx_ea == 0x3F46C:
        marker = " <-- MOV [si+0Ch], 2 (category 2!)"
    
    print(f"  0x{ctx_ea:05X}: {ctx_disasm}{marker}")
    ctx_ea = idc.next_head(ctx_ea, key_call + 40)

print("\n" + "="*70)
print("INTERPRETATION")
print("="*70 + "\n")

print("Based on usage pattern:")
print("  - ai_record_offset_get returns value in DX register")
print("  - DX is compared with 4 to make category decision")
print("  - DX < 4: Entity is CLOSE → Category 2 (AI_FIGHTER)")
print("  - DX >= 4: Entity is FAR → Category 3 or 0 (non-combat)")
print()
print("DX likely represents:")
print("  - Distance range/band (0=very close, 1-3=close, 4+=far)")
print("  - OR: LOD level (0-3=detailed, 4+=simplified)")
print("  - OR: Engagement zone (0-3=combat range, 4+=non-combat)")

print("\nai_record_offset_get analysis complete.")
output_file.close()
idc.qexit(0)
