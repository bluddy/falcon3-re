import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\fixed_vec3_accumulate_a.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Disassembling fixed_vec3_accumulate_a...")
idaapi.auto_wait()

# Try to find the function
func_addr = idc.get_name_ea_simple("fixed_vec3_accumulate_a")

if func_addr == idc.BADADDR:
    print("Function 'fixed_vec3_accumulate_a' not found by name.")
    print("Searching by call pattern from ag_weapon_entity_initialize...\n")
    
    # We know it's called at 0x4C3E8, 0x4C434, etc.
    call_sites = [0x4C3E8, 0x4C434, 0x4C480, 0x4C4CC, 0x4C51D, 0x4C569]
    
    for call_site in call_sites:
        target = idc.get_operand_value(call_site, 0)
        if target != idc.BADADDR:
            func_addr = target
            print(f"Found via call @ 0x{call_site:05X} → 0x{func_addr:05X}")
            break

if func_addr == idc.BADADDR:
    print("ERROR: Could not locate function")
    output_file.close()
    idc.qexit(0)

# Get function details
func = idaapi.get_func(func_addr)
if not func:
    print(f"ERROR: Address 0x{func_addr:05X} is not a function")
    output_file.close()
    idc.qexit(0)

func_start = func.start_ea
func_end = func.end_ea
func_size = func_end - func_start
func_name = idc.get_func_name(func_addr)

print("="*70)
print("FUNCTION INFORMATION")
print("="*70 + "\n")

print(f"Name: {func_name}")
print(f"Address: 0x{func_start:05X} - 0x{func_end:05X}")
print(f"Size: {func_size} bytes ({func_size} decimal)")
print()

# Get all xrefs to this function
print("Callers:")
caller_count = 0
for xref in idautils.XrefsTo(func_start):
    caller_addr = xref.frm
    caller_func = idc.get_func_name(caller_addr)
    print(f"  0x{caller_addr:05X} in {caller_func}")
    caller_count += 1
    if caller_count >= 10:
        print(f"  ... (showing first 10)")
        break

print(f"\nTotal callers: {caller_count}")

print("\n" + "="*70)
print("COMPLETE DISASSEMBLY")
print("="*70 + "\n")

# Disassemble entire function
ea = func_start
inst_count = 0
cx_operations = []
ax_operations = []
dx_operations = []

while ea < func_end and ea != idc.BADADDR:
    # Get disassembly
    disasm = idc.generate_disasm_line(ea, 0)
    mnem = idc.print_insn_mnem(ea)
    
    # Get instruction bytes
    size = idc.get_item_size(ea)
    byte_list = [idc.get_wide_byte(ea + i) for i in range(min(size, 8))]
    byte_str = " ".join(f"{b:02X}" for b in byte_list)
    
    # Track register operations
    marker = ""
    if "cx" in disasm.lower():
        marker = " <-- CX"
        cx_operations.append((ea, disasm))
    elif "ax" in disasm.lower():
        marker = " <-- AX"
        ax_operations.append((ea, disasm))
    elif "dx" in disasm.lower():
        marker = " <-- DX"
        dx_operations.append((ea, disasm))
    
    if mnem in ["ret", "retf", "retn"]:
        marker = " <-- RETURN (CX contains result?)"
    elif mnem == "call":
        marker = " (CALL)"
    
    print(f"0x{ea:05X}: {byte_str:24s} {disasm:45s}{marker}")
    
    ea = idc.next_head(ea, func_end)
    inst_count += 1

print(f"\n\nTotal instructions: {inst_count}")
print(f"CX operations: {len(cx_operations)}")
print(f"AX operations: {len(ax_operations)}")
print(f"DX operations: {len(dx_operations)}")

print("\n" + "="*70)
print("CX REGISTER OPERATIONS SUMMARY")
print("="*70 + "\n")

print("All CX operations in order:\n")

for i, (addr, disasm) in enumerate(cx_operations, 1):
    print(f"{i:2d}. 0x{addr:05X}: {disasm}")

print("\n" + "="*70)
print("RETURN VALUE ANALYSIS")
print("="*70 + "\n")

# Find what CX contains at return
print("Analyzing CX value at function return...\n")

# Look backwards from return instruction
ret_addr = func_end - 10  # Start near end
found_ret = False

for i in range(20):
    if idc.print_insn_mnem(ret_addr) in ["ret", "retf", "retn"]:
        found_ret = True
        break
    ret_addr = idc.prev_head(ret_addr)

if found_ret:
    print(f"Return instruction @ 0x{ret_addr:05X}")
    print("\nLast 10 instructions before return:\n")
    
    # Show context before return
    ctx_ea = ret_addr - 40
    for i in range(12):
        ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
        
        marker = ""
        if ctx_ea == ret_addr:
            marker = " <-- RETURN HERE"
        elif "cx" in ctx_disasm.lower():
            marker = " <-- CX (return value?)"
        
        print(f"  0x{ctx_ea:05X}: {ctx_disasm}{marker}")
        ctx_ea = idc.next_head(ctx_ea, ret_addr + 5)

print("\n" + "="*70)
print("FUNCTION PARAMETERS")
print("="*70 + "\n")

# Check what's passed in SI (entity pointer + 0x3A from ag_weapon_entity_initialize)
print("From callers, we know:")
print("  - SI points to entity position data (entity + 0x3A)")
print("  - Function is called after setting up weapon parameters")
print()

# Check first few instructions for parameter usage
print("First 20 instructions (parameter setup):\n")

ea = func_start
for i in range(20):
    disasm = idc.generate_disasm_line(ea, 0)
    
    marker = ""
    if "si" in disasm.lower():
        marker = " <-- SI (position data)"
    elif "di" in disasm.lower():
        marker = " <-- DI"
    elif "bp" in disasm.lower():
        marker = " <-- BP"
    
    print(f"  0x{ea:05X}: {disasm}{marker}")
    ea = idc.next_head(ea, func_end)

print("\n" + "="*70)
print("INTERPRETATION")
print("="*70 + "\n")

print("Based on disassembly:")
print()

# Analyze the pattern
if len(cx_operations) > 0:
    print(f"Function performs {len(cx_operations)} operations on CX register.")
    print()
    
    # Check if CX is calculated or loaded
    has_mov_cx = any("mov" in op[1] and "cx," in op[1] for op in cx_operations)
    has_add_cx = any("add" in op[1] and "cx" in op[1] for op in cx_operations)
    has_or_cx = any("or" in op[1] and "cx" in op[1] for op in cx_operations)
    
    if has_mov_cx:
        print("✓ CX is loaded from memory or register")
    if has_add_cx:
        print("✓ CX is modified by addition")
    if has_or_cx:
        print("✓ CX is modified by bitwise OR")
    
    print()
    print("Return value in CX likely represents:")
    print("  - A calculated value based on position data")
    print("  - May include category in lower bits")
    print("  - May include other data in upper bits")
    print("  - Caller masks with 0x3FF to get 10-bit value")

print("\n" + "="*70)
print("CROSS-REFERENCE WITH CALLERS")
print("="*70 + "\n")

# Show how CX is used after return
print("After function returns, caller does:\n")
print("  0x4C3E8: call    fixed_vec3_accumulate_a")
print("  0x4C3ED: and     cx, 3FFh                  ; Mask to 10 bits")
print("  0x4C3F1: mov     [si+0Ch], cx              ; Write to object_category")
print()
print("This confirms CX is the return value containing category+subcat.")

print("\nDisassembly complete.")
output_file.close()
idc.qexit(0)
