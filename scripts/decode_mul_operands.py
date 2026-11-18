"""
Decode the MUL/DIV operands from fixed_vec3_accumulate_a by reading instruction bytes.
"""

import idc
import idaapi
import json
from pathlib import Path

print("=" * 70)
print("DECODING MUL/DIV OPERANDS")
print("=" * 70)
print()

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# fixed_vec3_accumulate_a function address
func_addr = 0x22C91

print(f"Analyzing function at 0x{func_addr:X}")
print()

# Disassemble the function and print each instruction
print("Complete disassembly:")
print("-" * 70)

ea = func_addr
for i in range(20):  # First 20 instructions
    # Get instruction bytes
    insn_len = idc.get_item_size(ea)
    insn_bytes = idc.get_bytes(ea, insn_len)
    hex_bytes = ' '.join(f'{b:02X}' for b in insn_bytes)
    
    # Get disassembly
    disasm = idc.GetDisasm(ea)
    
    # Get mnemonic and operands
    mnem = idc.print_insn_mnem(ea)
    op0 = idc.print_operand(ea, 0)
    op1 = idc.print_operand(ea, 1)
    
    print(f"0x{ea:05X}: {hex_bytes:20s} {disasm}")
    
    # For MUL and DIV, try to resolve the operand address
    if mnem in ["mul", "div"]:
        # Check operand type
        op_type = idc.get_operand_type(ea, 0)
        op_value = idc.get_operand_value(ea, 0)
        
        print(f"         Operand: '{op0}' type={op_type} value=0x{op_value:X}")
        
        # Try to read from the operand value as an address
        if op_value != 0:
            try:
                data = idc.get_wide_word(op_value)
                print(f"         Data at 0x{op_value:X} = {data} (0x{data:04X})")
            except:
                print(f"         Cannot read from 0x{op_value:X}")
        
        # Also manually decode the CS: reference from instruction bytes
        # Format: 2E F7 26 XX YY (mul cs:[YYXX])
        # or:     2E F7 36 XX YY (div cs:[YYXX])
        if len(insn_bytes) == 5 and insn_bytes[0] == 0x2E:
            cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
            print(f"         CS offset from bytes: 0x{cs_offset:04X}")
            
            # Try reading from CS base + offset
            # Get CS segment
            cs_seg = idc.selector_by_name("seg000")  # Code segment
            if cs_seg != idc.BADADDR:
                cs_base = idc.get_segm_by_sel(cs_seg).start_ea if idc.get_segm_by_sel(cs_seg) else 0
                actual_addr = cs_base + cs_offset
                print(f"         CS segment base: 0x{cs_base:X}")
                print(f"         Actual address: 0x{actual_addr:X}")
                
                try:
                    data = idc.get_wide_word(actual_addr)
                    print(f"         Data at actual address: {data} (0x{data:04X})")
                except:
                    print(f"         Cannot read from actual address")
        
        print()
    
    ea = idc.next_head(ea)

print("=" * 70)

# Exit
idc.qexit(0)
