"""
Extract disassembly and callee list for function 0x101A12
"""
import idaapi
import idc
import idautils

def main():
    addr = 0x101A12
    func_name = idc.get_func_name(addr)
    func = idaapi.get_func(addr)
    
    if not func:
        print(f"ERROR: No function at 0x{addr:06X}")
        return 1
    
    print(f"Function: {func_name} at 0x{addr:06X}")
    print(f"Size: {func.size()} bytes")
    print(f"Start: 0x{func.start_ea:06X}, End: 0x{func.end_ea:06X}")
    print("=" * 70)
    
    # Extract callees
    callees = set()
    for ea in idautils.FuncItems(func.start_ea):
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call near/far
                target_name = idc.get_func_name(xref.to)
                if target_name:
                    callees.add((xref.to, target_name))
    
    print(f"\nCallees: {len(callees)} distinct functions")
    print("-" * 70)
    for addr_callee, name_callee in sorted(callees):
        print(f"  0x{addr_callee:06X}: {name_callee}")
    
    # Extract first 100 lines of disassembly
    print("\n" + "=" * 70)
    print("Disassembly (first 100 lines):")
    print("=" * 70)
    
    line_count = 0
    ea = func.start_ea
    while ea < func.end_ea and line_count < 100:
        disasm = idc.generate_disasm_line(ea, 0)
        if disasm:
            print(f"  {ea:06X}  {disasm}")
            line_count += 1
        ea = idc.next_head(ea)
    
    if ea < func.end_ea:
        print(f"\n... truncated at {line_count} lines ...")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
