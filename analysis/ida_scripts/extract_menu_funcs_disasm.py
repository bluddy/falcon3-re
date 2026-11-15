"""
Extract disassembly of key menu functions
"""
import idaapi
import idautils
import idc
import json

def get_function_disasm(func_ea, max_lines=200):
    """Get disassembly of function"""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    lines = []
    ea = func.start_ea
    count = 0
    
    while ea < func.end_ea and count < max_lines:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Check for interesting operations
        mnem = idc.print_insn_mnem(ea)
        interesting = False
        note = None
        
        if mnem in ['call', 'callf']:
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target) if target != idc.BADADDR else None
            if target_name:
                note = f"calls {target_name}"
                interesting = True
        elif mnem in ['jmp', 'jmpf'] and 'far ptr' in disasm:
            interesting = True
            note = "far jump (overlay?)"
        elif 'str' in mnem.lower() or mnem in ['push', 'pop']:
            # String operations or stack ops
            pass
        
        lines.append({
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'disasm': disasm,
            'interesting': interesting,
            'note': note
        })
        
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    return lines

def main():
    # Key menu functions to analyze
    functions = {
        'ui_loadout_menu_enter': 0x683C1,
        'menu_cmd_store_and_record_scan': 0x160780,
        'ui_loadout_menu_enter_683C5': 0x683C5,  # Alternative address
    }
    
    results = {}
    
    for name, addr in functions.items():
        print(f"Extracting {name} at 0x{addr:X}...")
        
        disasm = get_function_disasm(addr, max_lines=200)
        if disasm:
            # Count interesting operations
            calls = [l for l in disasm if l['interesting'] and 'calls' in str(l.get('note', ''))]
            far_jumps = [l for l in disasm if l['interesting'] and 'far' in str(l.get('note', ''))]
            
            results[name] = {
                'address': addr,
                'hex_addr': f'0x{addr:X}',
                'name': name,
                'disasm_lines': len(disasm),
                'calls_count': len(calls),
                'far_jumps_count': len(far_jumps),
                'disassembly': disasm,
                'notable_calls': [c['note'] for c in calls[:10]]
            }
            
            print(f"  Lines: {len(disasm)}, Calls: {len(calls)}, Far jumps: {len(far_jumps)}")
        else:
            print(f"  Failed to extract")
    
    # Save
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\menu_functions_disasm.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved disassembly to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
