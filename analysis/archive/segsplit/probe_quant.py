"""Read-only quantification.
1) per sreg value (ds/es/ss known), min/max linear EA of o_mem/o_displ refs.
2) per code segment with fixup anchors: near CALL/JMP/Jcc whose IDA target
   (wrapped at the IDA segment base) differs from the target computed with
   the anchor-derived CS (base of the anchor block containing the insn)."""
import json
import bisect
import collections
import traceback

import ida_segment
import ida_segregs
import ida_ua
import ida_idp
import ida_bytes
import ida_funcs
import idautils
import idaapi
import idc

ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
OUT = ROOT + r"\probe_quant.json"
anchors = json.load(open(ROOT + r"\anchors.json"))
res = {"sreg": {}, "branch": {}, "samples": []}
DS, ES, SS = (ida_idp.str2reg(r) for r in ("ds", "es", "ss"))


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def s8(v):
    return v - 0x100 if v & 0x80 else v


def head_kind(ea):
    f = ida_bytes.get_flags(ea)
    if not (ida_bytes.is_code(f) and ida_bytes.is_head(f)):
        return "nohead"
    fn = ida_funcs.get_func(ea)
    return "fstart" if fn and fn.start_ea == ea else "head"


def main():
    rng = {}
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        for ea in idautils.Heads(s.start_ea, s.end_ea):
            if not idc.is_code(idc.get_full_flags(ea)):
                continue
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, ea):
                continue
            for op in insn.ops:
                if op.type == ida_ua.o_void:
                    break
                if op.type not in (ida_ua.o_mem, ida_ua.o_displ):
                    continue
                txt = idc.print_operand(ea, op.n) or ""
                if "es:" in txt:
                    reg = ES
                elif "ss:" in txt or (op.type == ida_ua.o_displ and op.phrase in (2, 3, 6)):
                    continue
                elif "cs:" in txt:
                    continue
                else:
                    reg = DS
                v = ida_segregs.get_sreg(ea, reg)
                if v in (idaapi.BADSEL, 0xFFFFFFFFFFFFFFFF) or v > 0xFFFF:
                    continue
                off = op.addr & 0xFFFF
                k = "%04X" % v
                r = rng.setdefault(k, [0xFFFF, 0, 0])
                r[0] = min(r[0], off)
                r[1] = max(r[1], off)
                r[2] += 1
    res["sreg"] = rng

    for idx, o in anchors.items():
        if not o["anchors"]:
            continue
        lo, hi = o["ida_ea"], o["ida_ea"] + o["len"]
        s = ida_segment.getseg(lo)
        base = ida_segment.get_segm_base(s)
        cuts = sorted(set([a["ea"] for a in o["anchors"]] + [lo]))
        st = collections.Counter()
        for ea in idautils.Heads(lo, hi):
            if not idc.is_code(idc.get_full_flags(ea)):
                continue
            b = ida_bytes.get_byte(ea)
            sz = idc.get_item_size(ea)
            if b in (0xE8, 0xE9) and sz == 3:
                rel = s16(ida_bytes.get_word(ea + 1))
                kind = "call" if b == 0xE8 else "jmp"
            elif (b == 0xEB or 0x70 <= b <= 0x7F or 0xE0 <= b <= 0xE3) and sz == 2:
                rel = s8(ida_bytes.get_byte(ea + 1))
                kind = "jcc"
            else:
                continue
            ab = cuts[bisect.bisect_right(cuts, ea) - 1]
            t_ida = base + (((ea - base) + sz + rel) & 0xFFFF)
            t_anc = ab + (((ea - ab) + sz + rel) & 0xFFFF)
            if t_ida == t_anc:
                st[kind + "_same"] += 1
                continue
            ki, ka = head_kind(t_ida), head_kind(t_anc)
            st["%s_DIFF ida=%s anc=%s" % (kind, ki, ka)] += 1
            if len(res["samples"]) < 40:
                res["samples"].append([o["name"], ea, t_ida, t_anc, ki, ka,
                                       idc.generate_disasm_line(ea, 0)])
        res["branch"][o["name"]] = dict(st)


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
