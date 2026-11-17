"""
Check what view mode 3 actually is and when viewmode3_vector_project is called.

USER QUESTION: Falcon 3 doesn't have 3D cockpits, why would it use 3D rendering?
Front view instruments are 2D bitmaps, only side views need angle correction.

HYPOTHESIS TO TEST:
- Mode 3 might be SIDE VIEW (left/right), not front cockpit
- Front cockpit might be mode 0 or 1 (no 3D projection)
- viewmode3_vector_project might only run for side/angled views

SEARCH FOR:
1. All references to state_word_44d3d_get()
2. Mode comparisons (cmp ax, 0/1/2/3/4...)
3. View switching logic
4. What calls viewmode3_vector_project
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\view_mode_analysis.json"

def find_mode_checks():
    """Find all places that check view mode."""
    state_func = idc.get_name_ea_simple("state_word_44d3d_get")
    if state_func == idc.BADADDR:
        return []
    
    mode_checks = []
    
    for xref in idautils.XrefsTo(state_func, 0):
        func = idaapi.get_func(xref.frm)
        if not func:
            continue
        
        func_name = idc.get_func_name(func.start_ea)
        
        # Look for mode comparisons after the call
        ea = xref.frm
        next_ea = idc.next_head(ea, func.end_ea)
        
        # Check next few instructions for cmp
        for i in range(5):
            if next_ea >= func.end_ea:
                break
            
            mnem = idc.print_insn_mnem(next_ea)
            disasm = idc.GetDisasm(next_ea)
            
            if mnem == "cmp":
                op2 = idc.print_operand(next_ea, 1)
                mode_checks.append({
                    "function": func_name,
                    "call_site": hex(xref.frm),
                    "check_at": hex(next_ea),
                    "comparison": disasm,
                    "mode_value": op2,
                    "context": [
                        idc.GetDisasm(next_ea),
                        idc.GetDisasm(idc.next_head(next_ea)),
                        idc.GetDisasm(idc.next_head(idc.next_head(next_ea)))
                    ]
                })
                break
            
            next_ea = idc.next_head(next_ea, func.end_ea)
    
    return mode_checks

def analyze_viewmode3_callers():
    """Who calls viewmode3_vector_project and when?"""
    func_addr = idc.get_name_ea_simple("viewmode3_vector_project")
    if func_addr == idc.BADADDR:
        return {"error": "function not found"}
    
    callers = []
    for xref in idautils.XrefsTo(func_addr, 0):
        caller_func = idaapi.get_func(xref.frm)
        if not caller_func:
            continue
        
        caller_name = idc.get_func_name(caller_func.start_ea)
        
        # Get context around the call
        context = []
        ea = max(xref.frm - 20, caller_func.start_ea)
        end = min(xref.frm + 20, caller_func.end_ea)
        
        while ea < end:
            context.append(f"{ea:08X}: {idc.GetDisasm(ea)}")
            ea = idc.next_head(ea, end)
        
        callers.append({
            "caller": caller_name,
            "call_site": hex(xref.frm),
            "context": context
        })
    
    return callers

def find_view_mode_names():
    """Search for strings that might indicate view mode names."""
    view_strings = []
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            if idc.is_strlit(idc.get_full_flags(head)):
                str_val = idc.get_strlit_contents(head)
                if str_val:
                    str_val = str_val.decode('ascii', errors='ignore').lower()
                    # Look for view-related strings
                    if any(x in str_val for x in ['view', 'cockpit', 'left', 'right', 'front', 'rear', 'hud']):
                        view_strings.append({
                            "address": hex(head),
                            "string": str_val[:100]  # Truncate long strings
                        })
    
    return view_strings[:50]

def check_game_frame_pipeline():
    """Examine game_frame_pipeline_step to see the view mode dispatch."""
    func_addr = idc.get_name_ea_simple("game_frame_pipeline_step")
    if func_addr == idc.BADADDR:
        return {"error": "not found"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    # Find all calls to view-related functions
    view_calls = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            
            if target_name and any(x in target_name.lower() for x in ['view', 'mode', 'cockpit']):
                # Get context
                context = []
                ctx_ea = max(ea - 30, func.start_ea)
                ctx_end = min(ea + 10, func.end_ea)
                
                while ctx_ea < ctx_end:
                    context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                    ctx_ea = idc.next_head(ctx_ea, ctx_end)
                
                view_calls.append({
                    "offset": hex(ea - func.start_ea),
                    "function": target_name,
                    "address": hex(target),
                    "context": context
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "address": hex(func_addr),
        "view_related_calls": view_calls
    }

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "question": "Is mode 3 really front cockpit, or is it side view?",
            "hypothesis": "Front cockpit = 2D bitmap, only side views need 3D projection",
            "mode_checks": find_mode_checks(),
            "viewmode3_callers": analyze_viewmode3_callers(),
            "view_strings": find_view_mode_names(),
            "game_frame_pipeline": check_game_frame_pipeline()
        }
        
        # Summary
        mode_3_checks = [m for m in result["mode_checks"] if "3" in str(m.get("mode_value", ""))]
        result["summary"] = {
            "total_mode_checks": len(result["mode_checks"]),
            "mode_3_specific": len(mode_3_checks),
            "viewmode3_call_count": len(result["viewmode3_callers"]),
            "view_strings_found": len(result["view_strings"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Found {len(result['mode_checks'])} mode checks")
        print(f"Found {len(mode_3_checks)} mode 3 specific checks")
        print(f"viewmode3_vector_project called from {len(result['viewmode3_callers'])} places")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
