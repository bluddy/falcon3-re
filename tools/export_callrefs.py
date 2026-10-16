"""Export raw call/jump references from IDA for call-graph construction.

Emits every non-flow code reference (explicit CALL/JMP targets — flow=0 so
we exclude the implicit fall-through-to-next-instruction) as
[src_ea, dst_ea, is_call]. Host side resolves both ends to functions using
classification.json intervals (so MID/tail-jump cases stay visible).

Output: analysis/ida_falconcd/callgraph_refs.json
  {"refs": [[src, dst, is_call], ...], "n_functions": N}

Usage: cmd /c "tools\\run_idat.bat tools\\export_callrefs.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_ua
import idaapi
import idautils

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\callgraph_refs.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\export_refs.log"

log = []
try:
    fns = list(idautils.Functions())
    refs = []
    for fea in fns:
        f = ida_funcs.get_func(fea)
        for h in idautils.Heads(f.start_ea, f.end_ea):
            mnem = (idc_mnem := ida_ua.print_insn_mnem(h)) or ""
            is_call = mnem.lower().startswith("call")
            is_jmp = mnem.lower().startswith("jmp")
            if not (is_call or is_jmp):
                continue
            # flow=0 -> only explicit (non-fallthrough) code refs
            for dst in idautils.CodeRefsFrom(h, 0):
                refs.append([h, dst, 1 if is_call else 0])
    json.dump({"refs": refs, "n_functions": len(fns)}, open(OUT, "w"))
    n_call = sum(1 for r in refs if r[2])
    log.append("functions: %d" % len(fns))
    log.append("refs: %d (calls=%d jmps=%d)" % (len(refs), n_call, len(refs) - n_call))
    log.append("wrote %s" % OUT)
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
