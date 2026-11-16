"""
Find functions in R45 overlay segment.
The overlay calls use segment:offset addressing.
We need to find the segment base and calculate absolute addresses.
"""
import idaapi
import idautils
import idc
import json

def find_segment_for_function(func_ea):
    """Find which segment a function belongs to."""
    seg = idaapi.getseg(func_ea)
    if seg:
        return {
            "name": idaapi.get_segm_name(seg),
            "start": seg.start_ea,
            "end": seg.end_ea,
            "size": seg.size(),
            "type": seg.type
        }
    return None

def analyze_r45_overlay():
    """Analyze R45 overlay and find segment structure."""
    
    # Known R45 overlay function
    r45_addr = 0x156945
    
    seg_info = find_segment_for_function(r45_addr)
    if not seg_info:
        print(f"ERROR: Could not find segment for 0x{r45_addr:X}")
        return
    
    print(f"R45 overlay function at 0x{r45_addr:X}")
    print(f"Segment: {seg_info['name']}")
    print(f"Segment range: 0x{seg_info['start']:X} - 0x{seg_info['end']:X}")
    print(f"Segment size: {seg_info['size']} bytes")
    print()
    
    # Now try to find functions at offsets 0x18C and 0x1213 within this segment
    targets = [
        (0x18C, "sub_18C_position_calc"),
        (0x1213, "sub_1213_renderer")
    ]
    
    results = {}
    
    for offset, name in targets:
        # Try absolute address first
        abs_addr = offset
        func = idaapi.get_func(abs_addr)
        
        if not func:
            # Try segment-relative
            abs_addr = seg_info['start'] + offset
            func = idaapi.get_func(abs_addr)
        
        if not func:
            # Try searching for any function near this offset
            print(f"Searching for function near offset 0x{offset:X}...")
            # Search in all segments
            for seg_ea in idautils.Segments():
                test_addr = seg_ea + offset
                test_func = idaapi.get_func(test_addr)
                if test_func:
                    print(f"  Found at 0x{test_addr:X} (segment 0x{seg_ea:X} + 0x{offset:X})")
                    func = test_func
                    abs_addr = test_addr
                    break
        
        if func:
            print(f"\n{name}:")
            print(f"  Address: 0x{abs_addr:X}")
            print(f"  Size: {func.size()} bytes")
            print(f"  Name in IDA: {idc.get_func_name(abs_addr)}")
            
            func_seg = find_segment_for_function(abs_addr)
            if func_seg:
                print(f"  Segment: {func_seg['name']} (0x{func_seg['start']:X})")
            
            # Extract basic info
            results[name] = {
                "address": abs_addr,
                "size": func.size(),
                "ida_name": idc.get_func_name(abs_addr),
                "segment": func_seg['name'] if func_seg else None
            }
        else:
            print(f"\nERROR: Could not find function for {name} at offset 0x{offset:X}")
    
    # List all functions in R45 segment
    print(f"\n\nAll functions in segment {seg_info['name']}:")
    func_count = 0
    for func_ea in idautils.Functions(seg_info['start'], seg_info['end']):
        func = idaapi.get_func(func_ea)
        offset = func_ea - seg_info['start']
        print(f"  0x{func_ea:X} (offset 0x{offset:X}): {idc.get_func_name(func_ea)} - {func.size()} bytes")
        func_count += 1
        if func_count > 50:  # Limit output
            print(f"  ... (showing first 50 functions)")
            break
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_segment_analysis.json"
    output = {
        "r45_overlay": r45_addr,
        "segment": seg_info,
        "target_functions": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to {output_path}")

if __name__ == "__main__":
    analyze_r45_overlay()
