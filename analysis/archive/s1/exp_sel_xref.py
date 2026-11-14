"""Probe-copy experiment (DBFL_KILL): selector mapping + cref swap only (no del_items)."""
import json, traceback, collections
import idaapi, idautils, idc, ida_bytes, ida_segment, ida_ua, ida_xref, ida_funcs
D = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/"
OUT = D + "exp_sel_xref.json"
R = {}
try:
    A = json.load(open(D + "arena_resolve.json"))
    an = A["anchors"]
    r29x = sorted(set(an["R29"]) - set(an["R05"])) + [0x3FA8]
    R29 = 0x11C3C0
    sel = {a + 0x1000: (R29 >> 4) + (a - 0x1E10) for a in r29x}
    fn_before = [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions()]
    items_before = sum(1 for _ in idautils.Heads(0x2E100, 0x669F0))
    for s, p in sel.items():
        assert ida_segment.set_selector(s, p)
    rows = [r for r in A["rows"] if r["seg"] in sel]
    c = collections.Counter()
    for r in rows:
        ea = r["ea"]
        want = R29 + ((r["seg"] - 0x1000) - 0x1E10) * 16 + r["off"]
        ft = ida_xref.fl_CF if r["op"] == 0x9A else ida_xref.fl_JF
        for x in list(idautils.XrefsFrom(ea, ida_xref.XREF_FAR)):
            if x.iscode and x.to != want and x.type in (ida_xref.fl_CF, ida_xref.fl_JF):
                ida_xref.del_cref(ea, x.to, 0)
                c["del"] += 1
        ida_xref.add_cref(ea, want, ft | ida_xref.XREF_USER)
    for r in rows:
        want = R29 + ((r["seg"] - 0x1000) - 0x1E10) * 16 + r["off"]
        refs = [x.to for x in idautils.XrefsFrom(r["ea"], ida_xref.XREF_FAR) if x.iscode and x.type in (ida_xref.fl_CF, ida_xref.fl_JF)]
        c["ok" if refs == [want] else "mismatch"] += 1
        c["disasm_ok" if ("%X" % want) in idc.generate_disasm_line(r["ea"], 0).upper() or idc.get_name(want) in idc.generate_disasm_line(r["ea"], 0) else "disasm_other"] += 1
    fn_after = [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions()]
    items_after = sum(1 for _ in idautils.Heads(0x2E100, 0x669F0))
    R.update({"rows": len(rows), "c": c, "fn_same": fn_before == fn_after, "nfn": len(fn_after),
              "items_r05": [items_before, items_after], "auto_ok": idaapi.auto_is_ok(),
              "diff": [["%X-%X" % ab for ab in sorted(set(fn_before) - set(fn_after))], ["%X-%X" % ab for ab in sorted(set(fn_after) - set(fn_before))]]})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
