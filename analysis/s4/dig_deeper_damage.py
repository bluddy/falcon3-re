"""
Dig deeper into damage model - find subsystem storage and probability system.

GOALS:
1. Locate subsystem damage state storage (array/bitfield)
2. Trace op_dispatch to find probability tables
3. Find fault panel display function
4. Map subsystem indices to names

METHOD:
- Trace table_dword_set to find storage location
- Export op_dispatch function
- Search for display functions that read subsystem state
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\damage_deep_dive.json"

def trace_table_dword_set():
    """Find table_dword_set and trace where it stores data."""
    func_addr = idc.get_name_ea_simple("table_dword_set")
    if func_addr == idc.BADADDR:
        return {"error": "table_dword_set not found"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    # Export complete function
    lines = []
    data_writes = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        # Look for memory writes
        mnem = idc.print_insn_mnem(ea)
        if mnem == "mov" and "]" in disasm:
            # This is a write to memory
            data_writes.append({
                "offset": hex(ea - func.start_ea),
                "instruction": disasm,
                "address": hex(ea)
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func_addr, 0))
    callers = []
    for xref in xrefs[:20]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers.append({
                "name": caller_name,
                "call_site": hex(xref.frm)
            })
    
    return {
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea if func else 0,
        "disassembly": lines,
        "data_writes": data_writes,
        "callers": callers
    }

def export_op_dispatch():
    """Export op_dispatch function to understand damage type dispatch."""
    func_addr = idc.get_name_ea_simple("op_dispatch")
    if func_addr == idc.BADADDR:
        return {"error": "op_dispatch not found"}
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function"}
    
    lines = []
    calls = []
    jumps = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            if target_name:
                calls.append({
                    "offset": hex(ea - func.start_ea),
                    "target": target_name
                })
        
        # Look for dispatch tables (indirect jumps)
        if mnem in ["jmp", "call"] and "cs:" in disasm:
            jumps.append({
                "offset": hex(ea - func.start_ea),
                "instruction": disasm
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea if func else 0,
        "disassembly": lines,
        "calls": calls,
        "indirect_jumps": jumps
    }

def find_damage_state_reads():
    """Find functions that READ subsystem damage state (for display)."""
    # Look for functions that might display fault panel
    # They should read from subsystem state array
    
    display_funcs = []
    
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if not name:
            continue
        
        # Look for display/draw/fault/warn functions
        if any(x in name.lower() for x in ["display", "draw", "fault", "warn", "panel", "caution", "status"]):
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            # Check if function accesses arrays (likely subsystem state)
            has_array_access = False
            ea = func.start_ea
            
            while ea < func.end_ea and ea < func.start_ea + 200:  # Check first 200 bytes
                disasm = idc.GetDisasm(ea)
                # Look for indexed array access patterns
                if any(x in disasm for x in ["+bx]", "+si]", "+di]", "+cx]"]):
                    has_array_access = True
                    break
                ea = idc.next_head(ea, func.end_ea)
            
            if has_array_access:
                display_funcs.append({
                    "name": name,
                    "address": hex(func_ea),
                    "size": func.end_ea - func.start_ea
                })
    
    return display_funcs[:30]

def analyze_damage_handler_loc_41167():
    """Analyze the damage application function called from store_impact_step."""
    func_addr = 0x41167
    
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "no function at 0x41167"}
    
    name = idc.get_func_name(func_addr)
    
    lines = []
    calls = []
    data_refs = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        lines.append(f"{ea:08X}: {disasm}")
        
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == "call":
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            if target_name:
                calls.append({
                    "offset": hex(ea - func.start_ea),
                    "target": target_name,
                    "address": hex(target)
                })
        
        # Track data references
        if mnem in ["mov", "cmp", "test", "and", "or"]:
            for i in range(2):
                op = idc.print_operand(ea, i)
                if any(x in op for x in ["[", ":", "ds:", "es:"]):
                    data_refs.append({
                        "offset": hex(ea - func.start_ea),
                        "operand": op,
                        "instruction": disasm
                    })
                    break
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "name": name if name else f"sub_{func_addr:X}",
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": lines,
        "calls": calls,
        "data_refs": data_refs[:50]
    }

def search_subsystem_globals():
    """Search for global variables that might be subsystem state."""
    # Look in data segments for byte/word arrays of size 8-16 (subsystem count)
    
    candidates = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Focus on data segments
        if not any(x in seg_name.lower() for x in ["data", "bss", ".data"]):
            continue
        
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            # Check if this is a named variable
            name = idc.get_name(ea)
            if name:
                # Check size
                size = idc.get_item_size(ea)
                
                # Likely subsystem state: array of 8-16 bytes
                if 8 <= size <= 20 and idc.is_data(idc.get_full_flags(ea)):
                    # Check for xrefs (should be accessed)
                    xrefs = list(idautils.XrefsTo(ea, 0))
                    if len(xrefs) > 0:
                        # Get first few xrefs
                        xref_funcs = []
                        for xref in xrefs[:5]:
                            func_name = idc.get_func_name(xref.frm)
                            if func_name:
                                xref_funcs.append(func_name)
                        
                        candidates.append({
                            "name": name,
                            "address": hex(ea),
                            "segment": seg_name,
                            "size": size,
                            "xref_count": len(xrefs),
                            "accessed_by": xref_funcs
                        })
            
            ea = idc.next_head(ea, seg_end)
    
    return candidates[:50]

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "goal": "Deep dive into damage model - find subsystem storage and probability",
            "table_dword_set": trace_table_dword_set(),
            "op_dispatch": export_op_dispatch(),
            "display_functions": find_damage_state_reads(),
            "damage_handler_loc_41167": analyze_damage_handler_loc_41167(),
            "subsystem_global_candidates": search_subsystem_globals()
        }
        
        # Summary
        result["summary"] = {
            "table_writes": len(result["table_dword_set"].get("data_writes", [])),
            "display_funcs_found": len(result["display_functions"]),
            "damage_handler_calls": len(result["damage_handler_loc_41167"].get("calls", [])),
            "subsystem_candidates": len(result["subsystem_global_candidates"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"table_dword_set: {result['summary']['table_writes']} writes")
        print(f"Display functions: {result['summary']['display_funcs_found']}")
        print(f"Damage handler: {result['summary']['damage_handler_calls']} calls")
        print(f"Subsystem candidates: {result['summary']['subsystem_candidates']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
