"""
Discover and analyze the Terrain rendering system.

Based on the HUD analysis, we know:
- External view renderer connects to terrain system
- view_terrain_frame_step calls view_limits_install_step
- Terrain functions were mentioned in discovery report

Goal: Find all terrain-related functions and understand the architecture.
"""

import idc
import idaapi
import idautils
import json

def find_terrain_functions():
    """Find all terrain-related functions."""
    
    print("=" * 80)
    print("DISCOVERING TERRAIN SYSTEM FUNCTIONS")
    print("=" * 80)
    
    # Search patterns
    keywords = [
        "terrain",
        "height",
        "ground",
        "tile",
        "lod",
        "mesh",
        "poly",
        "landscape"
    ]
    
    terrain_funcs = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_name_lower = func_name.lower()
        
        # Check if function name contains terrain keywords
        for keyword in keywords:
            if keyword in func_name_lower:
                func = idaapi.get_func(func_ea)
                if func:
                    func_size = func.end_ea - func.start_ea
                    
                    # Count calls and data refs
                    call_count = 0
                    for xref in idautils.XrefsTo(func_ea):
                        if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                            call_count += 1
                    
                    terrain_funcs.append({
                        "name": func_name,
                        "address": func_ea,
                        "size": func_size,
                        "callers": call_count,
                        "keyword": keyword
                    })
                    
                    print(f"  {func_name:50} 0x{func_ea:05X} ({func_size:4} bytes, {call_count} callers) [{keyword}]")
                
                break
    
    print(f"\nTotal terrain functions found: {len(terrain_funcs)}")
    
    return terrain_funcs

def analyze_key_terrain_functions():
    """Analyze key terrain functions we know about."""
    
    print("\n" + "=" * 80)
    print("ANALYZING KEY TERRAIN FUNCTIONS")
    print("=" * 80)
    
    # Functions we know from previous analysis
    known_funcs = [
        ("view_terrain_frame_step", 0x31CA1),  # Calls view_limits_install_step
        ("terrain_attr_scan_clamp", 0x3606C),  # Mentioned in HUD analysis
        ("terrain_point_label_draw", 0x36347), # Draws terrain labels
    ]
    
    results = {}
    
    for func_name_hint, expected_addr in known_funcs:
        # Try to find it
        found_addr = None
        
        # Search by name
        for func_ea in idautils.Functions():
            func_name = idc.get_func_name(func_ea)
            if func_name_hint in func_name or func_ea == expected_addr:
                found_addr = func_ea
                func_name = idc.get_func_name(func_ea)
                break
        
        if found_addr:
            func = idaapi.get_func(found_addr)
            func_size = func.end_ea - func.start_ea
            
            print(f"\n[*] {func_name} at 0x{found_addr:05X} ({func_size} bytes)")
            
            # Get calls
            calls = []
            ea = func.start_ea
            while ea < func.end_ea:
                if idc.print_insn_mnem(ea) == "call":
                    for xref in idautils.XrefsFrom(ea):
                        if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                            target_name = idc.get_func_name(xref.to)
                            calls.append(target_name)
                            
                            # Print if terrain-related
                            if any(kw in target_name.lower() for kw in ["terrain", "height", "ground", "tile"]):
                                print(f"    → {target_name}")
                
                ea = idc.next_head(ea)
            
            results[func_name] = {
                "address": found_addr,
                "size": func_size,
                "calls": calls
            }
    
    return results

def find_terrain_data_structures():
    """Find terrain-related data structures."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR TERRAIN DATA STRUCTURES")
    print("=" * 80)
    
    # Look for data with "terrain", "height", "map" in names
    keywords = ["terrain", "height", "map", "tile", "ground"]
    
    data_structs = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Skip code segments
        seg_type = idc.get_segm_attr(seg_ea, idc.SEGATTR_TYPE)
        if seg_type == 2:  # CODE segment
            continue
        
        # Search for named data in this segment
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            name = idc.get_name(ea)
            if name:
                name_lower = name.lower()
                for keyword in keywords:
                    if keyword in name_lower:
                        # Get size
                        next_ea = idc.next_head(ea)
                        size = next_ea - ea if next_ea > ea else 0
                        
                        data_structs.append({
                            "name": name,
                            "address": ea,
                            "size": size,
                            "segment": seg_name
                        })
                        
                        print(f"  {name:40} 0x{ea:05X} ({size:4} bytes) in {seg_name}")
                        break
            
            ea = idc.next_head(ea)
    
    return data_structs

def find_view_terrain_callers():
    """Find what calls view_terrain_frame_step."""
    
    print("\n" + "=" * 80)
    print("TRACING TERRAIN SYSTEM ENTRY POINTS")
    print("=" * 80)
    
    # Find view_terrain_frame_step
    target_addr = 0x31CA1
    
    print(f"[*] Looking for callers of view_terrain_frame_step at 0x{target_addr:05X}")
    print("-" * 40)
    
    callers = []
    for xref in idautils.XrefsTo(target_addr):
        if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(caller_func.start_ea)
                callers.append({
                    "name": caller_name,
                    "addr": caller_func.start_ea,
                    "call_site": xref.frm
                })
                
                print(f"  {caller_name} at 0x{caller_func.start_ea:05X} (calls from 0x{xref.frm:05X})")
    
    return callers

def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - TERRAIN SYSTEM DISCOVERY")
    print("=" * 80)
    
    # Discover all terrain functions
    terrain_funcs = find_terrain_functions()
    
    # Analyze key functions
    key_funcs = analyze_key_terrain_functions()
    
    # Find data structures
    data_structs = find_terrain_data_structures()
    
    # Find entry points
    callers = find_view_terrain_callers()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Terrain functions discovered: {len(terrain_funcs)}")
    print(f"Key functions analyzed: {len(key_funcs)}")
    print(f"Data structures found: {len(data_structs)}")
    print(f"Entry point callers: {len(callers)}")
    
    # Save results
    output = {
        "terrain_functions": terrain_funcs,
        "key_functions": key_funcs,
        "data_structures": data_structs,
        "entry_point_callers": callers
    }
    
    output_path = "terrain_system_discovery.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
