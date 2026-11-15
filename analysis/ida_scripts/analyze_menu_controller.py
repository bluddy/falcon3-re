"""
Analyze the monolithic menu controller (sub_683C5, 4169 bytes) to find:
1. All entry points (labels/xrefs within the function)
2. All unique callees from this massive function
3. Which callees are undocumented

Run in IDA: File > Script file > analyze_menu_controller.py
"""

import idaapi
import idc
import idautils
import json

def is_documented(func_ea):
    """Check if a function has a non-default name."""
    name = idc.get_func_name(func_ea)
    if not name:
        return False
    if name.startswith('sub_') or name.startswith('nullsub_'):
        return False
    return True

def get_all_labels_in_function(func_ea):
    """Get all labels (entry points) within a function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    labels = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        # Check if this address has xrefs (is a target)
        xrefs = list(idautils.XrefsTo(head, 0))
        if xrefs and head != func.start_ea:
            name = idc.get_name(head)
            if not name:
                name = f"loc_{head:X}"
            labels.append({
                'address': f'0x{head:x}',
                'name': name,
                'xref_count': len(xrefs),
                'xrefs_from': [f'0x{xref.frm:x}' for xref in xrefs[:5]]  # First 5
            })
    
    return labels

def get_all_callees(func_ea):
    """Get all functions called by this function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return set()
    
    callees = set()
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Near/Far call
                target_func = idaapi.get_func(xref.to)
                if target_func:
                    callees.add(target_func.start_ea)
    
    return callees

def count_comparisons(func_ea):
    """Count comparison instructions in function."""
    count = 0
    func = idaapi.get_func(func_ea)
    if not func:
        return 0
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head).lower()
        if mnem in ['cmp', 'test', 'jz', 'jnz', 'je', 'jne', 'jg', 'jl', 
                    'jge', 'jle', 'ja', 'jb', 'jae', 'jbe', 'js', 'jns']:
            count += 1
    
    return count

def count_callers(func_ea):
    """Count how many functions call this one."""
    callers = set()
    for xref in idautils.XrefsTo(func_ea, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.add(caller_func.start_ea)
    return len(callers)

def analyze_menu_controller():
    """Analyze the monolithic menu controller (sub_683C5)."""
    
    controller_ea = 0x683C5
    
    print("="*70)
    print("Analyzing Menu Controller: sub_683C5")
    print("="*70)
    
    func = idaapi.get_func(controller_ea)
    if not func:
        print(f"ERROR: No function at 0x{controller_ea:x}")
        return
    
    size = func.end_ea - func.start_ea
    print(f"\nFunction: {idc.get_func_name(controller_ea)}")
    print(f"Address:  0x{controller_ea:x}")
    print(f"Size:     {size} bytes")
    
    # Find all entry points (labels with xrefs)
    print(f"\n{'='*70}")
    print("ENTRY POINTS (labels within function with external xrefs):")
    print(f"{'='*70}")
    
    labels = get_all_labels_in_function(controller_ea)
    print(f"Found {len(labels)} internal entry points:\n")
    
    for label in labels[:20]:  # Show first 20
        print(f"  {label['address']:10s} {label['name']:40s} ({label['xref_count']:2d} xrefs)")
    
    if len(labels) > 20:
        print(f"  ... and {len(labels) - 20} more")
    
    # Find all callees
    print(f"\n{'='*70}")
    print("CALLEES (functions called by controller):")
    print(f"{'='*70}")
    
    callees = get_all_callees(controller_ea)
    print(f"Total unique callees: {len(callees)}\n")
    
    # Analyze callees
    callee_info = []
    for ea in callees:
        name = idc.get_func_name(ea)
        if not name:
            continue
        
        callee_func = idaapi.get_func(ea)
        if not callee_func:
            continue
        
        size = callee_func.end_ea - callee_func.start_ea
        comps = count_comparisons(ea)
        callers = count_callers(ea)
        documented = is_documented(ea)
        
        callee_info.append({
            'address': f'0x{ea:x}',
            'name': name,
            'size': size,
            'comparisons': comps,
            'callers': callers,
            'documented': documented
        })
    
    # Sort by documented status (undocumented first), then by callers
    callee_info.sort(key=lambda x: (x['documented'], -x['callers'], -x['size']))
    
    # Separate documented and undocumented
    undoc = [c for c in callee_info if not c['documented']]
    doc = [c for c in callee_info if c['documented']]
    
    print(f"Documented callees:   {len(doc)}")
    print(f"Undocumented callees: {len(undoc)}")
    
    print(f"\n{'='*70}")
    print("TOP 30 UNDOCUMENTED CALLEES (by caller count):")
    print(f"{'='*70}\n")
    
    for c in undoc[:30]:
        doc_status = "DOC" if c['documented'] else "UNDOC"
        print(f"  {c['address']:10s} {c['name']:30s} {c['size']:4d}B  "
              f"{c['comparisons']:3d} cmps  {c['callers']:3d} callers  [{doc_status}]")
    
    # Save results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\menu_controller_analysis.json'
    result = {
        'controller': {
            'address': f'0x{controller_ea:x}',
            'name': idc.get_func_name(controller_ea),
            'size': size
        },
        'entry_points': labels,
        'total_callees': len(callees),
        'documented_callees': len(doc),
        'undocumented_callees': len(undoc),
        'callees': callee_info
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Analysis saved to: {output_file}")
    print(f"{'='*70}")

if __name__ == '__main__':
    idaapi.auto_wait()
    analyze_menu_controller()
