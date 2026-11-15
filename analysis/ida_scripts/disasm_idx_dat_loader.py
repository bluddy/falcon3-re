"""
Extract disassembly of madfont_idx_dat_loader - the .IDX/.DAT file loader
"""
import idaapi
import idautils
import idc
import json

def get_function_disasm_detailed(ea, max_size=2000):
    """Get complete disassembly of a function with all details"""
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    lines = []
    ea = func.start_ea
    instr_count = 0
    
    while ea < func.end_ea and instr_count < max_size:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Get operand details
        operands = []
        for i in range(8):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_void:
                break
            op_str = idc.print_operand(ea, i)
            operands.append({
                'str': op_str,
                'type': op_type
            })
        
        # Get any comment
        comment = idc.get_cmt(ea, 0)
        if not comment:
            comment = idc.get_cmt(ea, 1)
        
        # Get any xrefs from this instruction  
        xrefs = []
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idc.fl_CF, idc.fl_CN, idc.fl_JN, idc.fl_JF]:
                target_name = idc.get_func_name(xref.to)
                if not target_name:
                    target_name = idc.get_name(xref.to)
                xref_type = 'call'
                if xref.type in [idc.fl_JN, idc.fl_JF]:
                    xref_type = 'jump'
                xrefs.append({
                    'to': xref.to,
                    'hex_to': f'0x{xref.to:X}',
                    'name': target_name,
                    'type': xref_type
                })
        
        # Get bytes
        item_size = idc.get_item_size(ea)
        bytes_val = [idc.get_wide_byte(ea + i) for i in range(item_size)]
        
        lines.append({
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'disasm': disasm,
            'operands': operands,
            'comment': comment,
            'xrefs': xrefs,
            'bytes': bytes_val
        })
        
        ea = idc.next_head(ea, func.end_ea)
        instr_count += 1
    
    return lines

def main():
    # Target the IDX/DAT loader function found in xrefs
    targets = {
        'madfont_idx_dat_loader': 0x139909,
    }
    
    # Also try to find PEOPLE.DAT references manually
    # Search for strings
    people_addrs = []
    monitor_addrs = []
    
    print("Searching for PEOPLE and MONITOR strings...")
    for s in idautils.Strings():
        str_val = str(s).upper()
        if 'PEOPLE' in str_val:
            print(f"  Found PEOPLE string at 0x{s.ea:X}: {s}")
            people_addrs.append(s.ea)
        if 'MONITOR' in str_val:
            print(f"  Found MONITOR string at 0x{s.ea:X}: {s}")
            monitor_addrs.append(s.ea)
    
    # Find xrefs to these strings
    all_funcs = set()
    for addr in people_addrs + monitor_addrs:
        for xref in idautils.XrefsTo(addr, 0):
            func_name = idc.get_func_name(xref.frm)
            if func_name:
                func_addr = idc.get_name_ea_simple(func_name)
                all_funcs.add((func_name, func_addr))
                print(f"  Found xref from function {func_name} at 0x{func_addr:X}")
    
    # Add these functions to targets
    for name, addr in all_funcs:
        if addr and addr != idc.BADADDR:
            targets[name] = addr
    
    result = {}
    
    for name, addr in targets.items():
        print(f"\nExtracting {name} at 0x{addr:X}...")
        disasm = get_function_disasm_detailed(addr)
        if disasm:
            result[name] = {
                'address': addr,
                'hex_addr': f'0x{addr:X}',
                'name': name,
                'size': len(disasm),
                'disassembly': disasm
            }
            print(f"  Got {len(disasm)} instructions")
        else:
            print(f"  Failed to get function")
    
    # Save results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\idx_dat_loader_disasm.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Found {len(result)} functions")

if __name__ == '__main__':
    main()
    idc.qexit(0)
