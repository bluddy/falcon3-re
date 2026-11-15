"""
Document graphics format discoveries in IDA database.
Add comments and update function names based on RLE investigation.
"""
import idaapi
import idc

def set_function_comment(addr, comment):
    """Set or update function comment."""
    func = idaapi.get_func(addr)
    if func:
        idc.set_func_cmt(addr, comment, 0)
        return True
    return False

def set_comment(addr, comment):
    """Set or update regular comment."""
    idc.set_cmt(addr, comment, 0)

def main():
    idaapi.auto_wait()
    
    updates = []
    
    # Document font loaders
    picfont_addr = 0x1297F0
    comment = """PICFONT.IDX/.DAT Loader (TEMPLATE PATTERN)
Format: .IDX contains (offset, size) word pairs pointing into .DAT
.DAT records: [magic 0x0400][width 2B][height 2B][RLE compressed pixels]

PICFONT.DAT example:
- Record 0: 22×492 pixels = 10,824 pixels compressed to 37 bytes (0.34% ratio!)
- Uses bit-packed variable-length RLE (algorithm TBD)

Calls op_dispatch with:
  Op 6: File open
  Op 0xA: File read (INCLUDES RLE DECOMPRESSION)
  Op 8: File close"""
    
    if set_function_comment(picfont_addr, comment):
        updates.append(f"Updated picfont_idx_dat_loader @ 0x{picfont_addr:X}")
    
    madfont_addr = 0x1397CE
    comment = """MADFONT.IDX/.DAT Loader
Same format as PICFONT loader (see 0x1297F0 for details).
Loads MADFONT.IDX/.DAT font file pair with RLE compressed graphics.
Calls op_dispatch extensively for file I/O + decompression."""
    
    if set_function_comment(madfont_addr, comment):
        updates.append(f"Updated madfont_idx_dat_loader @ 0x{madfont_addr:X}")
    
    # Document dispatch system
    dispatch_addr = 0x2257B
    comment = """Main Operation Dispatcher
Calls: cs:op_dispatch_table[bx]
BX = operation code (0-16, total 17 operations)

Key file I/O operations:
  Op 6: File open
  Op 8: File close
  Op 0xA (10): File read - INCLUDES RLE DECOMPRESSION for .DAT files
  Op 0xE: Unknown file operation

RLE Decompression:
- Operation 0xA handler decompresses .DAT graphics on-the-fly during file read
- Format: bit-packed variable-length RLE achieving 0.34%-2% compression ratios
- Used for fonts (PICFONT, MADFONT) and backgrounds
- NOT used for BUTTON files (those are uncompressed raw pixels)"""
    
    if set_function_comment(dispatch_addr, comment):
        updates.append(f"Updated op_dispatch @ 0x{dispatch_addr:X}")
    
    dispatch_far_addr = 0x22598
    comment = """Far Entry Wrapper for op_dispatch
Marshals arguments from far call stack to near call convention.
Just a 30-byte wrapper - see 0x2257B for actual dispatcher."""
    
    if set_function_comment(dispatch_far_addr, comment):
        updates.append(f"Updated op_dispatch_far_entry @ 0x{dispatch_far_addr:X}")
    
    # Document VGA palette function
    vga_addr = 0x4F271
    comment = """VGA DAC Palette Upload
Uploads color palette to VGA hardware.
Called after decompressing graphics to set colors.
4 known callers in the codebase."""
    
    if set_function_comment(vga_addr, comment):
        updates.append(f"Updated vga_dac_palette_upload @ 0x{vga_addr:X}")
    
    # Try to find and document the dispatch table
    # Look for data near op_dispatch that could be the table
    dispatch_area_start = 0x22000
    dispatch_area_end = 0x22600
    
    # Search for arrays of word pointers
    potential_tables = []
    for addr in range(dispatch_area_start, dispatch_area_end, 2):
        # Check if this looks like a function pointer table
        consecutive_valid = 0
        for i in range(20):  # Check 20 entries
            ptr = idc.get_wide_word(addr + i * 2)
            if ptr == 0 or ptr == 0xFFFF:
                break
            # Check if pointer points to valid code
            if idc.is_code(idc.get_full_flags(ptr)):
                consecutive_valid += 1
            else:
                break
        
        if consecutive_valid >= 10:  # At least 10 valid function pointers
            potential_tables.append((addr, consecutive_valid))
    
    if potential_tables:
        updates.append(f"\nFound {len(potential_tables)} potential dispatch tables:")
        for addr, count in potential_tables:
            updates.append(f"  0x{addr:X}: {count} consecutive function pointers")
            
            # Document the most promising one (should be 17 entries for op_dispatch_table)
            if 15 <= count <= 20:
                idc.set_name(addr, "op_dispatch_table_candidate", idc.SN_NOWARN)
                set_comment(addr, f"Potential dispatch table: {count} function pointers")
                updates.append(f"    -> Tagged as op_dispatch_table_candidate")
    
    # Print summary
    print("=" * 80)
    print("GRAPHICS FORMAT DOCUMENTATION UPDATE")
    print("=" * 80)
    for update in updates:
        print(update)
    
    print("\n" + "=" * 80)
    print("KEY DISCOVERIES DOCUMENTED:")
    print("=" * 80)
    print("1. Two graphics systems: BUTTON (uncompressed) vs .IDX/.DAT (RLE)")
    print("2. .IDX format: (offset, size) word pairs")
    print("3. .DAT format: [0x0400][width][height][RLE data]")
    print("4. RLE decompression in op_dispatch operation 0xA")
    print("5. Compression ratio: 0.34%-2% (extremely high, 50:1 to 300:1)")
    
    # Write summary
    with open('ida_graphics_documentation.txt', 'w') as f:
        f.write("IDA Graphics Format Documentation Update\n")
        f.write("=" * 80 + "\n\n")
        f.write('\n'.join(updates))
        f.write("\n\nNext steps:\n")
        f.write("1. Locate op_dispatch_table (17 function pointers)\n")
        f.write("2. Disassemble operation 0xA handler (file read + RLE decompression)\n")
        f.write("3. Reverse-engineer bit-packed RLE algorithm\n")
    
    print("\nWrote summary to ida_graphics_documentation.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
