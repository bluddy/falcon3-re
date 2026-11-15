import idaapi
import idautils
import idc
import json

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Analyzing remaining 3 Path B functions in detail...")

# The 3 remaining functions
functions = [
    (0x1FF5D, "quat_orient_flags_911"),
    (0x21240, "vec_delta_scaled_stosw"),
    (0x20BCE, "farptr_off1f710_scaled_set"),
]

for addr, expected_name in functions:
    print(f"\n{'='*60}")
    print(f"[*] Analyzing {expected_name} @ 0x{addr:X}")
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"  [!] No function found")
        continue
    
    current_name = idc.get_func_name(addr)
    print(f"  Current name: {current_name}")
    print(f"  Size: {func.end_ea - func.start_ea} bytes")
    
    # Get all xrefs TO this function (callers)
    callers = []
    for xref in idautils.XrefsTo(addr):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            caller_addr = xref.frm
            callers.append((caller_addr, caller_name))
    
    print(f"  Callers: {len(callers)}")
    if callers:
        for caller_addr, caller_name in callers[:5]:
            print(f"    - 0x{caller_addr:X}: {caller_name}")
    
    # Check for data references
    print(f"\n  Data references:")
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.DataRefsFrom(head):
            name = idc.get_name(xref)
            if name:
                print(f"    - 0x{xref:X}: {name}")
    
    # Look for string references
    print(f"\n  String references:")
    for head in idautils.Heads(func.start_ea, func.end_ea):
        insn = idc.generate_disasm_line(head, 0)
        if 'offset' in insn or 'asc_' in insn or 'byte_' in insn:
            print(f"    - {insn}")
    
    # Check what it calls
    print(f"\n  Callees:")
    callees_found = False
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.CodeRefsFrom(head, 0):
            if xref != head + idc.get_item_size(head):  # Not fall-through
                callee_name = idc.get_func_name(xref)
                if callee_name and callee_name != current_name:
                    print(f"    - 0x{xref:X}: {callee_name}")
                    callees_found = True
    
    if not callees_found:
        print(f"    No callees (leaf function)")
    
    # Extract first 30 instructions for analysis
    print(f"\n  First 30 instructions:")
    count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            disasm = idc.generate_disasm_line(head, 0)
            print(f"    {count:2}. 0x{head:X}: {disasm}")
            count += 1
            if count >= 30:
                break

print("\n[+] Analysis complete!")

# Don't exit - keep IDA open for manual inspection
print("\n[*] IDA remains open for manual inspection")
