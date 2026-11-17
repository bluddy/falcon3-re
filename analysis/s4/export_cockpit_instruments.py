"""
Export cockpit instrument rendering functions for detailed analysis.

FOCUS AREAS:
1. view_cockpit_hud_initialize (0x359B2, 381B) - Cockpit/HUD initialization
2. viewmode3_vector_project (0x2F535, 91B) - Mode 3 cockpit vectors
3. hud_heading_tape_draw (0x3708F, 254B) - Heading indicator
4. Flight instrument gauges (airspeed, altitude, VSI, etc.)

PATTERN: Look for functions that:
- Read flight data (speed, altitude, attitude)
- Convert to gauge positions (needle angles, tape positions)
- Call drawing primitives
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\cockpit_instruments_detailed.json"

def export_function_full(addr, name=None):
    """Export complete function analysis."""
    if addr == idc.BADADDR:
        return {"error": "invalid address"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": "no function"}
    
    if not name:
        name = idc.get_func_name(addr)
    
    lines = []
    calls = []
    data_refs = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        mnem = idc.print_insn_mnem(ea)
        
        # Track calls
        if mnem == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            if target_name:
                calls.append({
                    "offset": hex(ea - func.start_ea),
                    "target": target_name,
                    "address": hex(target)
                })
        
        # Track data accesses
        if mnem in ["mov", "cmp", "test", "add", "sub", "lea"]:
            for i in range(2):
                op = idc.print_operand(ea, i)
                # Look for segment:offset patterns
                if ":" in op or "[" in op:
                    data_refs.append({
                        "offset": hex(ea - func.start_ea),
                        "operand": op,
                        "instruction": disasm
                    })
                    break
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(addr, 0))
    callers = []
    for xref in xrefs[:30]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers.append({
                "name": caller_name,
                "call_site": hex(xref.frm)
            })
    
    return {
        "name": name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": lines,
        "calls": calls,
        "data_refs": data_refs[:50],  # Limit data refs
        "callers": callers
    }

def find_gauge_drawing_functions():
    """Find functions that likely draw individual gauges."""
    # Search for patterns like "needle", "scale", "tape", etc.
    gauge_keywords = ["needle", "scale", "tape", "ladder", "strip", "digit",
                      "readout", "indicator", "dial", "meter"]
    
    gauge_funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name and "hud_" in name:
            name_lower = name.lower()
            for keyword in gauge_keywords:
                if keyword in name_lower:
                    func = idaapi.get_func(func_ea)
                    gauge_funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "type": keyword
                    })
                    break
    
    return gauge_funcs

def find_flight_data_globals():
    """Find global variables that store flight data."""
    # Look for named variables with flight-related names
    flight_keywords = ["airspeed", "altitude", "heading", "pitch", "roll",
                       "throttle", "fuel", "gforce", "aoa", "vsi", "mach",
                       "climb", "descent", "bank", "turn"]
    
    flight_globals = []
    
    # Search in data segments
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        # Focus on data segments
        if "data" in seg_name.lower() or "bss" in seg_name.lower():
            for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
                name = idc.get_name(head)
                if name:
                    name_lower = name.lower()
                    for keyword in flight_keywords:
                        if keyword in name_lower:
                            # Check if it's actually a variable (not code)
                            if idc.is_data(idc.get_full_flags(head)):
                                flight_globals.append({
                                    "name": name,
                                    "address": hex(head),
                                    "segment": seg_name,
                                    "type": keyword,
                                    "size": idc.get_item_size(head)
                                })
                                break
    
    return flight_globals[:50]

def analyze_instrument_pipeline():
    """Analyze the instrument rendering pipeline."""
    # Start from game_frame_pipeline_step
    game_frame = idc.get_name_ea_simple("game_frame_pipeline_step")
    if game_frame == idc.BADADDR:
        return {"error": "game_frame_pipeline_step not found"}
    
    func = idaapi.get_func(game_frame)
    if not func:
        return {"error": "no function"}
    
    # Find calls to cockpit/view functions
    cockpit_calls = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            if target_name:
                # Look for view/cockpit related calls
                if any(x in target_name.lower() for x in ["view", "cockpit", "mode"]):
                    cockpit_calls.append({
                        "offset": hex(ea - func.start_ea),
                        "function": target_name,
                        "address": hex(target),
                        "call_site": hex(ea)
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "game_frame_address": hex(game_frame),
        "cockpit_related_calls": cockpit_calls[:30]
    }

def main():
    try:
        idaapi.auto_wait()
        
        # Key cockpit functions to analyze
        funcs_to_export = [
            ("view_cockpit_hud_initialize", 0x359B2),
            ("viewmode3_vector_project", 0x2F535),
            ("hud_heading_tape_draw", 0x3708F),
            ("hud_terrain_strip_render", 0x3718D),  # Might be attitude indicator
            ("hud_data_panel_draw", 0x30F11),
            ("hud_readout_render", 0x36785)
        ]
        
        result = {
            "goal": "Decode cockpit instrument rendering system",
            "functions": {},
            "gauge_drawing_functions": find_gauge_drawing_functions(),
            "flight_data_globals": find_flight_data_globals(),
            "instrument_pipeline": analyze_instrument_pipeline()
        }
        
        # Export each key function
        for name, addr in funcs_to_export:
            func_addr = idc.get_name_ea_simple(name)
            if func_addr == idc.BADADDR:
                func_addr = addr
            
            if func_addr != idc.BADADDR:
                result["functions"][name] = export_function_full(func_addr, name)
        
        # Summary
        result["summary"] = {
            "key_functions_analyzed": len([f for f in result["functions"].values() if "error" not in f]),
            "gauge_functions_found": len(result["gauge_drawing_functions"]),
            "flight_data_variables": len(result["flight_data_globals"]),
            "cockpit_calls_in_game_loop": len(result["instrument_pipeline"].get("cockpit_related_calls", []))
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {result['summary']['key_functions_analyzed']} key functions")
        print(f"Found {result['summary']['gauge_functions_found']} gauge drawing functions")
        print(f"Found {result['summary']['flight_data_variables']} flight data variables")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
