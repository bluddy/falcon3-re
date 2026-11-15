"""
Disassemble all 67 functions found in expansion analysis.
Save complete disassembly for manual inspection.
"""
import idaapi
import idc
import json

def disasm_function_complete(addr, name):
    """Get complete disassembly of a function."""
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        return []
    
    lines = []
    lines.append(f"\n{'=' * 80}")
    lines.append(f"{name} @ 0x{addr:08X}")
    lines.append("=" * 80)
    
    ea = addr
    count = 0
    
    while ea < func_end and ea != idc.BADADDR and count < 2000:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"  0x{ea:08X}: {disasm}")
        ea = idc.next_head(ea)
        count += 1
    
    return lines

def main():
    idaapi.auto_wait()
    
    # Load the expansion results
    with open('expansion_analysis_results.json', 'r') as f:
        results = json.load(f)
    
    all_funcs = results['all_functions']
    
    print(f"Disassembling {len(all_funcs)} functions...")
    
    output = []
    output.append("COMPLETE DISASSEMBLY OF EXPANSION ANALYSIS FUNCTIONS")
    output.append("=" * 80)
    output.append(f"Total functions: {len(all_funcs)}")
    output.append("=" * 80)
    
    # Sort by depth, then by score
    funcs_sorted = sorted(
        [(addr, info) for addr, info in all_funcs.items()],
        key=lambda x: (x[1]['depth'], -x[1]['score'])
    )
    
    for addr_str, info in funcs_sorted:
        addr = int(addr_str, 16)
        name = info['name']
        
        print(f"Disassembling {name}...")
        
        disasm = disasm_function_complete(addr, name)
        output.extend(disasm)
    
    result_text = '\n'.join(output)
    
    # Write to file
    with open('all_expansion_disassembly.txt', 'w') as f:
        f.write(result_text)
    
    print(f"\nComplete disassembly saved to all_expansion_disassembly.txt")
    print(f"Total lines: {len(output)}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
