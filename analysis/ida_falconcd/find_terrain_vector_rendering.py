"""
Falcon 3.0 Terrain Vector Rendering Discovery
Find functions that render coastlines, roads, and rivers
"""

import idc
import idaapi
import idautils
import json

def analyze_line_drawing_functions():
    """Analyze the 30+ line drawing functions to find terrain vector renderers"""
    
    print("=" * 80)
    print("TERRAIN VECTOR RENDERING DISCOVERY")
    print("=" * 80)
    
    # Known line drawing functions from previous analysis
    line_functions = [
        ('line_draw_441e', 0x28B08),
        ('line_table_scan_slope', 0x292F4),
        ('line_table_scan_dispatch', 0x29435),
        ('line_table_scan_20', 0x29468),
        ('line_table_scan_40', 0x29521),
    ]
    
    # Search for functions with "coast", "river", "road", "vector", "polyline", "polygon"
    terrain_patterns = ['coast', 'river', 'road', 'vector', 'poly', 'line', 'edge', 'shore']
    
    print("\n1. SEARCHING FOR TERRAIN VECTOR FUNCTIONS")
    print("-" * 80)
    
    terrain_vector_funcs = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        name_lower = func_name.lower()
        
        # Look for terrain-related patterns
        for pattern in terrain_patterns:
            if pattern in name_lower:
                size = idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
                terrain_vector_funcs.append({
                    'name': func_name,
                    'address': hex(func_ea),
                    'size': size,
                    'pattern': pattern
                })
                print(f"  {hex(func_ea):12s} {func_name:50s} ({size:4d} bytes) - matched '{pattern}'")
                break
    
    print(f"\nFound {len(terrain_vector_funcs)} terrain vector functions")
    
    return terrain_vector_funcs

def find_polygon_fill_functions():
    """Find polygon fill and clipping functions"""
    
    print("\n2. POLYGON RENDERING FUNCTIONS")
    print("-" * 80)
    
    poly_patterns = ['poly', 'fill', 'clip', 'raster', 'scan', 'edge']
    
    poly_funcs = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        name_lower = func_name.lower()
        
        # Look for polygon-related AND rendering-related
        if any(p in name_lower for p in ['poly', 'fill', 'clip']) and \
           any(p in name_lower for p in ['draw', 'render', 'raster']):
            size = idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            poly_funcs.append({
                'name': func_name,
                'address': hex(func_ea),
                'size': size
            })
            print(f"  {hex(func_ea):12s} {func_name:50s} ({size:4d} bytes)")
    
    # Also look for tile_clip_draw which we found earlier
    tile_clip_draw = 0x14200
    if idc.get_func_attr(tile_clip_draw, idc.FUNCATTR_START) != idc.BADADDR:
        func_name = idc.get_func_name(tile_clip_draw)
        size = idc.get_func_attr(tile_clip_draw, idc.FUNCATTR_END) - tile_clip_draw
        print(f"\n  Known: {hex(tile_clip_draw):12s} {func_name:50s} ({size:4d} bytes)")
    
    print(f"\nFound {len(poly_funcs)} polygon rendering functions")
    
    return poly_funcs

def trace_terrain_strip_render_calls():
    """Trace what hud_terrain_strip_render calls to find vector rendering"""
    
    print("\n3. TRACING hud_terrain_strip_render CALLS")
    print("-" * 80)
    
    terrain_strip_render = 0x3718D
    func_end = idc.get_func_attr(terrain_strip_render, idc.FUNCATTR_END)
    
    print(f"Analyzing hud_terrain_strip_render @ {hex(terrain_strip_render)}")
    print(f"Size: {func_end - terrain_strip_render} bytes\n")
    
    calls = []
    
    ea = terrain_strip_render
    while ea < func_end:
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR:
                target_name = idc.get_func_name(target)
                if target_name:
                    calls.append({
                        'address': hex(ea),
                        'target': hex(target),
                        'name': target_name
                    })
                    
                    # Check if this might be vector rendering
                    name_lower = target_name.lower()
                    if any(p in name_lower for p in ['line', 'poly', 'vector', 'edge', 'coast', 'road', 'river']):
                        print(f"  *** {hex(ea):12s} calls {target_name:40s} @ {hex(target)}")
                    else:
                        print(f"      {hex(ea):12s} calls {target_name:40s} @ {hex(target)}")
        
        ea = idc.next_head(ea)
    
    print(f"\nTotal function calls: {len(calls)}")
    
    return calls

def find_isl_data_loader():
    """Find function that loads ISL theater files (coastline data)"""
    
    print("\n4. SEARCHING FOR ISL FILE LOADER")
    print("-" * 80)
    
    # Search for "ISL" string references
    isl_refs = []
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            # Look for string "ISL" or ".ISL"
            flags = idc.get_full_flags(head)
            if idc.is_strlit(flags):
                str_val = idc.get_strlit_contents(head)
                if str_val and b'ISL' in str_val.upper():
                    print(f"  String @ {hex(head)}: {str_val}")
                    
                    # Find xrefs to this string
                    for xref in idautils.XrefsTo(head):
                        func_ea = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
                        if func_ea != idc.BADADDR:
                            func_name = idc.get_func_name(func_ea)
                            isl_refs.append({
                                'string': str_val,
                                'string_addr': hex(head),
                                'xref_addr': hex(xref.frm),
                                'function': func_name,
                                'func_addr': hex(func_ea)
                            })
                            print(f"    Used by {func_name} @ {hex(func_ea)}")
    
    return isl_refs

def analyze_terrain_rendering_pipeline():
    """Try to understand the complete terrain rendering pipeline"""
    
    print("\n5. TERRAIN RENDERING PIPELINE RECONSTRUCTION")
    print("-" * 80)
    
    # Start from the main terrain frame step
    terrain_frame_step = 0x36547  # view_terrain_frame_step
    
    print(f"Starting from view_terrain_frame_step @ {hex(terrain_frame_step)}")
    
    # Get all functions it calls
    func_end = idc.get_func_attr(terrain_frame_step, idc.FUNCATTR_END)
    
    calls = []
    ea = terrain_frame_step
    while ea < func_end:
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR:
                target_name = idc.get_func_name(target)
                if target_name:
                    calls.append(target_name)
                    print(f"  → {target_name}")
        ea = idc.next_head(ea)
    
    return calls

def find_lod_switching_logic():
    """Find LOD (Level of Detail) switching logic"""
    
    print("\n6. LOD SWITCHING LOGIC")
    print("-" * 80)
    
    # We know LOD table is at ds:0x7A0
    lod_table_addr = 0x7A0
    
    print(f"LOD table at ds:{hex(lod_table_addr)}")
    
    # Find all xrefs to this address in data segment
    xrefs = []
    
    # Search for references to 0x7A0
    for func_ea in idautils.Functions():
        func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
        ea = func_ea
        
        while ea < func_end:
            # Look for references to 0x7A0
            operands = [idc.print_operand(ea, i) for i in range(6)]
            
            if any('7A0h' in op or '[7A0h]' in op for op in operands):
                func_name = idc.get_func_name(func_ea)
                disasm = idc.GetDisasm(ea)
                xrefs.append({
                    'function': func_name,
                    'address': hex(ea),
                    'disasm': disasm
                })
                print(f"  {hex(ea):12s} {func_name:40s}: {disasm}")
            
            ea = idc.next_head(ea)
    
    print(f"\nFound {len(xrefs)} references to LOD table")
    
    return xrefs

if __name__ == '__main__':
    idaapi.auto_wait()
    
    results = {
        'terrain_vector_funcs': analyze_line_drawing_functions(),
        'polygon_funcs': find_polygon_fill_functions(),
        'terrain_strip_calls': trace_terrain_strip_render_calls(),
        'isl_loaders': find_isl_data_loader(),
        'pipeline': analyze_terrain_rendering_pipeline(),
        'lod_refs': find_lod_switching_logic()
    }
    
    # Save results
    with open('terrain_vector_rendering.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("TERRAIN VECTOR RENDERING DISCOVERY COMPLETE")
    print("=" * 80)
    print(f"Results saved to terrain_vector_rendering.json")
