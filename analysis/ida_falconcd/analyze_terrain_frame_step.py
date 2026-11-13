"""
Analyze view_terrain_frame_step - the main terrain rendering coordinator.

This is the terrain equivalent of hud_readout_render.
Called from main_frame_update_loop every frame.
"""

import idc
import idaapi
import idautils
import json

def analyze_terrain_frame_step():
    """Analyze the main terrain rendering function."""
    
    func_addr = 0x31CA1
    func = idaapi.get_func(func_addr)
    
    if not func:
        print("ERROR: Function not found")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("=" * 80)
    print(f"ANALYZING: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("=" * 80)
    
    # Get full disassembly
    print("\nDISASSEMBLY (first 100 instructions):")
    print("-" * 80)
    
    ea = func.start_ea
    disasm_lines = []
    count = 0
    max_show = 100
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({"addr": ea, "disasm": disasm})
        
        if count < max_show:
            print(f"0x{ea:05X}  {disasm}")
        
        ea = idc.next_head(ea)
        count += 1
    
    if count > max_show:
        print(f"... ({count - max_show} more instructions)")
    
    # Analyze function calls
    print("\n" + "-" * 80)
    print("FUNCTION CALLS:")
    print("-" * 80)
    
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                    target_ea = xref.to
                    target_name = idc.get_func_name(target_ea)
                    
                    calls.append({
                        "addr": ea,
                        "target": target_ea,
                        "target_name": target_name
                    })
                    
                    # Highlight terrain-related calls
                    is_terrain = any(kw in target_name.lower() for kw in ["terrain", "tile", "height", "ground", "view"])
                    marker = "★" if is_terrain else " "
                    
                    print(f"  {marker} 0x{ea:05X} → {target_name} at 0x{target_ea:05X}")
        
        ea = idc.next_head(ea)
    
    print(f"\nTotal calls: {len(calls)}")
    
    # Look for data references
    print("\n" + "-" * 80)
    print("DATA REFERENCES (first 30):")
    print("-" * 80)
    
    data_refs = []
    ea = func.start_ea
    while ea < func.end_ea:
        for xref in idautils.DataRefsFrom(ea):
            ref_name = idc.get_name(xref)
            if not ref_name:
                ref_name = f"data_{xref:05X}"
            
            data_refs.append({
                "addr": ea,
                "target": xref,
                "name": ref_name
            })
            
            if len(data_refs) <= 30:
                disasm = idc.generate_disasm_line(ea, 0)
                print(f"  0x{ea:05X}: {disasm}")
        
        ea = idc.next_head(ea)
    
    if len(data_refs) > 30:
        print(f"  ... ({len(data_refs) - 30} more data references)")
    
    print(f"\nTotal data refs: {len(data_refs)}")
    
    # Find who calls this
    print("\n" + "-" * 80)
    print("CALLERS:")
    print("-" * 80)
    
    callers = []
    for xref in idautils.XrefsTo(func_addr):
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
    
    return {
        "name": func_name,
        "address": func_addr,
        "size": func_size,
        "disassembly": disasm_lines,
        "calls": calls,
        "data_refs": data_refs,
        "callers": callers,
        "instruction_count": count,
        "call_count": len(calls),
        "data_ref_count": len(data_refs)
    }

def analyze_terrain_subsystems():
    """Categorize terrain functions by subsystem."""
    
    print("\n" + "=" * 80)
    print("TERRAIN SUBSYSTEM CATEGORIZATION")
    print("=" * 80)
    
    categories = {
        "height_lookup": [],
        "tile_management": [],
        "attribute_system": [],
        "rendering": [],
        "vm_system": [],  # Virtual memory/streaming
        "grid_system": [],
        "frame_update": []
    }
    
    # Categorize based on name patterns
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_name_lower = func_name.lower()
        
        if "terrain" not in func_name_lower and "tile" not in func_name_lower and "height" not in func_name_lower:
            continue
        
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_size = func.end_ea - func.start_ea
        
        func_info = {
            "name": func_name,
            "addr": func_ea,
            "size": func_size
        }
        
        # Categorize
        if "height" in func_name_lower or "lookup" in func_name_lower:
            categories["height_lookup"].append(func_info)
        elif "tile" in func_name_lower:
            categories["tile_management"].append(func_info)
        elif "attr" in func_name_lower:
            categories["attribute_system"].append(func_info)
        elif "draw" in func_name_lower or "render" in func_name_lower or "project" in func_name_lower:
            categories["rendering"].append(func_info)
        elif "vm" in func_name_lower or "stream" in func_name_lower or "buffer" in func_name_lower:
            categories["vm_system"].append(func_info)
        elif "grid" in func_name_lower or "scan" in func_name_lower:
            categories["grid_system"].append(func_info)
        elif "frame" in func_name_lower or "step" in func_name_lower or "update" in func_name_lower:
            categories["frame_update"].append(func_info)
    
    # Print summary
    for cat_name, funcs in categories.items():
        if funcs:
            print(f"\n{cat_name.upper().replace('_', ' ')} ({len(funcs)} functions):")
            for func_info in funcs[:10]:  # Show first 10
                print(f"  {func_info['name']:50} 0x{func_info['addr']:05X} ({func_info['size']:4} bytes)")
            
            if len(funcs) > 10:
                print(f"  ... ({len(funcs) - 10} more)")
    
    return categories

def main():
    """Main analysis."""
    
    print("=" * 80)
    print("FALCON 3.0 - TERRAIN FRAME COORDINATOR ANALYSIS")
    print("=" * 80)
    
    # Analyze main coordinator
    frame_step_result = analyze_terrain_frame_step()
    
    # Categorize subsystems
    subsystems = analyze_terrain_subsystems()
    
    # Save results
    output = {
        "view_terrain_frame_step": frame_step_result,
        "subsystems": subsystems
    }
    
    output_path = "terrain_frame_step_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
