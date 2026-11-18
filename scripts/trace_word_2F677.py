"""
Trace word_2F677 - the source of the RFM pointer
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\word_2F677_analysis.txt"

with open(output_file, 'w') as f:
    f.write("=== Analysis of word_2F677 (RFM Data Pointer Source) ===\n\n")
    
    # Calculate the actual address in data segment
    # Segment 0x2F64 + offset 0x77 should be around 0x2F6B7
    data_addr = 0x2F677
    
    f.write(f"Searching for: word_2F677\n")
    f.write(f"Address: 0x{data_addr:X}\n\n")
    
    # Try to find the symbol
    name = idc.get_name(data_addr)
    f.write(f"Symbol name: {name}\n")
    
    # Get type info
    tinfo = idaapi.tinfo_t()
    if idaapi.get_tinfo(tinfo, data_addr):
        f.write(f"Type: {tinfo}\n")
    
    # Get data value
    val = idc.get_wide_word(data_addr)
    if val is not None:
        f.write(f"Current value: 0x{val:X}\n\n")
    
    # Find all xrefs TO this address
    f.write("=" * 80 + "\n")
    f.write("XREFS TO word_2F677:\n")
    f.write("=" * 80 + "\n\n")
    
    xref_count = 0
    for xref in idautils.XrefsTo(data_addr):
        xref_count += 1
        f.write(f"\nXREF #{xref_count}:\n")
        f.write(f"  From: 0x{xref.frm:X}\n")
        f.write(f"  Type: {xref.type}\n")
        
        # Get function
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(xref.frm)
            f.write(f"  Function: {func_name} @ 0x{func.start_ea:X}\n")
            
            # Context around reference
            f.write(f"  Context:\n")
            for i in range(-5, 6):
                addr = xref.frm + (i * 4)
                if addr >= func.start_ea and addr < func.end_ea:
                    mnem = idc.print_insn_mnem(addr)
                    if mnem:
                        disasm = idc.generate_disasm_line(addr, 0)
                        marker = " >>> " if i == 0 else "     "
                        f.write(f"{marker}0x{addr:X}: {disasm}\n")
        else:
            f.write(f"  Not in a function\n")
    
    f.write(f"\n\nTotal xrefs: {xref_count}\n")
    
    # Also check nearby addresses for context
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("DATA CONTEXT (±16 bytes):\n")
    f.write("=" * 80 + "\n\n")
    
    for offset in range(-16, 17, 2):
        addr = data_addr + offset
        val = idc.get_wide_word(addr)
        name = idc.get_name(addr)
        if val is not None:
            marker = " >>> " if offset == 0 else "     "
            if name:
                f.write(f"{marker}0x{addr:X} ({name}): 0x{val:04X} ({val})\n")
            else:
                f.write(f"{marker}0x{addr:X}: 0x{val:04X} ({val})\n")

print(f"Analysis complete: {output_file}")
idc.qexit(0)
