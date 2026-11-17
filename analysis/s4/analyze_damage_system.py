"""
Analyze Falcon 3.0 damage model system.

USER QUESTION: How is subsystem damage determined on missile/gun impact or crash?
Multiple systems can be damaged (appear on right inner view with text abbreviations).

SEARCH FOR:
1. Functions with "damage", "hit", "impact", "collision", "crash", "subsystem"
2. Missile impact handlers
3. Gun impact/bullet hit handlers
4. Ground collision detection
5. Damage state storage (which subsystems are damaged)
6. Damage probability/distribution logic
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\damage_system_analysis.json"

def find_damage_functions():
    """Find all functions related to damage."""
    damage_keywords = ["damage", "hit", "impact", "collision", "crash", "destroy",
                       "subsystem", "fault", "fail", "weapon", "missile", "bullet",
                       "gun", "explode", "kill"]
    
    damage_funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for keyword in damage_keywords:
                if keyword in name_lower:
                    func = idaapi.get_func(func_ea)
                    damage_funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": keyword
                    })
                    break
    
    return damage_funcs

def find_subsystem_data():
    """Find subsystem state data (damaged systems bitfield/array)."""
    # Look for arrays or bitfields that might track subsystem damage
    # Common patterns: byte array for on/off, bitfield for multiple systems
    
    subsystem_keywords = ["fault", "damage", "system", "subsys", "health",
                          "status", "fail", "broken"]
    
    subsystem_vars = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        # Focus on data segments
        if not any(x in seg_name.lower() for x in ["data", "bss", "seg"]):
            continue
        
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            name = idc.get_name(head)
            if name:
                name_lower = name.lower()
                for keyword in subsystem_keywords:
                    if keyword in name_lower:
                        if idc.is_data(idc.get_full_flags(head)):
                            subsystem_vars.append({
                                "name": name,
                                "address": hex(head),
                                "segment": seg_name,
                                "size": idc.get_item_size(head),
                                "keyword": keyword
                            })
                            break
    
    return subsystem_vars[:50]

def find_collision_detection():
    """Find collision detection functions."""
    collision_funcs = []
    
    # Look for functions that check distances, bounding boxes, etc.
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name and any(x in name.lower() for x in ["collision", "collide", "intersect", "bounds", "distance", "proximity"]):
            func = idaapi.get_func(func_ea)
            collision_funcs.append({
                "name": name,
                "address": hex(func_ea),
                "size": func.end_ea - func.start_ea if func else 0
            })
    
    return collision_funcs[:30]

def find_aircraft_slot_flags():
    """Find aircraft slot flags (bit 2 = collision from flight_physics.md)."""
    # From flight_physics.md: aircraft_slot_cycle_step
    # Flags at +0x00: bit 2 = collision, bit 4 = respawn
    
    slot_func = idc.get_name_ea_simple("aircraft_slot_cycle_step")
    if slot_func == idc.BADADDR:
        return {"error": "aircraft_slot_cycle_step not found"}
    
    func = idaapi.get_func(slot_func)
    if not func:
        return {"error": "no function"}
    
    # Look for flag checks
    flag_checks = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        
        # Look for bit tests (test, and with constants)
        if any(x in disasm.lower() for x in ["test", "and"]) and any(x in disasm for x in ["2", "4", "8"]):
            context = []
            ctx_ea = max(ea - 10, func.start_ea)
            ctx_end = min(ea + 10, func.end_ea)
            
            while ctx_ea < ctx_end:
                context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                ctx_ea = idc.next_head(ctx_ea, ctx_end)
            
            flag_checks.append({
                "address": hex(ea),
                "instruction": disasm,
                "context": context
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "function": "aircraft_slot_cycle_step",
        "address": hex(slot_func) if slot_func != idc.BADADDR else "not found",
        "flag_checks": flag_checks[:20]
    }

def analyze_weapon_impact():
    """Find weapon impact handlers."""
    # Look for missile and gun impact functions
    
    weapon_funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name and any(x in name.lower() for x in ["weapon", "missile", "bullet", "gun", "ammo", "fire", "shoot", "launch"]):
            func = idaapi.get_func(func_ea)
            
            # Check if function has references to damage-related functions
            has_damage_ref = False
            ea = func.start_ea if func else func_ea
            end = func.end_ea if func else func_ea + 100
            
            check_ea = ea
            while check_ea < end and check_ea < ea + 500:  # Limit search
                if idc.print_insn_mnem(check_ea) == "call":
                    target = idc.get_operand_value(check_ea, 0)
                    target_name = idc.get_func_name(target)
                    if target_name and any(x in target_name.lower() for x in ["damage", "hit", "impact", "destroy"]):
                        has_damage_ref = True
                        break
                check_ea = idc.next_head(check_ea, end)
            
            weapon_funcs.append({
                "name": name,
                "address": hex(func_ea),
                "size": func.end_ea - func.start_ea if func else 0,
                "has_damage_call": has_damage_ref
            })
    
    return weapon_funcs[:40]

def find_strings_damage():
    """Find strings related to damage (subsystem abbreviations)."""
    damage_strings = []
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            if idc.is_strlit(idc.get_full_flags(head)):
                str_val = idc.get_strlit_contents(head)
                if str_val:
                    str_val = str_val.decode('ascii', errors='ignore').lower()
                    # Look for system abbreviations (typically 3-4 chars)
                    if any(x in str_val for x in ['eng', 'hyd', 'fuel', 'elec', 'fire', 'avionics', 
                                                   'radar', 'rwr', 'ecm', 'gear', 'flap', 'brake',
                                                   'damage', 'fault', 'fail', 'warn', 'caution']):
                        damage_strings.append({
                            "address": hex(head),
                            "string": str_val[:50]
                        })
    
    return damage_strings[:50]

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "goal": "Analyze damage model - subsystem damage on impact/crash",
            "damage_functions": find_damage_functions(),
            "subsystem_data": find_subsystem_data(),
            "collision_detection": find_collision_detection(),
            "aircraft_slot_flags": find_aircraft_slot_flags(),
            "weapon_impact": analyze_weapon_impact(),
            "damage_strings": find_strings_damage()
        }
        
        # Summary
        result["summary"] = {
            "damage_functions": len(result["damage_functions"]),
            "subsystem_variables": len(result["subsystem_data"]),
            "collision_functions": len(result["collision_detection"]),
            "weapon_functions": len(result["weapon_impact"]),
            "weapon_with_damage_calls": len([w for w in result["weapon_impact"] if w.get("has_damage_call")]),
            "damage_strings": len(result["damage_strings"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Found {result['summary']['damage_functions']} damage functions")
        print(f"Found {result['summary']['subsystem_variables']} subsystem variables")
        print(f"Found {result['summary']['collision_functions']} collision functions")
        print(f"Found {result['summary']['weapon_functions']} weapon functions")
        print(f"  ({result['summary']['weapon_with_damage_calls']} with damage calls)")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
