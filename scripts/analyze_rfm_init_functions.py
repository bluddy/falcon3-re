"""
Analyze the two functions that initialize cs:word_3B830
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\rfm_init_analysis.txt"

with open(output_file, 'w') as f:
    f.write("=== RFM Initialization Analysis ===\n\n")
    
    # Function 1: entity_slot_update_loop @ 0x3C1BD (sets constant 0x2F64)
    f.write("=" * 80 + "\n")
    f.write("FUNCTION 1: entity_slot_update_loop @ 0x3C1BD\n")
    f.write("=" * 80 + "\n\n")
    
    func1_addr = 0x3C1BD
    func1 = idaapi.get_func(func1_addr)
    if func1:
        f.write(f"Start: 0x{func1.start_ea:X}\n")
        f.write(f"End: 0x{func1.end_ea:X}\n")
        f.write(f"Size: {func1.end_ea - func1.start_ea} bytes\n\n")
        
        f.write("Disassembly:\n")
        f.write("-" * 80 + "\n")
        addr = func1.start_ea
        while addr < func1.end_ea:
            disasm = idc.generate_disasm_line(addr, 0)
            if disasm:
                f.write(f"0x{addr:X}: {disasm}\n")
            addr = idc.next_head(addr)
        
        # Find xrefs TO this function
        f.write("\n\nCallers (Xrefs to this function):\n")
        f.write("-" * 80 + "\n")
        caller_count = 0
        for xref in idautils.XrefsTo(func1.start_ea):
            caller_count += 1
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                f.write(f"  {caller_count}. 0x{xref.frm:X} in {caller_name}\n")
            else:
                f.write(f"  {caller_count}. 0x{xref.frm:X} (no function)\n")
    
    # Function 2: farobj_slot_table_copy @ 0x419FC (loads from memory)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("FUNCTION 2: farobj_slot_table_copy @ 0x419FC\n")
    f.write("=" * 80 + "\n\n")
    
    func2_addr = 0x419FC
    func2 = idaapi.get_func(func2_addr)
    if func2:
        f.write(f"Start: 0x{func2.start_ea:X}\n")
        f.write(f"End: 0x{func2.end_ea:X}\n")
        f.write(f"Size: {func2.end_ea - func2.start_ea} bytes\n\n")
        
        f.write("Disassembly:\n")
        f.write("-" * 80 + "\n")
        addr = func2.start_ea
        while addr < func2.end_ea:
            disasm = idc.generate_disasm_line(addr, 0)
            if disasm:
                f.write(f"0x{addr:X}: {disasm}\n")
            addr = idc.next_head(addr)
        
        # Find xrefs TO this function
        f.write("\n\nCallers (Xrefs to this function):\n")
        f.write("-" * 80 + "\n")
        caller_count = 0
        for xref in idautils.XrefsTo(func2.start_ea):
            caller_count += 1
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                f.write(f"  {caller_count}. 0x{xref.frm:X} in {caller_name}\n")
            else:
                f.write(f"  {caller_count}. 0x{xref.frm:X} (no function)\n")
    
    # Also check what farobj_slot_table_load does (right before copy)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("FUNCTION 3: farobj_slot_table_load @ 0x418AC (loads data)\n")
    f.write("=" * 80 + "\n\n")
    
    func3_addr = 0x418AC
    func3 = idaapi.get_func(func3_addr)
    if func3:
        f.write(f"Start: 0x{func3.start_ea:X}\n")
        f.write(f"End: 0x{func3.end_ea:X}\n")
        f.write(f"Size: {func3.end_ea - func3.start_ea} bytes\n\n")
        
        f.write("Disassembly:\n")
        f.write("-" * 80 + "\n")
        addr = func3.start_ea
        while addr < func3.end_ea:
            disasm = idc.generate_disasm_line(addr, 0)
            if disasm:
                # Highlight file operations
                if 'call' in disasm.lower() and any(x in disasm.lower() for x in ['file', 'open', 'read', 'dos']):
                    f.write(f"0x{addr:X}: {disasm}  *** FILE OPERATION ***\n")
                else:
                    f.write(f"0x{addr:X}: {disasm}\n")
            addr = idc.next_head(addr)
        
        # Find xrefs TO this function
        f.write("\n\nCallers (Xrefs to this function):\n")
        f.write("-" * 80 + "\n")
        caller_count = 0
        for xref in idautils.XrefsTo(func3.start_ea):
            caller_count += 1
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                f.write(f"  {caller_count}. 0x{xref.frm:X} in {caller_name}\n")
            else:
                f.write(f"  {caller_count}. 0x{xref.frm:X} (no function)\n")

print(f"Analysis complete: {output_file}")
idc.qexit(0)
