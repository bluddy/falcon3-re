"""
Complete the remaining 5% of flight physics analysis.

CURRENT STATUS: 95% complete
REMAINING WORK:
1. Fourth axis purpose ([si+2Ah])
2. Physics coefficient fields +0x62 and +0x64
3. Extract aircraft-specific coefficient values (F-16, F/A-18, MiG-29)
4. Find thrust/engine model

KNOWN:
- Axis 1: [si+18h] - Calculated from [si+2Eh]
- Axis 2: [si+1Ah] - Elevator (pitch control) ✅
- Axis 3: [si+1Ch] - Aileron (roll control) ✅
- Axis 4: [si+2Ah] - Unknown (throttle? rudder?)
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\flight_model_complete.json"

def find_axis_4_usage():
    """Find where [si+2Ah] is used to determine its purpose."""
    # Search in the aerodynamics function
    aero_func = idc.get_name_ea_simple("sub_38CF3")
    if aero_func == idc.BADADDR:
        return {"error": "aerodynamics function not found"}
    
    func = idaapi.get_func(aero_func)
    if not func:
        return {"error": "no function"}
    
    axis4_usage = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        
        # Look for [si+2Ah] or [si+2A]
        if "+2Ah]" in disasm or "+2A]" in disasm:
            # Get context (5 instructions before and after)
            context = []
            ctx_ea = max(ea - 20, func.start_ea)
            ctx_end = min(ea + 20, func.end_ea)
            
            while ctx_ea < ctx_end:
                context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                ctx_ea = idc.next_head(ctx_ea, ctx_end)
            
            axis4_usage.append({
                "offset": hex(ea - func.start_ea),
                "address": hex(ea),
                "instruction": disasm,
                "context": context
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return axis4_usage

def find_physics_fields_62_64():
    """Find where fields +62h and +64h are used."""
    aero_func = idc.get_name_ea_simple("sub_38CF3")
    if aero_func == idc.BADADDR:
        return []
    
    func = idaapi.get_func(aero_func)
    if not func:
        return []
    
    field_usage = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        
        # Look for +62h or +64h
        if any(x in disasm for x in ["+62h]", "+64h]", "+62]", "+64]"]):
            context = []
            ctx_ea = max(ea - 15, func.start_ea)
            ctx_end = min(ea + 15, func.end_ea)
            
            while ctx_ea < ctx_end:
                context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                ctx_ea = idc.next_head(ctx_ea, ctx_end)
            
            field_usage.append({
                "offset": hex(ea - func.start_ea),
                "address": hex(ea),
                "instruction": disasm,
                "context": context
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return field_usage

def find_thrust_functions():
    """Search for engine/thrust related functions."""
    thrust_keywords = ["thrust", "engine", "throttle", "afterburn", "power", "rpm"]
    
    thrust_funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for keyword in thrust_keywords:
                if keyword in name_lower:
                    func = idaapi.get_func(func_ea)
                    thrust_funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": keyword
                    })
                    break
    
    return thrust_funcs

def extract_aircraft_coefficients():
    """Try to find aircraft data tables with physics coefficients."""
    # Look for patterns: multiple int16 values in sequence at +60h-70h range
    # Search in data segments
    
    coeff_tables = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        # Focus on data segments
        if not any(x in seg_name.lower() for x in ["data", "seg"]):
            continue
        
        # Search for potential aircraft template structures
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end - 0x70:
            # Check if this looks like an aircraft template
            # (has reasonable values at offsets +60h-70h)
            
            # Read potential coefficients
            try:
                speed_thresh = idc.get_wide_word(ea + 0x60)
                force_div_1 = idc.get_wide_word(ea + 0x66)
                control_auth = idc.get_wide_word(ea + 0x68)
                min_effect = idc.get_wide_word(ea + 0x6A)
                force_div_2 = idc.get_wide_word(ea + 0x6C)
                
                # Check if values are in reasonable ranges
                if (0 < speed_thresh < 5000 and 
                    0 < force_div_1 < 10000 and
                    0 < control_auth < 1000 and
                    0 < min_effect < 1000 and
                    0 < force_div_2 < 10000):
                    
                    # Check for xrefs to this address (should be referenced)
                    xrefs = list(idautils.XrefsTo(ea, 0))
                    if len(xrefs) > 0:
                        coeff_tables.append({
                            "address": hex(ea),
                            "segment": seg_name,
                            "coefficients": {
                                "speed_threshold": speed_thresh,
                                "field_62": idc.get_wide_word(ea + 0x62),
                                "field_64": idc.get_wide_word(ea + 0x64),
                                "force_divisor_1": force_div_1,
                                "control_authority": control_auth,
                                "min_speed_effect": min_effect,
                                "force_divisor_2": force_div_2,
                                "control_mult_2": idc.get_wide_word(ea + 0x6E),
                                "speed_threshold_2": idc.get_wide_word(ea + 0x70)
                            },
                            "xref_count": len(xrefs),
                            "xrefs": [hex(x.frm) for x in xrefs[:5]]
                        })
                        
                        # Limit to reasonable number
                        if len(coeff_tables) >= 20:
                            break
            except:
                pass
            
            ea += 2  # Move by word
        
        if len(coeff_tables) >= 20:
            break
    
    return coeff_tables

def analyze_control_axis_store():
    """Analyze control_axis_store_step to understand axis 4."""
    func_addr = idc.get_name_ea_simple("control_axis_store_step")
    if func_addr == idc.BADADDR:
        return {"error": "not found"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    # Export relevant section
    lines = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": lines
    }

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "goal": "Complete remaining 5% of flight physics",
            "axis_4_usage": find_axis_4_usage(),
            "physics_fields_62_64": find_physics_fields_62_64(),
            "thrust_functions": find_thrust_functions(),
            "aircraft_coefficients": extract_aircraft_coefficients(),
            "control_axis_store_analysis": analyze_control_axis_store()
        }
        
        # Summary
        result["summary"] = {
            "axis_4_references": len(result["axis_4_usage"]) if isinstance(result["axis_4_usage"], list) else 0,
            "field_62_64_references": len(result["physics_fields_62_64"]),
            "thrust_functions_found": len(result["thrust_functions"]),
            "aircraft_templates_found": len(result["aircraft_coefficients"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Found {result['summary']['axis_4_references']} axis 4 references")
        print(f"Found {result['summary']['field_62_64_references']} field +62/64 references")
        print(f"Found {result['summary']['thrust_functions_found']} thrust functions")
        print(f"Found {result['summary']['aircraft_templates_found']} aircraft templates")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
