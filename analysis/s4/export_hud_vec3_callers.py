"""
Export detailed analysis of HUD functions that call fixed_vec3_accumulate_a.

DISCOVERY: Found 3 HUD functions that use 3D projection:
- hud_ai_target_tracking_draw (0x425a2)
- hud_state_table_processor (0x45074)
- hud_rowlist_timer_step (0x47bde)

These are the HUD targeting system functions (30K calls/frame mentioned in rendering.md).
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\hud_vec3_tracking_system.json"

def export_function_detailed(addr):
    """Export complete function with call graph."""
    if addr == idc.BADADDR:
        return {"error": "invalid address"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": "no function"}
    
    name = idc.get_func_name(addr)
    lines = []
    calls = []
    vec3_calls = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            
            if target_name:
                calls.append({
                    "offset": ea - func.start_ea,
                    "target": target_name,
                    "address": hex(target)
                })
                
                # Track vec3 accumulator calls specifically
                if "vec3" in target_name.lower() or "accum" in target_name.lower():
                    vec3_calls.append({
                        "offset": ea - func.start_ea,
                        "line": disasm,
                        "target": target_name
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(addr, 0))
    callers = []
    for xref in xrefs[:30]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers.append(caller_name)
    
    return {
        "address": hex(addr),
        "name": name,
        "size": func.end_ea - func.start_ea,
        "disassembly": lines,
        "calls": calls,
        "vec3_calls": vec3_calls,
        "vec3_call_count": len(vec3_calls),
        "callers": callers
    }

def find_all_vec3_paths():
    """Find all call paths to fixed_vec3_accumulate_a from HUD system."""
    vec3_addr = idc.get_name_ea_simple("fixed_vec3_accumulate_a")
    if vec3_addr == idc.BADADDR:
        return {"error": "vec3 function not found"}
    
    # First level: direct callers
    direct_callers = []
    for xref in idautils.XrefsTo(vec3_addr, 0):
        func = idaapi.get_func(xref.frm)
        if func:
            name = idc.get_func_name(func.start_ea)
            if "hud" in name.lower() or "track" in name.lower() or "target" in name.lower():
                direct_callers.append({
                    "name": name,
                    "address": hex(func.start_ea)
                })
    
    # Second level: who calls the direct callers?
    call_chains = []
    for caller in direct_callers[:10]:
        addr = idc.get_name_ea_simple(caller["name"])
        if addr != idc.BADADDR:
            second_level = []
            for xref in idautils.XrefsTo(addr, 0):
                func = idaapi.get_func(xref.frm)
                if func:
                    second_name = idc.get_func_name(func.start_ea)
                    second_level.append(second_name)
            
            call_chains.append({
                "direct_caller": caller["name"],
                "called_by": second_level[:20]
            })
    
    return {
        "direct_callers": direct_callers,
        "call_chains": call_chains
    }

def main():
    try:
        idaapi.auto_wait()
        
        # The 3 HUD functions that use 3D projection
        target_funcs = [
            "hud_ai_target_tracking_draw",   # 0x425a2
            "hud_state_table_processor",      # 0x45074
            "hud_rowlist_timer_step"          # 0x47bde
        ]
        
        result = {
            "discovery": "HUD targeting system uses same 3D projection as tactical map",
            "vec3_accumulator": "fixed_vec3_accumulate_a (0x22C91, 68 bytes)",
            "estimated_calls_per_frame": "~30,000 (from rendering.md)",
            "functions": {}
        }
        
        for func_name in target_funcs:
            addr = idc.get_name_ea_simple(func_name)
            if addr != idc.BADADDR:
                result["functions"][func_name] = export_function_detailed(addr)
        
        # Find complete call graph
        result["call_graph"] = find_all_vec3_paths()
        
        # Check if HUD uses farobj system
        farobj_funcs = []
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            if ("hud" in name.lower() or "track" in name.lower()) and "farobj" in name.lower():
                farobj_funcs.append({
                    "name": name,
                    "address": hex(func_ea)
                })
        
        result["hud_farobj_functions"] = farobj_funcs[:20]
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Exported HUD vec3 tracking system to {OUTPUT_FILE}")
        print(f"Found {len(target_funcs)} functions using 3D projection")
        print(f"Found {len(farobj_funcs)} HUD+farobj functions")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
