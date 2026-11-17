"""
Export detailed analysis of damage system handlers.

KEY FUNCTIONS FOUND:
- damage_event_dispatch_handler (0x2EAA7, 190B)
- store_impact_step (0x397FB, 169B)
- collision_layer_test_and_store (0x4AC1E, 64B)
- collision_aabb_distance_test (0x4AE66, 64B)
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\damage_handlers_detailed.json"

def export_function_complete(func_addr, name=None):
    """Export complete function with calls and data refs."""
    if func_addr == idc.BADADDR:
        return {"error": "invalid address"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    if not name:
        name = idc.get_func_name(func_addr)
    
    lines = []
    calls = []
    data_refs = []
    constants = []
    
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
        
        # Track data references and constants
        if mnem in ["mov", "cmp", "test", "and", "or"]:
            for i in range(2):
                op = idc.print_operand(ea, i)
                # Look for memory references
                if "[" in op or ":" in op:
                    data_refs.append({
                        "offset": hex(ea - func.start_ea),
                        "operand": op,
                        "instruction": disasm
                    })
                    break
                # Look for interesting constants (bit masks, sizes)
                elif "h" in op and any(x in op for x in ["0", "1", "2", "4", "8", "F"]):
                    try:
                        val = int(op.replace("h", ""), 16)
                        if val > 0 and val not in [val for _, val in constants]:
                            constants.append((op, val))
                    except:
                        pass
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func_addr, 0))
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
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": lines,
        "calls": calls,
        "data_refs": data_refs[:50],
        "constants": constants[:20],
        "callers": callers
    }

def find_subsystem_state_storage():
    """Find where subsystem damage state is stored."""
    # Look for byte or word arrays that might be subsystem flags
    # Typically 8-16 subsystems in F-16
    
    # Check for structures with multiple flags
    damage_func = idc.get_name_ea_simple("damage_event_dispatch_handler")
    if damage_func == idc.BADADDR:
        return []
    
    func = idaapi.get_func(damage_func)
    if not func:
        return []
    
    storage_refs = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        # Look for writes to memory
        if idc.print_insn_mnem(ea) in ["mov", "or", "and", "inc", "dec"]:
            disasm = idc.GetDisasm(ea)
            # Look for array-like accesses or flag operations
            if any(x in disasm for x in ["+", "[", "ptr"]):
                storage_refs.append({
                    "offset": hex(ea - func.start_ea),
                    "instruction": disasm,
                    "address": hex(ea)
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return storage_refs[:30]

def analyze_damage_dispatch():
    """Analyze damage_event_dispatch_handler to find dispatch table."""
    func_addr = idc.get_name_ea_simple("damage_event_dispatch_handler")
    if func_addr == idc.BADADDR:
        return {"error": "not found"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    # Look for switch/dispatch patterns
    dispatch_patterns = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        
        # Look for jumps (switch tables)
        if mnem in ["jmp", "call"] and "cs:" in disasm:
            dispatch_patterns.append({
                "type": "indirect_jump",
                "offset": hex(ea - func.start_ea),
                "instruction": disasm
            })
        
        # Look for comparisons (if-else chains)
        if mnem == "cmp":
            dispatch_patterns.append({
                "type": "comparison",
                "offset": hex(ea - func.start_ea),
                "instruction": disasm
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return dispatch_patterns

def find_impact_detection():
    """Analyze store_impact_step and collision functions."""
    funcs_to_analyze = [
        ("store_impact_step", 0x397FB),
        ("collision_layer_test_and_store", 0x4AC1E),
        ("collision_aabb_distance_test", 0x4AE66)
    ]
    
    results = {}
    for name, addr in funcs_to_analyze:
        func_addr = idc.get_name_ea_simple(name)
        if func_addr == idc.BADADDR:
            func_addr = addr
        
        if func_addr != idc.BADADDR:
            results[name] = export_function_complete(func_addr, name)
    
    return results

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "goal": "Detailed damage system analysis",
            "damage_event_dispatch": export_function_complete(
                idc.get_name_ea_simple("damage_event_dispatch_handler"),
                "damage_event_dispatch_handler"
            ),
            "subsystem_storage": find_subsystem_state_storage(),
            "damage_dispatch_patterns": analyze_damage_dispatch(),
            "impact_detection": find_impact_detection()
        }
        
        # Summary
        result["summary"] = {
            "damage_handler_size": result["damage_event_dispatch"].get("size", 0),
            "damage_handler_calls": len(result["damage_event_dispatch"].get("calls", [])),
            "subsystem_refs": len(result["subsystem_storage"]),
            "dispatch_patterns": len(result["damage_dispatch_patterns"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Damage handler: {result['summary']['damage_handler_size']} bytes")
        print(f"  Calls: {result['summary']['damage_handler_calls']}")
        print(f"  Subsystem refs: {result['summary']['subsystem_refs']}")
        print(f"  Dispatch patterns: {result['summary']['dispatch_patterns']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
