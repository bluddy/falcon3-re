import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\dispatcher_disasm.txt"

try:
    with open(output_path, 'w') as f:
        # ai_entity_behavior_dispatcher at 0x3CE92
        addr = 0x3CE92
        func = idaapi.get_func(addr)
        
        if not func:
            f.write(f"ERROR: No function at {addr:#x}\n")
        else:
            name = idc.get_func_name(addr)
            size = func.end_ea - func.start_ea
            
            f.write(f"=== {name} ===\n")
            f.write(f"Address: {func.start_ea:#x} - {func.end_ea:#x}\n")
            f.write(f"Size: {size} bytes\n\n")
            
            # Export all instructions
            ea = func.start_ea
            while ea < func.end_ea:
                disasm = idc.generate_disasm_line(ea, 0)
                comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
                
                if comment:
                    f.write(f"{ea:#x}: {disasm:50s} ; {comment}\n")
                else:
                    f.write(f"{ea:#x}: {disasm}\n")
                
                ea = idc.next_head(ea)
                if ea == idc.BADADDR:
                    break
            
            # Also export the two mystery functions
            f.write(f"\n\n=== sub_3CEDD (23 bytes) ===\n")
            f.write(f"Address: 0x3CEDD - 0x3CEF4\n\n")
            ea = 0x3CEDD
            while ea < 0x3CEF4:
                disasm = idc.generate_disasm_line(ea, 0)
                comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
                if comment:
                    f.write(f"{ea:#x}: {disasm:50s} ; {comment}\n")
                else:
                    f.write(f"{ea:#x}: {disasm}\n")
                ea = idc.next_head(ea)
                if ea == idc.BADADDR:
                    break
            
            f.write(f"\n\n=== undoc_3CEF4 (169 bytes) ===\n")
            f.write(f"Address: 0x3CEF4 - 0x3CF9D\n\n")
            ea = 0x3CEF4
            while ea < 0x3CF9D:
                disasm = idc.generate_disasm_line(ea, 0)
                comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
                if comment:
                    f.write(f"{ea:#x}: {disasm:50s} ; {comment}\n")
                else:
                    f.write(f"{ea:#x}: {disasm}\n")
                ea = idc.next_head(ea)
                if ea == idc.BADADDR:
                    break
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
