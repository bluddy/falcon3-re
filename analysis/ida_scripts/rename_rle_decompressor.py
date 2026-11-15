"""
Rename undoc_88460 to rle_vga_decompressor and document it.
"""
import idc
import idaapi

def main():
    idaapi.auto_wait()
    
    addr = 0x88460
    new_name = "rle_vga_decompressor"
    
    print("=" * 80)
    print(f"RENAMING RLE DECOMPRESSOR")
    print("=" * 80)
    
    # Rename function
    if idc.set_name(addr, new_name, idc.SN_NOWARN):
        print(f"\n✓ Renamed 0x{addr:06X} to {new_name}")
    else:
        print(f"\n✗ Failed to rename 0x{addr:06X}")
    
    # Add function comment
    comment = """RLE Decompressor for VGA graphics.
Algorithm:
  Read control byte:
    If bit 7 set: Run-length encoding
      - Low 7 bits = count
      - Next byte = value to repeat
      - Uses REP STOSW/STOSB
    Else: Literal copy
      - Control byte = count
      - Copy next N bytes literally
      - Uses REP MOVSW/MOVSB
  
Handles VGA planes via EGA sequencer (port 3C4h).
Used by font loaders and menu graphics system."""
    
    idc.set_func_cmt(addr, comment, 1)
    print(f"✓ Added function comment")
    
    print("\nDone!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
