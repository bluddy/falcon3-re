import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\dispatch_call.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Finding entity function dispatch call...")
idaapi.auto_wait()

# Search in entity_slot_update_loop
func_start = 0x3C1BD
func_end = 0x3C505  # From previous analysis: 348 bytes

print(f"Searching entity_slot_update_loop @ 0x{func_start:X}-0x{func_end:X}")
print("Looking for pattern: load [si+0Ch], multiply by 2, call function\n")

# Disassemble the entire function
print("="*70)
print("COMPLETE DISASSEMBLY:")
print("="*70 + "\n")

ea = func_start
inst_count = 0
while ea < func_end and ea != idc.BADADDR:
    # Get disassembly
    disasm = idc.generate_disasm_line(ea, 0)
    
    # Get instruction bytes
    size = idc.get_item_size(ea)
    byte_list = [idc.get_wide_byte(ea + i) for i in range(min(size, 8))]
    byte_str = " ".join(f"{b:02X}" for b in byte_list)
    
    # Get mnemonic
    mnem = idc.print_insn_mnem(ea)
    
    # Mark interesting instructions
    marker = ""
    if "[si+0Ch]" in disasm or "[si+0xc]" in disasm.lower():
        marker = " <-- ACCESS si+0Ch (object_category)"
    elif mnem == "shl" and "di" in disasm:
        marker = " <-- SHIFT DI (table index)"
    elif mnem == "call" and ("bx" in disasm or "di" in disasm):
        marker = " <-- CALL via register (DISPATCH?)"
    elif mnem == "jmp" and ("bx" in disasm or "di" in disasm):
        marker = " <-- JUMP via register (DISPATCH?)"
    
    print(f"0x{ea:05X}: {byte_str:24s} {disasm:40s}{marker}")
    
    ea = idc.next_head(ea, func_end)
    inst_count += 1
    
    if inst_count > 200:
        print("\n... (truncated, too many instructions)")
        break

print("\n" + "="*70)
print("SEARCHING FOR INDIRECT CALLS/JUMPS:")
print("="*70 + "\n")

# Search for all indirect calls in function
ea = func_start
while ea < func_end and ea != idc.BADADDR:
    mnem = idc.print_insn_mnem(ea)
    disasm = idc.generate_disasm_line(ea, 0)
    
    # Look for indirect calls or jumps
    if mnem in ["call", "jmp"]:
        # Check if it's indirect (register-based)
        if any(reg in disasm for reg in ["bx", "di", "si", "ax", "cx", "dx"]):
            print(f"0x{ea:05X}: {disasm}")
            
            # Show context (3 instructions before)
            print("  Context:")
            ctx_ea = ea - 15  # Go back
            for i in range(6):
                ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
                marker = " <-- HERE" if ctx_ea == ea else ""
                print(f"    0x{ctx_ea:05X}: {ctx_disasm}{marker}")
                ctx_ea = idc.next_head(ctx_ea, ea + 5)
            print()
    
    ea = idc.next_head(ea, func_end)

print("\n" + "="*70)
print("LOOKING FOR TABLE REFERENCES:")
print("="*70 + "\n")

# Search for references to address 0x3C261 (the table)
table_addr = 0x3C261
print(f"Searching for references to 0x{table_addr:X}...\n")

# Check in this function
ea = func_start
while ea < func_end and ea != idc.BADADDR:
    disasm = idc.generate_disasm_line(ea, 0)
    
    # Check if instruction references the table address
    # Look for the address in the operands
    if "3C261" in disasm or "funcs_3C261" in disasm:
        print(f"0x{ea:05X}: {disasm}")
        
        # Show surrounding context
        print("  Context:")
        ctx_ea = ea - 10
        for i in range(5):
            ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
            marker = " <-- HERE" if ctx_ea == ea else ""
            print(f"    0x{ctx_ea:05X}: {ctx_disasm}{marker}")
            ctx_ea = idc.next_head(ctx_ea, ea + 10)
        print()
    
    ea = idc.next_head(ea, func_end)

print("Dispatch call search complete.")
output_file.close()
idc.qexit(0)
