"""Probe (DBFL_KILL) v2: S1b registration incl. jump-table-tail pre-fixes; reports far calls in new code,
outside-R29 head changes, runtime target coverage."""
import json, traceback, collections, struct
import idaapi, idautils, idc, ida_bytes, ida_funcs, ida_ua, ida_segment, ida_xref, ida_idp, ida_nalt
ROOT = "C:/Users/ybarnoy/projects/falcon3/"
OUT = ROOT + "analysis/s1/exp_reg2.json"
R = {"rounds": [], "order": [], "fail": [], "c": collections.Counter(), "sw": {}}
try:
    for jt, swea in ((0x127E4C, 0x1277F4), (0x128A9A, None)):
        # find the switch insn referencing the table
        for x in idautils.XrefsTo(jt, 0):
            R["sw"]["%X" % jt] = R["sw"].get("%X" % jt, []) + [["%X" % x.frm, x.type]]
    for ea in list(idautils.Heads(0x127700, 0x127E4C)) + list(idautils.Heads(0x128598, 0x128A9A)):
        si = ida_nalt.get_switch_info(ea)
        if si:
            R["sw"]["si_%X" % ea] = {"jumps": "%X" % si.jumps, "ncases": si.ncases, "elsz": si.get_jtable_element_size(), "lowcase": si.lowcase}
    doc = json.load(open(ROOT + "registry/variant_sel_expected.json"))
    lo29, hi29 = 0x11C3C0, 0x154CB0
    in29 = lambda ea: lo29 <= ea < hi29
    fn0 = {f: ida_funcs.get_func(f).end_ea for f in idautils.Functions()}
    out0 = set(json.load(open(ROOT + "analysis/s1/outside_heads_before.json")))
    it0 = {h: ida_bytes.get_item_size(h) for h in idautils.Heads(lo29, hi29)}
    # pre-fix: misdecoded jump-table tails overlapping an enter
    pre = {0x127E5A: (0x127E56, 0x127E5A), 0x128AA6: (0x128AA6, 0x128AA6)}
    for ent, (tlo, thi) in pre.items():
        h = ida_bytes.get_item_head(tlo if tlo < thi else ent)
        x = ida_bytes.get_item_head(tlo) if tlo < thi else ent
        dels = []
        while x < ent + 4:
            hh = ida_bytes.get_item_head(x)
            if ida_bytes.is_code(ida_bytes.get_flags(hh)) and not ida_funcs.get_func(hh):
                dels.append([hh, ida_bytes.get_item_size(hh)])
                ida_bytes.del_items(hh, 0, ida_bytes.get_item_size(hh))
            x = hh + max(1, ida_bytes.get_item_size(hh)) if ida_bytes.is_code(ida_bytes.get_flags(hh)) else x + 1
        for w in range(tlo, thi, 2):
            ida_bytes.create_word(w, 2)
        R["c"]["pre_%X" % ent] = dels
    todo = sorted({c["to"] for c in doc["crefs"] if in29(c["to"]) and not (ida_funcs.get_func(c["to"]) and ida_funcs.get_func(c["to"]).start_ea == c["to"])})
    seen, rnd = set(), 0
    while todo and rnd < 8:
        rnd += 1; added = []
        for ea in todo:
            seen.add(ea)
            fl = ida_bytes.get_flags(ea)
            if ida_funcs.get_func(ea) or ida_bytes.is_data(fl) or (ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) != ea):
                R["fail"].append(["%X" % ea, rnd]); continue
            if not ida_funcs.add_func(ea) or ida_funcs.get_func(ea).start_ea != ea:
                R["fail"].append(["%X" % ea, rnd, "add_func"]); continue
            added.append(ea); R["order"].append([ea, ida_funcs.get_func(ea).end_ea, rnd])
        nxt = set()
        for ea in added:
            for h in idautils.FuncItems(ea):
                insn = ida_ua.insn_t(); ida_ua.decode_insn(insn, h)
                if not ida_idp.is_call_insn(insn): continue
                for t in idautils.CodeRefsFrom(h, 0):
                    g = ida_funcs.get_func(t)
                    if in29(t) and t not in seen and not (g and g.start_ea == t):
                        nxt.add(t)
        R["rounds"].append([rnd, len(todo), len(added), len(nxt)])
        todo = sorted(nxt)
    new = sorted(set(f for f in idautils.Functions()) - set(fn0))
    R["c"]["new"] = len(new)
    R["c"]["old_changed"] = sum(1 for f, e in fn0.items() if not ida_funcs.get_func(f) or ida_funcs.get_func(f).start_ea != f or ida_funcs.get_func(f).end_ea != e)
    R["c"]["old_r29_items_changed"] = [["%X" % h, s, ida_bytes.get_item_size(h) if ida_bytes.get_item_head(h) == h else None] for h, s in it0.items()
                                       if ida_bytes.get_item_head(h) != h or ida_bytes.get_item_size(h) != s]
    out1 = {h for s in idautils.Segments() for h in idautils.Heads(s, ida_segment.getseg(s).end_ea) if not in29(h)}
    R["outside_new"] = [["%X" % h, idc.generate_disasm_line(h, 0), [("%X" % x.frm) for x in idautils.XrefsTo(h, 0)][:4]] for h in sorted(out1 - out0)]
    R["outside_gone"] = ["%X" % h for h in sorted(out0 - out1)]
    # far calls in new functions
    fc = collections.Counter(); fce = []
    for f in new:
        for h in idautils.FuncItems(f):
            if ida_bytes.get_byte(h) in (0x9A, 0xEA) and ida_bytes.get_item_size(h) == 5:
                off, seg = struct.unpack("<HH", idc.get_bytes(h, 5)[1:])
                refs = [x.to for x in idautils.XrefsFrom(h, ida_xref.XREF_FAR) if x.iscode and x.type in (ida_xref.fl_CF, ida_xref.fl_JF)]
                k = "r29" if refs and in29(refs[0]) else "arena05" if refs and 0x2E100 <= refs[0] < 0x669F0 else "other"
                fc[(k, "seg%X" % seg if k == "arena05" else "")] += 1
                if k == "arena05" and len(fce) < 20: fce.append(["%X" % h, "%X:%X" % (seg, off), ["%X" % r for r in refs]])
    R["farcalls_new"] = {"%s %s" % k: v for k, v in fc.items()}; R["farcalls_arena05_eg"] = fce
    rt = {int(k): v for k, v in json.load(open(ROOT + "analysis/s1/r29_runtime_targets.json")).items()}
    cov = collections.Counter()
    for t, n in rt.items():
        g = ida_funcs.get_func(t)
        k = "fs" if g and g.start_ea == t else "mid" if g else "nofn"
        cov[k] += 1; cov[k + "_ev"] += n
    R["runtime"] = dict(cov)
    R["runtime_mid"] = [["%X" % t, n, "%X" % ida_funcs.get_func(t).start_ea] for t, n in rt.items() if ida_funcs.get_func(t) and ida_funcs.get_func(t).start_ea != t]
    R["runtime_nofn"] = [["%X" % t, n, (idc.get_bytes(t, 4) or b"").hex()] for t, n in rt.items() if not ida_funcs.get_func(t)]
    R["fns"] = [[f, ida_funcs.get_func(f).end_ea] for f in new]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
