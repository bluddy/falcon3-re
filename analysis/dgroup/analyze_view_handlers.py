"""
Analyze the view handler functions to understand how they work.

We found these handlers in game_mode_r53_main_coordinator dispatcher:
- scan 0x01 -> handler at 0x3F3
- scan 0x03 -> handler at 0x3E5 (Key 2 - Ground view - external)
- scan 0x04 -> handler at 0x408 (Key 3 - Front cockpit - internal)
- scan 0xFF -> handler at 0x54A

The addresses 0x3F3, 0x3E5, etc. are offsets from the jump table location.
Need to calculate actual linear addresses.
"""

import idc
import idaapi
import idautils
import json

def resolve_handler_address(dispatcher_addr, handler_offset):
    """
    Resolve handler address from the jump table.
    
    The dispatcher does: jmp word ptr cs:[bx+8]
    Where bx points to the matched scan code entry.
    The handler address is stored 8 bytes after the scan code.
    """
    
    # Get the segment of the dispatcher
    seg = idaapi.getseg(dispatcher_addr)
    if not seg:
        return None
    
    # The handler offset might be relative to the segment
    # Try adding segment base
    handler_addr = seg.start_ea + handler_offset
    
    if idc.is_mapped(handler_addr):
        return handler_addr
    
    # Try the offset as absolute
    if idc.is_mapped(handler_offset):
        return handler_offset
    
    return None

def analyze_handler_function(handler_addr, handler_name, flag_addr=0x107762):
    """
    Analyze a view handler function.
    
    Look for:
    1. Writes to r15_external_view_flag
    2. Calls to other functions
    3. Parameter passing patterns
    """
    
    print(f"\n{'='*80}")
    print(f"ANALYZING: {handler_name} at 0x{handler_addr:X}")
    print('='*80)
    
    func = idaapi.get_func(handler_addr)
    if not func:
        print(f"  ERROR: Not a function at 0x{handler_addr:X}")
        print(f"  Showing raw disassembly:")
        
        # Show raw disassembly
        ea = handler_addr
        for i in range(30):
            insn = idc.GetDisasm(ea)
            print(f"    0x{ea:X}: {insn}")
            ea = idc.next_head(ea)
        
        return {
            'addr': f'0x{handler_addr:X}',
            'name': handler_name,
            'is_function': False,
            'raw_disasm': 'see output'
        }
    
    print(f"  Function: {idc.get_func_name(handler_addr)}")
    print(f"  Start: 0x{func.start_ea:X}")
    print(f"  End: 0x{func.end_ea:X}")
    print(f"  Size: {func.end_ea - func.start_ea} bytes")
    print()
    
    result = {
        'addr': f'0x{handler_addr:X}',
        'name': handler_name,
        'func_name': idc.get_func_name(handler_addr),
        'start': f'0x{func.start_ea:X}',
        'end': f'0x{func.end_ea:X}',
        'size': func.end_ea - func.start_ea,
        'is_function': True,
        'flag_writes': [],
        'function_calls': [],
        'interesting': []
    }
    
    # Analyze instructions
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        
        # Check for writes to flag
        if mnem in ['mov', 'xor', 'or', 'and', 'inc', 'dec']:
            op0_type = idc.get_operand_type(ea, 0)
            if op0_type == idc.o_mem:
                op0_addr = idc.get_operand_value(ea, 0)
                if op0_addr == flag_addr:
                    print(f"  *** FLAG WRITE: 0x{ea:X}: {insn}")
                    result['flag_writes'].append({
                        'addr': f'0x{ea:X}',
                        'insn': insn
                    })
        
        # Check for function calls
        if mnem == 'call':
            target_addr = idc.get_operand_value(ea, 0)
            target_name = idc.get_name(target_addr)
            if not target_name:
                target_name = f"sub_{target_addr:X}"
            
            print(f"  CALL: 0x{ea:X}: {target_name}")
            result['function_calls'].append({
                'addr': f'0x{ea:X}',
                'target': f'0x{target_addr:X}',
                'name': target_name
            })
        
        # Check for view-related names
        if any(x in insn.lower() for x in ['view', 'external', 'cockpit', 'camera']):
            print(f"  VIEW-RELATED: 0x{ea:X}: {insn}")
            result['interesting'].append({
                'addr': f'0x{ea:X}',
                'insn': insn,
                'reason': 'view_related'
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Show first 20 instructions
    print(f"\n  First 20 instructions:")
    ea = func.start_ea
    for i in range(min(20, result['size'])):
        insn = idc.GetDisasm(ea)
        print(f"    0x{ea:X}: {insn}")
        ea = idc.next_head(ea, func.end_ea)
        if ea >= func.end_ea:
            break
    
    return result

def trace_function_call_chain(func_addr, flag_addr, depth=0, max_depth=3, visited=None):
    """
    Recursively trace function calls to see if they eventually write the flag.
    """
    
    if visited is None:
        visited = set()
    
    if func_addr in visited or depth > max_depth:
        return []
    
    visited.add(func_addr)
    
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    flag_writes = []
    
    # Check this function
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # Check for flag write
        if mnem in ['mov', 'xor', 'or', 'and']:
            op0_type = idc.get_operand_type(ea, 0)
            if op0_type == idc.o_mem:
                op0_addr = idc.get_operand_value(ea, 0)
                if op0_addr == flag_addr:
                    insn = idc.GetDisasm(ea)
                    flag_writes.append({
                        'depth': depth,
                        'func': f'0x{func_addr:X}',
                        'func_name': idc.get_func_name(func_addr),
                        'addr': f'0x{ea:X}',
                        'insn': insn
                    })
        
        # Recurse into calls
        if mnem == 'call' and depth < max_depth:
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR:
                sub_writes = trace_function_call_chain(target, flag_addr, depth + 1, max_depth, visited)
                flag_writes.extend(sub_writes)
        
        ea = idc.next_head(ea, func.end_ea)
    
    return flag_writes

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("ANALYZING VIEW HANDLER FUNCTIONS")
    print("="*80)
    
    FLAG_ADDR = 0x107762
    
    # From jump_table_addresses.json, Table 2 (R53) had:
    # scan 0x01 -> handler 0x3F3
    # scan 0x03 -> handler 0x3E5 (ground view)
    # scan 0x04 -> handler 0x408 (cockpit view)
    # scan 0xFF -> handler 0x54A
    
    # The dispatcher is at 0x182476 in game_mode_r53_main_coordinator
    dispatcher_addr = 0x182476
    
    # Try to resolve actual handler addresses
    handlers = [
        (0x3F3, 'handler_scan_01', 0x01),
        (0x3E5, 'handler_scan_03_ground_external', 0x03),
        (0x408, 'handler_scan_04_cockpit_internal', 0x04),
        (0x54A, 'handler_scan_FF', 0xFF),
    ]
    
    results = []
    
    for handler_offset, handler_name, scan_code in handlers:
        # Try multiple address resolution strategies
        
        # Strategy 1: Offset from dispatcher segment
        handler_addr = resolve_handler_address(dispatcher_addr, handler_offset)
        
        # Strategy 2: The offset might already be linear in table2 segment
        if not handler_addr:
            # Table2 was at 0x1852D5
            table_seg = idaapi.getseg(0x1852D5)
            if table_seg:
                handler_addr = table_seg.start_ea + handler_offset
        
        # Strategy 3: Look near the table itself
        if not handler_addr or not idc.is_mapped(handler_addr):
            # Try addresses near the dispatcher
            handler_addr = 0x182400 + handler_offset  # Rough guess
        
        if handler_addr and idc.is_mapped(handler_addr):
            result = analyze_handler_function(handler_addr, handler_name, FLAG_ADDR)
            result['scan_code'] = f'0x{scan_code:02X}'
            results.append(result)
            
            # If no direct flag write, trace call chain
            if not result.get('flag_writes'):
                print(f"\n  [*] No direct flag write, tracing call chain...")
                if result['is_function']:
                    chain_writes = trace_function_call_chain(handler_addr, FLAG_ADDR)
                    if chain_writes:
                        print(f"  [*] FOUND FLAG WRITE IN CALL CHAIN:")
                        for w in chain_writes:
                            print(f"      Depth {w['depth']}: {w['func_name']} at {w['addr']}: {w['insn']}")
                        result['flag_writes_in_chain'] = chain_writes
                    else:
                        print(f"  [*] No flag writes found in call chain (depth 3)")
        else:
            print(f"\n[!] Could not resolve address for {handler_name} (offset 0x{handler_offset:X})")
    
    # Save results
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\view_handlers_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
