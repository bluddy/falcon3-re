"""
Analyze mode_stream_select_step function in detail.

This is the F6 (ACM mode) handler - likely contains the radar mode switching logic.

Address: 0x39E62
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\mode_stream_select_analysis.json"
DISASM_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\mode_stream_select_disasm.txt"

def export_function_full(func_addr):
    """Export complete disassembly of a function."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    func_name = idc.get_func_name(func_addr)
    
    # Get all disassembly
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        offset = ea - func.start_ea
        disasm_lines.append(f"{ea:08X} +{offset:04X}: {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'name': func_name,
        'address': hex(func.start_ea),
        'size': func.end_ea - func.start_ea,
        'disassembly': disasm_lines
    }

def find_mode_comparisons(func_addr):
    """Find mode value comparisons in the function."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    comparisons = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == "cmp":
            # Get what's being compared
            op0 = idc.print_operand(ea, 0)
            op1 = idc.print_operand(ea, 1)
            
            # Check if comparing to a small constant (mode value)
            if idc.get_operand_type(ea, 1) == idc.o_imm:
                value = idc.get_operand_value(ea, 1)
                
                if value <= 10:  # Mode values typically 0-5
                    # Get context
                    context = []
                    ctx_ea = ea
                    for i in range(15):
                        if ctx_ea >= func.end_ea:
                            break
                        context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                        ctx_ea = idc.next_head(ctx_ea, func.end_ea)
                    
                    comparisons.append({
                        'address': hex(ea),
                        'offset': hex(ea - func.start_ea),
                        'operand0': op0,
                        'value': value,
                        'context': context
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return comparisons

def find_memory_writes(func_addr):
    """Find all memory writes in the function (mode state changes)."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    writes = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ["mov", "or", "and", "xor", "inc", "dec"]:
            op0_type = idc.get_operand_type(ea, 0)
            
            # Check if destination is memory
            if op0_type in [idc.o_mem, idc.o_displ]:
                op0_val = idc.get_operand_value(ea, 0)
                op0_name = idc.get_name(op0_val) if op0_val else None
                
                # Get source value if immediate
                src_value = None
                if idc.get_operand_type(ea, 1) == idc.o_imm:
                    src_value = idc.get_operand_value(ea, 1)
                
                writes.append({
                    'address': hex(ea),
                    'offset': hex(ea - func.start_ea),
                    'instruction': idc.GetDisasm(ea),
                    'operation': mnem,
                    'target': op0_name if op0_name else hex(op0_val),
                    'target_addr': hex(op0_val) if op0_val else None,
                    'value': src_value
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return writes

def find_function_calls(func_addr):
    """Find all function calls and what they're called with."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    calls = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ["call", "callf"]:
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            
            # Get previous few instructions (parameters)
            params = []
            param_ea = ea
            for i in range(5):
                param_ea = idc.prev_head(param_ea, func.start_ea)
                if param_ea == idc.BADADDR:
                    break
                param_insn = idc.GetDisasm(param_ea)
                params.insert(0, f"{param_ea:08X}: {param_insn}")
            
            calls.append({
                'address': hex(ea),
                'offset': hex(ea - func.start_ea),
                'instruction': idc.GetDisasm(ea),
                'target': target_name if target_name else hex(target),
                'parameters': params
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return calls

def find_string_references(func_addr):
    """Find string references in the function."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    strings = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        # Look for references to string data
        for xref in idautils.XrefsFrom(ea, 0):
            if idc.is_strlit(idc.get_full_flags(xref.to)):
                str_val = idc.get_strlit_contents(xref.to)
                if str_val:
                    strings.append({
                        'address': hex(ea),
                        'offset': hex(ea - func.start_ea),
                        'string': str_val.decode('ascii', errors='ignore')[:60],
                        'string_addr': hex(xref.to)
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return strings

def analyze_control_flow(func_addr):
    """Analyze control flow - branches and jumps."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    branches = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # Check for conditional jumps
        if mnem in ["je", "jz", "jne", "jnz", "ja", "jb", "jg", "jl", "jge", "jle", "jbe", "jae"]:
            target = idc.get_operand_value(ea, 0)
            
            branches.append({
                'address': hex(ea),
                'offset': hex(ea - func.start_ea),
                'instruction': idc.GetDisasm(ea),
                'type': mnem,
                'target': hex(target),
                'target_offset': hex(target - func.start_ea) if target >= func.start_ea and target < func.end_ea else "external"
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return branches

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        func_addr = 0x39E62  # mode_stream_select_step
        
        print("[1] Exporting full disassembly...")
        full_disasm = export_function_full(func_addr)
        if not full_disasm:
            print("ERROR: Function not found")
            idc.qexit(1)
            return
        
        print(f"Function: {full_disasm['name']}")
        print(f"Size: {full_disasm['size']} bytes")
        print(f"Lines: {len(full_disasm['disassembly'])}")
        
        # Save full disassembly to text file
        with open(DISASM_FILE, 'w') as f:
            f.write(f"; {full_disasm['name']}\n")
            f.write(f"; Address: {full_disasm['address']}\n")
            f.write(f"; Size: {full_disasm['size']} bytes\n")
            f.write("\n")
            for line in full_disasm['disassembly']:
                f.write(line + "\n")
        
        print(f"Disassembly saved to {DISASM_FILE}")
        
        print("\n[2] Finding mode comparisons...")
        comparisons = find_mode_comparisons(func_addr)
        print(f"Found {len(comparisons)} mode comparisons")
        for cmp in comparisons[:5]:
            print(f"  @ {cmp['offset']}: cmp {cmp['operand0']}, {cmp['value']}")
        
        print("\n[3] Finding memory writes (mode state changes)...")
        writes = find_memory_writes(func_addr)
        print(f"Found {len(writes)} memory writes")
        
        # Group by target
        by_target = {}
        for w in writes:
            target = w['target']
            if target not in by_target:
                by_target[target] = []
            by_target[target].append(w)
        
        print(f"Writing to {len(by_target)} unique variables:")
        for target, ops in sorted(by_target.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"  {target}: {len(ops)} writes")
        
        print("\n[4] Finding function calls...")
        calls = find_function_calls(func_addr)
        print(f"Found {len(calls)} function calls")
        
        # Count unique functions
        unique_funcs = set(c['target'] for c in calls)
        print(f"Calling {len(unique_funcs)} unique functions")
        for func in list(unique_funcs)[:10]:
            print(f"  {func}")
        
        print("\n[5] Finding string references...")
        strings = find_string_references(func_addr)
        print(f"Found {len(strings)} string references")
        for s in strings[:5]:
            print(f"  '{s['string']}'")
        
        print("\n[6] Analyzing control flow...")
        branches = analyze_control_flow(func_addr)
        print(f"Found {len(branches)} conditional branches")
        
        # Create result
        result = {
            'function': full_disasm['name'],
            'address': full_disasm['address'],
            'size': full_disasm['size'],
            'mode_comparisons': comparisons,
            'memory_writes': writes,
            'memory_writes_by_target': {k: len(v) for k, v in by_target.items()},
            'function_calls': calls,
            'string_references': strings,
            'control_flow_branches': branches,
            'summary': {
                'comparisons': len(comparisons),
                'writes': len(writes),
                'unique_targets': len(by_target),
                'calls': len(calls),
                'unique_functions': len(unique_funcs),
                'strings': len(strings),
                'branches': len(branches)
            }
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[7] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
