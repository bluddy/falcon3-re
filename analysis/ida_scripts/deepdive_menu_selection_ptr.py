"""
Deep-dive analysis of menu_selection_ptr_get
This function is called 14 times by ui_loadout_menu_enter - it's the core of the menu loop
"""
import idaapi
import idautils
import idc
import json

def find_menu_selection_ptr_get():
    """Find the menu_selection_ptr_get function"""
    # Search by name
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if 'menu_selection_ptr_get' in name.lower():
            return func_ea
    
    # If not found by name, search in loadout function's callees
    loadout_ea = 0x683C1
    func = idaapi.get_func(loadout_ea)
    if func:
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) in ['call', 'callf']:
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type in [idc.fl_CN, idc.fl_CF]:
                        target_name = idc.get_func_name(xref.to)
                        if target_name and 'selection' in target_name.lower():
                            return xref.to
            ea = idc.next_head(ea, func.end_ea)
    
    return None

def analyze_function_complete(func_ea):
    """Complete analysis of a function"""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    func_name = idc.get_func_name(func_ea)
    
    # Get all instructions with details
    instructions = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        instr = {
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'mnem': mnem,
            'disasm': disasm,
            'operands': []
        }
        
        # Get operands
        for i in range(3):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_void:
                break
            
            op_str = idc.print_operand(ea, i)
            instr['operands'].append(op_str)
        
        # Mark interesting instructions
        if mnem in ['ret', 'retf', 'retn']:
            instr['note'] = 'RETURN'
        elif mnem in ['call', 'callf']:
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target) if target != idc.BADADDR else None
            if target_name:
                instr['note'] = f'calls {target_name}'
        elif mnem.startswith('j') and mnem != 'jmp':
            instr['note'] = f'conditional branch'
        elif mnem in ['mov', 'lea'] and 'ptr' in disasm:
            instr['note'] = 'pointer operation'
        
        instructions.append(instr)
        ea = idc.next_head(ea, func.end_ea)
    
    # Get all callees
    callees = []
    for instr in instructions:
        if instr['mnem'] in ['call', 'callf'] and 'note' in instr and instr['note'].startswith('calls'):
            callee_name = instr['note'].split('calls ')[1]
            if callee_name not in [c['name'] for c in callees]:
                callees.append({'name': callee_name})
    
    # Get all callers
    callers = []
    for xref in idautils.XrefsTo(func.start_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name and caller_name not in [c['name'] for c in callers]:
                callers.append({
                    'name': caller_name,
                    'addr': xref.frm,
                    'hex_addr': f'0x{xref.frm:X}'
                })
    
    # Count instruction types
    mnem_counts = {}
    for instr in instructions:
        m = instr['mnem']
        mnem_counts[m] = mnem_counts.get(m, 0) + 1
    
    # Find return points
    returns = [i for i in instructions if i['mnem'] in ['ret', 'retf', 'retn']]
    
    return {
        'name': func_name,
        'address': func.start_ea,
        'hex_addr': f'0x{func.start_ea:X}',
        'size': func.end_ea - func.start_ea,
        'instruction_count': len(instructions),
        'return_count': len(returns),
        'callee_count': len(callees),
        'caller_count': len(callers),
        'instructions': instructions,
        'callees': callees,
        'callers': callers,
        'mnem_counts': mnem_counts,
        'returns': returns
    }

def analyze_parameters(func_info):
    """Analyze function parameters from instruction patterns"""
    instructions = func_info['instructions']
    
    # Look for [bp+X] references in first few instructions
    params = []
    for i, instr in enumerate(instructions[:20]):
        for op in instr['operands']:
            if '[bp+' in op or '[ebp+' in op:
                # Extract offset
                import re
                match = re.search(r'\[e?bp\+([0-9A-Fa-fx]+)\]', op)
                if match:
                    offset = match.group(1)
                    param_name = f'arg_{offset}'
                    if param_name not in [p['name'] for p in params]:
                        params.append({
                            'name': param_name,
                            'offset': offset,
                            'first_use': i,
                            'instruction': instr['disasm']
                        })
    
    return params

def main():
    print("="*60)
    print("DEEP-DIVE: menu_selection_ptr_get")
    print("="*60)
    
    # Find the function
    print("\n1. Locating function...")
    func_ea = find_menu_selection_ptr_get()
    
    if not func_ea:
        print("ERROR: Could not find menu_selection_ptr_get")
        return
    
    print(f"   Found at: 0x{func_ea:X}")
    
    # Analyze completely
    print("\n2. Analyzing function...")
    analysis = analyze_function_complete(func_ea)
    
    if not analysis:
        print("ERROR: Could not analyze function")
        return
    
    print(f"   Name: {analysis['name']}")
    print(f"   Size: {analysis['size']} bytes")
    print(f"   Instructions: {analysis['instruction_count']}")
    print(f"   Callees: {analysis['callee_count']}")
    print(f"   Callers: {analysis['caller_count']}")
    print(f"   Return points: {analysis['return_count']}")
    
    # Analyze parameters
    print("\n3. Analyzing parameters...")
    params = analyze_parameters(analysis)
    print(f"   Parameters detected: {len(params)}")
    for p in params:
        print(f"     {p['name']} (offset {p['offset']}) - first use: {p['instruction']}")
    
    # Instruction statistics
    print("\n4. Instruction breakdown:")
    for mnem, count in sorted(analysis['mnem_counts'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {mnem:10s}: {count:3d}")
    
    # Show who calls this
    print(f"\n5. Called by {len(analysis['callers'])} functions:")
    for caller in analysis['callers'][:10]:
        print(f"   {caller['name']:40s} (0x{caller['addr']:X})")
    
    # Show full disassembly
    print(f"\n6. Complete disassembly:")
    print("   " + "-"*58)
    for instr in analysis['instructions']:
        note = f"  <-- {instr['note']}" if 'note' in instr else ""
        print(f"   {instr['hex_addr']}  {instr['disasm']:45s}{note}")
    print("   " + "-"*58)
    
    # Add parameter analysis to results
    analysis['parameters'] = params
    
    # Save
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\menu_selection_ptr_deepdive.json'
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Analysis saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
