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

# batch range: L0_START..L0_END over the dyn-sorted Level-N list (finding 39+)
# LVL selects the callgraph level (0 = endpoints, 1 = their callers, ...)
import os
LVL = int(os.environ.get("LVL", "0"))
L0_START = int(os.environ.get("L0_START", "0"))
L0_END = int(os.environ.get("L0_END", "24"))
N = L0_END

log = []
try:
    cg = json.loads(open(CG).read())
    cls = json.loads(open(CLS).read())
    # semantic names from function_bytes.json (written by naming.py apply) --
    # IDAPython has NO PyYAML, so reading naming.yaml here always failed and
    # silently fell back to led={} (finding 45).
    fb = json.loads(open(
        r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\function_bytes.json"
    ).read())
    led = {k: v["name"] for k, v in fb.items() if v.get("name")}
    log.append("ledger names loaded from function_bytes: %d" % len(led))
    # exclude already-named nodes so L0_START/L0_END index the *unnamed*
    # list (otherwise batch slices drift as the ledger grows)
    lvl0 = [k for k in cg["levels"][LVL] if k in cls and k not in led]
    lvl0.sort(key=lambda k: -cg["dyn_target_calls"].get(k, 0))
    top = lvl0[L0_START:L0_END]
    log.append("level %d batch [%d:%d] of %d UNNAMED nodes" % (LVL, L0_START, L0_END, len(lvl0)))

    # callee list per node (outgoing static edges)
    import json as _j
    edges = _j.loads(open(
        r"C:\Users\yotam\projects\falcon3\analysis\traces\callgraph_partial.json",
        encoding="utf-8").read())["edges"]
    callees = {}
    for a, b in edges:
        callees.setdefault(a, []).append(b)

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
        # outgoing callees (this is what makes Level-1 interpretable)
        outs = callees.get(name, [])
        if outs:
            parts = []
            for c in sorted(set(outs)):
                if c in led:
                    parts.append("%s<=%s" % (c, led[c]))
                elif c in cls:
                    parts.append("%s(%dB,%s)" % (c, cls[c]["size"], cls[c]["class"]))
                else:
                    parts.append("%s(?)" % c)
            log.append("  callees(%d): %s" % (len(set(outs)), ", ".join(parts[:14])))
        log.append("")

except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
