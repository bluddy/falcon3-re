"""
Extract squadron_mission_file_loader function with detailed analysis
to find MissionSlot field assignments
"""

import idaapi
import idc
import idautils
import json

def analyze_mission_slot_loader():
    """Analyze the squadron_mission_file_loader function to find MissionSlot field assignments"""
    
    func_addr = 0x17B437  # squadron_mission_file_loader
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: Function not found at 0x{func_addr:X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    print(f"Analyzing {func_name} at 0x{func_addr:X}")
    
    result = {
        'address': func_addr,
        'name': func_name,
        'start': func.start_ea,
        'end': func.end_ea,
        'size': func.end_ea - func.start_ea,
        'mission_slot_operations': [],
        'file_operations': [],
        'memory_writes': [],
        'calls': [],
        'data_refs': []
    }
    
    # Track mission slot array pointer (dword_79D3E)
    mission_slot_ptr = 0x79D3E
    
    # Scan all instructions
    ea = func.start_ea
    instr_count = 0
    
    while ea < func.end_ea:
        instr_count += 1
        mnem = idc.print_insn_mnem(ea)
        op0 = idc.print_operand(ea, 0)
        op1 = idc.print_operand(ea, 1)
        disasm = idc.GetDisasm(ea)
        
        # Look for references to mission slot pointer
        if 'dword_79D3E' in disasm or '79D3E' in disasm:
            result['mission_slot_operations'].append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'mnem': mnem,
                'op0': op0,
                'op1': op1,
                'disasm': disasm
            })
        
        # Look for memory writes with [bx+offset] patterns (field assignments)
        if mnem in ['mov', 'lea'] and '[' in op0:
            # Extract offset if present
            if '+' in op0:
                result['memory_writes'].append({
                    'addr': ea,
                    'offset': ea - func.start_ea,
                    'mnem': mnem,
                    'dest': op0,
                    'src': op1,
                    'disasm': disasm
                })
        
        # Look for DOS INT 21h file operations
        if mnem == 'int' and '21h' in op0:
            # Get AH register value from preceding instructions
            result['file_operations'].append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'disasm': disasm
            })
        
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
        
        # Track data references
        for i in range(2):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_mem:  # Memory reference
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
        
        ea = idc.next_head(ea, func.end_ea)
    
    result['instruction_count'] = instr_count
    
    print(f"Found {len(result['mission_slot_operations'])} mission slot operations")
    print(f"Found {len(result['memory_writes'])} memory writes")
    print(f"Found {len(result['file_operations'])} file operations")
    print(f"Found {len(result['calls'])} calls")
    print(f"Found {len(result['data_refs'])} data refs")
    
    return result

def main():
    print("Starting mission slot loader analysis...")
    
    # Wait for IDA auto-analysis
    idaapi.auto_wait()
    
    result = analyze_mission_slot_loader()
    
    if result:
        output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\mission_slot_loader_analysis.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults written to {output_path}")
        print(f"Total instructions: {result['instruction_count']}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
