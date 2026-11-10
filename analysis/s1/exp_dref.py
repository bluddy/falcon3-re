"""Probe (DBFL_KILL): (1) count code heads whose DS/ES sreg is an R29-exclusive selector and that carry
drefs into the R05 arena; (2) test whether create_insn on an existing head (no del_items) re-emulates refs."""
import json, traceback, collections
import idaapi, idautils, idc, ida_bytes, ida_segment, ida_ua, ida_xref, ida_funcs, ida_segregs, ida_idp
D = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/"
OUT = D + "exp_dref.json"
R = {"c": collections.Counter(), "eg": []}
try:
    A = json.load(open(D + "arena_resolve.json"))
    an = A["anchors"]
    r29x = sorted(set(an["R29"]) - set(an["R05"])) + [0x3FA8]
    sel = {a + 0x1000: (0x11C3C0 >> 4) + (a - 0x1E10) for a in r29x}
    DS, ES = ida_idp.str2reg("ds"), ida_idp.str2reg("es")
    heads = []
    for s in idautils.Segments():
        for h in idautils.Heads(s, ida_segment.getseg(s).end_ea):
            if not ida_bytes.is_code(ida_bytes.get_flags(h)):
                continue
            dv, ev = ida_segregs.get_sreg(h, DS), ida_segregs.get_sreg(h, ES)
            if dv in sel or ev in sel:
                dr = [x.to for x in idautils.XrefsFrom(h, 0) if not x.iscode]
                arena = [t for t in dr if 0x2E100 <= t < 0x669F0]
                R["c"]["heads_sel"] += 1
                if dr:
                    R["c"]["with_dref"] += 1
                if arena:
                    R["c"]["dref_into_r05arena"] += 1
                    heads.append(h)
    for s, p in sel.items():
        ida_segment.set_selector(s, p)
    fb = [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions()]
    for h in heads[:400]:
        before = sorted(x.to for x in idautils.XrefsFrom(h, 0) if not x.iscode)
        n = ida_ua.create_insn(h)
        after = sorted(x.to for x in idautils.XrefsFrom(h, 0) if not x.iscode)
        R["c"]["recreate_changed" if before != after else "recreate_same"] += 1
        if before != after and len(R["eg"]) < 8:
            R["eg"].append(["%X" % h, idc.generate_disasm_line(h, 0), ["%X" % t for t in before], ["%X" % t for t in after]])
    R["fn_same"] = fb == [(f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions()]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
