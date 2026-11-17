"""
Analyze Falcon 3.0 cockpit instrument system.

HYPOTHESIS: Cockpit instruments use the same 3D projection infrastructure as HUD and tactical map.

KNOWN STARTING POINTS:
- viewmode3_vector_project (0x2F535, 91B) - cockpit view vectors
- state_word_44d3d_get() returns 3 for cockpit mode
- DS:0x62D4 - cockpit vector data segment

SEARCH FOR:
1. Functions with "cockpit" in name
2. Functions that call view_projection or fixed_vec3_accumulate_a
3. Gauge update functions (airspeed, altitude, heading, etc.)
4. Instrument panel rendering
5. MFD (Multi-Function Display) rendering
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\cockpit_system_analysis.json"

def find_cockpit_functions():
    """Find all functions with cockpit-related names."""
    cockpit_funcs = []
    keywords = ["cockpit", "instrument", "gauge", "panel", "mfd", "avionics", 
                "airspeed", "altitude", "heading", "pitch", "roll", "compass",
                "vsi", "aoa", "indicator", "dial", "tape", "ladder"]
    
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for keyword in keywords:
                if keyword in name_lower:
                    func = idaapi.get_func(func_ea)
                    cockpit_funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": keyword
                    })
                    break
    
    return cockpit_funcs

def analyze_viewmode3():
    """Analyze viewmode3_vector_project and related functions."""
    func_addr = idc.get_name_ea_simple("viewmode3_vector_project")
    if func_addr == idc.BADADDR:
        return {"error": "function not found"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    # Export disassembly
    lines = []
    calls = []
    data_refs = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        # Track calls
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            if target_name:
                calls.append({
                    "offset": hex(ea - func.start_ea),
                    "target": target_name,
                    "address": hex(target)
                })
        
        # Track data references
        if idc.print_insn_mnem(ea) == "mov":
            for i in range(2):
                op = idc.print_operand(ea, i)
                if ":" in op and "ds:" in op.lower():
                    data_refs.append({
                        "offset": hex(ea - func.start_ea),
                        "reference": op,
                        "line": disasm
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Find callers
    xrefs = list(idautils.XrefsTo(func_addr, 0))
    callers = []
    for xref in xrefs[:20]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers.append(caller_name)
    
    return {
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": lines,
        "calls": calls,
        "data_refs": data_refs,
        "callers": callers
    }

def find_view_projection_callers():
    """Find all callers of view_projection (cockpit context)."""
    view_proj_addr = idc.get_name_ea_simple("view_projection")
    if view_proj_addr == idc.BADADDR:
        return []
    
    callers = []
    for xref in idautils.XrefsTo(view_proj_addr, 0):
        func = idaapi.get_func(xref.frm)
        if func:
            name = idc.get_func_name(func.start_ea)
            if name and not any(x in name for x in ["hud_", "map_", "tactical_"]):
                # Likely cockpit or generic 3D
                callers.append({
                    "name": name,
                    "address": hex(func.start_ea),
                    "size": func.end_ea - func.start_ea,
                    "call_site": hex(xref.frm)
                })
    
    return callers[:30]

def find_state_mode_checks():
    """Find functions that check view mode/state for cockpit rendering."""
    # Look for state_word_44d3d_get callers
    state_func = idc.get_name_ea_simple("state_word_44d3d_get")
    if state_func == idc.BADADDR:
        return []
    
    mode_checks = []
    for xref in idautils.XrefsTo(state_func, 0):
        func = idaapi.get_func(xref.frm)
        if func:
            name = idc.get_func_name(func.start_ea)
            
            # Look for comparison with 3 (cockpit mode)
            ea = xref.frm
            end = min(ea + 50, func.end_ea)  # Check next ~10 instructions
            
            while ea < end:
                if idc.print_insn_mnem(ea) == "cmp":
                    op2 = idc.print_operand(ea, 1)
                    if "3" in op2:
                        mode_checks.append({
                            "function": name,
                            "address": hex(func.start_ea),
                            "check_at": hex(ea),
                            "comparison": idc.GetDisasm(ea)
                        })
                        break
                ea = idc.next_head(ea, end)
    
    return mode_checks[:20]

def find_instrument_data_sources():
    """Find global variables that might be instrument data sources."""
    # Common instrument data variable patterns
    patterns = ["airspeed", "altitude", "heading", "pitch", "roll", 
                "throttle", "fuel", "gforce", "aoa", "mach", "vsi"]
    
    data_sources = []
    
    # Search for named variables
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            name = idc.get_name(head)
            if name:
                name_lower = name.lower()
                for pattern in patterns:
                    if pattern in name_lower:
                        data_sources.append({
                            "name": name,
                            "address": hex(head),
                            "segment": idc.get_segm_name(seg_ea),
                            "type": pattern
                        })
                        break
    
    return data_sources[:30]

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "analysis_goal": "Decode cockpit instrument rendering system",
            "hypothesis": "Uses same 3D projection as HUD and tactical map",
            "cockpit_functions": find_cockpit_functions(),
            "viewmode3_analysis": analyze_viewmode3(),
            "view_projection_callers": find_view_projection_callers(),
            "mode_state_checks": find_state_mode_checks(),
            "instrument_data_sources": find_instrument_data_sources()
        }
        
        # Summary statistics
        result["summary"] = {
            "cockpit_functions_found": len(result["cockpit_functions"]),
            "view_projection_callers": len(result["view_projection_callers"]),
            "mode_checks_found": len(result["mode_state_checks"]),
            "data_sources_found": len(result["instrument_data_sources"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Found {len(result['cockpit_functions'])} cockpit-related functions")
        print(f"Found {len(result['view_projection_callers'])} view_projection callers")
        print(f"Found {len(result['mode_state_checks'])} mode 3 checks")
        print(f"Found {len(result['instrument_data_sources'])} instrument data sources")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
