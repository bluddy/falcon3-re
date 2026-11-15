"""
Analyze overlay structure and what overlays contain
"""
import idaapi
import idautils
import idc
import json

def find_overlay_jumps():
    """Find all far jumps to overlays"""
    overlay_jumps = []
    
    print("Searching for overlay jumps...")
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for far jumps (jmp far ptr)
            if mnem == 'jmp':
                # Check if it's a far jump
                op_type = idc.get_operand_type(ea, 0)
                if op_type == idc.o_far or op_type == idc.o_mem:
                    target_str = idc.print_operand(ea, 0)
                    
                    # Get target address if available
                    target_ea = idc.get_operand_value(ea, 0)
                    
                    overlay_jumps.append({
                        'from_addr': ea,
                        'from_func': func_name,
                        'target_str': target_str,
                        'target_addr': target_ea if target_ea != idc.BADADDR else None,
                        'disasm': idc.generate_disasm_line(ea, 0)
                    })
            
            ea = idc.next_head(ea, func.end_ea)
    
    return overlay_jumps

def find_overlay_calls():
    """Find functions that load overlays"""
    overlay_loaders = []
    
    # Look for functions with names suggesting overlay loading
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        
        if any(keyword in func_name.lower() for keyword in 
               ['overlay', 'load', 'bridge', 'tail']):
            func = idaapi.get_func(func_ea)
            if func:
                overlay_loaders.append({
                    'address': func_ea,
                    'hex_addr': f'0x{func_ea:X}',
                    'name': func_name,
                    'size': func.end_ea - func.start_ea
                })
    
    return overlay_loaders

def analyze_segment_structure():
    """Analyze segment layout to find overlay segments"""
    segments = []
    
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        seg_name = idc.get_segm_name(seg_ea)
        
        # Get segment info
        segments.append({
            'name': seg_name,
            'start': seg_ea,
            'end': idc.get_segm_end(seg_ea),
            'hex_start': f'0x{seg_ea:X}',
            'hex_end': f'0x{idc.get_segm_end(seg_ea):X}',
            'size': idc.get_segm_end(seg_ea) - seg_ea,
            'type': idc.get_segm_attr(seg_ea, idc.SEGATTR_TYPE)
        })
    
    return segments

def main():
    print("="*60)
    print("OVERLAY ANALYSIS")
    print("="*60)
    
    # Find overlay-related functions
    print("\n1. Finding overlay loader functions...")
    loaders = find_overlay_calls()
    print(f"   Found {len(loaders)} overlay-related functions:")
    for loader in loaders[:10]:
        print(f"     0x{loader['address']:06X}: {loader['name']} ({loader['size']} bytes)")
    
    # Find overlay jumps
    print("\n2. Finding far jumps to overlays...")
    jumps = find_overlay_jumps()
    print(f"   Found {len(jumps)} far jumps:")
    for jump in jumps[:10]:
        print(f"     {jump['from_func']} -> {jump['target_str']}")
    
    # Analyze segments
    print("\n3. Analyzing segment structure...")
    segments = analyze_segment_structure()
    print(f"   Found {len(segments)} segments:")
    for seg in segments:
        print(f"     {seg['name']:20s} {seg['hex_start']} - {seg['hex_end']} ({seg['size']:6d} bytes)")
    
    # Save results
    results = {
        'overlay_loaders': loaders,
        'overlay_jumps': jumps[:100],  # Limit to first 100
        'segments': segments
    }
    
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\overlay_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n4. Results saved to: {output_path}")
    
    # Summary
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Overlay loader functions: {len(loaders)}")
    print(f"Far jumps to overlays: {len(jumps)}")
    print(f"Total segments: {len(segments)}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
