"""
Extract R45 overlay menu system for analysis.
"""

import idaapi
import idautils
import idc
import json

def extract_function_disasm(func_addr, max_instructions=500):
    """Extract disassembly for a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    instructions = []
    ea = func.start_ea
    count = 0
    
    while ea < func.end_ea and count < max_instructions:
        disasm = idc.generate_disasm_line(ea, 0)
        mnem = idc.print_insn_mnem(ea)
        
        instructions.append({
            'address': ea,
            'offset': ea - func.start_ea,
            'mnem': mnem,
            'disasm': disasm
        })
        
        ea = idc.next_head(ea)
        count += 1
    
    return instructions

def analyze_r45_system():
    """Analyze R45 menu overlay."""
    idaapi.auto_wait()
    
    print("="*80)
    print("ANALYZING R45 MENU OVERLAY")
    print("="*80)
    
    # R45 functions from registry
    r45_functions = {
        'overlay_r45_logic': 0x181E80,
    }
    
    # Search for more R45 functions
    print("\nSearching for R45 functions...")
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if 'r45' in func_name.lower() or 'R45' in func_name:
            r45_functions[func_name] = func_ea
            print(f"  Found: {func_name} at 0x{func_ea:X}")
    
    print(f"\nFound {len(r45_functions)} R45 functions")
    
    # Analyze each function
    results = {}
    
    for name, addr in sorted(r45_functions.items(), key=lambda x: x[1]):
        print(f"\n{'='*80}")
        print(f"FUNCTION: {name} at 0x{addr:X}")
        print(f"{'='*80}")
        
        func = idaapi.get_func(addr)
        if not func:
            print("  ERROR: Cannot get function")
            continue
        
        size = func.end_ea - func.start_ea
        print(f"Size: {size} bytes (0x{size:X})")
        
        # Get calls
        calls = []
        for ea in range(func.start_ea, func.end_ea):
            if idc.print_insn_mnem(ea) in ['call', 'callf']:
                target = idc.get_operand_value(ea, 0)
                if target != idc.BADADDR:
                    target_name = idc.get_func_name(target)
                    if not target_name:
                        target_name = f"sub_{target:X}"
                    calls.append({
                        'addr': ea,
                        'target': target,
                        'name': target_name
                    })
        
        print(f"Calls: {len(calls)}")
        for call in calls[:10]:
            print(f"  0x{call['addr']:X}: {call['name']} (0x{call['target']:X})")
        if len(calls) > 10:
            print(f"  ... and {len(calls) - 10} more")
        
        # Get xrefs
        xrefs = list(idautils.XrefsTo(addr))
        print(f"Cross-references: {len(xrefs)}")
        for xref in xrefs[:10]:
            func_from = idaapi.get_func(xref.frm)
            if func_from:
                caller_name = idc.get_func_name(func_from.start_ea)
                print(f"  0x{xref.frm:X}: called by {caller_name}")
        
        # Look for string references
        strings = []
        for ea in range(func.start_ea, func.end_ea):
            for xref in idautils.XrefsFrom(ea):
                target = xref.to
                str_type = idc.get_str_type(target)
                if str_type is not None:
                    str_val = idc.get_strlit_contents(target)
                    if str_val:
                        str_text = str_val.decode('ascii', errors='ignore')
                        strings.append((ea, str_text))
        
        if strings:
            print(f"\nString references: {len(strings)}")
            for ea, s in strings[:10]:
                print(f"  0x{ea:X}: {repr(s)}")
        
        # Extract disassembly
        print(f"\nExtracting disassembly...")
        instructions = extract_function_disasm(addr, max_instructions=200)
        
        if instructions:
            print(f"First 50 instructions:")
            for instr in instructions[:50]:
                print(f"  {instr['offset']:4X}: {instr['disasm']}")
            
            results[name] = {
                'address': addr,
                'size': size,
                'calls': calls,
                'xrefs_count': len(xrefs),
                'strings': strings,
                'instructions': instructions
            }
    
    # Save results
    output_file = "r45_menu_extraction.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    analyze_r45_system()
