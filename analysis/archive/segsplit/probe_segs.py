"""Read-only probe: segment table, selectors, DS/ES immediate loads.

Run on a COPY of the IDB. Never saves (qexit without save is not possible in
headless -A, so this is only ever pointed at analysis/segsplit/probe.i64).
"""
import json
import collections
import traceback

import ida_segment
import ida_segregs
import ida_ua
import ida_idp
import ida_funcs
import ida_bytes
import idautils
import idaapi
import idc

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\probe_segs.json"
res = {}


def main():
    segs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        sel = s.sel
        para = ida_segment.sel2para(sel)
        nfn = sum(1 for _ in idautils.Functions(s.start_ea, s.end_ea))
        segs.append({
            "name": ida_segment.get_segm_name(s),
            "start": s.start_ea, "end": s.end_ea, "sel": sel, "para": para,
            "base": ida_segment.get_segm_base(s), "bitness": s.bitness,
            "cls": ida_segment.get_segm_class(s), "type": s.type,
            "nfuncs": nfn,
            "ds_default": ida_segregs.get_sreg(s.start_ea, ida_idp.str2reg("ds")),
        })
    res["segs"] = segs

    # selector table
    sels = []
    n = ida_segment.get_selector_qty()
    for i in range(n):
        sel = ida_segment.getn_selector(i)
        sels.append(sel)
    res["selectors"] = n

    # DS/ES immediate loads: mov ax,imm16 ; mov ds|es,ax  (and push imm / pop ds)
    ds_r = ida_idp.str2reg("ds")
    es_r = ida_idp.str2reg("es")
    loads = collections.Counter()
    samples = collections.defaultdict(list)
    tracked = collections.Counter()
    for s in segs:
        ea = s["start"]
        while ea < s["end"] and ea != idaapi.BADADDR:
            if ida_bytes.is_code(ida_bytes.get_flags(ea)):
                insn = ida_ua.insn_t()
                if ida_ua.decode_insn(insn, ea):
                    m = insn.get_canon_mnem()
                    if m == "mov" and insn.ops[0].type == ida_ua.o_reg and insn.ops[0].reg in (ds_r, es_r) \
                            and insn.ops[1].type == ida_ua.o_reg:
                        prev = idc.prev_head(ea, s["start"])
                        if prev != idaapi.BADADDR:
                            pi = ida_ua.insn_t()
                            if ida_ua.decode_insn(pi, prev) and pi.get_canon_mnem() == "mov" \
                                    and pi.ops[0].type == ida_ua.o_reg and pi.ops[0].reg == insn.ops[1].reg \
                                    and pi.ops[1].type == ida_ua.o_imm:
                                v = pi.ops[1].value & 0xFFFF
                                r = "ds" if insn.ops[0].reg == ds_r else "es"
                                loads[(v, r)] += 1
                                if len(samples[v]) < 3:
                                    samples[v].append(ea)
                                # what does IDA believe after this insn?
                                nxt = ea + insn.size
                                got = ida_segregs.get_sreg(nxt, insn.ops[0].reg)
                                tracked[(v, r, got)] += 1
            ea = idc.next_head(ea, s["end"])
    res["loads"] = sorted([[v, r, c] for (v, r), c in loads.items()], key=lambda x: -x[2])
    res["samples"] = {"%04X" % k: v for k, v in samples.items()}
    res["tracked"] = sorted([[v, r, g, c] for (v, r, g), c in tracked.items()], key=lambda x: -x[3])[:80]


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
