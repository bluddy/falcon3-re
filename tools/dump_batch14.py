#!/usr/bin/env python3
"""Finding 71 (IDA-side, read-only): dump disasm+context for Batch 7 = Slice A
(top 18 dyn>=10 Level-0) + Slice B (top 18 dyn==0 flag-ranked Level-0).
Reads targets from analysis/ida_falconcd/batch14_targets.json.
Writes analysis/ida_falconcd/batch14_disasm.txt + batch14_context.json.

Usage: cmd /c "tools\\run_idat.bat tools\\dump_batch14.py"
"""
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
cg = json.load(open(os.path.join(ROOT, "analysis/traces/callgraph_partial.json"), encoding="utf-8"))
cls = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/classification.json"), encoding="utf-8"))
fb = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/function_bytes.json"), encoding="utf-8"))
levels = cg["node_levels"]; dyn = cg["dyn_target_calls"]; sin = cg["static_in_degree"]
cd = cg.get("caller_dyn_sum", {})
edges = [tuple(e) for e in cg["edges"]]
_t = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/batch14_targets.json"), encoding="utf-8"))
sliceA = _t["A"]; sliceB = _t["B"]

callers = {}
for a, b in edges:
    callers.setdefault(b, []).append(a)

lines = []
ctx = []
for label, targets in (("L0-SLICE (top 36)", sliceA),
                        ("", sliceB)):
    lines.append("#" * 70)
    lines.append("## %s" % label)
    lines.append("#" * 70)
    for i, k in enumerate(targets, 1):
        v = cls[k]; ea = v["ea"]; size = v["size"]
        fn = ida_funcs.get_func(ea)
        end = fn.end_ea if fn else ea + size
        lines.append("=" * 70)
        lines.append("%s #%d %s  ea=0x%X  size=%d  class=%s  in=%d  dyn=%d  cd=%d  fb=%s" % (
            label.split()[0], i, k, ea, size, v["class"],
            sin.get(k, 0), dyn.get(k, 0), cd.get(k, 0), fb.get(k, {}).get("name")))
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
            crefs = [hex(x) for x in idautils.CodeRefsFrom(cur, 0)]
            dref = [hex(x) for x in idautils.DataRefsFrom(cur)]
            extra = ""
            if crefs: extra += "  ->code %s" % crefs
            if dref: extra += "  ->data %s" % dref
            body.append("  0x%X: %-6s %s%s" % (cur, mn, ops, extra))
            n += 1
            if mn.lower() in ("retn", "retf", "ret", "iret"):
                body.append("  [TERM %s @ 0x%X]" % (mn.upper(), cur)); break
            cur += kk
        lines.extend(body)
        cl = sorted(set(callers.get(k, [])))
        lines.append("  --- callers (%d): %s" % (len(cl), ", ".join(cl[:10])))
        for c in cl[:8]:
            cv = cls.get(c, {})
            lines.append("      %s ea=0x%X cls=%s dyn=%d" % (c, cv.get("ea",0), cv.get("class","?"), dyn.get(c,0)))
        if sin.get(k, 0) == 0:
            lines.append("  --- NO static caller (indirect far-call target)")
        lines.append("")
        ctx.append({"slice": label.split()[0], "rank": i, "key": k, "ea": ea,
                    "size": size, "class": v["class"], "in": sin.get(k,0),
                    "dyn": dyn.get(k,0), "cd": cd.get(k,0),
                    "callers": cl, "body": body})

with open(os.path.join(ROOT, "analysis/ida_falconcd/batch14_disasm.txt"), "w") as f:
    f.write("\n".join(lines))
json.dump(ctx, open(os.path.join(ROOT, "analysis/ida_falconcd/batch14_context.json"), "w"), indent=1)
print("dumped SliceA=%d SliceB=%d -> batch14_disasm.txt + batch14_context.json" % (len(sliceA), len(sliceB)))
idaapi.qexit(0)