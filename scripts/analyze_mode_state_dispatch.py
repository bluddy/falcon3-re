"""
Analyze mode_state_dispatch - the function that returns the RFM pointer
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\mode_state_dispatch_analysis.txt"

with open(output_file, 'w') as f:
    f.write("=== mode_state_dispatch Analysis ===\n\n")
    
    # Find the function by name
    func_ea = idc.get_name_ea_simple("mode_state_dispatch")
    
    if func_ea == idaapi.BADADDR:
        f.write("ERROR: Function 'mode_state_dispatch' not found!\n")
        f.write("Searching for it in all functions...\n\n")
        
        # Search for the name in all functions
        for func_addr in idautils.Functions():
            name = idc.get_func_name(func_addr)
            if "dispatch" in name.lower() or "mode" in name.lower():
                f.write(f"Found: {name} @ 0x{func_addr:X}\n")
    else:
        f.write(f"Found: mode_state_dispatch @ 0x{func_ea:X}\n\n")
        
        func = idaapi.get_func(func_ea)
        if func:
            f.write(f"Start: 0x{func.start_ea:X}\n")
            f.write(f"End: 0x{func.end_ea:X}\n")
            f.write(f"Size: {func.end_ea - func.start_ea} bytes\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("FULL DISASSEMBLY:\n")
            f.write("=" * 80 + "\n\n")
            
            addr = func.start_ea
            while addr < func.end_ea:
                disasm = idc.generate_disasm_line(addr, 0)
                if disasm:
                    # Highlight calls and returns
                    if 'call' in disasm.lower():
                        f.write(f"0x{addr:X}: {disasm}  *** CALL ***\n")
                    elif 'ret' in disasm.lower():
                        f.write(f"0x{addr:X}: {disasm}  *** RETURN ***\n")
                    elif '.rfm' in disasm.lower() or 'rfm' in disasm.lower():
                        f.write(f"0x{addr:X}: {disasm}  *** RFM ***\n")
                    else:
                        f.write(f"0x{addr:X}: {disasm}\n")
                addr = idc.next_head(addr)
            
            # Find all calls made by this function
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("CALLED FUNCTIONS:\n")
            f.write("=" * 80 + "\n\n")
            
            called_funcs = set()
            addr = func.start_ea
            while addr < func.end_ea:
                if idc.print_insn_mnem(addr) == 'call':
                    op0 = idc.get_operand_value(addr, 0)
                    if op0:
                        called_name = idc.get_func_name(op0)
                        if called_name:
                            called_funcs.add((op0, called_name))
                addr = idc.next_head(addr)
            
            for call_addr, call_name in sorted(called_funcs):
                f.write(f"  - {call_name} @ 0x{call_addr:X}\n")
            
            # Find callers of this function
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("CALLERS OF mode_state_dispatch:\n")
            f.write("=" * 80 + "\n\n")
            
            for xref in idautils.XrefsTo(func_ea):
                caller_func = idaapi.get_func(xref.frm)
                if caller_func:
                    caller_name = idc.get_func_name(xref.frm)
                    f.write(f"  - 0x{xref.frm:X} in {caller_name}\n")

print(f"Analysis complete: {output_file}")
idc.qexit(0)
