"""
Analyze ui_slot_scan_step - the real menu_selection_ptr_get implementation in overlay
"""
import idaapi
import idautils
import idc
import json

def find_function_by_name(name):
    """Find function by name"""
    for func_ea in idautils.Functions():
        if name.lower() in idc.get_func_name(func_ea).lower():
            return func_ea
    return None

def analyze_function_detailed(func_ea):
    """Detailed function analysis"""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    func_name = idc.get_func_name(func_ea)
    
    # Get all instructions
    instructions = []
    data_refs = set()
    callees = set()
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        instr = {
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'offset': ea - func.start_ea,
            'mnem': mnem,
            'disasm': disasm
        }
        
        # Track calls
        if mnem in ['call', 'callf']:
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    target_name = idc.get_func_name(xref.to)
                    if target_name:
                        callees.add(target_name)
                        instr['calls'] = target_name
        
        # Track data references
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type == idc.fl_F:
                data_name = idc.get_name(xref.to)
                if data_name:
                    data_refs.add((xref.to, data_name))
        
        instructions.append(instr)
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    callers = []
    for xref in idautils.XrefsTo(func.start_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                callers.append({
                    'name': caller_name,
                    'addr': xref.frm
                })
    
    return {
        'name': func_name,
        'address': func.start_ea,
        'hex_addr': f'0x{func.start_ea:X}',
        'end_address': func.end_ea,
        'size': func.end_ea - func.start_ea,
        'instruction_count': len(instructions),
        'instructions': instructions,
        'callees': list(callees),
        'callers': callers,
        'data_refs': [{'addr': addr, 'name': name} for addr, name in data_refs]
    }

def main():
    print("="*60)
    print("ANALYZING: ui_slot_scan_step")
    print("="*60)
    
    # Find the function
    func_ea = find_function_by_name('ui_slot_scan_step')
    
    if not func_ea:
        print("ERROR: Could not find ui_slot_scan_step")
        print("\nSearching for similar names...")
        for f_ea in idautils.Functions():
            name = idc.get_func_name(f_ea)
            if 'slot' in name.lower() and 'scan' in name.lower():
                print(f"  Found: {name} at 0x{f_ea:X}")
        return
    
    print(f"\nFound at: 0x{func_ea:X}")
    
    # Analyze
    print("\nAnalyzing function...")
    analysis = analyze_function_detailed(func_ea)
    
    if not analysis:
        print("ERROR: Could not analyze")
        return
    
    print(f"\nFunction: {analysis['name']}")
    print(f"Address: {analysis['hex_addr']}")
    print(f"Size: {analysis['size']} bytes")
    print(f"Instructions: {analysis['instruction_count']}")
    print(f"Callees: {len(analysis['callees'])}")
    print(f"Callers: {len(analysis['callers'])}")
    print(f"Data refs: {len(analysis['data_refs'])}")
    
    # Show callees
    if analysis['callees']:
        print(f"\nCalls these functions:")
        for callee in analysis['callees'][:15]:
            print(f"  - {callee}")
    
    # Show callers
    if analysis['callers']:
        print(f"\nCalled by:")
        for caller in analysis['callers'][:10]:
            print(f"  - {caller['name']} (0x{caller['addr']:X})")
    
    # Show key data references
    if analysis['data_refs']:
        print(f"\nData references:")
        for ref in analysis['data_refs'][:10]:
            print(f"  - {ref['name']} (0x{ref['addr']:X})")
    
    # Show first 30 instructions
    print(f"\nFirst 30 instructions:")
    print("  " + "-"*58)
    for instr in analysis['instructions'][:30]:
        offset_str = f"+{instr['offset']:03X}"
        call_note = f"  -> {instr.get('calls', '')}" if 'calls' in instr else ""
        print(f"  {offset_str}  {instr['hex_addr']}  {instr['disasm']}{call_note}")
    
    if len(analysis['instructions']) > 30:
        print(f"  ... ({len(analysis['instructions']) - 30} more instructions)")
    print("  " + "-"*58)
    
    # Save
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\ui_slot_scan_step_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Analysis saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
