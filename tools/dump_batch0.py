#!/usr/bin/env python3
"""Finding 66 (IDA-side, read-only): dump full disassembly + caller context for
the Top-30 unnamed Level-0 naming_queue functions from callgraph_partial.json.
Writes analysis/ida_falconcd/batch0_disasm.txt (readable) + batch0_context.json.

Usage: cmd /c "tools\\run_idat.bat tools\\dump_batch0.py"
"""
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
cg = json.load(open(os.path.join(ROOT, "analysis/traces/callgraph_partial.json"), encoding="utf-8"))
cls = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/classification.json"), encoding="utf-8"))
fb = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/function_bytes.json"), encoding="utf-8"))
levels = cg["node_levels"]; dyn = cg["dyn_target_calls"]; sin = cg["static_in_degree"]
queue = set(cg["naming_queue"]); edges = [tuple(e) for e in cg["edges"]]

lvl0 = [k for k in levels if levels[k] == 0 and k in queue]
lvl0.sort(key=lambda k: (-dyn.get(k, 0), -sin.get(k, 0), cls[k]["ea"]))
targets = lvl0[:30]

# caller map
callers = {}
for a, b in edges:
    callers.setdefault(b, []).append(a)

lines = []
ctx = []
for i, k in enumerate(targets, 1):
    v = cls[k]; ea = v["ea"]; size = v["size"]
    fn = ida_funcs.get_func(ea)
    end = fn.end_ea if fn else ea + size
    lines.append("=" * 70)
    lines.append("#%d %s  ea=0x%X  size=%d  class=%s  in=%d  dyn=%d  fb_name=%s" % (
        i, k, ea, size, v["class"], sin.get(k, 0), dyn.get(k, 0),
        fb.get(k, {}).get("name")))
    # decode full body
    cur = ea; n = 0; body = []
    while cur < end and n < 400:
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
        # refs
        crefs = [hex(x) for x in idautils.CodeRefsFrom(cur, 0)]
        dref = [hex(x) for x in idautils.DataRefsFrom(cur)]
        extra = ""
        if crefs: extra += "  ->code %s" % crefs
        if dref: extra += "  ->data %s" % dref
        body.append("  0x%X: %-6s %s%s" % (cur, mn, ops, extra))
        n += 1
        if mn.lower() in ("retn", "retf", "ret", "iret"):
            body.append("  [TERMINATOR %s @ 0x%X]" % (mn.upper(), cur))
            break
        cur += kk
    lines.extend(body)
    # caller context (up to 8)
    cl = sorted(set(callers.get(k, [])))
    lines.append("  --- callers (%d): %s" % (len(cl), ", ".join(cl[:8])))
    for c in cl[:6]:
        cv = cls.get(c, {})
        lines.append("      %s ea=0x%X class=%s dyn=%d" % (c, cv.get("ea", 0), cv.get("class", "?"), dyn.get(c, 0)))
    # if in_deg==0 note
    if sin.get(k, 0) == 0:
        lines.append("  --- NO static caller (indirect far-call dispatch target)")
    lines.append("")
    ctx.append({"rank": i, "key": k, "ea": ea, "size": size,
                "class": v["class"], "in": sin.get(k, 0), "dyn": dyn.get(k, 0),
                "callers": cl, "body": body})

with open(os.path.join(ROOT, "analysis/ida_falconcd/batch0_disasm.txt"), "w") as f:
    f.write("\n".join(lines))
json.dump(ctx, open(os.path.join(ROOT, "analysis/ida_falconcd/batch0_context.json"), "w"), indent=1)
print("dumped %d functions -> batch0_disasm.txt + batch0_context.json" % len(targets))
idaapi.qexit(0)