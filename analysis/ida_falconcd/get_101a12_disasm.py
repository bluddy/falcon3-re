"""
Extract complete disassembly and callees for function 0x101A12
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def main():
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    func_addr = 0x101A12
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: No function at {hex(func_addr)}")
        idc.qexit(1)
    
    func_name = idc.get_func_name(func_addr)
    
    # Extract callees
    callees = []
    callee_set = set()
    for ea in idautils.FuncItems(func.start_ea):
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call near/far
                target_name = idc.get_func_name(xref.to)
                if target_name and target_name not in callee_set:
                    callees.append({
                        'addr': hex(xref.to),
                        'name': target_name
                    })
                    callee_set.add(target_name)
    
    # Extract disassembly
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    # Prepare results
    result = {
        'name': func_name,
        'address': hex(func_addr),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'callee_count': len(callees),
        'callees': callees,
        'disasm_line_count': len(disasm_lines),
        'disasm': disasm_lines[:200]  # First 200 lines
    }
    
    # Save to JSON
    output_path = Path(__file__).parent / "func_101a12.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Function: {func_name}")
    print(f"Size: {result['size']} bytes")
    print(f"Callees: {len(callees)} distinct functions")
    print(f"Disassembly: {len(disasm_lines)} lines")
    print(f"Results saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
