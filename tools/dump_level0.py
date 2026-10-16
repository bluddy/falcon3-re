"""Disassemble top Level-0 endpoints for identification (safe: read-only).

Reads existing item heads via next_head — never del_items (that deletion
persisted and destroyed 4 fns, finding 39).

Usage: cmd /c "tools\\run_idat.bat tools\\dump_level0.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import idaapi
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\level0_disasm.log"
CG = r"C:\Users\yotam\projects\falcon3\analysis\traces\callgraph_partial.json"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"

# batch range: L0_START..L0_END over the dyn-sorted Level-0 list (finding 39+)
import os
L0_START = int(os.environ.get("L0_START", "0"))
L0_END = int(os.environ.get("L0_END", "24"))
N = L0_END

log = []
try:
    cg = json.loads(open(CG).read())
    cls = json.loads(open(CLS).read())
    lvl0 = [k for k in cg["levels"][0] if k in cls]
    lvl0.sort(key=lambda k: -cg["dyn_target_calls"].get(k, 0))
    top = lvl0[L0_START:L0_END]
    log.append("batch [%d:%d] of %d endpoints" % (L0_START, L0_END, len(lvl0)))

    for name in top:
        ea = cls[name]["ea"]
        f = ida_funcs.get_func(ea)
        if not f:
            log.append("%s @0x%X: NO FUNC" % (name, ea))
            continue
        log.append("=== %s  0x%X..0x%X (%dB)  dyn=%d ===" %
                   (name, f.start_ea, f.end_ea, f.end_ea - f.start_ea,
                    cg["dyn_target_calls"].get(name, 0)))
        pos = f.start_ea
        n = 0
        while pos < f.end_ea and n < 80:
            mn = idc.print_insn_mnem(pos) or "??"
            o1 = idc.print_operand(pos, 0) or ""
            o2 = idc.print_operand(pos, 1) or ""
            o3 = idc.print_operand(pos, 2) or ""
            log.append("  0x%X: %-5s %s %s %s" % (pos, mn, o1, o2, o3))
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                log.append("    <zero-size item>")
                break
            pos += sz
            n += 1
        # incoming callers (top few)
        import idautils
        callers = []
        for h in idautils.Heads(f.start_ea, f.end_ea):
            for fr in idautils.CodeRefsTo(h, 0):
                cf = ida_funcs.get_func(fr)
                if cf:
                    callers.append(idc.get_func_name(cf.start_ea) or hex(cf.start_ea))
        uniq = sorted(set(callers))
        log.append("  callers(%d uniq): %s" % (len(uniq), ", ".join(uniq[:12])))
        log.append("")

except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
