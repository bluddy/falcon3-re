"""
Analyze HUD system - r32_hud_phase_dispatch and related functions.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\hud_system_analysis.json"

def analyze_func(name):
    addr = idc.get_name_ea_simple(name)
    if addr == idc.BADADDR:
        return {"error": "not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": "no function"}
    
    # Get calls (limit to 30)
    calls = []
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 30:
        if idc.print_insn_mnem(ea) == "call":
            disasm = idc.GetDisasm(ea)
            target_name = disasm.split()[-1] if ' ' in disasm else "unknown"
            calls.append(target_name)
            count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(addr, 0))
    callers = {}
    for xref in xrefs[:20]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers[caller_name] = callers.get(caller_name, 0) + 1
    
    return {
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "call_count": count,
        "calls": calls,
        "xref_count": len(xrefs),
        "callers": callers
    }

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "r32_hud_phase_dispatch": analyze_func("r32_hud_phase_dispatch"),
            "hud_map_overlay_frame": analyze_func("hud_map_overlay_frame"),
            "hud_map_overlay_step": analyze_func("hud_map_overlay_step")
        }
        
        # Search for more HUD functions
        hud_funcs = []
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            if "hud" in name.lower():
                func = idaapi.get_func(func_ea)
                hud_funcs.append({
                    "address": hex(func_ea),
                    "name": name,
                    "size": func.end_ea - func.start_ea if func else 0
                })
                if len(hud_funcs) >= 30:
                    break
        
        result["hud_functions_found"] = len(hud_funcs)
        result["hud_functions"] = hud_funcs
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
