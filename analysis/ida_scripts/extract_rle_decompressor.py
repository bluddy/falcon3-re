"""
Extract the RLE decompressor at 0x88460 to understand PICFONT sprite format.

From GRAPHICS_SYSTEM_FINDINGS.md:
- rle_vga_decompressor at 0x88460, 114 bytes
- Input: SI=data ptr, DI=Y coord, BX=X coord/4
- Data format: [width:word][height:word][rle_compressed_planes]
- RLE: flag byte - bit7=1: run (count+value), bit7=0: literal (count+data)
"""

import idc
import idaapi
import idautils
from pathlib import Path

def get_function_complete(addr):
    """Get complete function disassembly with annotations."""
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    result = {
        'address': hex(addr),
        'name': idc.get_func_name(addr),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'disassembly': []
    }
    
    # Get every instruction
    ea = func.start_ea
    while ea < func.end_ea:
        # Get disassembly with comments
        disasm = idc.generate_disasm_line(ea, 0)
        comment = idc.get_cmt(ea, 0)  # Get regular comment
        if not comment:
            comment = idc.get_cmt(ea, 1)  # Get repeatable comment
        
        line = f"{ea:08X}  {disasm}"
        if comment:
            line += f"  ; {comment}"
        
        result['disassembly'].append(line)
        ea = idc.next_head(ea, func.end_ea)
    
    return result

def main():
    print("="*80)
    print("EXTRACTING RLE DECOMPRESSOR AND RELATED FUNCTIONS")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    output_dir = Path(__file__).parent.parent
    
    # Extract RLE decompressor and any related functions
    functions = {
        'rle_vga_decompressor': 0x88460,
    }
    
    results = {}
    
    print("\nExtracting RLE decompressor...")
    for name, addr in functions.items():
        print(f"  {name} at 0x{addr:08X}...")
        info = get_function_complete(addr)
        if info:
            results[name] = info
            print(f"    Size: {info['size']} bytes")
            print(f"    Lines: {len(info['disassembly'])}")
        else:
            print(f"    ERROR: Not a function!")
    
    # Save detailed disassembly
    txt_file = output_dir / "rle_decompressor_complete.txt"
    with open(txt_file, 'w') as f:
        if 'rle_vga_decompressor' in results:
            func = results['rle_vga_decompressor']
            f.write("="*80 + "\n")
            f.write(f"RLE VGA DECOMPRESSOR\n")
            f.write(f"Function: {func['name']}\n")
            f.write(f"Address: {func['address']}\n")
            f.write(f"Size: {func['size']} bytes\n")
            f.write("="*80 + "\n\n")
            
            f.write("From GRAPHICS_SYSTEM_FINDINGS.md:\n")
            f.write("  Input: SI=data ptr, DI=Y coord, BX=X coord/4\n")
            f.write("  Data format: [width:word][height:word][rle_compressed_planes]\n")
            f.write("  RLE: flag byte - bit7=1: run (count+value), bit7=0: literal (count+data)\n")
            f.write("  Output: VGA mode 13h planar format (4 bit planes)\n")
            f.write("\n" + "="*80 + "\n\n")
            
            f.write("DISASSEMBLY:\n\n")
            for i, line in enumerate(func['disassembly']):
                f.write(f"{i:4d}: {line}\n")
    
    print(f"\nSaved to: {txt_file}")
    
    # Try to find related decompressor functions by searching for similar patterns
    print("\nSearching for similar decompressor functions...")
    
    # Look for functions that:
    # 1. Access SI register (source pointer)
    # 2. Access DI register (destination)
    # 3. Have loops (jnz, jz, loop instructions)
    # 4. Are around 100-200 bytes
    
    similar_funcs = []
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        size = func.end_ea - func.start_ea
        if size < 50 or size > 500:
            continue
        
        # Check for SI/DI usage and loops
        has_si = False
        has_di = False
        has_loop = False
        
        for ea in idautils.FuncItems(func_ea):
            disasm = idc.generate_disasm_line(ea, 0).lower()
            if 'si' in disasm:
                has_si = True
            if 'di' in disasm:
                has_di = True
            if any(x in disasm for x in ['loop', 'jnz', 'jz', 'jl', 'jg']):
                has_loop = True
        
        if has_si and has_di and has_loop:
            similar_funcs.append({
                'name': idc.get_func_name(func_ea),
                'address': hex(func_ea),
                'size': size
            })
    
    print(f"  Found {len(similar_funcs)} similar functions")
    if similar_funcs:
        print("\n  Top candidates:")
        for func in sorted(similar_funcs, key=lambda x: abs(x['size'] - 114))[:10]:
            print(f"    {func['name']:40} {func['address']} ({func['size']}B)")
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    
    # Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
