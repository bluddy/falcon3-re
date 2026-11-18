"""
Analyze the mode dispatch table and find RFM-related functions
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\mode_dispatch_table_analysis.txt"

with open(output_file, 'w') as f:
    f.write("=== Mode Dispatch Table Analysis ===\n\n")
    
    # The dispatch uses ds:40Ah as index
    # Jump table is at [bx+392h]
    # We need to find what segment ds is
    
    # In mode_state_dispatch, we can see it accesses ds:23Bh and ds:40Ah
    # This suggests ds is a data segment
    
    # Let's examine the jump table
    # First, find where 0x392 points to in the data segment
    
    f.write("Looking for jump table...\n")
    f.write("The dispatch uses: jmp word ptr [bx+392h]\n")
    f.write("Where bx = (ds:40Ah) << 1\n\n")
    
    # Try to find data references to 0x392
    # This might be a segment offset
    
    # Let's search for functions that might load RFM files
    # by looking for file operations
    f.write("=" * 80 + "\n")
    f.write("SEARCHING FOR FILE OPERATIONS (dos_file_open callers):\n")
    f.write("=" * 80 + "\n\n")
    
    dos_file_open = 0x0226BD
    
    caller_count = 0
    for xref in idautils.XrefsTo(dos_file_open):
        caller_func = idaapi.get_func(xref.frm)
        if caller_func:
            func_name = idc.get_func_name(caller_func.start_ea)
            caller_count += 1
            
            # Check if this function might load RFM
            # by searching for "RFM" string refs or specific patterns
            has_rfm = False
            
            # Search for string references in this function
            addr = caller_func.start_ea
            while addr < caller_func.end_ea:
                # Check for string references
                for xref2 in idautils.XrefsFrom(addr):
                    # Check if it points to a string
                    str_val = idc.get_strlit_contents(xref2.to)
                    if str_val and b'RFM' in str_val.upper():
                        has_rfm = True
                        break
                if has_rfm:
                    break
                addr = idc.next_head(addr)
            
            marker = " *** RFM LOADER? ***" if has_rfm else ""
            f.write(f"{caller_count}. {func_name} @ 0x{caller_func.start_ea:X}{marker}\n")
            f.write(f"   Call from: 0x{xref.frm:X}\n")
            
            if has_rfm or caller_count < 30:  # Show first 30 or any with RFM
                # Show a snippet around the call
                f.write(f"   Context:\n")
                for i in range(-3, 4):
                    ctx_addr = xref.frm + (i * 4)
                    if ctx_addr >= caller_func.start_ea and ctx_addr < caller_func.end_ea:
                        disasm = idc.generate_disasm_line(ctx_addr, 0)
                        if disasm:
                            marker2 = " >>>" if i == 0 else "    "
                            f.write(f"   {marker2} 0x{ctx_addr:X}: {disasm}\n")
                f.write("\n")
    
    f.write(f"\nTotal functions calling dos_file_open: {caller_count}\n")
    
    # Now let's specifically search for functions that return pointers
    # and might be called from mode_state_dispatch
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("FUNCTIONS NEAR mode_state_dispatch:\n")
    f.write("=" * 80 + "\n\n")
    
    mode_dispatch_addr = 0x321C1
    
    # Look at functions in the range [mode_dispatch - 0x1000, mode_dispatch + 0x1000]
    for func_addr in idautils.Functions(mode_dispatch_addr - 0x1000, mode_dispatch_addr + 0x1000):
        func_name = idc.get_func_name(func_addr)
        func = idaapi.get_func(func_addr)
        if func:
            size = func.end_ea - func.start_ea
            f.write(f"  {func_name} @ 0x{func_addr:X} (size: {size} bytes)\n")

print(f"Analysis complete: {output_file}")
idc.qexit(0)
