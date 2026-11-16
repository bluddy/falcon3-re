"""
Find the actual addresses of the jump tables by examining the dispatcher code.

The dispatcher at 0x12DFD6 loads table address into BX:
  mov bx, 1E99h

But this is relative to CS segment. Need to find actual linear address.
"""

import idc
import idaapi
import json

def analyze_dispatcher_detail(dispatch_addr):
    """Analyze dispatcher to find table address."""
    
    func_name = idc.get_func_name(dispatch_addr)
    seg_name = idc.get_segm_name(dispatch_addr)
    
    print(f"\n[*] Analyzing dispatcher at 0x{dispatch_addr:X}")
    print(f"    Function: {func_name}")
    print(f"    Segment: {seg_name}")
    print()
    
    # Read next 30 instructions
    ea = dispatch_addr
    table_addr_offset = None
    
    for i in range(30):
        insn = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        
        print(f"  0x{ea:X}: {insn}")
        
        # Look for "mov bx, <offset>"
        if mnem == 'mov' and 'bx' in insn:
            op1_type = idc.get_operand_type(ea, 1)
            if op1_type == idc.o_imm:
                table_addr_offset = idc.get_operand_value(ea, 1)
                print(f"    ^^^ TABLE OFFSET: 0x{table_addr_offset:X}")
        
        # Look for the jump table indirect jump
        if 'jmp' in mnem and 'ptr' in insn and '[bx' in insn:
            print(f"    ^^^ JUMP TABLE ACCESS")
            # The table is accessed as cs:[bx+8]
            # This means: scan_code at cs:[bx], handler at cs:[bx+8]
        
        ea = idc.next_head(ea)
    
    # Calculate absolute address
    if table_addr_offset is not None:
        # Get segment base
        seg = idaapi.getseg(dispatch_addr)
        if seg:
            # For code segment references, need to get CS segment base
            # In this case, the offset is within the same segment
            func = idaapi.get_func(dispatch_addr)
            if func:
                # The table is in the code segment, use function's segment
                seg_start = seg.start_ea
                # The linear address is segment_base + offset
                # But we need to find where offset 0x1E99 actually is in linear space
                
                print(f"\n    Segment start: 0x{seg_start:X}")
                print(f"    Table offset: 0x{table_addr_offset:X}")
                
                # Try to resolve the address
                # The mov bx, 1E99h is loading an offset within CS
                # Need to add to segment base
                table_linear = seg_start + table_addr_offset
                print(f"    Calculated linear: 0x{table_linear:X}")
                
                # Verify it's valid
                if idc.is_mapped(table_linear):
                    print(f"    ✓ Address is valid")
                    return table_linear
                else:
                    print(f"    ✗ Address not mapped, trying alternate calculation")
                    
                    # Maybe it's already an absolute address within the overlay
                    # Try using it directly
                    if idc.is_mapped(table_addr_offset):
                        print(f"    ✓ Offset itself is valid linear address: 0x{table_addr_offset:X}")
                        return table_addr_offset
    
    return None

def read_table_entries(table_addr, max_entries=10):
    """Read jump table entries."""
    
    print(f"\n[*] Reading table at 0x{table_addr:X}")
    print()
    
    entries = []
    
    for i in range(max_entries):
        # Read scan code (word)
        scan_addr = table_addr + (i * 2)
        scan_code = idc.get_wide_word(scan_addr)
        
        # Handler is 8 bytes after scan code entry
        handler_ptr_addr = scan_addr + 8
        handler_addr = idc.get_wide_word(handler_ptr_addr)
        
        # Stop if we hit invalid data
        if scan_code == 0xFFFF or scan_code == 0:
            if i == 0:
                print(f"    [ERROR] First entry is 0x{scan_code:X}, table address likely wrong")
            break
        
        handler_name = idc.get_name(handler_addr)
        if not handler_name:
            handler_name = f"sub_{handler_addr:X}"
        
        print(f"  [{i}] Scan 0x{scan_code:02X} @ 0x{scan_addr:X} -> {handler_name} @ 0x{handler_ptr_addr:X} (target: 0x{handler_addr:X})")
        
        entries.append({
            'index': i,
            'scan_code': scan_code,
            'scan_code_hex': f'0x{scan_code:02X}',
            'handler_addr': f'0x{handler_addr:X}',
            'handler_name': handler_name
        })
    
    return entries

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("FINDING JUMP TABLE ADDRESSES")
    print("=" * 80)
    
    # Dispatcher 1: r29_tactical_screen_coordinator
    dispatch1 = 0x12DFD6
    table1 = analyze_dispatcher_detail(dispatch1)
    
    # Dispatcher 2: game_mode_r53_main_coordinator
    dispatch2 = 0x182476
    table2 = analyze_dispatcher_detail(dispatch2)
    
    # Read table entries if we found them
    results = {}
    
    if table1:
        print("\n" + "=" * 80)
        print("TABLE 1 ENTRIES (R29)")
        print("=" * 80)
        entries1 = read_table_entries(table1)
        results['table1'] = {
            'address': f'0x{table1:X}',
            'entries': entries1
        }
    
    if table2:
        print("\n" + "=" * 80)
        print("TABLE 2 ENTRIES (R53)")
        print("=" * 80)
        entries2 = read_table_entries(table2)
        results['table2'] = {
            'address': f'0x{table2:X}',
            'entries': entries2
        }
    
    # Save
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\jump_table_addresses.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
