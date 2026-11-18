"""
Export disassembly of specific code sections to text file
Follows IDA automation guidelines - module-level code only
"""

import idc
import idaapi
import idautils

# Wait for auto-analysis
idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\disasm_word_3B830_refs.txt"

with open(output_file, 'w') as f:
    f.write("=== Search for cs:word_3B830 References ===\n\n")
    
    # Target address in code segment
    target_addr = 0x3B830
    
    f.write(f"Target address: 0x{target_addr:X}\n")
    f.write(f"Symbol name: {idc.get_name(target_addr)}\n\n")
    
    # Get all code xrefs TO this address
    f.write("=== XREFS TO 0x3B830 ===\n")
    xref_count = 0
    for xref in idautils.XrefsTo(target_addr):
        xref_count += 1
        f.write(f"\nXREF #{xref_count}:\n")
        f.write(f"  From: 0x{xref.frm:X}\n")
        f.write(f"  Type: {xref.type}\n")
        
        # Get function containing this xref
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(xref.frm)
            f.write(f"  Function: {func_name} @ 0x{func.start_ea:X}\n")
            
            # Disassemble 10 lines around the reference
            f.write(f"  Context (±10 lines):\n")
            for i in range(-10, 11):
                addr = xref.frm + (i * 4)  # Approximate
                if addr >= func.start_ea and addr < func.end_ea:
                    mnem = idc.print_insn_mnem(addr)
                    if mnem:
                        disasm = idc.generate_disasm_line(addr, 0)
                        marker = " >>> " if i == 0 else "     "
                        f.write(f"{marker}0x{addr:X}: {disasm}\n")
        else:
            f.write(f"  Not in a function\n")
    
    f.write(f"\n\nTotal xrefs found: {xref_count}\n")
    
    # Search for string references to RFM
    f.write("\n\n=== STRING SEARCH FOR 'RFM' ===\n")
    string_count = 0
    for string_addr in idautils.Strings():
        string_val = str(string_addr)
        if 'RFM' in string_val.upper():
            string_count += 1
            f.write(f"\nString #{string_count}:\n")
            f.write(f"  Address: 0x{string_addr.ea:X}\n")
            f.write(f"  Value: {string_val}\n")
            
            # Find xrefs to this string
            xref_list = list(idautils.XrefsTo(string_addr.ea))
            f.write(f"  Xrefs: {len(xref_list)}\n")
            for xref in xref_list:
                func = idaapi.get_func(xref.frm)
                if func:
                    func_name = idc.get_func_name(xref.frm)
                    f.write(f"    From: 0x{xref.frm:X} in {func_name}\n")
    
    f.write(f"\n\nTotal RFM strings found: {string_count}\n")

print(f"Export complete: {output_file}")
idc.qexit(0)
