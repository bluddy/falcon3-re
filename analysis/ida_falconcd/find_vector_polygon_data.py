"""
Find vector and polygon data storage for roads/rivers/coastlines.

We need to locate:
1. Road/river coordinate data (vector line lists)
2. Coastline polygon vertex data
3. Color palette / height->color mapping
4. LOD table structure
"""

import idc
import idaapi
import idautils
import json

def analyze_line_drawing_functions():
    """Analyze key line drawing functions to find data structures."""
    
    print("=" * 80)
    print("ANALYZING LINE DRAWING FUNCTIONS (roads/rivers)")
    print("=" * 80)
    
    # Key line functions
    functions = [
        (0x28B08, "line_draw_441e", "Main line drawer (Bresenham)"),
        (0x27A20, "anim_line_object_draw", "Animated line objects"),
        (0x28E50, "line_record_draw_loop", "Line record loop"),
    ]
    
    results = {}
    
    for addr, name, desc in functions:
        print(f"\n[*] {name} at 0x{addr:05X}")
        print(f"    {desc}")
        print("-" * 40)
        
        func = idaapi.get_func(addr)
        if not func:
            print("    ERROR: Function not found")
            continue
        
        # Look for data references in first 50 instructions
        ea = func.start_ea
        count = 0
        data_refs = []
        
        while ea < func.end_ea and count < 50:
            # Check for data references
            for xref in idautils.DataRefsFrom(ea):
                ref_name = idc.get_name(xref)
                if not ref_name:
                    ref_name = f"data_{xref:05X}"
                
                disasm = idc.generate_disasm_line(ea, 0)
                
                data_refs.append({
                    "addr": ea,
                    "target": xref,
                    "name": ref_name,
                    "disasm": disasm
                })
                
                # Print interesting references
                if "table" in ref_name.lower() or "list" in ref_name.lower() or "array" in ref_name.lower():
                    print(f"    ★ 0x{ea:05X}: {disasm}")
                elif len(data_refs) <= 10:
                    print(f"      0x{ea:05X}: {disasm}")
            
            ea = idc.next_head(ea)
            count += 1
        
        results[name] = data_refs
    
    return results

def search_for_line_tables():
    """Search for line table data structures."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR LINE TABLE DATA STRUCTURES")
    print("=" * 80)
    
    # Look for data segments with "line" in name
    line_data = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        # Skip code segments
        seg_type = idc.get_segm_attr(seg_ea, idc.SEGATTR_TYPE)
        if seg_type == 2:  # CODE
            continue
        
        # Search for named data
        ea = seg_ea
        while ea < seg_end:
            name = idc.get_name(ea)
            if name:
                name_lower = name.lower()
                
                # Look for line, vector, road, river, path related data
                if any(kw in name_lower for kw in ["line", "vector", "road", "river", "path", "route"]):
                    next_ea = idc.next_head(ea)
                    size = next_ea - ea if next_ea > ea else 0
                    
                    # Get some bytes
                    sample_bytes = []
                    for i in range(min(16, size)):
                        byte_val = idc.get_wide_byte(ea + i)
                        sample_bytes.append(f"{byte_val:02X}")
                    
                    line_data.append({
                        "name": name,
                        "addr": ea,
                        "size": size,
                        "segment": seg_name,
                        "sample": " ".join(sample_bytes)
                    })
                    
                    print(f"  {name:50} 0x{ea:05X} ({size:5}B) [{seg_name}]")
                    print(f"    Sample: {' '.join(sample_bytes[:8])}")
            
            ea = idc.next_head(ea)
    
    return line_data

def analyze_tile_drawing():
    """Analyze tile drawing to find polygon data."""
    
    print("\n" + "=" * 80)
    print("ANALYZING TILE/POLYGON DRAWING")
    print("=" * 80)
    
    # tile_clip_draw_14200 - draws clipped tiles/polygons
    func_addr = 0x14200
    func = idaapi.get_func(func_addr)
    
    if not func:
        print("ERROR: tile_clip_draw not found")
        return None
    
    func_name = idc.get_func_name(func_addr)
    print(f"\n[*] {func_name} at 0x{func_addr:05X}")
    print("-" * 40)
    
    # Get disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)

def search_for_color_palette():
    """Find color palette and height->color mapping."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR COLOR PALETTE / HEIGHT MAPPING")
    print("=" * 80)
    
    # Look for palette, color, or map data
    keywords = ["palette", "color", "map", "rgb", "vga"]
    
    found = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        seg_type = idc.get_segm_attr(seg_ea, idc.SEGATTR_TYPE)
        
        if seg_type == 2:  # Skip code
            continue
        
        ea = seg_ea
        while ea < seg_end:
            name = idc.get_name(ea)
            if name:
                name_lower = name.lower()
                
                for keyword in keywords:
                    if keyword in name_lower:
                        next_ea = idc.next_head(ea)
                        size = next_ea - ea if next_ea > ea else 0
                        
                        # Sample bytes
                        sample = []
                        for i in range(min(32, size)):
                            sample.append(f"{idc.get_wide_byte(ea + i):02X}")
                        
                        found.append({
                            "name": name,
                            "addr": ea,
                            "size": size,
                            "segment": seg_name
                        })
                        
                        print(f"  {name:50} 0x{ea:05X} ({size:5}B)")
                        print(f"    Sample: {' '.join(sample[:16])}")
                        
                        break
            
            ea = idc.next_head(ea)
    
    return found

def analyze_lod_table():
    """Analyze the LOD scale table at 0x7A0."""
    
    print("\n" + "=" * 80)
    print("ANALYZING LOD SCALE TABLE")
    print("=" * 80)
    
    # We know LOD table is at ds:7A0h
    table_addr = 0x7A0
    
    print(f"LOD table location: ds:0x{table_addr:03X}")
    print("\nTable contents (first 32 words):")
    print("-" * 40)
    
    lod_values = []
    for i in range(32):
        word_val = idc.get_wide_word(table_addr + i * 2)
        lod_values.append(word_val)
        
        if i < 16:  # Show first 16
            print(f"  LOD[{i:2}] = 0x{word_val:04X} ({word_val:5} decimal)")
    
    if len(lod_values) > 16:
        print(f"  ... ({len(lod_values) - 16} more values)")
    
    return lod_values

def find_heightmap_segment():
    """Find and analyze the heightmap segment."""
    
    print("\n" + "=" * 80)
    print("ANALYZING HEIGHTMAP SEGMENT")
    print("=" * 80)
    
    # Heightmap segment pointer at cs:word_11BE8
    # Heightmap data at offset 0x3840
    # Attribute cache at offset 0x1F40
    
    print("Heightmap structure:")
    print("  Segment pointer: cs:word_11BE8")
    print("  Height/Attribute data: offset 0x3840")
    print("  Attribute cache: offset 0x1F40")
    print("  Size: 31×31 cells = 1,922 bytes")
    print("\nFormat:")
    print("  Bits 0-8:  Height value (0-511)")
    print("  Bits 9-15: Terrain attributes")
    
    # Try to read some heightmap values
    print("\nSample heightmap values:")
    print("-" * 40)
    
    # We can't directly access runtime segment, but we can look for references
    # Search for functions that access 0x3840 offset
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        found_heightmap = False
        
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for access to 0x3840 or 0x1F40
            if "3840h" in disasm or "1F40h" in disasm:
                if not found_heightmap:
                    func_name = idc.get_func_name(func_ea)
                    print(f"\n  {func_name} accesses heightmap:")
                    found_heightmap = True
                print(f"    0x{ea:05X}: {disasm}")
            
            ea = idc.next_head(ea)
        
        if found_heightmap:
            break  # Just show first few

def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - FINDING VECTOR/POLYGON/COLOR DATA")
    print("Final push to 100% terrain understanding!")
    print("=" * 80)
    
    # Analyze line drawing functions
    line_results = analyze_line_drawing_functions()
    
    # Search for line table data
    line_data = search_for_line_tables()
    
    # Analyze tile/polygon drawing
    analyze_tile_drawing()
    
    # Search for color palette
    color_data = search_for_color_palette()
    
    # Analyze LOD table
    lod_values = analyze_lod_table()
    
    # Find heightmap references
    find_heightmap_segment()
    
    # Save results
    output = {
        "line_function_data_refs": line_results,
        "line_table_data": line_data,
        "color_palette_data": color_data,
        "lod_table_values": lod_values
    }
    
    output_path = "vector_polygon_data.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
