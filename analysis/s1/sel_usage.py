"""Read-only: who uses the paragraph values of R29-only anchors (and 0x3FA8 etc.) as selectors:
segment-register ranges, fixups, far operands."""
import json, traceback, collections
import idaapi, idautils, idc, ida_segment, ida_segregs, ida_fixup, ida_idp
D = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/"
OUT = D + "sel_usage.json"
R = {"sreg": collections.Counter(), "fix": collections.Counter(), "fix_eg": {}, "sel_table": []}
try:
    A = json.load(open(D + "arena_resolve.json"))["anchors"]
    r05 = set(A["R05"])
    cand = sorted(set(a for k in ("R27", "R28", "R29") for a in A[k]) - r05) + [0x3FA8, 0x1F86, 0x1F02]
    paras = {a + 0x1000 for a in cand} | set(range(0x2E10, 0x669F))  # whole arena paragraph range
    want = {a + 0x1000 for a in cand}
    for i in range(ida_segment.get_selector_qty()):
        s = ida_segment.getn_selector(i)
        R["sel_table"].append([s[1] if isinstance(s, tuple) else s, ida_segment.sel2para(s[1] if isinstance(s, tuple) else s)])
    names = {ida_idp.str2reg("ds"): "ds", ida_idp.str2reg("es"): "es", ida_idp.str2reg("ss"): "ss", ida_idp.str2reg("cs"): "cs"}
    for rg, nm in names.items():
        n = ida_segregs.get_sreg_ranges_qty(rg)
        for i in range(n):
            r = ida_segregs.sreg_range_t()
            ida_segregs.getn_sreg_range(r, rg, i)
            v = r.val
            if 0x2E10 <= v < 0x669F:
                seg = ida_segment.getseg(r.start_ea)
                R["sreg"]["%s=%X in %s %s" % (nm, v, ida_segment.get_segm_name(seg)[:3] if seg else None, "R29anchor" if v in want else "arena")] += 1
    ea = ida_fixup.get_first_fixup_ea()
    while ea != idaapi.BADADDR:
        fd = ida_fixup.fixup_data_t()
        if ida_fixup.get_fixup(fd, ea):
            s = fd.sel
            if 0x2E10 <= s < 0x669F:
                seg = ida_segment.getseg(ea)
                k = "sel=%X src=%s %s" % (s, ida_segment.get_segm_name(seg)[:3] if seg else None, "R29anchor" if s in want else "arena")
                R["fix"][k] += 1
                R["fix_eg"].setdefault(k, "%X" % ea)
        ea = ida_fixup.get_next_fixup_ea(ea)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
