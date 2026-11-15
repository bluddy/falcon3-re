"""
Extract disassembly of undoc_88460 @ 0x88460 - likely RLE decompressor!
Found via bytecode search: has both REP STOSB and REP STOSW.
"""
import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    addr = 0x88460
    
    print("=" * 80)
    print(f"EXTRACTING undoc_88460 @ 0x{addr:06X}")
    print("LIKELY RLE DECOMPRESSOR!")
    print("=" * 80)
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"ERROR: No function at 0x{addr:06X}")
        idc.qexit(1)
    
    print(f"\nFunction: {idc.get_func_name(addr)}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    print(f"Segment: {idc.get_segm_name(addr)}")
    
    # Get disassembly
    lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    # Save to text file
    import os
    text_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'undoc_88460_DECOMPRESSOR.txt')
    with open(text_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"; undoc_88460 - LIKELY RLE DECOMPRESSOR\n")
        f.write(f"; Address: 0x{func.start_ea:06X} - 0x{func.end_ea:06X}\n")
        f.write(f"; Size: {func.end_ea - func.start_ea} bytes\n")
        f.write(f"; Segment: {idc.get_segm_name(addr)}\n")
        f.write(f"; Found via bytecode search: REP STOSB + REP STOSW\n")
        f.write("=" * 80 + "\n\n")
        f.write('\n'.join(lines))
    
    print(f"\nDisassembly saved to: {text_path}")
    print("\nDone!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
