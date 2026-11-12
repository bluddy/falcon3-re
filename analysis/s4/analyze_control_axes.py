"""
Analyze control_axes_read - main control input function.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\control_axes_analysis.json"

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
    
    # Get sample disassembly (first 30 instructions)
    disasm = []
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 30:
        disasm.append({
            "address": hex(ea),
            "disasm": idc.GetDisasm(ea)
        })
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    return {
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "calls": calls,
        "xref_count": len(xrefs),
        "callers": callers,
        "disasm_sample": disasm
    }

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "control_axes_read": analyze_func("control_axes_read"),
            "joystick_poll": analyze_func("joystick_poll"),
            "key_event_process": analyze_func("key_event_process"),
            "mouse_int33_dispatch": analyze_func("mouse_int33_dispatch")
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
