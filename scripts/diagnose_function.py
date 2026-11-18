import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\function_diagnostic.txt"

try:
    with open(output_path, 'w') as f:
        addr = 0x3CE92
        
        f.write(f"=== Diagnostic for address 0x{addr:X} ===\n\n")
        
        # Check if it's code
        flags = idc.get_full_flags(addr)
        f.write(f"Address flags: {flags:#x}\n")
        f.write(f"Is code: {idc.is_code(flags)}\n")
        f.write(f"Is data: {idc.is_data(flags)}\n")
        f.write(f"Is unknown: {idc.is_unknown(flags)}\n\n")
        
        # Try to get function
        func = idaapi.get_func(addr)
        if func:
            f.write(f"Function found!\n")
            f.write(f"  Start: {func.start_ea:#x}\n")
            f.write(f"  End: {func.end_ea:#x}\n")
            f.write(f"  Size: {func.end_ea - func.start_ea} bytes\n")
            
            # Get function name
            name = idc.get_func_name(addr)
            f.write(f"  Name: {name}\n\n")
        else:
            f.write(f"No function at address {addr:#x}\n")
            f.write(f"Trying to find nearest function...\n")
            
            # Find previous function
            prev_func = idaapi.get_prev_func(addr)
            if prev_func:
                f.write(f"  Previous function: {prev_func.start_ea:#x} - {prev_func.end_ea:#x}\n")
            
            # Find next function
            next_func = idaapi.get_next_func(addr)
            if next_func:
                f.write(f"  Next function: {next_func.start_ea:#x} - {next_func.end_ea:#x}\n\n")
        
        # Show first few instructions regardless
        f.write(f"First 10 instructions at {addr:#x}:\n")
        ea = addr
        for i in range(10):
            disasm = idc.generate_disasm_line(ea, 0)
            f.write(f"  {ea:#x}: {disasm}\n")
            ea = idc.next_head(ea)
            if ea == idc.BADADDR:
                break
        
        # Search for function by name pattern
        f.write(f"\n=== Searching for 'dispatcher' functions ===\n")
        for func_ea in idautils.Functions():
            func_name = idc.get_func_name(func_ea)
            if func_name and 'dispatch' in func_name.lower():
                func_obj = idaapi.get_func(func_ea)
                size = func_obj.end_ea - func_obj.start_ea if func_obj else 0
                f.write(f"  {func_ea:#x}: {func_name} ({size} bytes)\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
