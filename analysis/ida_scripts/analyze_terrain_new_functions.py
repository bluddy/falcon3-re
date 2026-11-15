"""
Analyze the 6 new terrain-related functions in detail.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

# The 6 new functions found
TARGETS = [
    0x04F964,  # 207B, 1 caller
    0x04FDB3,  # 79B, 1 caller
    0x04FB1C,  # 23B, 2 callers
    0x04FD82,  # 11B, 1 caller
    0x02BEA1,  # 8B, 2 callers
    0x028CA1,  # 3B, 3 callers
]

def get_callers(func_addr):
    """Get list of callers."""
    callers = []
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_addr = caller_func.start_ea
                caller_name = idc.get_func_name(caller_addr)
                callers.append({
                    'address': caller_addr,
                    'name': caller_name,
                    'call_site': xref.frm
                })
    return callers

def get_callees(func_addr):
    """Get list of functions this one calls."""
    callees = []
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target = xref.to
                target_func = idaapi.get_func(target)
                if target_func:
                    callee_addr = target_func.start_ea
                    callee_name = idc.get_func_name(callee_addr)
                    if {'address': callee_addr, 'name': callee_name} not in callees:
                        callees.append({
                            'address': callee_addr,
                            'name': callee_name
                        })
    return callees

def get_disassembly(func_addr, max_lines=50):
    """Get disassembly listing."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    lines = []
    count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if count >= max_lines:
            lines.append(f"... ({func.end_ea - head} bytes remaining)")
            break
        
        disasm = idc.GetDisasm(head)
        lines.append(f"{head:#08x}  {disasm}")
        count += 1
    
    return lines

def analyze_data_references(func_addr):
    """Analyze data references."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    refs = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_dR, idaapi.fl_dW]:  # Data read/write
                target = xref.to
                name = idc.get_name(target)
                if name:
                    refs.append({
                        'address': target,
                        'name': name,
                        'type': 'read' if xref.type == idaapi.fl_dR else 'write'
                    })
    return refs

def main():
    print("="*80)
    print("ANALYZING 6 NEW TERRAIN-RELATED FUNCTIONS")
    print("="*80)
    
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    analysis = []
    
    for addr in TARGETS:
        print(f"\n{'='*80}")
        print(f"FUNCTION @ {addr:#08x}")
        print("="*80)
        
        func = idaapi.get_func(addr)
        if not func:
            print("ERROR: Not a function!")
            continue
        
        name = idc.get_func_name(addr)
        size = func.end_ea - func.start_ea
        
        print(f"Name: {name}")
        print(f"Size: {size}B")
        
        # Callers
        callers = get_callers(addr)
        print(f"\nCallers ({len(callers)}):")
        for c in callers:
            print(f"  {c['address']:#08x}: {c['name']}")
        
        # Callees
        callees = get_callees(addr)
        print(f"\nCallees ({len(callees)}):")
        for c in callees:
            print(f"  {c['address']:#08x}: {c['name']}")
        
        # Data references
        data_refs = analyze_data_references(addr)
        if data_refs:
            print(f"\nData References ({len(data_refs)}):")
            for ref in data_refs[:10]:  # First 10
                print(f"  {ref['address']:#08x}: {ref['name']} ({ref['type']})")
        
        # Disassembly
        disasm = get_disassembly(addr, max_lines=30)
        print(f"\nDisassembly (first 30 lines):")
        for line in disasm:
            print(f"  {line}")
        
        # Store analysis
        analysis.append({
            'address': addr,
            'name': name,
            'size': size,
            'callers': callers,
            'callees': callees,
            'data_refs': data_refs,
            'disasm': disasm
        })
    
    # Save detailed analysis
    output_path = Path(__file__).parent.parent / "terrain_new_functions_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Detailed analysis saved to: {output_path}")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
