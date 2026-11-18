import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\ag_weapon_cx_trace.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Tracing CX register in ag_weapon_entity_initialize...")
idaapi.auto_wait()

func_start = 0x4C3C7
func_end = 0x4CAE2

print(f"Function: ag_weapon_entity_initialize")
print(f"Range: 0x{func_start:05X}-0x{func_end:05X}")
print(f"Size: {func_end - func_start} bytes\n")

print("="*70)
print("COMPLETE DISASSEMBLY WITH CX TRACKING")
print("="*70 + "\n")

# Track all CX operations
cx_operations = []
category_writes = []

ea = func_start
inst_count = 0

while ea < func_end and ea != idc.BADADDR:
    disasm = idc.generate_disasm_line(ea, 0)
    mnem = idc.print_insn_mnem(ea)
    
    # Track CX usage
    cx_usage = ""
    if "cx" in disasm.lower():
        cx_usage = " <-- CX"
        cx_operations.append((ea, disasm))
    
    # Track category writes
    if mnem == "mov" and ("[si+0Ch]" in disasm or "[si+0xc]" in disasm.lower()):
        category_writes.append((ea, disasm))
        cx_usage += " *** CATEGORY WRITE ***"
    
    # Track AND operations (masking)
    if mnem == "and" and "cx" in disasm.lower():
        cx_usage += " [MASK]"
    
    # Track calls
    if mnem == "call":
        cx_usage += " (CALL)"
    
    print(f"0x{ea:05X}: {disasm:60s}{cx_usage}")
    
    ea = idc.next_head(ea, func_end)
    inst_count += 1
    
    if inst_count > 500:
        print("\n... (truncated, too many instructions)")
        break

print(f"\n\nTotal instructions analyzed: {inst_count}")
print(f"CX operations found: {len(cx_operations)}")
print(f"Category writes found: {len(category_writes)}\n")

print("="*70)
print("CX OPERATIONS SUMMARY")
print("="*70 + "\n")

for i, (addr, disasm) in enumerate(cx_operations[:30], 1):
    print(f"{i:2d}. 0x{addr:05X}: {disasm}")

if len(cx_operations) > 30:
    print(f"\n... ({len(cx_operations) - 30} more CX operations)")

print("\n" + "="*70)
print("FUNCTION ENTRY - WHERE DOES CX COME FROM?")
print("="*70 + "\n")

# Show first 30 instructions
print("First 30 instructions (looking for CX initialization):\n")

ea = func_start
for i in range(30):
    disasm = idc.generate_disasm_line(ea, 0)
    mnem = idc.print_insn_mnem(ea)
    
    marker = ""
    if "cx" in disasm.lower():
        marker = " <-- CX USAGE"
    
    print(f"  0x{ea:05X}: {disasm:50s}{marker}")
    ea = idc.next_head(ea, func_end)

print("\n" + "="*70)
print("WHO CALLS ag_weapon_entity_initialize?")
print("="*70 + "\n")

# Find callers
callers = []
for xref in idautils.XrefsTo(func_start):
    caller_addr = xref.frm
    caller_func = idc.get_func_name(caller_addr)
    callers.append((caller_addr, caller_func))

print(f"Found {len(callers)} callers:\n")

for caller_addr, caller_func in callers:
    print(f"0x{caller_addr:05X} in {caller_func}")
    
    # Show context around call
    print(f"  Context (10 instructions before call):")
    ctx_ea = caller_addr - 40
    for i in range(12):
        ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
        
        marker = ""
        if ctx_ea == caller_addr:
            marker = " <-- CALL HERE"
        elif "cx" in ctx_disasm.lower():
            marker = " <-- CX USAGE"
        
        print(f"    0x{ctx_ea:05X}: {ctx_disasm:50s}{marker}")
        ctx_ea = idc.next_head(ctx_ea, caller_addr + 10)
    print()

print("\n" + "="*70)
print("PATTERN ANALYSIS")
print("="*70 + "\n")

# Look for the pattern before first category write
first_write_addr = category_writes[0][0] if category_writes else 0

if first_write_addr:
    print(f"First category write @ 0x{first_write_addr:05X}")
    print("Looking 50 instructions back for CX source:\n")
    
    # Go back and find CX assignment
    ea = first_write_addr - 200
    found_cx_source = False
    
    for i in range(50):
        disasm = idc.generate_disasm_line(ea, 0)
        mnem = idc.print_insn_mnem(ea)
        
        # Look for MOV CX, X or XOR CX, CX or similar
        if mnem in ["mov", "xor", "or", "add", "sub"] and "cx," in disasm:
            print(f"  0x{ea:05X}: {disasm} <-- POTENTIAL CX SOURCE")
            found_cx_source = True
        elif "cx" in disasm.lower():
            print(f"  0x{ea:05X}: {disasm}")
        
        ea = idc.next_head(ea, first_write_addr)
    
    if not found_cx_source:
        print("\n  No direct CX assignment found - CX likely comes from caller!")

print("\nag_weapon_entity_initialize CX trace complete.")
output_file.close()
idc.qexit(0)
