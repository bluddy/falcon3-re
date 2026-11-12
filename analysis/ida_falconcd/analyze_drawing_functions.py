"""
Simple analysis of key drawing functions:
- font_glyph_advance_11860 (62 bytes) - likely text drawing
- line_draw_441e (409 bytes) - likely line/shape drawing
- tile_clip_draw_14200 (106 bytes) - likely filled rectangle drawing
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\drawing_functions_analysis.json"

def analyze_function_simple(func_name):
    """Get basic analysis of a function."""
    idaapi.auto_wait()
    
    addr = idc.get_name_ea_simple(func_name)
    if addr == idc.BADADDR:
        return {"name": func_name, "error": "Not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"name": func_name, "error": "Not a function"}
    
    result = {
        "name": func_name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "disasm_first_20": [],
        "disasm_last_10": [],
        "calls": []
    }
    
    # Get first 20 instructions
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 20:
        result["disasm_first_20"].append({
            "addr": hex(ea),
            "inst": idc.GetDisasm(ea)
        })
        
        # Track calls
        if idc.print_insn_mnem(ea) == "call":
            parts = idc.GetDisasm(ea).split()
            if len(parts) >= 2:
                result["calls"].append(parts[-1])
        
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    # Get last 10 instructions
    instructions = []
    ea = func.start_ea
    while ea < func.end_ea:
        instructions.append(ea)
        ea = idc.next_head(ea, func.end_ea)
    
    for ea in instructions[-10:]:
        result["disasm_last_10"].append({
            "addr": hex(ea),
            "inst": idc.GetDisasm(ea)
        })
    
    return result

# Main execution
try:
    functions_to_analyze = [
        "font_glyph_advance_11860",
        "font_glyph_lookup",
        "line_draw_441e",
        "tile_clip_draw_14200",
        "sprite_offset_dispatch_343e"
    ]
    
    results = []
    
    for func_name in functions_to_analyze:
        print(f"Analyzing {func_name}...")
        analysis = analyze_function_simple(func_name)
        
        if "error" not in analysis:
            print(f"  Size: {analysis['size']} bytes")
            print(f"  First instruction: {analysis['disasm_first_20'][0]['inst']}")
            if analysis["calls"]:
                print(f"  Calls: {', '.join(analysis['calls'][:3])}")
        else:
            print(f"  ERROR: {analysis['error']}")
        
        results.append(analysis)
    
    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"functions": results}, f, indent=2)
    
    print(f"\nSaved: {OUTPUT_FILE}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
