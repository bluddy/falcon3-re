"""
Find functions that call picfont_idx_dat_loader and analyze what they do next.
"""
import idaapi
import idautils
import idc

def main():
    idaapi.auto_wait()
    
    target_addr = 0x1297F0  # picfont_idx_dat_loader
    target_name = idc.get_func_name(target_addr)
    
    print(f"=== Callers of {target_name} @ 0x{target_addr:X} ===\n")
    
    callers = []
    for xref in idautils.XrefsTo(target_addr, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:  # Call near/far
            caller_addr = xref.frm
            caller_func = idc.get_func_attr(caller_addr, idc.FUNCATTR_START)
            if caller_func != idc.BADADDR:
                caller_name = idc.get_func_name(caller_func)
                caller_size = idc.get_func_attr(caller_func, idc.FUNCATTR_END) - caller_func
                callers.append((caller_func, caller_name, caller_size, caller_addr))
    
    print(f"Found {len(callers)} caller(s):\n")
    
    for func_addr, func_name, func_size, call_addr in callers:
        print(f"Caller: {func_name} @ 0x{func_addr:X} ({func_size}B)")
        print(f"  Calls from: 0x{call_addr:X}")
        
        # Get next 10 instructions after the call
        print(f"  Instructions after the call:")
        ea = idc.next_head(call_addr)
        for i in range(10):
            if ea == idc.BADADDR:
                break
            disasm = idc.generate_disasm_line(ea, 0)
            print(f"    0x{ea:X}: {disasm}")
            ea = idc.next_head(ea)
        
        # Find functions called after picfont_idx_dat_loader
        print(f"  Functions called after:")
        ea = idc.next_head(call_addr)
        for i in range(50):  # Check next 50 instructions
            if ea == idc.BADADDR or ea >= idc.get_func_attr(func_addr, idc.FUNCATTR_END):
                break
            
            if idc.print_insn_mnem(ea) in ['call', 'lcall']:
                # Get call target
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type in [idc.fl_CN, idc.fl_CF]:
                        target = xref.to
                        target_name = idc.get_func_name(target)
                        if target_name:
                            print(f"    -> {target_name} @ 0x{target:X}")
            
            ea = idc.next_head(ea)
        
        print()
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
