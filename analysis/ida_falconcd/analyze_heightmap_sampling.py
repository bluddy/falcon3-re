"""
Analyze heightmap sampling and terrain attribute functions.

Now understanding that Falcon 3 uses:
- Heightmap blocks (not textures)
- Pseudo-shading from height differences
- Rectangular block rendering
- Vector roads/rivers
- Polygon coastlines

tile_quad_sample - samples HEIGHT from heightmap
terrain_attr_lookup - gets terrain color/type
"""

import idc
import idaapi
import idautils
import json

def analyze_tile_quad_sample():
    """Analyze heightmap sampling function."""
    
    func_addr = 0x14956
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: No function at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("=" * 80)
    print(f"ANALYZING: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("Understanding: This samples HEIGHT from heightmap, not texture color")
    print("=" * 80)
    
    # Get disassembly
    print("\nDISASSEMBLY:")
    print("-" * 80)
    
    ea = func.start_ea
    disasm_lines = []
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({"addr": ea, "disasm": disasm})
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
    
    # Function calls
    print("\n" + "-" * 80)
    print("FUNCTION CALLS:")
    print("-" * 80)
    
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                    target_name = idc.get_func_name(xref.to)
                    calls.append(target_name)
                    print(f"  → {target_name}")
        ea = idc.next_head(ea)
    
    # Look for terrain/height related calls
    print("\n" + "-" * 80)
    print("TERRAIN-RELATED CALLS:")
    print("-" * 80)
    
    for call in calls:
        if any(kw in call.lower() for kw in ["terrain", "height", "attr", "lookup"]):
            print(f"  ★ {call}")
    
    return {
        "name": func_name,
        "address": func_addr,
        "size": func_size,
        "disassembly": disasm_lines,
        "calls": calls
    }

def analyze_terrain_height_lookup():
    """Analyze the terrain height lookup function."""
    
    func_addr = 0x11D40  # terrain_height_lookup_11cc8
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: No function at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("\n" + "=" * 80)
    print(f"ANALYZING: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("This returns elevation Z given world position X,Y")
    print("=" * 80)
    
    # Get disassembly (first 80 instructions)
    print("\nDISASSEMBLY (first 80 instructions):")
    print("-" * 80)
    
    ea = func.start_ea
    count = 0
    max_show = 80
    
    while ea < func.end_ea and count < max_show:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
        count += 1
    
    if ea < func.end_ea:
        remaining = 0
        while ea < func.end_ea:
            ea = idc.next_head(ea)
            remaining += 1
        print(f"... ({remaining} more instructions)")
    
    # Function calls
    print("\n" + "-" * 80)
    print("FUNCTION CALLS:")
    print("-" * 80)
    
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                    target_name = idc.get_func_name(xref.to)
                    calls.append(target_name)
                    
                    # Highlight important calls
                    is_important = any(kw in target_name.lower() for kw in 
                                      ["tile", "height", "lookup", "attr"])
                    marker = "★" if is_important else " "
                    print(f"  {marker} {target_name}")
        ea = idc.next_head(ea)
    
    return {
        "name": func_name,
        "address": func_addr,
        "size": func_size,
        "calls": calls
    }

def analyze_terrain_attr_lookup():
    """Analyze terrain attribute lookup (color/type)."""
    
    func_addr = 0x12F27  # terrain_attr_lookup_3840
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: No function at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("\n" + "=" * 80)
    print(f"ANALYZING: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("This returns color/type attributes for terrain")
    print("=" * 80)
    
    # Get disassembly (first 80 instructions)
    print("\nDISASSEMBLY (first 80 instructions):")
    print("-" * 80)
    
    ea = func.start_ea
    count = 0
    max_show = 80
    
    while ea < func.end_ea and count < max_show:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
        count += 1
    
    if ea < func.end_ea:
        remaining = 0
        while ea < func.end_ea:
            ea = idc.next_head(ea)
            remaining += 1
        print(f"... ({remaining} more instructions)")
    
    # Function calls
    print("\n" + "-" * 80)
    print("FUNCTION CALLS:")
    print("-" * 80)
    
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                    target_name = idc.get_func_name(xref.to)
                    print(f"  → {target_name}")
        ea = idc.next_head(ea)

def find_vector_drawing_functions():
    """Find functions related to vector roads/rivers."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR VECTOR DRAWING (roads/rivers)")
    print("=" * 80)
    
    # Search for line, vector, road, river
    keywords = ["line", "vector", "road", "river", "strip", "path"]
    
    found = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_name_lower = func_name.lower()
        
        for keyword in keywords:
            if keyword in func_name_lower:
                func = idaapi.get_func(func_ea)
                if func:
                    func_size = func.end_ea - func.start_ea
                    
                    # Count callers
                    callers = 0
                    for xref in idautils.XrefsTo(func_ea):
                        if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                            callers += 1
                    
                    found.append({
                        "name": func_name,
                        "addr": func_ea,
                        "size": func_size,
                        "callers": callers,
                        "keyword": keyword
                    })
                    
                    # Highlight drawing functions
                    is_draw = "draw" in func_name_lower or "render" in func_name_lower
                    marker = "★" if is_draw else " "
                    
                    print(f"  {marker} {func_name:50} 0x{func_ea:05X} ({func_size:4}B, {callers} callers) [{keyword}]")
                
                break
    
    return found

def find_polygon_coastline_functions():
    """Find functions related to polygon coastline rendering."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR POLYGON/COASTLINE RENDERING")
    print("=" * 80)
    
    keywords = ["poly", "polygon", "coast", "shore", "edge", "clip"]
    
    found = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_name_lower = func_name.lower()
        
        for keyword in keywords:
            if keyword in func_name_lower:
                func = idaapi.get_func(func_ea)
                if func:
                    func_size = func.end_ea - func.start_ea
                    
                    found.append({
                        "name": func_name,
                        "addr": func_ea,
                        "size": func_size,
                        "keyword": keyword
                    })
                    
                    is_draw = "draw" in func_name_lower or "render" in func_name_lower
                    marker = "★" if is_draw else " "
                    
                    print(f"  {marker} {func_name:50} 0x{func_ea:05X} ({func_size:4}B) [{keyword}]")
                
                break
    
    return found

def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - HEIGHTMAP & TERRAIN RENDERING ANALYSIS")
    print("Corrected Understanding:")
    print("- No texture mapping (heightmap-based rendering)")
    print("- Rectangular blocks with pseudo-shading")
    print("- Vector roads/rivers")
    print("- Polygon coastlines")
    print("=" * 80)
    
    # Analyze heightmap sampling
    tile_sample = analyze_tile_quad_sample()
    
    # Analyze height lookup
    height_lookup = analyze_terrain_height_lookup()
    
    # Analyze attribute lookup
    analyze_terrain_attr_lookup()
    
    # Find vector drawing
    vector_funcs = find_vector_drawing_functions()
    
    # Find polygon/coastline
    polygon_funcs = find_polygon_coastline_functions()
    
    # Save results
    output = {
        "tile_quad_sample": tile_sample,
        "terrain_height_lookup": height_lookup,
        "vector_functions": vector_funcs,
        "polygon_functions": polygon_funcs
    }
    
    output_path = "heightmap_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
