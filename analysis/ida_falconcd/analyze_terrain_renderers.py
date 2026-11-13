"""
Deep analysis of the 3 core terrain rendering functions.

1. hud_terrain_strip_render at 0x3718D (988 bytes) - Main coordinator
2. tile_strip_project_draw at 0x361FC (331 bytes) - 3D projection
3. tile_strip_sample_draw at 0x16060 (126 bytes) - Pixel output

These are the heart of the terrain rendering system.
"""

import idc
import idaapi
import idautils
import json

def analyze_large_function(func_addr, func_name_hint):
    """Analyze a large function in detail."""
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"ERROR: No function at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print("=" * 80)
    print(f"ANALYZING: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("=" * 80)
    
    # Get disassembly (limit output for large functions)
    print("\nDISASSEMBLY (first 150 instructions):")
    print("-" * 80)
    
    ea = func.start_ea
    disasm_lines = []
    count = 0
    max_show = 150
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({"addr": ea, "disasm": disasm})
        
        if count < max_show:
            print(f"0x{ea:05X}  {disasm}")
        
        ea = idc.next_head(ea)
        count += 1
    
    if count > max_show:
        print(f"... ({count - max_show} more instructions)")
    
    # Analyze loops (look for jmp backwards)
    print("\n" + "-" * 80)
    print("LOOP STRUCTURES:")
    print("-" * 80)
    
    loops = []
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # Look for backward jumps (loops)
        if mnem in ["jmp", "jl", "jle", "jg", "jge", "jz", "jnz", "jb", "jbe", "ja", "jae"]:
            # Get jump target
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_JN or xref.type == idaapi.fl_JF:
                    target = xref.to
                    
                    # Backward jump = loop
                    if target < ea:
                        loop_size = ea - target
                        loops.append({
                            "loop_start": target,
                            "loop_end": ea,
                            "size": loop_size,
                            "condition": mnem
                        })
                        
                        print(f"  Loop: 0x{target:05X} → 0x{ea:05X} ({loop_size} bytes, condition: {mnem})")
        
        ea = idc.next_head(ea)
    
    print(f"\nTotal loops detected: {len(loops)}")
    
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
        
        ea = idc.next_head(ea)
    
    # Group calls by target
    call_counts = {}
    for call in calls:
        target = call["target_name"]
        if target not in call_counts:
            call_counts[target] = []
        call_counts[target].append(call["addr"])
    
    # Sort by frequency
    sorted_calls = sorted(call_counts.items(), key=lambda x: len(x[1]), reverse=True)
    
    print("\nCalls by frequency:")
    for target_name, call_addrs in sorted_calls[:20]:  # Top 20
        # Highlight terrain/tile/draw functions
        is_important = any(kw in target_name.lower() for kw in 
                          ["terrain", "tile", "draw", "project", "render", "strip", "sample"])
        marker = "★" if is_important else " "
        
        print(f"  {marker} {len(call_addrs):2}x {target_name}")
        
        # Show first few call sites for important functions
        if is_important and len(call_addrs) <= 3:
            for addr in call_addrs:
                print(f"       └─ 0x{addr:05X}")
    
    if len(sorted_calls) > 20:
        print(f"  ... ({len(sorted_calls) - 20} more unique functions)")
    
    print(f"\nTotal calls: {len(calls)} to {len(call_counts)} unique functions")
    
    # Look for important data references
    print("\n" + "-" * 80)
    print("KEY DATA REFERENCES:")
    print("-" * 80)
    
    # Look for coordinate/viewport data
    coord_refs = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for common coordinate/viewport variables
        if any(pattern in disasm for pattern in ["6F8h", "6FAh", "6FCh", "6FEh", "700h", "702h"]):
            coord_refs.append({
                "addr": ea,
                "disasm": disasm
            })
            
            if len(coord_refs) <= 10:
                print(f"  0x{ea:05X}: {disasm}")
        
        ea = idc.next_head(ea)
    
    if len(coord_refs) > 10:
        print(f"  ... ({len(coord_refs) - 10} more coordinate references)")
    
    # Identify function purpose from calls
    print("\n" + "-" * 80)
    print("FUNCTION PURPOSE ANALYSIS:")
    print("-" * 80)
    
    purpose_hints = []
    
    if any("project" in name.lower() for name in call_counts.keys()):
        purpose_hints.append("3D projection")
    if any("draw" in name.lower() for name in call_counts.keys()):
        purpose_hints.append("Drawing/rendering")
    if any("tile" in name.lower() for name in call_counts.keys()):
        purpose_hints.append("Tile management")
    if any("strip" in name.lower() for name in call_counts.keys()):
        purpose_hints.append("Strip processing")
    if len(loops) > 3:
        purpose_hints.append(f"Complex iteration ({len(loops)} loops)")
    
    if purpose_hints:
        print("  This function appears to handle:")
        for hint in purpose_hints:
            print(f"    • {hint}")
    
    return {
        "name": func_name,
        "address": func_addr,
        "size": func_size,
        "instruction_count": count,
        "disassembly": disasm_lines,
        "calls": calls,
        "call_counts": {name: len(addrs) for name, addrs in call_counts.items()},
        "loops": loops,
        "purpose_hints": purpose_hints
    }

def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - TERRAIN RENDERING CORE ANALYSIS")
    print("=" * 80)
    
    renderers = [
        (0x3718D, "hud_terrain_strip_render", "Main terrain renderer"),
        (0x361FC, "tile_strip_project_draw", "3D projection to 2D"),
        (0x16060, "tile_strip_sample_draw", "Pixel sampling and output")
    ]
    
    results = {}
    
    for addr, name_hint, description in renderers:
        print(f"\n{'='*80}")
        print(f"TARGET: {name_hint} - {description}")
        print(f"{'='*80}\n")
        
        result = analyze_large_function(addr, name_hint)
        if result:
            results[name_hint] = result
            results[name_hint]["description"] = description
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("COMPARATIVE SUMMARY")
    print("=" * 80)
    
    for name_hint, result in results.items():
        print(f"\n{name_hint}:")
        print(f"  Size: {result['size']} bytes")
        print(f"  Instructions: ~{result['instruction_count']}")
        print(f"  Function calls: {len(result['calls'])}")
        print(f"  Unique functions: {len(result['call_counts'])}")
        print(f"  Loops: {len(result['loops'])}")
        print(f"  Purpose: {', '.join(result['purpose_hints'])}")
    
    # Save results
    output_path = "terrain_renderers_analysis.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
