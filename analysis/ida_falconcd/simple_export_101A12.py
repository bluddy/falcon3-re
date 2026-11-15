import ida_auto
import ida_funcs
import ida_xref
import idc
import sys

ida_auto.auto_wait()

addr = 0x101A12
func = ida_funcs.get_func(addr)

output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\func_101A12_export.txt"

with open(output_file, 'w') as f:
    if not func:
        f.write(f"ERROR: No function at 0x{addr:X}\n")
        print(f"ERROR: No function at 0x{addr:X}", file=sys.stderr)
        idc.qexit(1)
    
    f.write(f"=== FUNCTION 0x{addr:X} ===\n")
    f.write(f"Name: {idc.get_func_name(addr)}\n")
    f.write(f"Start: 0x{func.start_ea:X}\n")
    f.write(f"End: 0x{func.end_ea:X}\n")
    f.write(f"Size: {func.end_ea - func.start_ea} bytes\n\n")
    
    # Callers
    callers = []
    for xref in ida_xref.XrefsTo(addr, 0):
        if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
            callers.append(xref.frm)
    
    f.write(f"=== CALLERS ({len(set(callers))} unique) ===\n")
    for caller_addr in list(set(callers))[:50]:
        caller_func = ida_funcs.get_func(caller_addr)
        if caller_func:
            caller_name = idc.get_func_name(caller_func.start_ea)
            f.write(f"0x{caller_func.start_ea:X}: {caller_name}\n")
    
    # Callees
    callees = []
    for head in ida_funcs.FuncItems(addr):
        for xref in ida_xref.XrefsFrom(head, 0):
            if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
                callees.append(xref.to)
    
    unique_callees = list(set(callees))
    f.write(f"\n=== CALLEES ({len(unique_callees)} unique) ===\n")
    for callee_addr in unique_callees:
        callee_name = idc.get_func_name(callee_addr)
        f.write(f"0x{callee_addr:X}: {callee_name}\n")
    
    # Disassembly
    f.write(f"\n=== DISASSEMBLY ===\n")
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        f.write(f"0x{ea:X}: {disasm}\n")
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"SUCCESS: Exported to {output_file}")

idc.qexit(0)
