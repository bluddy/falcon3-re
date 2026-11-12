"""
Analyze the actual renderer functions now that we have their addresses.

Cockpit Mode:
- Primary: mode_ratio_dispatch at 0x35971
- Secondary: rect_arg_store at 0x25A56

External View Mode:
- Primary: far_cb_with_args at 0x24DB8 
- Secondary: dispatch_220d4_stub at 0x263F0
"""

import idc
import idaapi
import idautils
import json

def analyze_renderer(func_addr, renderer_name):
    """Analyze a renderer function."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"\n[!] ERROR: No function at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("\n" + "=" * 80)
    print(f"{renderer_name}")
    print(f"Function: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("=" * 80)
    
    # Get disassembly (limit to first 50 instructions)
    print("\nDISASSEMBLY (first 50 instructions):")
    print("-" * 80)
    
    ea = func.start_ea
    disasm_lines = []
    count = 0
    max_show = 50
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({"addr": ea, "disasm": disasm})
        
        if count < max_show:
            print(f"0x{ea:05X}  {disasm}")
        
        ea = idc.next_head(ea)
        count += 1
    
    if count > max_show:
        print(f"... ({count - max_show} more instructions)")
    
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
                    target_ea = xref.to
                    target_name = idc.get_func_name(target_ea) if target_ea else "unknown"
                    
                    calls.append({
                        "addr": ea,
                        "target": target_ea,
                        "target_name": target_name
                    })
        
        ea = idc.next_head(ea)
    
    # Show all calls
    for call in calls:
        print(f"  0x{call['addr']:05X} → {call['target_name']} at 0x{call['target']:05X}")
    
    print(f"\nTotal calls: {len(calls)}")
    
    # Check for known drawing functions
    print("\n" + "-" * 80)
    print("KEY DRAWING FUNCTION REFERENCES:")
    print("-" * 80)
    
    key_funcs = {
        0x11AE7: "font_glyph_advance_11860",
        0x24D64: "far_cb_gated",
        0x24DB8: "far_cb_with_args",
        0x28B08: "line_draw_441e",
        0x14200: "tile_clip_draw_14200"
    }
    
    found = False
    for call in calls:
        if call["target"] in key_funcs:
            print(f"  ✓ Calls {key_funcs[call['target']]}")
            found = True
    
    if not found:
        print("  (no direct calls to known drawing primitives)")
    
    return {
        "renderer_name": renderer_name,
        "function_name": func_name,
        "address": func_addr,
        "size": func_size,
        "disassembly": disasm_lines,
        "calls": calls,
        "call_count": len(calls)
    }

def main():
    """Main analysis."""
    
    print("=" * 80)
    print("FALCON 3.0 - ACTUAL RENDERER FUNCTION ANALYSIS")
    print("=" * 80)
    
    renderers = [
        (0x35971, "COCKPIT PRIMARY: mode_ratio_dispatch"),
        (0x25A56, "COCKPIT SECONDARY: rect_arg_store"),
        (0x24DB8, "EXTERNAL PRIMARY: far_cb_with_args"),
        (0x263F0, "EXTERNAL SECONDARY: dispatch_220d4_stub")
    ]
    
    results = {}
    
    for addr, name in renderers:
        result = analyze_renderer(addr, name)
        if result:
            results[name] = result
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Function: {result['function_name']}")
        print(f"  Address: 0x{result['address']:05X}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Calls: {result['call_count']}")
    
    # Save
    output_path = "actual_renderers_analysis.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
