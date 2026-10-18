#!/usr/bin/env python3
"""Finding 74 prep (IDA-side, read-only): dump FULL bodies (no early break at
first terminator) for Level-3 targets whose dump_level1 output was truncated.

Reads keys from analysis/ida_falconcd/full_dump_targets.json (key 'A').
Writes analysis/ida_falconcd/full_dump_disasm.txt.

Usage: cmd /c "tools\\run_idat.bat tools\\dump_full.py"
"""
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
cg = json.load(open(os.path.join(ROOT, "analysis/traces/callgraph_partial.json"), encoding="utf-8"))
fb = json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/function_bytes.json"), encoding="utf-8"))
_tf = os.environ.get("FALCON_FULL_TARGETS") or os.path.join(
    ROOT, "analysis/ida_falconcd/full_dump_targets.json")
targets = json.load(open(_tf, encoding="utf-8"))["A"]
levels = cg["node_levels"]
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
for k in targets:
    ea = fb[k]["ea"]; size = fb[k]["size"]
    fn = ida_funcs.get_func(ea)
    end = fn.end_ea if fn else ea + size
    callees = outg.get(k, [])
    callers = sorted(set(inc.get(k, [])))
    lines.append("=" * 70)
    lines.append("%s  ea=0x%X  size=%d  L%d  in=%d" % (
        k, ea, size, levels.get(k, -1), len(callers)))
    if callees:
        lines.append("  --- callees (%d): %s" % (len(callees),
                     ", ".join("%s(L%d)" % (nm(c), levels.get(c, -1)) for c in sorted(set(callees)))))
    cur = ea; n = 0
    while cur < end and n < 4000:
        h = ida_bytes.get_item_head(cur)
        if h != cur:
            cur = h + max(ida_bytes.get_item_size(h), 1); continue
        insn = ida_ua.insn_t()
        kk = ida_ua.decode_insn(insn, cur)
        if kk <= 0:
            lines.append("  0x%X: <undecodable 0x%02X>" % (cur, ida_bytes.get_byte(cur)))
            cur += 1; continue
        mn = idc.print_insn_mnem(cur)
        ops = ", ".join(idc.print_operand(cur, t) for t in range(3) if idc.print_operand(cur, t))
        crefs = [x for x in idautils.CodeRefsFrom(cur, 0)]
        extra = ""
        if crefs:
            extra = "  ->code %s" % [idc.get_func_name(x) or hex(x) for x in crefs]
        lines.append("  0x%X: %-6s %s%s" % (cur, mn, ops, extra))
        n += 1
        cur += kk
    lines.append("  --- callers: %s" % ", ".join(nm(c) for c in callers[:14]))
    lines.append("")

with open(os.path.join(ROOT, "analysis/ida_falconcd/full_dump_disasm.txt"), "w") as f:
    f.write("\n".join(lines))
print("dumped %d full bodies" % len(targets))
idaapi.qexit(0)