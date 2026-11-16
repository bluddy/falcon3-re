"""
Examine the jump tables found in input dispatchers.

Found two dispatchers:
1. r29_tactical_screen_coordinator at 0x12DFD6 - table at cs:0x1E99
2. game_mode_r53_main_coordinator at 0x182476 - table at cs:0x3225

Both use pattern:
  - Table has scan codes followed by handler addresses
  - Loop searches for matching scan code
  - On match: jmp word ptr cs:[bx+8]
"""

import idc
import idaapi
import idautils
import json

def read_dispatch_table(table_addr, entry_count, segment_name):
    """
    Read a dispatch table.
    
    Format appears to be:
      word: scan_code
      ...gap of 8 bytes...
      word: handler_address
    """
    
    print(f"\n[*] Reading dispatch table at 0x{table_addr:X} ({segment_name})")
    print(f"    Expected entries: {entry_count}")
    print()
    
    entries = []
    
    for i in range(entry_count):
        # Read scan code
        offset = i * 2
        scan_code_addr = table_addr + offset
        scan_code = idc.get_wide_word(scan_code_addr)
        
        # Handler is at offset +8 from scan code entry
        handler_addr_location = scan_code_addr + 8
        handler_addr = idc.get_wide_word(handler_addr_location)
        
        # Get handler name if it exists
        handler_name = idc.get_name(handler_addr)
        if not handler_name:
            handler_name = f"sub_{handler_addr:X}"
        
        entry = {
            'index': i,
            'scan_code': scan_code,
            'scan_code_hex': f'0x{scan_code:02X}',
            'scan_code_addr': f'0x{scan_code_addr:X}',
            'handler_addr': f'0x{handler_addr:X}',
            'handler_name': handler_name
        }
        
        entries.append(entry)
        
        print(f"  [{i}] Scan 0x{scan_code:02X} -> {handler_name} (0x{handler_addr:X})")
    
    return entries

def check_handler_for_flag_write(handler_addr, flag_addr=0x107762):
    """Check if a handler function writes to r15_external_view_flag."""
    
    func = idaapi.get_func(handler_addr)
    if not func:
        return {
            'writes_flag': False,
            'reason': 'not_a_function'
        }
    
    # Search function for writes to flag
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # Check for writes
        if mnem in ['mov', 'xor', 'or', 'and']:
            # Check if destination is our flag
            op0_type = idc.get_operand_type(ea, 0)
            if op0_type == idc.o_mem:
                op0_addr = idc.get_operand_value(ea, 0)
                if op0_addr == flag_addr:
                    insn = idc.GetDisasm(ea)
                    return {
                        'writes_flag': True,
                        'addr': f'0x{ea:X}',
                        'insn': insn
                    }
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'writes_flag': False,
        'reason': 'no_write_found'
    }

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("EXAMINING INPUT DISPATCH JUMP TABLES")
    print("=" * 80)
    
    # Table 1: r29_tactical_screen_coordinator
    table1_addr = 0x1E99
    table1_entries = read_dispatch_table(table1_addr, 4, "R29_2F8As")
    
    # Table 2: game_mode_r53_main_coordinator  
    table2_addr = 0x3225
    table2_entries = read_dispatch_table(table2_addr, 4, "R53_569Fs")
    
    # Check each handler for flag writes
    print("\n" + "=" * 80)
    print("CHECKING HANDLERS FOR FLAG WRITES")
    print("=" * 80)
    print(f"Looking for writes to r15_external_view_flag at 0x107762")
    print()
    
    all_handlers = {}
    
    for table_name, entries in [("Table1_R29", table1_entries), ("Table2_R53", table2_entries)]:
        print(f"\n[{table_name}]")
        for entry in entries:
            handler_addr = int(entry['handler_addr'], 16)
            print(f"  Checking {entry['handler_name']} (scan 0x{entry['scan_code']:02X})...", end="")
            
            result = check_handler_for_flag_write(handler_addr)
            
            if result['writes_flag']:
                print(f" *** WRITES FLAG! ***")
                print(f"      {result['addr']}: {result['insn']}")
            else:
                print(f" no ({result['reason']})")
            
            all_handlers[entry['handler_name']] = {
                'table': table_name,
                'scan_code': entry['scan_code_hex'],
                'addr': entry['handler_addr'],
                'flag_check': result
            }
    
    # Save results
    output = {
        'table1_r29_tactical': {
            'addr': f'0x{table1_addr:X}',
            'entries': table1_entries
        },
        'table2_r53_coordinator': {
            'addr': f'0x{table2_addr:X}',
            'entries': table2_entries
        },
        'handlers_analysis': all_handlers
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\jump_tables_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
