"""Read-only probe: near CALL/JMP/Jcc targets in every segment.  IDA wraps
IP+rel at 16 bits relative to the *IDA segment base*.  For each branch, compare
IDA's target with the alternatives +/-0x10000 and classify which one lands on
an instruction head (and on a function start, for calls)."""
import json
import collections
import traceback

import ida_segment
import ida_bytes
import ida_funcs
import ida_xref
import idautils
import idaapi
import idc

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\probe_wrap.json"
res = {"per_seg": {}, "samples": []}


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def s8(v):
    return v - 0x100 if v & 0x80 else v


def is_insn_head(ea):
    f = ida_bytes.get_flags(ea)
    return ida_bytes.is_code(f) and ida_bytes.is_head(f)


def fstart(ea):
    f = ida_funcs.get_func(ea)
    return f is not None and f.start_ea == ea


def main():
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        name = ida_segment.get_segm_name(s)
        base = ida_segment.get_segm_base(s)
        st = collections.Counter()
        for ea in idautils.Heads(s.start_ea, s.end_ea):
            if not idc.is_code(idc.get_full_flags(ea)):
                continue
            b = ida_bytes.get_byte(ea)
            sz = idc.get_item_size(ea)
            if b in (0xE8, 0xE9) and sz == 3:
                rel = s16(ida_bytes.get_word(ea + 1))
                kind = "call" if b == 0xE8 else "jmp"
            elif (b == 0xEB or 0x70 <= b <= 0x7F) and sz == 2:
                rel = s8(ida_bytes.get_byte(ea + 1))
                kind = "jshort"
            else:
                continue
            ip = ea - base
            ida_t = base + ((ip + sz + rel) & 0xFFFF)
            alts = [t for t in (ida_t - 0x10000, ida_t + 0x10000)]
            ida_ok = is_insn_head(ida_t)
            alt_ok = [t for t in alts if is_insn_head(t)]
            if kind == "call":
                ida_ok = ida_ok and fstart(ida_t)
                alt_ok = [t for t in alt_ok if fstart(t)]
            wrapped = (ip + sz + rel) != ((ip + sz + rel) & 0xFFFF) or (ip >= 0x10000)
            if ida_ok and not alt_ok:
                c = "ida_only"
            elif alt_ok and not ida_ok:
                c = "ALT_ONLY"
            elif ida_ok and alt_ok:
                c = "both"
            else:
                c = "neither"
            st["%s_%s" % (kind, c)] += 1
            if c == "ALT_ONLY" and len(res["samples"]) < 40:
                res["samples"].append({"seg": name, "ea": ea, "ida": ida_t, "alt": alt_ok,
                                       "dis": idc.generate_disasm_line(ea, 0)})
        if st:
            res["per_seg"][name] = dict(st)


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
