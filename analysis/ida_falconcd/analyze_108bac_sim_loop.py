import idaapi
import idautils
import idc
import ida_funcs
import ida_xref
import ida_bytes
import json

def analyze_sim_loop():
    """Deep analysis of the R15 simulation loop"""
    
    func_ea = 0x108BAC
    func = ida_funcs.get_func(func_ea)
    
    result = {
        'function': {
            'address': hex(func_ea),
            'name': idc.get_func_name(func_ea),
            'size': func.end_ea - func.start_ea
        },
        'flag_check': {},
        'path_a': {'start': None, 'calls': []},
        'path_b': {'start': None, 'calls': []},
        'data_structures': {},
        'globals_accessed': []
    }
    
    # Analyze the flag check at entry
    result['flag_check'] = {
        'address': '0x108BAC',
        'flag': 'cs:byte_107762',
        'flag_address': '0x107762',
        'branch_if_zero': '0x108BB7',
        'branch_if_nonzero': '0x108CDF'
    }
    
    # Analyze Path A (flag == 0)
    result['path_a']['start'] = '0x108BB7'
    path_a_calls = []
    
    # Manually trace Path A calls
    for ea in range(0x108BB7, 0x108CDF):
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target) or idc.get_name(target) or hex(target)
            
            # Get any comment
            comment = idc.get_cmt(ea, 0) or ""
            
            path_a_calls.append({
                'address': hex(ea),
                'target': hex(target),
                'name': target_name,
                'comment': comment
            })
    
    result['path_a']['calls'] = path_a_calls
    result['path_a']['call_count'] = len(path_a_calls)
    
    # Analyze Path B (flag != 0)
    result['path_b']['start'] = '0x108CDF'
    path_b_calls = []
    
    for ea in range(0x108CDF, 0x108E79):
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target) or idc.get_name(target) or hex(target)
            
            comment = idc.get_cmt(ea, 0) or ""
            
            path_b_calls.append({
                'address': hex(ea),
                'target': hex(target),
                'name': target_name,
                'comment': comment
            })
    
    result['path_b']['calls'] = path_b_calls
    result['path_b']['call_count'] = len(path_b_calls)
    
    # Compare paths
    path_a_names = [c['name'] for c in path_a_calls]
    path_b_names = [c['name'] for c in path_b_calls]
    
    result['path_comparison'] = {
        'identical_sequence': path_a_names == path_b_names,
        'path_a_unique': [n for n in path_a_names if n not in path_b_names],
        'path_b_unique': [n for n in path_b_names if n not in path_a_names],
        'common': [n for n in path_a_names if n in path_b_names]
    }
    
    # Analyze data structure offsets used
    offsets_used = set()
    for ea in idautils.Heads(func.start_ea, func.end_ea):
        # Look for operations with immediate offsets
        if idc.print_insn_mnem(ea) in ['mov', 'lea']:
            op_str = idc.print_operand(ea, 1)
            # Extract hex offsets like 0x2E, 0x3A, etc.
            if 'h' in op_str or 'Ah' in op_str or 'Eh' in op_str:
                offsets_used.add(op_str)
    
    result['data_structures'] = {
        'offsets_referenced': sorted(list(offsets_used)),
        'offset_0x2E': 'Source buffer (18 bytes copied to 0x40)',
        'offset_0x3A': 'Entity/flight record pointer',
        'offset_0x40': 'Destination buffer',
        'offset_0x22': 'Entity state buffer'
    }
    
    # Find all globals accessed
    for ea in idautils.Heads(func.start_ea, func.end_ea):
        for i in range(2):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_mem:  # Memory reference
                mem_addr = idc.get_operand_value(ea, i)
                mem_name = idc.get_name(mem_addr) or hex(mem_addr)
                if mem_name not in [c['name'] for c in result['globals_accessed']]:
                    result['globals_accessed'].append({
                        'address': hex(mem_addr),
                        'name': mem_name,
                        'first_access': hex(ea)
                    })
    
    # Analyze key subsystems called
    subsystems = {
        'terrain': [],
        'viewport': [],
        'ai': [],
        'entities': [],
        'hud': [],
        'physics': [],
        'timing': [],
        'tasks': [],
        'memory': []
    }
    
    all_calls = path_a_calls + path_b_calls
    for call in all_calls:
        name_lower = call['name'].lower()
        if 'terrain' in name_lower or 'height' in name_lower:
            subsystems['terrain'].append(call)
        elif 'view' in name_lower or 'project' in name_lower:
            subsystems['viewport'].append(call)
        elif 'ai' in name_lower or 'context' in name_lower:
            subsystems['ai'].append(call)
        elif 'entity' in name_lower or 'farobj' in name_lower:
            subsystems['entities'].append(call)
        elif 'hud' in name_lower or 'r32' in name_lower:
            subsystems['hud'].append(call)
        elif 'pos' in name_lower or 'clamp' in name_lower or 'wrap' in name_lower:
            subsystems['physics'].append(call)
        elif 'tick' in name_lower or 'timer' in name_lower or 'rate' in name_lower:
            subsystems['timing'].append(call)
        elif 'task' in name_lower or 'pending' in name_lower:
            subsystems['tasks'].append(call)
        elif 'ems' in name_lower or 'memory' in name_lower:
            subsystems['memory'].append(call)
    
    result['subsystems'] = {k: len(v) for k, v in subsystems.items() if v}
    result['subsystem_details'] = subsystems
    
    return result

# Run analysis
result = analyze_sim_loop()

# Save to JSON
output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\sim_loop_108bac_analysis.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print("=== R15 SIMULATION LOOP ANALYSIS ===")
print(f"Function: {result['function']['name']} at {result['function']['address']}")
print(f"Size: {result['function']['size']} bytes")
print(f"\nFlag Check: {result['flag_check']['flag']} at {result['flag_check']['flag_address']}")
print(f"  if 0 → Path A at {result['flag_check']['branch_if_zero']}")
print(f"  if !0 → Path B at {result['flag_check']['branch_if_nonzero']}")
print(f"\nPath A: {result['path_a']['call_count']} function calls")
print(f"Path B: {result['path_b']['call_count']} function calls")
print(f"Paths identical: {result['path_comparison']['identical_sequence']}")

print(f"\n=== SUBSYSTEMS CALLED ===")
for subsys, count in result['subsystems'].items():
    print(f"  {subsys}: {count} calls")

print(f"\n=== KEY GLOBALS ===")
for g in result['globals_accessed'][:10]:
    print(f"  {g['name']} ({g['address']}) first at {g['first_access']}")

print(f"\nFull analysis saved to: {output_file}")

idc.qexit(0)
