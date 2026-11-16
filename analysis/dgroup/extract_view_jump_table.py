"""
Extract the 10-entry view jump table from overlay_r45_logic.

Found at 0x156DC5:
  mov bx, es:word_79F16
  cmp bx, 9
  jbe short loc_156DD2
  jmp default
  shl bx, 1
  jmp cs:jpt_156DD4[bx]  ; Jump table named jpt_156DD4

Need to find the actual table and extract all 10 handler addresses.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("EXTRACTING VIEW JUMP TABLE")
    print("="*80)
    
    # The jump table instruction is at 0x156DD4
    jump_insn_addr = 0x156DD4
    
    print(f"\n[*] Jump instruction at 0x{jump_insn_addr:X}")
    insn = idc.GetDisasm(jump_insn_addr)
    print(f"    {insn}")
    
    # Get the table address from the instruction
    # "jmp cs:jpt_156DD4[bx]"
    # The table name is jpt_156DD4
    
    table_addr = idc.get_name_ea_simple("jpt_156DD4")
    
    if table_addr == idc.BADADDR:
        print(f"\n[!] Table jpt_156DD4 not found by name")
        print(f"[*] Trying to extract from instruction operand...")
        
        # Try to get it from the instruction
        op_val = idc.get_operand_value(jump_insn_addr, 0)
        if op_val != idc.BADADDR:
            table_addr = op_val
            print(f"[*] Found table address: 0x{table_addr:X}")
        else:
            print(f"[!] Could not find table address")
            idc.qexit(1)
            return
    else:
        print(f"\n[*] Found table jpt_156DD4 at 0x{table_addr:X}")
    
    # Read 10 entries (words)
    print(f"\n[*] Reading 10 table entries:")
    print()
    
    entries = []
    
    for i in range(10):
        entry_addr = table_addr + (i * 2)  # word = 2 bytes
        handler_offset = idc.get_wide_word(entry_addr)
        
        # The offset might be relative to CS segment
        # Try to resolve to actual address
        handler_addr = handler_offset  # Try as-is first
        
        # Get handler name if it exists
        handler_name = idc.get_name(handler_addr)
        if not handler_name:
            handler_name = f"view_handler_{i}"
        
        # Try to get the function
        func = idaapi.get_func(handler_addr)
        if func:
            func_name = idc.get_func_name(handler_addr)
            func_size = func.end_ea - func.start_ea
        else:
            func_name = "NOT_A_FUNCTION"
            func_size = 0
        
        entry = {
            'index': i,
            'table_offset': f'0x{entry_addr:X}',
            'handler_offset': f'0x{handler_offset:X}',
            'handler_addr': f'0x{handler_addr:X}',
            'handler_name': handler_name,
            'func_name': func_name,
            'func_size': func_size
        }
        
        entries.append(entry)
        
        print(f"  [{i}] 0x{entry_addr:X}: 0x{handler_offset:04X} -> {func_name} ({func_size} bytes)")
        
        # Show first few instructions of each handler
        if func:
            print(f"       First 5 instructions:")
            ea = handler_addr
            for j in range(5):
                ins = idc.GetDisasm(ea)
                print(f"         0x{ea:X}: {ins}")
                ea = idc.next_head(ea, func.end_ea)
                if ea >= func.end_ea:
                    break
            print()
    
    # Save results
    output = {
        'table_name': 'jpt_156DD4',
        'table_addr': f'0x{table_addr:X}',
        'jump_insn': f'0x{jump_insn_addr:X}',
        'entry_count': 10,
        'entries': entries
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\view_jump_table.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
