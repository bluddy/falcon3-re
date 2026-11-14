"""Probe-copy experiment (DBFL_KILL): map the 21 R29-exclusive anchor selectors (+0x3FA8) to their
R29 paragraphs, re-create every direct far call/jmp whose operand segment is one of them, and measure."""
import json, traceback, collections, struct
import idaapi, idautils, idc, ida_bytes, ida_segment, ida_ua, ida_xref, ida_funcs
D = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/"
OUT = D + "exp_sel_all.json"
R = {}
try:
    A = json.load(open(D + "arena_resolve.json"))
    an = A["anchors"]
    r29x = sorted(set(an["R29"]) - set(an["R05"])) + [0x3FA8]
    R29 = 0x11C3C0
    sel = {a + 0x1000: (R29 >> 4) + (a - 0x1E10) for a in r29x}
    fn_before = [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions()]
    for s, p in sel.items():
        assert ida_segment.set_selector(s, p)
    rows = [r for r in A["rows"] if r["seg"] in sel]
    bad = []
    for r in rows:
        ea = r["ea"]
        sz = ida_bytes.get_item_size(ea)
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, sz)
        if ida_ua.create_insn(ea) != 5:
            bad.append(ea)
    c = collections.Counter()
    for r in rows:
        refs = [x.to for x in idautils.XrefsFrom(r["ea"], ida_xref.XREF_FAR) if x.iscode]
        want = R29 + ((r["seg"] - 0x1000) - 0x1E10) * 16 + r["off"]
        f = ida_funcs.get_func(want)
        c["ok" if refs and all(t == want for t in refs) else "mismatch"] += 1
        c["tgt_fs" if f and f.start_ea == want else ("tgt_mid" if f else "tgt_nofn")] += 1
    fn_after = [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions()]
    R.update({"sel": {"%X" % k: "%X" % v for k, v in sel.items()}, "rows": len(rows), "bad": bad[:20], "nbad": len(bad),
              "c": c, "fn_same": fn_before == fn_after, "nfn": len(fn_after),
              "lost": ["%X-%X %s" % (a, b, idc.get_name(a)) for a, b in sorted(set(fn_before) - set(fn_after))],
              "new": ["%X-%X" % (a, b) for a, b in sorted(set(fn_after) - set(fn_before))]})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
