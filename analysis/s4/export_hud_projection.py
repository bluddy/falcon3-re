"""
Export HUD projection functions to verify they use the same infrastructure
as tactical map (fixed_vec3_accumulate_a, farobj system).

Based on tactical map analysis, we expect:
- HUD tracking uses fixed_vec3_accumulate_a (30K calls/frame)
- HUD should use farobj_vec3_accum_b_ret wrapper
- HUD drawing should dispatch via function pointers
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\hud_projection_analysis.json"

def export_function(addr):
    """Export function disassembly with analysis."""
    if addr == idc.BADADDR:
        return {"error": "invalid address"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": "no function"}
    
    name = idc.get_func_name(addr)
    lines = []
    calls = []
    vec3_accum_calls = 0
    farobj_calls = 0
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        # Check for vec3 accumulator calls
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            
            if target_name:
                calls.append(target_name)
                
                # Count key functions
                if "vec3" in target_name.lower() or "accum" in target_name.lower():
                    vec3_accum_calls += 1
                if "farobj" in target_name.lower():
                    farobj_calls += 1
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "address": hex(addr),
        "name": name,
        "size": func.end_ea - func.start_ea,
        "disassembly": lines[:100],  # First 100 lines
        "calls": calls[:30],
        "vec3_accum_calls": vec3_accum_calls,
        "farobj_calls": farobj_calls,
        "uses_3d_projection": vec3_accum_calls > 0 or farobj_calls > 0
    }

def find_vec3_accumulator_callers():
    """Find all functions that call fixed_vec3_accumulate_a."""
    vec3_addr = idc.get_name_ea_simple("fixed_vec3_accumulate_a")
    if vec3_addr == idc.BADADDR:
        return []
    
    callers = []
    for xref in idautils.XrefsTo(vec3_addr, 0):
        caller_addr = xref.frm
        func = idaapi.get_func(caller_addr)
        if func:
            caller_name = idc.get_func_name(func.start_ea)
            if "hud" in caller_name.lower():
                callers.append({
                    "name": caller_name,
                    "address": hex(func.start_ea),
                    "size": func.end_ea - func.start_ea
                })
    
    return callers

def main():
    try:
        idaapi.auto_wait()
        
        # Key HUD functions from previous analysis
        hud_funcs = [
            "hud_track_project_draw",       # 0x4227a - likely uses projection
            "hud_crosshair_ratio_draw",     # 0x3a771 - crosshair drawing
            "hud_terrain_strip_render",     # 0x3718d - terrain rendering
            "hud_map_overlay_frame",        # 0x3a6b1 - map overlay (known to call map_view_project_pipeline)
            "hud_track_marker_draw",        # 0x42686 - track markers
            "hud_draw_chain_step"           # 0x35bce - main drawing chain
        ]
        
        result = {
            "analysis_goal": "Verify HUD uses same 3D projection as tactical map",
            "functions": {}
        }
        
        for func_name in hud_funcs:
            addr = idc.get_name_ea_simple(func_name)
            if addr != idc.BADADDR:
                result["functions"][func_name] = export_function(addr)
        
        # Find HUD functions that call vec3 accumulator
        result["vec3_accumulator_callers"] = find_vec3_accumulator_callers()
        
        # Check for farobj_vec3_accum_b_ret wrapper usage
        wrapper_addr = idc.get_name_ea_simple("farobj_vec3_accum_b_ret")
        if wrapper_addr != idc.BADADDR:
            wrapper_xrefs = []
            for xref in idautils.XrefsTo(wrapper_addr, 0):
                caller_name = idc.get_func_name(xref.frm)
                if caller_name and "hud" in caller_name.lower():
                    wrapper_xrefs.append(caller_name)
            result["farobj_vec3_accum_wrapper_hud_callers"] = wrapper_xrefs[:20]
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Exported HUD projection analysis to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
