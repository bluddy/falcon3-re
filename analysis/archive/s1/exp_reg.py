"""Probe (DBFL_KILL): register the R29 entries exposed by S1a with flow-based add_func(ea), iterating over
near/far call targets inside the new functions; measure side effects."""
import json, traceback, collections, hashlib
import idaapi, idautils, idc, ida_bytes, ida_funcs, ida_ua, ida_segment, ida_xref, ida_idp, ida_auto
ROOT = "C:/Users/ybarnoy/projects/falcon3/"
OUT = ROOT + "analysis/s1/exp_reg.json"
R = {"rounds": [], "fns": [], "fail": [], "c": collections.Counter()}
def chunks(f):
    it = ida_funcs.func_tail_iterator_t(f); out = []; ok = it.main()
    while ok:
        c = it.chunk(); out.append([c.start_ea, c.end_ea]); ok = it.next()
    return out
def items(lo, hi):
    return [(h, ida_bytes.get_item_size(h), ida_bytes.is_code(ida_bytes.get_flags(h))) for h in idautils.Heads(lo, hi)]
try:
    doc = json.load(open(ROOT + "registry/variant_sel_expected.json"))
    S = [(ida_segment.get_segm_name(s), s.start_ea, s.end_ea) for s in map(ida_segment.getseg, idautils.Segments())]
    r29 = [(n, a, b) for n, a, b in S if n.startswith("R29")]
    lo29, hi29 = r29[0][1], r29[-1][2]
    in29 = lambda ea: lo29 <= ea < hi29
    fn0 = {f: ida_funcs.get_func(f).end_ea for f in idautils.Functions()}
    it0 = items(lo29, hi29); outside0 = sum(1 for _ in idautils.Heads(0, lo29)) + sum(1 for _ in idautils.Heads(hi29, idaapi.BADADDR))
    todo = sorted({c["to"] for c in doc["crefs"] if in29(c["to"]) and not (ida_funcs.get_func(c["to"]) and ida_funcs.get_func(c["to"]).start_ea == c["to"])})
    seen = set()
    rnd = 0
    while todo and rnd < 8:
        rnd += 1
        added = []
        for ea in todo:
            seen.add(ea)
            g = ida_funcs.get_func(ea)
            if g:
                R["fail"].append([ea, "inside", g.start_ea, rnd]); continue
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_data(fl) or (ida_bytes.is_code(fl) is False and ida_bytes.get_item_head(ea) != ea and not ida_bytes.is_unknown(fl)):
                R["fail"].append([ea, "data/tail", None, rnd]); continue
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) != ea:
                R["fail"].append([ea, "mid-insn", ida_bytes.get_item_head(ea), rnd]); continue
            ok = ida_funcs.add_func(ea)
            f = ida_funcs.get_func(ea)
            if not ok or not f or f.start_ea != ea:
                R["fail"].append([ea, "add_func", f.start_ea if f else None, rnd]); continue
            added.append(ea)
        nxt = set()
        for ea in added:
            f = ida_funcs.get_func(ea)
            for h in idautils.FuncItems(ea):
                insn = ida_ua.insn_t(); ida_ua.decode_insn(insn, h)
                if not ida_idp.is_call_insn(insn): continue
                for t in idautils.CodeRefsFrom(h, 0):
                    g = ida_funcs.get_func(t)
                    if in29(t) and t not in seen and not (g and g.start_ea == t):
                        nxt.add(t)
        R["rounds"].append([rnd, len(todo), len(added), len(nxt)])
        todo = sorted(nxt)
    fn1 = {f: ida_funcs.get_func(f).end_ea for f in idautils.Functions()}
    R["changed_old"] = [[f, e, fn1.get(f)] for f, e in fn0.items() if fn1.get(f) != e]
    new = sorted(set(fn1) - set(fn0))
    for f in new:
        g = ida_funcs.get_func(f)
        ch = chunks(g)
        R["fns"].append({"ea": f, "end": g.end_ea, "chunks": ch, "seg": ida_segment.get_segm_name(ida_segment.getseg(f)),
                         "n": sum(1 for _ in idautils.FuncItems(f)), "flags": g.flags})
    # item side effects
    it1 = items(lo29, hi29)
    s0 = {h: (sz, c) for h, sz, c in it0}; s1 = {h: (sz, c) for h, sz, c in it1}
    R["c"]["r29_items"] = [len(s0), len(s1)]
    R["c"]["old_items_changed"] = sum(1 for h, v in s0.items() if s1.get(h) != v)
    R["c"]["old_code_lost"] = sum(1 for h, v in s0.items() if v[1] and s1.get(h) != v)
    R["c"]["old_data_lost"] = sum(1 for h, v in s0.items() if not v[1] and s1.get(h) != v)
    R["c"]["outside_items"] = [outside0, sum(1 for _ in idautils.Heads(0, lo29)) + sum(1 for _ in idautils.Heads(hi29, idaapi.BADADDR))]
    R["c"]["new_fns"] = len(new)
    R["c"]["multi_chunk"] = sum(1 for x in R["fns"] if len(x["chunks"]) > 1)
    R["auto_ok"] = ida_auto.auto_is_ok()
    # overlaps between new fns and old data items
    ov = []
    for x in R["fns"]:
        for a, b in x["chunks"]:
            for h, (sz, c) in s0.items():
                pass
    R["data_overlap"] = [[h, sz] for h, (sz, c) in s0.items() if not c and ida_funcs.get_func(h) and ida_funcs.get_func(h).start_ea in set(new)][:200]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
