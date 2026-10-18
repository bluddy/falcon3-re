#!/usr/bin/env python3
"""Finding 72 (IDA-side, read-only): dump disasm + CALLER and CALLEE context
for the Level-1 naming batches.  Callees are all at Level 0 (100% named in
f71), so each target shows its callees' semantic names -- the whole point of
bottom-up naming.

Reads targets from analysis/ida_falconcd/level1_batch1_targets.json (key 'A').
Writes analysis/ida_falconcd/level1_batch1_disasm.txt + _context.json.

Usage: cmd /c "tools\\run_idat.bat tools\\dump_level1.py"
"""
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
cg = json.load(open(os.path.join(ROOT, "analysis/traces/callgraph_partial.json"), encoding="utf-8"))
cls = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/classification.json"), encoding="utf-8"))
fb = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/function_bytes.json"), encoding="utf-8"))
_tf = os.environ.get("FALCON_L1_TARGETS") or os.path.join(
    ROOT, "analysis/ida_falconcd/level1_batch1_targets.json")
targets = json.load(open(_tf, encoding="utf-8"))["A"]
TAG = os.environ.get("FALCON_L1_TAG", "batch1")
levels = cg["node_levels"]; dyn = cg["dyn_target_calls"]; sin = cg["static_in_degree"]
cd = cg.get("caller_dyn_sum", {})
edges = [tuple(e) for e in cg["edges"]]

outg = {}
inc = {}
for a, b in edges:
    outg.setdefault(a, []).append(b)
    inc.setdefault(b, []).append(a)


def nm(k):
    n = fb.get(k, {}).get("name")
    return n if n else k


lines = []
ctx = []
lines.append("## LEVEL-1 BATCH (top 36 by dyn, caller_dyn, in) -- callees at Level 0")
for i, k in enumerate(targets, 1):
    v = cls[k]; ea = v["ea"]; size = v["size"]
    fn = ida_funcs.get_func(ea)
    end = fn.end_ea if fn else ea + size
    lines.append("=" * 70)
    lines.append("#%d %s  ea=0x%X  size=%d  class=%s  in=%d  dyn=%d  cd=%d" % (
        i, k, ea, size, v["class"], sin.get(k, 0), dyn.get(k, 0), cd.get(k, 0)))
    # ---- CALLEES with semantic names (the L1 context) ----
    callees = outg.get(k, [])
    if callees:
        lines.append("  --- callees (%d): %s" % (len(callees),
                     ", ".join("%s(L%d)" % (nm(c), levels.get(c, -1)) for c in sorted(set(callees)))))
    cur = ea; n = 0; body = []
    while cur < end and n < 300:
        h = ida_bytes.get_item_head(cur)
        if h != cur:
            cur = h + max(ida_bytes.get_item_size(h), 1); continue
        insn = ida_ua.insn_t()
        kk = ida_ua.decode_insn(insn, cur)
        if kk <= 0:
            body.append("  0x%X: <undecodable 0x%02X>" % (cur, ida_bytes.get_byte(cur)))
            break
        mn = idc.print_insn_mnem(cur)
        ops = ", ".join(idc.print_operand(cur, t) for t in range(3) if idc.print_operand(cur, t))
        crefs = [x for x in idautils.CodeRefsFrom(cur, 0)]
        extra = ""
        if crefs:
            extra = "  ->code %s" % [nm_c if (nm_c := idc.get_func_name(x)) else hex(x) for x in crefs]
        body.append("  0x%X: %-6s %s%s" % (cur, mn, ops, extra))
        n += 1
        if mn.lower() in ("retn", "retf", "ret", "iret"):
            body.append("  [TERM %s @ 0x%X]" % (mn.upper(), cur)); break
        cur += kk
    lines.extend(body)
    callers = sorted(set(inc.get(k, [])))
    lines.append("  --- callers (%d): %s" % (len(callers),
                 ", ".join("%s" % nm(c) for c in callers[:10])))
    if sin.get(k, 0) == 0:
        lines.append("  --- NO static caller (indirect far-call target)")
    lines.append("")
    ctx.append({"rank": i, "key": k, "ea": ea, "size": size, "class": v["class"],
                "in": sin.get(k, 0), "dyn": dyn.get(k, 0), "cd": cd.get(k, 0),
                "callees": [nm(c) for c in sorted(set(callees))],
                "callers": [nm(c) for c in callers], "body": body})

with open(os.path.join(ROOT, "analysis/ida_falconcd/level1_%s_disasm.txt" % TAG), "w") as f:
    f.write("\n".join(lines))
json.dump(ctx, open(os.path.join(ROOT, "analysis/ida_falconcd/level1_%s_context.json" % TAG), "w"), indent=1)
print("dumped %d Level-1 targets -> level1_%s_disasm.txt" % (len(targets), TAG))
idaapi.qexit(0)