"""Read-only: DS state of the IDB -> probe_ds.json
segments (base/sel/default sregs), per-function entry DS + implicit-DS operand
stats, call edges with DS at the call site, DS sreg-range tags."""
import collections
import json
import traceback

import ida_bytes
import ida_funcs
import ida_segment
import ida_segregs
import ida_ua
import ida_xref
import idaapi
import idautils
import idc

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\probe_ds.json"
DS, ES, SS, CS = (idaapi.str2reg(r) for r in ("ds", "es", "ss", "cs"))
res = {}


def para(v):
    if v in (idaapi.BADSEL, 0xFFFF, 0xFFFFFFFF) or v is None:
        return None
    return ida_segment.sel2para(v)


def ds_ops(ea, insn):
    """implicit-DS memory operands (no override, base not BP/SP)"""
    out = []
    for op in insn.ops:
        if op.type == ida_ua.o_void:
            break
        if op.type not in (ida_ua.o_mem, ida_ua.o_displ, ida_ua.o_phrase):
            continue
        txt = idc.print_operand(ea, op.n) or ""
        if any(p in txt for p in ("es:", "cs:", "ss:", "fs:", "gs:")):
            continue
        if op.type != ida_ua.o_mem and "bp" in txt:
            continue
        out.append(op)
    return out


def main():
    segs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        segs.append(dict(name=ida_segment.get_segm_name(s), start=s.start_ea, end=s.end_ea,
                         base=ida_segment.get_segm_base(s), sel=s.sel, bitness=s.bitness,
                         cls=ida_segment.get_segm_class(s), type=s.type,
                         defsr=[para(ida_segregs.get_sreg(s.start_ea, r)) for r in (ES, CS, SS, DS)]))
    res["segments"] = segs
    funcs = []
    edges = []
    loads = collections.Counter()
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        seg = ida_segment.getseg(fs)
        ent = para(ida_segregs.get_sreg(fs, DS))
        n = bad = 0
        vals = collections.Counter()
        explicit = []
        for h in idautils.FuncItems(fs):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, h):
                continue
            m = insn.get_canon_mnem()
            if m in ("mov", "pop", "lds") and insn.ops[0].type == ida_ua.o_reg and insn.ops[0].reg == DS:
                explicit.append([h, m])
            elif m == "lds":
                explicit.append([h, m])
            ops = ds_ops(h, insn)
            if not ops:
                continue
            v = para(ida_segregs.get_sreg(h, DS))
            n += len(ops)
            if v is None:
                bad += len(ops)
            vals["%X" % v if v is not None else "BAD"] += len(ops)
        for x in idautils.XrefsTo(fs, 0):
            if x.type in (ida_xref.fl_CN, ida_xref.fl_CF):
                edges.append([x.frm, fs, x.type == ida_xref.fl_CF,
                              para(ida_segregs.get_sreg(x.frm, DS)),
                              (ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm) else None)])
        funcs.append(dict(start=fs, end=f.end_ea, name=idaapi.get_name(fs),
                          seg=ida_segment.get_segm_name(seg), cs=para(seg.sel),
                          entry_ds=ent, n=n, bad=bad, vals=dict(vals), explicit=explicit))
    res["funcs"] = funcs
    res["edges"] = edges
    rr = ida_segregs.sreg_range_t()
    tags = collections.Counter()
    for k in range(ida_segregs.get_sreg_ranges_qty(DS)):
        ida_segregs.getn_sreg_range(rr, DS, k)
        tags["%d/%s" % (rr.tag, "BAD" if para(rr.val) is None else "known")] += 1
    res["ds_range_tags"] = dict(tags)


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"))
idaapi.qexit(0)
