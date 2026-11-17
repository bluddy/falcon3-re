"""
Disassemble R55 mission editor main loop
Focus on waypoint manipulation and mission editing operations
"""

import idaapi
import idc
import idautils
import json

def disassemble_function_detailed(func_addr, func_name):
    """Detailed disassembly with annotations"""
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"ERROR: Function not found at 0x{func_addr:X}")
        return None
    
    print(f"Disassembling {func_name} @ 0x{func_addr:X}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    result = {
        'name': func_name,
        'addr': func_addr,
        'start': func.start_ea,
        'end': func.end_ea,
        'size': func.end_ea - func.start_ea,
        'instructions': [],
        'calls': [],
        'data_refs': [],
        'waypoint_operations': [],
        'loops': []
    }
    
    ea = func.start_ea
    instr_num = 0
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1) or ""
        
        instr = {
            'num': instr_num,
            'addr': ea,
            'offset': ea - func.start_ea,
            'mnem': mnem,
            'disasm': disasm,
            'comment': comment
        }
        
        result['instructions'].append(instr)
        
        # Track function calls
        if mnem == 'call':
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target) if target else None
            result['calls'].append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'target': target,
                'target_name': target_name,
                'disasm': disasm
            })
        
        # Track waypoint operations (21-byte accesses)
        if 'mov' in mnem and 'dx' in disasm and '15h' in disasm:
            result['waypoint_operations'].append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'disasm': disasm,
                'context': 'waypoint_size_load'
            })
        
        # Track data references
        for i in range(2):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_mem:
                data_addr = idc.get_operand_value(ea, i)
                data_name = idc.get_name(data_addr)
                if data_name:
                    result['data_refs'].append({
                        'addr': ea,
                        'offset': ea - func.start_ea,
                        'data_addr': data_addr,
                        'data_name': data_name,
                        'disasm': disasm
                    })
        
        # Track loops
        if mnem in ['jmp', 'jl', 'jle', 'jg', 'jge', 'je', 'jne', 'jz', 'jnz']:
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR:
                result['loops'].append({
                    'addr': ea,
                    'offset': ea - func.start_ea,
                    'target': target,
                    'target_offset': target - func.start_ea,
                    'type': mnem,
                    'disasm': disasm
                })
        
        ea = idc.next_head(ea, func.end_ea)
        instr_num += 1
    
    result['instruction_count'] = instr_num
    
    return result

def create_readable_disassembly(result):
    """Create human-readable disassembly output"""
    
    lines = []
    lines.append("=" * 100)
    lines.append(f"FUNCTION: {result['name']}")
    lines.append(f"Address: 0x{result['addr']:08X}")
    lines.append(f"Size: {result['size']} bytes ({result['instruction_count']} instructions)")
    lines.append("=" * 100)
    lines.append("")
    
    # Show key statistics
    lines.append("STATISTICS:")
    lines.append(f"  Function calls: {len(result['calls'])}")
    lines.append(f"  Data references: {len(result['data_refs'])}")
    lines.append(f"  Waypoint operations: {len(result['waypoint_operations'])}")
    lines.append(f"  Branch/loop instructions: {len(result['loops'])}")
    lines.append("")
    
    # Show waypoint operations
    if result['waypoint_operations']:
        lines.append("WAYPOINT OPERATIONS:")
        lines.append("-" * 100)
        for op in result['waypoint_operations']:
            lines.append(f"  +0x{op['offset']:04X} @ 0x{op['addr']:06X}: {op['disasm']}")
        lines.append("")
    
    # Show key data references
    if result['data_refs']:
        lines.append("KEY DATA REFERENCES:")
        lines.append("-" * 100)
        for ref in result['data_refs'][:20]:  # First 20
            lines.append(f"  +0x{ref['offset']:04X} @ 0x{ref['addr']:06X}: {ref['data_name']}")
            lines.append(f"    {ref['disasm']}")
        lines.append("")
    
    # Show function calls
    if result['calls']:
        lines.append("FUNCTION CALLS:")
        lines.append("-" * 100)
        for call in result['calls'][:30]:  # First 30
            target_name = call['target_name'] or f"0x{call['target']:X}"
            lines.append(f"  +0x{call['offset']:04X} @ 0x{call['addr']:06X}: call {target_name}")
        lines.append("")
    
    # Full disassembly
    lines.append("COMPLETE DISASSEMBLY:")
    lines.append("-" * 100)
    
    for instr in result['instructions']:
        line = f"{instr['num']:4d} | +0x{instr['offset']:04X} | 0x{instr['addr']:06X} | {instr['disasm']}"
        if instr['comment']:
            line += f"  ; {instr['comment']}"
        lines.append(line)
    
    return "\n".join(lines)

def main():
    print("Starting R55 mission editor disassembly...")
    idaapi.auto_wait()
    
    # Functions to disassemble
    functions = {
        0x18BC28: "mission_editor_main_loop",
        0x18DE3B: "waypoint_flags_processor",
    }
    
    all_results = {}
    
    for addr, name in functions.items():
        print(f"\n{'=' * 80}")
        result = disassemble_function_detailed(addr, name)
        
        if result:
            all_results[name] = result
            
            # Create readable output
            readable = create_readable_disassembly(result)
            
            # Save to text file
            txt_path = f"C:\\Users\\ybarnoy\\projects\\falcon3\\analysis\\disassembly\\{name}_disasm.txt"
            with open(txt_path, 'w') as f:
                f.write(readable)
            
            print(f"Saved readable disassembly to {txt_path}")
            print(f"  Instructions: {result['instruction_count']}")
            print(f"  Calls: {len(result['calls'])}")
            print(f"  Waypoint ops: {len(result['waypoint_operations'])}")
    
    # Save JSON
    json_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r55_mission_editor_disasm.json'
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\nSaved JSON data to {json_path}")
    print(f"Total functions analyzed: {len(all_results)}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
