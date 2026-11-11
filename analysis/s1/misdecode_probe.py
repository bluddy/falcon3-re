"""misdecode_probe.py: enumerate all 'not_head' mid-body call targets (read-only, DBFL_KILL).
For each call target t where t is NOT on an instruction head inside the owning function,
emit both alignments of disassembly around t.
Output: analysis/s1/misdecode_all.json
"""
import os
os.environ["DBFL_KILL"] = "1"
import json
import collections
import traceback

import idaapi
import ida_bytes
import ida_funcs
import ida_ua
import ida_idp
import idc
import idautils

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\misdecode_all.json"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}

def disasm_range(lo, hi, max_insns=10):
    """Disassemble up to max_insns instructions starting at lo, stopping at hi."""
    out = []
    a = lo
    while a < hi and len(out) < max_insns:
        n = ida_bytes.get_item_size(a) if ida_bytes.is_code(ida_bytes.get_flags(a)) else 0
        if n > 0:
            out.append({"ea": "%X" % a, "text": idc.generate_disasm_line(a, 0), "size": n})
            a += n
        else:
            # try to decode as instruction
            insn = ida_ua.insn_t()
            n = ida_ua.decode_insn(insn, a)
            if n > 0:
                out.append({"ea": "%X" % a, "text": "? " + idc.generate_disasm_line(a, 0), "size": n})
                a += n
            else:
                out.append({"ea": "%X" % a, "text": "db %02X" % (ida_bytes.get_byte(a) & 0xFF), "size": 1})
                a += 1
    return out

try:
    results = []
    tg = collections.defaultdict(list)
    for fea in idautils.Functions():
        for item in idautils.FuncItems(fea):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, item) or not ida_idp.is_call_insn(insn):
                continue
            if insn.ops[0].type not in (idaapi.o_near, idaapi.o_far):
                continue
            for t in idautils.CodeRefsFrom(item, 0):
                g = ida_funcs.get_func(t)
                if g and g.start_ea != t:
                    tg[t].append(item)

    for t, callers in tg.items():
        if ida_bytes.get_item_head(t) == t:
            continue  # on a head: not a misdecode
        g = ida_funcs.get_func(t)
        if not g:
            continue
        # find the containing instruction head
        head = ida_bytes.get_item_head(t)
        if head == idaapi.BADADDR:
            continue
        # disassemble from head (current alignment)
        disasm_at_head = disasm_range(head, min(t + 20, g.end_ea), 5)
        # disassemble from t (target alignment)
        disasm_at_t = disasm_range(t, min(t + 20, g.end_ea), 5)
        # bytes around t
        ctx_lo = max(head - 4, g.start_ea)
        ctx_bytes = " ".join("%02X" % (ida_bytes.get_byte(a) & 0xFF) for a in range(ctx_lo, min(t + 8, g.end_ea)))
        results.append({
            "t": "%X" % t,
            "fn": "%X" % g.start_ea,
            "fn_name": idc.get_func_name(g.start_ea) or "",
            "fn_end": "%X" % g.end_ea,
            "head": "%X" % head,
            "offset_into_insn": t - head,
            "callers": len(callers),
            "caller_exa": ["%X" % c for c in callers[:3]],
            "ctx_bytes": ctx_bytes,
            "disasm_at_head": disasm_at_head,
            "disasm_at_t": disasm_at_t,
        })

    results.sort(key=lambda x: int(x["fn"], 16))
    open(OUT, "w").write(json.dumps({"total": len(results), "targets": results}, indent=1))
except Exception:
    open(OUT, "w").write(json.dumps({"error": traceback.format_exc()}))

idc.qexit(0)
