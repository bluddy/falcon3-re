"""
Analyze overlay_tail_bridge - overlay swapping mechanism from game loop.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\overlay_tail_bridge_analysis.json"

def main():
    try:
        idaapi.auto_wait()
        
        addr = idc.get_name_ea_simple("overlay_tail_bridge")
        if addr == idc.BADADDR:
            result = {"error": "Function not found"}
        else:
            func = idaapi.get_func(addr)
            if not func:
                result = {"error": "No function at address"}
            else:
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
                
                result = {
                    "name": "overlay_tail_bridge",
                    "address": hex(addr),
                    "size": func.end_ea - func.start_ea,
                    "call_count": len(calls),
                    "calls": calls,
                    "xref_count": len(xrefs),
                    "callers": callers,
                    "disassembly": disasm
                }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
