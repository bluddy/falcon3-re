#!/usr/bin/env python3
"""IDA probe: disassemble top 10 Level-0 functions for naming.

RUN IN IDA:  File → Script File → probe_level0_top10.py
"""
import json
import idc
import idaapi
import idautils

# Top 10 Level-0 by (dyn_calls DESC, static_in_degree DESC)
TARGETS = [
    0x263F6,   # sub_263F6  dyn=18079 in=8  122B
    0x12890,   # sub_12890  dyn=11513 in=1    5B
    0x2295C,   # sub_2295C  dyn=11154 in=6    2B
    0x22436,   # sub_22436  dyn=9698 in=5     5B
    0x2243B,   # sub_2243B  dyn=9698 in=5     5B
    0x2284B,   # sub_2284B  dyn=9189 in=1     5B
    0x230D8,   # sub_230D8  dyn=8914 in=2    92B
    0x22846,   # sub_22846  dyn=8066 in=1     5B
    0x23134,   # sub_23134  dyn=7994 in=1    88B
    0x22850,   # sub_22850  dyn=7528 in=1     5B
]

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\level0_top10.json"

def main():
    print("=== Probing top 10 Level-0 functions ===")
    result = {}
    
    for ea in TARGETS:
        name = idc.get_func_name(ea)
        print("  {:05X}  {}".format(ea, name))
        
        func = idaapi.get_func(ea)
        if not func:
            result[hex(ea)] = {"error": "Not a function"}
            continue
        
        # Disassembly
        disasm = []
        ea_cur = func.start_ea
        while ea_cur < func.end_ea:
            disasm.append("  {:05X}  {}".format(ea_cur, idc.GetDisasm(ea_cur)))
            ea_cur = idc.next_head(ea_cur, func.end_ea)
        
        # Data refs
        data_refs = []
        ea_cur = func.start_ea
        while ea_cur < func.end_ea:
            for ref in idautils.DataRefsFrom(ea_cur):
                ref_name = idc.get_name(ref)
                data_refs.append({
                    "from": hex(ea_cur),
                    "to": hex(ref),
                    "name": ref_name if ref_name else None,
                })
            ea_cur = idc.next_head(ea_cur, func.end_ea)
        
        # Callers
        callers = []
        for xref in idautils.XrefsTo(ea, 0):
            if xref.type in [idc.fl_CN, idc.fl_CF]:
                caller_func = idaapi.get_func(xref.frm)
                if caller_func:
                    callers.append({
                        "from": hex(xref.frm),
                        "fn": idc.get_func_name(caller_func.start_ea),
                        "mnem": idc.print_insn_mnem(xref.frm),
                    })
        
        result[hex(ea)] = {
            "ea": hex(ea),
            "name": name,
            "size": func.end_ea - func.start_ea,
            "seg": idc.get_segm_name(ea),
            "disasm": disasm,
            "data_refs": data_refs,
            "callers": callers,
        }
    
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print("\nWrote {}".format(OUT))
    print("Run WITHOUT qexit() - database left open for inspection")

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
