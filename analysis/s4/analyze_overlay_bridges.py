"""
Analyze overlay bridge functions.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\overlay_bridges_analysis.json"

def analyze_func(name):
    addr = idc.get_name_ea_simple(name)
    if addr == idc.BADADDR:
        return {"error": "not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": "no function"}
    
    # Get calls
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            disasm = idc.GetDisasm(ea)
            target_name = disasm.split()[-1] if ' ' in disasm else "unknown"
            calls.append(target_name)
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(addr, 0))
    callers = {}
    for xref in xrefs[:20]:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers[caller_name] = callers.get(caller_name, 0) + 1
    
    # Get disassembly
    disasm = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm.append({
            "address": hex(ea),
            "disasm": idc.GetDisasm(ea)
        })
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "calls": calls,
        "xref_count": len(xrefs),
        "callers": callers,
        "disassembly": disasm
    }

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "overlay_tail_bridge": analyze_func("overlay_tail_bridge"),
            "overlay_tail_bridge_b": analyze_func("overlay_tail_bridge_b"),
            "tail_bridge_overlay_load": analyze_func("tail_bridge_overlay_load"),
            "overlay_segment_load": analyze_func("overlay_segment_load"),
            "overlay_loader_main": analyze_func("overlay_loader_main")
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
