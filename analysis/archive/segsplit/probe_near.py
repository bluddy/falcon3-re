"""Read-only probe: are near branches / CS-relative operands resolved to the
right linear EA?  For every E8/E9/EB/7x/E0-E3 head, expected target is the
linear ea+len+rel (relative branches never wrap inside a real 8086 segment
unless IP wraps).  Compare with IDA's code xrefs."""
import json
import collections
import traceback

import ida_segment
import ida_ua
import ida_bytes
import ida_xref
import idautils
import idaapi
import idc

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\probe_near.json"
res = {"per_seg": {}, "bad": []}


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def s8(v):
    return v - 0x100 if v & 0x80 else v


def main():
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        name = ida_segment.get_segm_name(s)
        st = collections.Counter()
        for ea in idautils.Heads(s.start_ea, s.end_ea):
            if not idc.is_code(idc.get_full_flags(ea)):
                continue
            b = ida_bytes.get_byte(ea)
            sz = idc.get_item_size(ea)
            if b in (0xE8, 0xE9) and sz == 3:
                exp = ea + 3 + s16(ida_bytes.get_word(ea + 1))
            elif b == 0xEB or 0x70 <= b <= 0x7F or 0xE0 <= b <= 0xE3:
                if sz != 2:
                    continue
                exp = ea + 2 + s8(ida_bytes.get_byte(ea + 1))
            else:
                continue
            got = [x.to for x in idautils.XrefsFrom(ea, ida_xref.XREF_FAR)
                   if x.iscode and x.type in (ida_xref.fl_CN, ida_xref.fl_JN)]
            off = ea - s.start_ea
            hi = "hi" if off >= 0x10000 else "lo"
            if exp in got:
                st["ok_" + hi] += 1
            else:
                st["BAD_" + hi] += 1
                if len(res["bad"]) < 60:
                    res["bad"].append({"seg": name, "ea": ea, "exp": exp, "got": got,
                                       "dis": idc.generate_disasm_line(ea, 0)})
        if st:
            res["per_seg"][name] = dict(st)


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=1)
idaapi.qexit(0)
