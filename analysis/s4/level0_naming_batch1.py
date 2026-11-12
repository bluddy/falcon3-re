#!/usr/bin/env python3
"""IDA probe: Level-0 naming batch 1 (top 10 hottest leaf functions).

Extracts disassembly, data refs, caller context for the 10 most frequently-
called Level-0 leaf functions (0 callees, ranked by dyn_calls DESC).

RUN: ida64 -A -S"level0_naming_batch1.py" FALCONCD.EXE.i64
"""
import json
import idc
import idaapi
import idautils

# Top 10 Level-0 functions from callgraph_partial.json (ranked by dyn DESC)
TARGETS = [
    ("sub_263F6", 0x263F6, 122),   # dyn=18079 in=8
    ("sub_12890", 0x12890, 5),      # dyn=11513 in=1
    ("sub_2295C", 0x2295C, 2),      # dyn=11154 in=6
    ("sub_22436", 0x22436, 5),      # dyn=9698 in=5
    ("sub_2243B", 0x2243B, 5),      # dyn=9698 in=5
    ("sub_2284B", 0x2284B, 5),      # dyn=9189 in=1
    ("sub_230D8", 0x230D8, 92),     # dyn=8914 in=2
    ("sub_22846", 0x22846, 5),      # dyn=8066 in=1
    ("sub_23134", 0x23134, 88),     # dyn=7994 in=1
    ("sub_22850", 0x22850, 5),      # dyn=7528 in=1
]

OUT = "C:\\Users\\ybarnoy\\projects\\falcon3\\analysis\\s4\\level0_naming_batch1.json"

def get_func_disasm(ea):
    """Get disassembly lines for a function."""
    func = idaapi.get_func(ea)
    if not func:
        return []
    lines = []
    ea_cur = func.start_ea
    while ea_cur < func.end_ea:
        disasm = idc.GetDisasm(ea_cur)
        lines.append("  {:05X}  {}".format(ea_cur, disasm))
        ea_cur = idc.next_head(ea_cur, func.end_ea)
    return lines

def get_data_refs(ea):
    """Get all data references in the function."""
    func = idaapi.get_func(ea)
    if not func:
        return []
    refs = []
    ea_cur = func.start_ea
    while ea_cur < func.end_ea:
        for ref in idautils.DataRefsFrom(ea_cur):
            name = idc.get_name(ref)
            val_bytes = idc.get_bytes(ref, 2)
            val = None
            if val_bytes:
                val = int.from_bytes(val_bytes, 'little')
            refs.append({
                "from_ea": hex(ea_cur),
                "to_ea": hex(ref),
                "name": name if name else None,
                "value": hex(val) if val is not None else None,
            })
        ea_cur = idc.next_head(ea_cur, func.end_ea)
    return refs

def get_callers(ea):
    """Get all functions that call this address."""
    callers = []
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:  # near/far call
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(caller_func.start_ea)
                # get a few lines of context around the call site
                context = []
                ctx_start = max(caller_func.start_ea, xref.frm - 6)  # 2-3 instructions before
                ctx_end = min(caller_func.end_ea, xref.frm + 12)     # 2-3 instructions after
                ea_ctx = ctx_start
                while ea_ctx < ctx_end:
                    prefix = ">>> " if ea_ctx == xref.frm else "    "
                    disasm_line = idc.GetDisasm(ea_ctx)
                    context.append("{}{:05X}  {}".format(prefix, ea_ctx, disasm_line))
                    ea_ctx = idc.next_head(ea_ctx, ctx_end)
                
                callers.append({
                    "from": hex(xref.frm),
                    "fn": caller_name,
                    "mnem": idc.print_insn_mnem(xref.frm),
                    "context": context,
                })
    return callers

def main():
    idaapi.auto_wait()  # Wait for auto-analysis to complete
    
    result = {}
    for name, ea, size in TARGETS:
        print("Analyzing {} at 0x{:X}...".format(name, ea))
        result[name] = {
            "ea": hex(ea),
            "size": size,
            "seg": idc.get_segm_name(ea),
            "disasm": get_func_disasm(ea),
            "data_refs": get_data_refs(ea),
            "callers": get_callers(ea),
        }
    
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print("\nWrote {}".format(OUT))
    idc.qexit(0)  # Exit IDA after completion

if __name__ == "__main__":
    main()

