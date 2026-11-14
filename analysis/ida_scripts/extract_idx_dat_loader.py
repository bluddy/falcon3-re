"""
Extract idx_dat_loader function (sub_1297F0) - PICFONT.IDX/.DAT loader.
This is the template function for all .IDX/.DAT file loading in Falcon 3.0.

Based on verified pattern from analysis/s4/ scripts.
"""

import idc
import idaapi
import idautils
from pathlib import Path

def main():
    print("="*80)
    print("Extracting idx_dat_loader (sub_1297F0)")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    # Target function
    func_addr = 0x1297F0  # Linear address
    new_name = "idx_dat_loader"
    
    # Get function info
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"ERROR: No function found at {hex(func_addr)}")
        idc.qexit(1)
    
    old_name = idc.get_func_name(func_addr)
    print(f"Found function: {old_name}")
    print(f"Address: {hex(func.start_ea)} - {hex(func.end_ea)}")
    print(f"Size: {func.end_ea - func.start_ea} bytes\n")
    
    # Rename function
    print(f"Renaming to: {new_name}")
    if idc.set_name(func_addr, new_name, idc.SN_NOWARN):
        print(f"✓ Renamed successfully")
    else:
        print(f"✗ Rename failed (may already exist)")
    
    # Find string references
    print("\nFinding string references...")
    strings_found = []
    for s in idautils.Strings():
        s_str = str(s)
        if any(term in s_str.upper() for term in ["PICFONT", ".IDX", ".DAT"]):
            # Check if this function references it
            for xref in idautils.XrefsTo(s.ea):
                if func.start_ea <= xref.frm < func.end_ea:
                    strings_found.append({
                        'addr': hex(s.ea),
                        'string': s_str,
                        'ref_from': hex(xref.frm)
                    })
                    print(f"  {hex(s.ea)}: \"{s_str}\"")
                    print(f"    Referenced at {hex(xref.frm)}")
    
    # Export disassembly
    output_file = Path(__file__).parent.parent / "idx_dat_loader.asm"
    print(f"\nExporting disassembly to: {output_file}")
    
    with open(output_file, 'w') as f:
        f.write("; idx_dat_loader - Loads .IDX and .DAT file pairs\n")
        f.write(f"; Original name: {old_name}\n")
        f.write(f"; Address: {hex(func.start_ea)} - {hex(func.end_ea)}\n")
        f.write(f"; Size: {func.end_ea - func.start_ea} bytes\n")
        f.write(";\n")
        f.write("; This is the template function for ALL .IDX/.DAT file loading\n")
        f.write("; References:\n")
        for s in strings_found:
            f.write(f";   {s['addr']}: \"{s['string']}\" at {s['ref_from']}\n")
        f.write(";\n\n")
        
        f.write(f"{new_name} proc near\n\n")
        
        # Disassembly
        ea = func.start_ea
        line_count = 0
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            comment = idc.get_cmt(ea, 0)
            
            line = f"  {ea:08X}  {disasm}"
            if comment:
                line += f"  ; {comment}"
            
            f.write(line + "\n")
            line_count += 1
            ea = idc.next_head(ea, func.end_ea)
        
        f.write(f"\n{new_name} endp\n")
        f.write(f"\n; Total: {line_count} instructions\n")
    
    print(f"✓ Exported {line_count} instructions")
    
    # Summary
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"Function: {new_name}")
    print(f"Address: {hex(func_addr)}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    print(f"Instructions: {line_count}")
    print(f"String references: {len(strings_found)}")
    print(f"Output: {output_file}")
    print("="*80)
    
    # Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
