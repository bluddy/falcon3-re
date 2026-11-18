import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\mirror_to_target.txt"

try:
    with open(output_path, 'w') as f:
        # Check registry address 0x3D1B6 and also 0x3D1C5
        addresses = [0x3D1B6, 0x3D1C5]
        
        for addr in addresses:
            f.write(f"\n{'='*60}\n")
            f.write(f"Checking address {addr:#x}\n")
            f.write(f"{'='*60}\n\n")
            
            func = idaapi.get_func(addr)
            if func:
                name = idc.get_func_name(addr)
                size = func.end_ea - func.start_ea
                
                f.write(f"Function: {name}\n")
                f.write(f"Range: {func.start_ea:#x} - {func.end_ea:#x}\n")
                f.write(f"Size: {size} bytes\n\n")
                
                # Count xrefs
                xrefs_to = list(idautils.XrefsTo(func.start_ea))
                f.write(f"Called by {len(xrefs_to)} locations\n\n")
                
                # Disassembly
                f.write("Disassembly:\n")
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
            else:
                f.write(f"No function at {addr:#x}\n")
        
        # List all functions in range 0x3D1B0 - 0x3D200
        f.write(f"\n\n{'='*60}\n")
        f.write(f"All functions in range 0x3D1B0 - 0x3D200\n")
        f.write(f"{'='*60}\n\n")
        for func_ea in idautils.Functions(0x3D1B0, 0x3D200):
            func = idaapi.get_func(func_ea)
            if func:
                size = func.end_ea - func.start_ea
                name = idc.get_func_name(func_ea)
                f.write(f"{func_ea:#x} - {func.end_ea:#x}: {name} ({size} bytes)\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
