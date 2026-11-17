"""
Find all cross-references to radar mode variables.
Simple, focused script following IDA_AUTOMATION_GUIDE.md pattern.
"""

import idc
import idaapi
import idautils
import json

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Variables to investigate
    variables = {
        'byte_595B2': 0x595B2,  # Primary mode state
        'byte_59573': 0x59573,  # Radar type selector
        'word_5959B': 0x5959B   # Target index
    }
    
    results = {}
    
    for var_name, var_addr in variables.items():
        print(f"\nAnalyzing {var_name} at 0x{var_addr:X}...")
        
        xrefs = []
        for xref_ea in idautils.DataRefsTo(var_addr):
            func_ea = idc.get_func_attr(xref_ea, idc.FUNCATTR_START)
            func_name = idc.get_func_name(func_ea) if func_ea != idc.BADADDR else "unknown"
            
            disasm = idc.generate_disasm_line(xref_ea, 0)
            mnem = idc.print_insn_mnem(xref_ea)
            
            xrefs.append({
                'addr': hex(xref_ea),
                'func': func_name,
                'func_addr': hex(func_ea) if func_ea != idc.BADADDR else None,
                'mnem': mnem,
                'disasm': disasm
            })
        
        results[var_name] = {
            'addr': hex(var_addr),
            'xref_count': len(xrefs),
            'xrefs': xrefs
        }
        
        print(f"  Found {len(xrefs)} cross-references")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\mode_vars_xrefs.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
