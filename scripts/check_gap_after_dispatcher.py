import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\gap_analysis.txt"

try:
    with open(output_path, 'w') as f:
        # Dispatcher function
        dispatcher_start = 0x3CE92
        dispatcher_end = 0x3CEDD
        next_func_start = 0x3CFAA
        
        f.write(f"=== Gap Analysis ===\n\n")
        f.write(f"Dispatcher: {dispatcher_start:#x} - {dispatcher_end:#x} ({dispatcher_end - dispatcher_start} bytes)\n")
        f.write(f"Next function: {next_func_start:#x}\n")
        f.write(f"Gap: {dispatcher_end:#x} - {next_func_start:#x} ({next_func_start - dispatcher_end} bytes)\n\n")
        
        # Check what's in the gap
        f.write(f"=== Analyzing gap {dispatcher_end:#x} to {next_func_start:#x} ===\n\n")
        
        ea = dispatcher_end
        while ea < next_func_start:
            flags = idc.get_full_flags(ea)
            is_code = idc.is_code(flags)
            is_data = idc.is_data(flags)
            is_unknown = idc.is_unknown(flags)
            
            # Check if it's part of a function
            func = idaapi.get_func(ea)
            
            disasm = idc.generate_disasm_line(ea, 0)
            
            status = []
            if is_code: status.append("CODE")
            if is_data: status.append("DATA")
            if is_unknown: status.append("UNKNOWN")
            if func: status.append(f"FUNC@{func.start_ea:#x}")
            
            f.write(f"{ea:#x}: {disasm:50s} [{', '.join(status)}]\n")
            
            ea = idc.next_head(ea)
            if ea == idc.BADADDR or ea >= next_func_start:
                break
        
        # List all functions in the range 0x3CE00 to 0x3D000
        f.write(f"\n=== All functions in range 0x3CE00 - 0x3D000 ===\n")
        for func_ea in idautils.Functions(0x3CE00, 0x3D000):
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
