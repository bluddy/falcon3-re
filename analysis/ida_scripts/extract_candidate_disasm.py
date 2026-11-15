"""
Extract disassembly of top RLE decompressor candidates.
Focus on functions with STOSB+LODSB or ideal characteristics.
"""
import idc
import idaapi
import json

def get_function_disasm(func_addr):
    """Get complete disassembly of a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'name': idc.get_func_name(func_addr),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'disasm': '\n'.join(lines)
    }

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("EXTRACTING TOP RLE DECOMPRESSOR CANDIDATES")
    print("=" * 80)
    
    # Top candidates with STOSB+LODSB
    candidates = [
        0x0004F3EC,  # terrain_vm_buffer_decay (score=118, stosb=3, lodsb=3)
        0x0004FC2D,  # sub_4FC2D (score=118, stosb=6, lodsb=6)
        0x00026EFF,  # sprite_stride_lookup_26408 (score=106)
        0x00026A49,  # farobj_render_prep_1f712 (score=97)
        0x0002CC47,  # overlay_loader_main (score=86)
        0x0002AEA9,  # overlay_file_open (score=85)
        0x0004FA8A,  # palette_delta_blend (score=81)
        0x00088460,  # undoc_88460 (score=76)
        
        # Also check these from the expansion
        0x0012DF6A,  # overlay_handler_large_1
        0x001820B0,  # r53_sbi_stream_dispatch
    ]
    
    results = []
    
    for addr in candidates:
        print(f"\nExtracting: 0x{addr:06X}")
        result = get_function_disasm(addr)
        if result:
            results.append(result)
            print(f"  {result['name']}: {result['size']} bytes")
        else:
            print(f"  ERROR: No function at 0x{addr:06X}")
    
    # Save results
    import os
    output_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'candidate_disasm.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save as text for easy reading
    text_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'candidate_disasm.txt')
    with open(text_path, 'w') as f:
        for result in results:
            f.write("=" * 80 + "\n")
            f.write(f"; {result['name']}\n")
            f.write(f"; Address: {result['start']} - {result['end']}\n")
            f.write(f"; Size: {result['size']} bytes\n")
            f.write("=" * 80 + "\n\n")
            f.write(result['disasm'])
            f.write("\n\n\n")
    
    print(f"\n" + "=" * 80)
    print(f"Extracted {len(results)} functions")
    print(f"JSON: {output_path}")
    print(f"Text: {text_path}")
    print("=" * 80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
