"""Export per-function epilogue facts from IDA (read-only).

`classify_routines.py` decides DATA vs ASM from the raw byte string, which
only tests for a trailing `c3`/`cb`. That misses tail jumps (`jmp`/`iret`/
`hlt`/`int`), `ret imm16` (`c2`), `retf imm16` (`ca`) and any range that
runs a few bytes past its final `retn` -- so it labelled ~130 real routines
as DATA (finding 49). This script records what IDA actually decoded as the
last instruction, plus the call-ref facts needed to spot merged ranges.

Output: analysis/ida_falconcd/last_insns.json
  (named to avoid analysis/ida_falconcd/epilogues.json, which
   extract_prologues.py owns -- that file is {hex-pattern: count} for
   compiler fingerprinting, a different schema entirely.)
  { <ida_name>: {ea, size, last_mnem, ncallers, interior_refs, interior_eas} }

No del_items, no save -- strictly read-only (runbook rule 3).
"""
import json

import ida_bytes
import ida_funcs
import idaapi
import idautils
import idc

OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\last_insns.json"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"

cls = json.loads(open(CLS).read())
out = {}
log = []

for nm, info in cls.items():
    ea = info.get("ea")
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        continue

    # last instruction that actually decoded (stop at a zero-size gap)
    pos, last, ninstr = f.start_ea, None, 0
    while pos < f.end_ea:
        m = idc.print_insn_mnem(pos)
        if m:
            last = m
            ninstr += 1
        sz = ida_bytes.get_item_size(pos)
        if sz <= 0:
            break
        pos += sz

    # external call refs: to the start vs to interior addresses
    callers, interior = set(), []
    for h in idautils.Heads(f.start_ea, f.end_ea):
        for fr in idautils.CodeRefsTo(h, 0):
            cf = ida_funcs.get_func(fr)
            if not cf or cf.start_ea == f.start_ea:
                continue
            src = idc.get_func_name(cf.start_ea) or hex(cf.start_ea)
            if h == f.start_ea:
                callers.add(src)
            else:
                interior.append((h, src))

    out[nm] = {
        "ea": ea,
        "size": f.end_ea - f.start_ea,
        "last_mnem": (last or "").lower(),
        "ninstr": ninstr,
        "ncallers": len(callers),
        "interior_refs": len(interior),
        "interior_eas": sorted({hex(h) for h, _ in interior}),
    }

json.dump(out, open(OUT, "w"), indent=1)

from collections import Counter
c = Counter(v["last_mnem"] for v in out.values())
log.append("epilogues for %d functions -> %s" % (len(out), OUT))
log.append("last_mnem histogram: %s" % dict(c.most_common()))
log.append("functions with >=1 external caller : %d" %
           sum(1 for v in out.values() if v["ncallers"]))
log.append("functions with interior external ref: %d" %
           sum(1 for v in out.values() if v["interior_refs"]))
open(OUT + ".log", "w").write("\n".join(log))
idaapi.qexit(0)
