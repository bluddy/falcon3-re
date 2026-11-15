"""
Extract VGA palette data from the executable.
Find where vga_dac_palette_upload reads palette data from.
"""
import idaapi
import idc
import idautils

def analyze_palette_upload():
    """Analyze the vga_dac_palette_upload function."""
    addr = 0x4F271
    
    print(f"Analyzing vga_dac_palette_upload at 0x{addr:X}")
    print("=" * 70)
    
    # Get function bounds
    func = idaapi.get_func(addr)
    if not func:
        print(f"ERROR: No function at 0x{addr:X}")
        return
    
    print(f"Function: {idc.get_func_name(addr)}")
    print(f"Start: 0x{func.start_ea:X}")
    print(f"End: 0x{func.end_ea:X}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    print()
    
    # Disassemble the function
    print("Disassembly:")
    print("-" * 70)
    
    ea = func.start_ea
    palette_seg = None
    palette_offset = None
    
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        print(f"0x{ea:05X}: {disasm}")
        
        # Look for segment register loads (palette data location)
        if 'ds:' in disasm or 'es:' in disasm:
            # Extract operands
            op1 = idc.print_operand(ea, 0)
            op2 = idc.print_operand(ea, 1)
            print(f"    -> Accessing data: {op1} = {op2}")
            
        # Look for port I/O (VGA DAC ports 3C8, 3C9)
        if 'dx' in disasm and ('3C8h' in disasm or '3C9h' in disasm):
            print(f"    -> VGA DAC port access")
        
        if 'out' in disasm:
            print(f"    -> Output to port")
            
        ea = idc.next_head(ea, func.end_ea)
    
    print("-" * 70)
    print()
    
    # Find cross-references to see what calls this
    print("Callers:")
    for xref in idautils.XrefsTo(addr):
        caller_name = idc.get_func_name(xref.frm)
        print(f"  0x{xref.frm:05X}: {caller_name}")
    
    print()

def find_palette_tables():
    """Search for palette data tables in data segments."""
    print("\nSearching for palette data tables...")
    print("=" * 70)
    
    # VGA palette is 256 RGB triplets = 768 bytes
    # Each component is 0-63 (6-bit VGA DAC)
    # Look for consecutive data that looks like palette
    
    # Check DGROUP segment
    seg = idaapi.get_segm_by_name("DGROUP")
    if seg:
        print(f"\nSearching DGROUP: 0x{seg.start_ea:X} - 0x{seg.end_ea:X}")
        
        # Look for regions with palette-like data
        # Palette values are typically 0-63 (0x00-0x3F)
        search_addr = seg.start_ea
        candidates = []
        
        while search_addr < seg.end_ea - 768:
            # Check if this could be start of palette
            valid_count = 0
            for offset in range(768):
                byte_val = idc.get_wide_byte(search_addr + offset)
                if byte_val <= 0x3F:  # Valid 6-bit DAC value
                    valid_count += 1
                else:
                    break
            
            if valid_count >= 768:
                candidates.append(search_addr)
                print(f"  Candidate palette at 0x{search_addr:X}")
                search_addr += 768
            else:
                search_addr += 1
        
        print(f"\nFound {len(candidates)} candidate palette(s)")
        
        # Dump first candidate if found
        if candidates:
            addr = candidates[0]
            print(f"\nFirst candidate palette at 0x{addr:X}:")
            print("First 48 bytes (16 colors RGB):")
            for i in range(16):
                r = idc.get_wide_byte(addr + i * 3)
                g = idc.get_wide_byte(addr + i * 3 + 1)
                b = idc.get_wide_byte(addr + i * 3 + 2)
                print(f"  Color {i:2}: R={r:2} G={g:2} B={b:2}")

def main():
    analyze_palette_upload()
    find_palette_tables()
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    idc.qexit(0)

if __name__ == '__main__':
    main()
