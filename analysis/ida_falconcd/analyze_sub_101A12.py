import ida_auto
import ida_funcs
import ida_xref
import idc
import ida_bytes
import json

def analyze_sub_101A12():
    """Analyze Rank #9: sub_101A12 (104 callers, 1,719 bytes)"""
    
    addr = 0x101A12
    func = ida_funcs.get_func(addr)
    
    if not func:
        print(f"ERROR: No function at 0x{addr:X}")
        return
    
    print("=" * 80)
    print(f"ANALYZING: sub_101A12 (Rank #9, 104 callers, 1,719 bytes)")
    print("=" * 80)
    
    # Basic info
    print(f"\nAddress: 0x{addr:X}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    print(f"Current name: {idc.get_func_name(addr)}")
    
    # Count callers
    callers = []
    for xref in ida_xref.XrefsTo(addr, 0):
        if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
            callers.append(xref.frm)
    print(f"Callers: {len(set(callers))}")
    
    # Sample first 30 callers
    print(f"\nSample callers (first 30):")
    unique_callers = list(set(callers))[:30]
    for i, caller_addr in enumerate(unique_callers, 1):
        caller_func = ida_funcs.get_func(caller_addr)
        if caller_func:
            caller_name = idc.get_func_name(caller_func.start_ea)
            print(f"  {i}. {caller_name} (0x{caller_func.start_ea:X})")
        else:
            print(f"  {i}. 0x{caller_addr:X} (no function)")
    
    # Count callees
    callees = []
    for head in ida_funcs.FuncItems(addr):
        for xref in ida_xref.XrefsFrom(head, 0):
            if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
                callees.append(xref.to)
    
    unique_callees = list(set(callees))
    print(f"\nCallees: {len(unique_callees)} unique functions")
    
    # Sample all callees (should be manageable for 1.7KB function)
    print(f"\nAll callees:")
    for i, callee_addr in enumerate(unique_callees, 1):
        callee_name = idc.get_func_name(callee_addr)
        print(f"  {i}. {callee_name} (0x{callee_addr:X})")
    
    # Analyze string references
    strings = []
    for head in ida_funcs.FuncItems(addr):
        for xref in ida_xref.XrefsFrom(head, 0):
            if xref.type == ida_xref.fl_F:  # Data reference
                s = idc.get_strlit_contents(xref.to)
                if s:
                    strings.append(s.decode('ascii', errors='ignore'))
    
    if strings:
        print(f"\nString references: {len(strings)}")
        for i, s in enumerate(strings, 1):
            print(f"  {i}. \"{s[:80]}\"")
    else:
        print(f"\nString references: None")
    
    # Check for jump tables
    print(f"\nLooking for jump tables...")
    has_switch = False
    for head in ida_funcs.FuncItems(addr):
        if idc.get_switch_info(head):
            print(f"  Found switch at 0x{head:X}")
            has_switch = True
    if not has_switch:
        print(f"  No jump tables found")
    
    # Get first 100 instructions for pattern analysis
    print(f"\nFirst 100 instructions:")
    insn_count = 0
    ea = func.start_ea
    while ea < func.end_ea and insn_count < 100:
        disasm = idc.GetDisasm(ea)
        print(f"  0x{ea:X}: {disasm}")
        ea = idc.next_head(ea, func.end_ea)
        insn_count += 1
    
    # Analyze data references
    data_refs = []
    for head in ida_funcs.FuncItems(addr):
        for xref in ida_xref.XrefsFrom(head, 0):
            if xref.type == ida_xref.fl_F:  # Data reference
                data_refs.append(xref.to)
    
    unique_data_refs = list(set(data_refs))
    print(f"\nData references: {len(unique_data_refs)}")
    for i, data_addr in enumerate(unique_data_refs[:20], 1):
        seg_name = idc.get_segm_name(data_addr)
        print(f"  {i}. 0x{data_addr:X} ({seg_name})")
    
    # Save full analysis to JSON
    analysis = {
        'address': addr,
        'name': idc.get_func_name(addr),
        'size': func.end_ea - func.start_ea,
        'caller_count': len(set(callers)),
        'callee_count': len(unique_callees),
        'sample_callers': [
            {'addr': c, 'name': idc.get_func_name(ida_funcs.get_func(c).start_ea) if ida_funcs.get_func(c) else '?'}
            for c in unique_callers[:50]
        ],
        'all_callees': [
            {'addr': c, 'name': idc.get_func_name(c)}
            for c in unique_callees
        ],
        'strings': strings,
        'has_switch': has_switch,
        'data_refs': [{'addr': d, 'segment': idc.get_segm_name(d)} for d in unique_data_refs[:50]]
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\sub_101A12_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n? Full analysis written to: {output_file}")

if __name__ == "__main__":
    ida_auto.auto_wait()
    analyze_sub_101A12()
    idc.qexit(0)
