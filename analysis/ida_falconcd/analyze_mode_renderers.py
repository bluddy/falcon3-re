"""
Analyze the 4 mode-specific renderer functions.

Cockpit Mode Renderers:
- 0x6331 - Primary renderer (text/sprites/instruments)
- 0x6396 - Secondary renderer (shapes/vectors/targeting)

External View Renderers:
- 0x56F8 - Primary renderer (terrain)
- 0x6D30 - Secondary renderer (vectors/overlays)
"""

import idc
import idaapi
import idautils
import json

def analyze_renderer_function(func_addr, renderer_name):
    """Analyze a renderer function in detail."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"\n[!] ERROR: No function found at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("\n" + "=" * 80)
    print(f"RENDERER: {renderer_name}")
    print(f"Function: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("=" * 80)
    
    # Get disassembly
    print("\nDISASSEMBLY:")
    print("-" * 80)
    
    ea = func.start_ea
    disasm_lines = []
    line_count = 0
    max_lines = 100  # Limit output for readability
    
    while ea < func.end_ea and line_count < max_lines:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({"addr": ea, "disasm": disasm})
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
        line_count += 1
    
    if ea < func.end_ea:
        remaining = 0
        while ea < func.end_ea:
            ea = idc.next_head(ea)
            remaining += 1
        print(f"... ({remaining} more instructions, truncated for brevity)")
    
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
                    target_name = idc.get_func_name(target_ea) if target_ea else "unknown"
                    
                    calls.append({
                        "addr": ea,
                        "target": target_ea,
                        "target_name": target_name
                    })
                    
                    # Only print first 30 calls
                    if len(calls) <= 30:
                        print(f"  0x{ea:05X} → {target_name} at 0x{target_ea:05X}")
        
        ea = idc.next_head(ea)
    
    if len(calls) > 30:
        print(f"  ... ({len(calls) - 30} more calls)")
    
    print(f"\nTotal function calls: {len(calls)}")
    
    # Look for references to known drawing functions
    print("\n" + "-" * 80)
    print("REFERENCES TO KEY DRAWING FUNCTIONS:")
    print("-" * 80)
    
    key_functions = {
        0x11AE7: "font_glyph_advance_11860",
        0x11B6A: "font_glyph_lookup",
        0x24D64: "far_cb_gated",
        0x27877: "far_cb_vector_invoke_entry",
        0x28B08: "line_draw_441e",
        0x14200: "tile_clip_draw_14200",
        0x35B2F: "sprite_offset_dispatch_343e"
    }
    
    found_refs = []
    for call_info in calls:
        if call_info["target"] in key_functions:
            key_name = key_functions[call_info["target"]]
            found_refs.append(call_info)
            print(f"  ✓ Calls {key_name} at 0x{call_info['addr']:05X}")
    
    if not found_refs:
        print("  (no direct calls to known drawing functions)")
    
    # Look for data references
    print("\n" + "-" * 80)
    print("DATA REFERENCES (first 20):")
    print("-" * 80)
    
    data_refs = []
    ea = func.start_ea
    while ea < func.end_ea:
        for xref in idautils.DataRefsFrom(ea):
            # Get the name or value
            ref_name = idc.get_name(xref)
            if not ref_name:
                ref_name = f"data_{xref:05X}"
            
            data_refs.append({
                "addr": ea,
                "target": xref,
                "name": ref_name
            })
            
            if len(data_refs) <= 20:
                disasm = idc.generate_disasm_line(ea, 0)
                print(f"  0x{ea:05X}: {disasm}")
        
        ea = idc.next_head(ea)
    
    if len(data_refs) > 20:
        print(f"  ... ({len(data_refs) - 20} more data references)")
    
    print(f"\nTotal data references: {len(data_refs)}")
    
    # Who calls this renderer?
    print("\n" + "-" * 80)
    print("CALLERS (who calls this renderer?):")
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
    
    if not callers:
        # Check if this is called via callback pointer
        print("  (no direct callers - likely called via cs:dword_35924 or cs:dword_35920)")
    
    return {
        "name": func_name,
        "renderer_name": renderer_name,
        "address": func_addr,
        "size": func_size,
        "disassembly": disasm_lines,
        "function_calls": calls,
        "key_function_refs": found_refs,
        "data_refs": data_refs,
        "callers": callers,
        "call_count": len(calls),
        "data_ref_count": len(data_refs)
    }

def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - MODE-SPECIFIC RENDERER ANALYSIS")
    print("Completing HUD System to 100%")
    print("=" * 80)
    
    renderers = [
        (0x6331, "Cockpit Primary Renderer (text/sprites/instruments)"),
        (0x6396, "Cockpit Secondary Renderer (shapes/vectors/targeting)"),
        (0x56F8, "External Primary Renderer (terrain)"),
        (0x6D30, "External Secondary Renderer (vectors/overlays)")
    ]
    
    results = {}
    
    for addr, name in renderers:
        result = analyze_renderer_function(addr, name)
        if result:
            results[name] = result
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Function: {result['name']} at 0x{result['address']:05X}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Function calls: {result['call_count']}")
        print(f"  Data references: {result['data_ref_count']}")
        print(f"  Direct callers: {len(result['callers'])}")
    
    # Save results
    output_path = "mode_renderers_analysis.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
