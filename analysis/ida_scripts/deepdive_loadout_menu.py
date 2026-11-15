"""
Deep-dive analysis of ui_loadout_menu_enter (0x683C1)
Extract complete disassembly, analyze all calls, data references, and control flow
"""
import idaapi
import idautils
import idc
import json

def analyze_instruction(ea):
    """Detailed analysis of a single instruction"""
    mnem = idc.print_insn_mnem(ea)
    disasm = idc.generate_disasm_line(ea, 0)
    
    info = {
        'addr': ea,
        'hex_addr': f'0x{ea:X}',
        'mnem': mnem,
        'disasm': disasm,
        'operands': [],
        'data_refs': [],
        'code_refs': [],
        'comments': []
    }
    
    # Get operands
    for i in range(3):
        op_type = idc.get_operand_type(ea, i)
        if op_type == idc.o_void:
            break
        
        op_str = idc.print_operand(ea, i)
        op_value = idc.get_operand_value(ea, i)
        
        info['operands'].append({
            'index': i,
            'type': op_type,
            'string': op_str,
            'value': op_value if op_value != idc.BADADDR else None
        })
    
    # Get data references
    for xref in idautils.XrefsFrom(ea, 0):
        if xref.type == idc.fl_F:  # Data reference
            data_name = idc.get_name(xref.to)
            if not data_name:
                data_name = f'data_{xref.to:X}'
            
            info['data_refs'].append({
                'addr': xref.to,
                'hex_addr': f'0x{xref.to:X}',
                'name': data_name
            })
        elif xref.type in [idc.fl_CN, idc.fl_CF]:  # Call
            target_name = idc.get_func_name(xref.to)
            if not target_name:
                target_name = idc.get_name(xref.to)
            if not target_name:
                target_name = f'sub_{xref.to:X}'
            
            info['code_refs'].append({
                'addr': xref.to,
                'hex_addr': f'0x{xref.to:X}',
                'name': target_name,
                'type': 'call'
            })
        elif xref.type in [idc.fl_JN, idc.fl_JF]:  # Jump
            target_name = idc.get_name(xref.to)
            info['code_refs'].append({
                'addr': xref.to,
                'hex_addr': f'0x{xref.to:X}',
                'name': target_name if target_name else f'loc_{xref.to:X}',
                'type': 'jump'
            })
    
    # Get comments
    cmt = idc.get_cmt(ea, 0)
    if cmt:
        info['comments'].append(cmt)
    cmt = idc.get_cmt(ea, 1)
    if cmt:
        info['comments'].append(cmt)
    
    return info

def analyze_basic_blocks(func_ea):
    """Identify basic blocks (sequences without branches)"""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    # Get all jump/branch targets
    branch_targets = set([func.start_ea])
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # If this is a branch instruction, mark its target
        if mnem in ['jmp', 'jz', 'jnz', 'je', 'jne', 'jg', 'jl', 'jge', 'jle', 'ja', 'jb', 'jae', 'jbe', 'call']:
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_JN, idc.fl_JF]:
                    branch_targets.add(xref.to)
            
            # The instruction after a branch starts a new block
            next_ea = idc.next_head(ea, func.end_ea)
            if next_ea < func.end_ea:
                branch_targets.add(next_ea)
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Sort targets to create ordered blocks
    targets = sorted(list(branch_targets))
    
    blocks = []
    for i in range(len(targets)):
        start = targets[i]
        end = targets[i+1] if i+1 < len(targets) else func.end_ea
        
        if start < end:
            blocks.append({
                'start': start,
                'end': end,
                'hex_start': f'0x{start:X}',
                'hex_end': f'0x{end:X}'
            })
    
    return blocks

def get_all_data_references(func_ea):
    """Get all unique data addresses referenced by function"""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    data_refs = {}
    
    ea = func.start_ea
    while ea < func.end_ea:
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type == idc.fl_F:  # Data reference
                if xref.to not in data_refs:
                    data_name = idc.get_name(xref.to)
                    
                    # Try to get the data type
                    data_type = None
                    flags = idc.get_full_flags(xref.to)
                    if idc.is_byte(flags):
                        data_type = 'byte'
                    elif idc.is_word(flags):
                        data_type = 'word'
                    elif idc.is_dword(flags):
                        data_type = 'dword'
                    
                    data_refs[xref.to] = {
                        'addr': xref.to,
                        'hex_addr': f'0x{xref.to:X}',
                        'name': data_name if data_name else f'data_{xref.to:X}',
                        'type': data_type,
                        'ref_count': 0
                    }
                
                data_refs[xref.to]['ref_count'] += 1
        
        ea = idc.next_head(ea, func.end_ea)
    
    return list(data_refs.values())

def main():
    func_addr = 0x683C1  # ui_loadout_menu_enter
    
    print("="*60)
    print("DEEP-DIVE: ui_loadout_menu_enter")
    print(f"Address: 0x{func_addr:X}")
    print("="*60)
    
    func = idaapi.get_func(func_addr)
    if not func:
        print("ERROR: Could not get function")
        return
    
    print(f"\nFunction bounds: 0x{func.start_ea:X} - 0x{func.end_ea:X}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    # 1. Analyze all instructions
    print("\n1. Extracting complete disassembly...")
    instructions = []
    ea = func.start_ea
    while ea < func.end_ea:
        instr = analyze_instruction(ea)
        instructions.append(instr)
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"   Total instructions: {len(instructions)}")
    
    # 2. Identify basic blocks
    print("\n2. Identifying basic blocks...")
    basic_blocks = analyze_basic_blocks(func_addr)
    print(f"   Basic blocks: {len(basic_blocks)}")
    
    # 3. Get all data references
    print("\n3. Analyzing data references...")
    data_refs = get_all_data_references(func_addr)
    print(f"   Unique data addresses: {len(data_refs)}")
    
    # 4. Count instruction types
    print("\n4. Instruction statistics...")
    mnem_counts = {}
    for instr in instructions:
        m = instr['mnem']
        mnem_counts[m] = mnem_counts.get(m, 0) + 1
    
    top_mnems = sorted(mnem_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for mnem, count in top_mnems:
        print(f"   {mnem:10s}: {count:3d}")
    
    # 5. Analyze call patterns
    print("\n5. Function calls...")
    calls = [i for i in instructions if i['mnem'] in ['call', 'callf']]
    call_targets = {}
    for call in calls:
        if call['code_refs']:
            target = call['code_refs'][0]['name']
            call_targets[target] = call_targets.get(target, 0) + 1
    
    print(f"   Total call instructions: {len(calls)}")
    print(f"   Unique functions called: {len(call_targets)}")
    print(f"   Top 10 most called:")
    for target, count in sorted(call_targets.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     {target:40s}: {count:2d} times")
    
    # 6. Data access patterns
    print("\n6. Most accessed data:")
    top_data = sorted(data_refs, key=lambda x: x['ref_count'], reverse=True)[:10]
    for data in top_data:
        print(f"   {data['name']:40s}: {data['ref_count']:2d} refs ({data['type'] or 'unknown'})")
    
    # Compile results
    results = {
        'function': {
            'name': 'ui_loadout_menu_enter',
            'address': func.start_ea,
            'hex_addr': f'0x{func.start_ea:X}',
            'size': func.end_ea - func.start_ea,
            'instruction_count': len(instructions),
            'basic_block_count': len(basic_blocks),
            'unique_data_refs': len(data_refs),
            'unique_calls': len(call_targets)
        },
        'instructions': instructions,
        'basic_blocks': basic_blocks,
        'data_references': data_refs,
        'call_statistics': call_targets,
        'instruction_counts': mnem_counts
    }
    
    # Save
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\loadout_menu_deepdive.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Complete analysis saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
