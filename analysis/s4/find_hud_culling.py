"""
Find HUD culling/optimization logic that reduces projection calls.

MYSTERY: HUD should call fixed_vec3_accumulate_a 30K times/frame,
but this would take 116-232ms on a 66MHz 486 (way too slow for 60 FPS).

HYPOTHESIS: Early culling before vec3 call, possibly:
- Distance checks (cull entities beyond max range)
- Frustum culling (cull entities outside view cone)
- Occlusion culling (cull entities behind camera)
- Batch rejection (entire batches skipped)

SEARCH FOR:
- Distance comparisons before vec3 call
- Angle comparisons (frustum bounds)
- Negative Z checks (behind camera)
- Early return paths in targeting functions
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\hud_culling_analysis.json"

def analyze_early_exits(func_addr):
    """Find all early return paths in a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    early_exits = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # Find conditional returns (jz/jnz + ret)
        if mnem in ["jz", "jnz", "jge", "jle", "jb", "ja", "jbe", "jae"]:
            target = idc.get_operand_value(ea, 0)
            
            # Check if target is a return instruction
            target_mnem = idc.print_insn_mnem(target)
            if target_mnem in ["ret", "retn", "retf"]:
                disasm = idc.GetDisasm(ea)
                prev_disasm = idc.GetDisasm(idc.prev_head(ea))
                
                early_exits.append({
                    "offset": hex(ea - func.start_ea),
                    "address": hex(ea),
                    "condition": disasm,
                    "previous": prev_disasm,
                    "type": "conditional_return"
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return early_exits

def find_distance_checks(func_addr):
    """Find distance/range comparisons in function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    checks = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        # Look for cmp instructions
        if mnem == "cmp":
            disasm = idc.GetDisasm(ea)
            
            # Get the immediate value if present
            op1 = idc.print_operand(ea, 0)
            op2 = idc.print_operand(ea, 1)
            
            # Check if comparing against constants (likely thresholds)
            if any(x in op2 for x in ["h", "0x"]):  # Hex constant
                checks.append({
                    "offset": hex(ea - func.start_ea),
                    "address": hex(ea),
                    "comparison": disasm,
                    "operands": f"{op1} vs {op2}"
                })
        
        # Look for test instructions (bit flags)
        if mnem == "test":
            disasm = idc.GetDisasm(ea)
            checks.append({
                "offset": hex(ea - func.start_ea),
                "address": hex(ea),
                "test": disasm,
                "type": "flag_check"
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return checks

def find_vec3_call_context(func_addr):
    """Find what happens BEFORE the vec3_accumulate call."""
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    vec3_addr = idc.get_name_ea_simple("fixed_vec3_accumulate_a")
    if vec3_addr == idc.BADADDR:
        return {"error": "vec3 not found"}
    
    # Find the call to vec3 in this function
    ea = func.start_ea
    vec3_call_offset = None
    
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            if target == vec3_addr:
                vec3_call_offset = ea
                break
        ea = idc.next_head(ea, func.end_ea)
    
    if not vec3_call_offset:
        return {"error": "vec3 call not found in function"}
    
    # Get 20 instructions before the vec3 call
    before_call = []
    ea = func.start_ea
    prev_ea = None
    
    while ea <= vec3_call_offset:
        if ea == vec3_call_offset:
            # Collect previous 20 instructions
            temp_ea = prev_ea
            count = 0
            while temp_ea and count < 20:
                before_call.insert(0, {
                    "address": hex(temp_ea),
                    "disasm": idc.GetDisasm(temp_ea)
                })
                temp_ea = idc.prev_head(temp_ea, func.start_ea)
                count += 1
            break
        
        prev_ea = ea
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "vec3_call_address": hex(vec3_call_offset),
        "instructions_before": before_call
    }

def main():
    try:
        idaapi.auto_wait()
        
        # The 3 HUD functions that call vec3
        funcs = [
            ("hud_ai_target_tracking_draw", 0x425A2),
            ("hud_state_table_processor", 0x45074),
            ("hud_rowlist_timer_step", 0x47BDE)
        ]
        
        result = {
            "goal": "Find performance optimizations that reduce HUD projection calls",
            "analysis": {}
        }
        
        for name, addr in funcs:
            func_addr = idc.get_name_ea_simple(name)
            if func_addr == idc.BADADDR:
                func_addr = addr
            
            result["analysis"][name] = {
                "address": hex(func_addr),
                "early_exits": analyze_early_exits(func_addr),
                "distance_checks": find_distance_checks(func_addr),
                "vec3_call_context": find_vec3_call_context(func_addr)
            }
        
        # Also check the batch processor for culling logic
        batch_proc = idc.get_name_ea_simple("hud_state_table_processor")
        if batch_proc != idc.BADADDR:
            result["batch_culling"] = {
                "early_exits": analyze_early_exits(batch_proc),
                "checks": find_distance_checks(batch_proc)
            }
        
        # Search for functions with "cull" or "clip" in name (HUD context)
        cull_funcs = []
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            if name and "hud" in name.lower():
                if any(x in name.lower() for x in ["cull", "clip", "check", "valid", "range"]):
                    cull_funcs.append({
                        "name": name,
                        "address": hex(func_ea)
                    })
        
        result["potential_culling_functions"] = cull_funcs[:20]
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Found {sum(len(r['early_exits']) for r in result['analysis'].values())} early exits")
        print(f"Found {len(cull_funcs)} potential culling functions")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
