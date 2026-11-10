"""Read-only: item layout of R69 / DGROUP region and the gap after it -> probe_r69.json"""
import collections
import json
import traceback

import ida_bytes
import ida_segment
import idaapi
import idautils
import idc

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\probe_r69.json"
res = {}


def main():
    s = ida_segment.getseg(0x7A320)
    res["seg"] = [ida_segment.get_segm_name(s), s.start_ea, s.end_ea, ida_segment.get_segm_class(s), s.type,
                  s.perm, s.align, s.comb, s.bitness, s.sel]
    res["next_seg"] = [ida_segment.get_segm_name(ida_segment.get_next_seg(s.start_ea)),
                       ida_segment.get_next_seg(s.start_ea).start_ea]
    big = []
    kinds = collections.Counter()
    ea = s.start_ea
    n = 0
    for h in idautils.Heads(s.start_ea, s.end_ea):
        f = ida_bytes.get_flags(h)
        sz = ida_bytes.get_item_size(h)
        k = "code" if ida_bytes.is_code(f) else ("data" if ida_bytes.is_data(f) else "other")
        kinds[k] += 1
        if sz >= 64:
            big.append([h, sz, idc.get_name(h), k])
        if h < 0x7A320 <= h + sz - 1 and h != 0x7A320:
            res["straddle"] = [h, sz, idc.get_name(h)]
    res["kinds"] = dict(kinds)
    res["big"] = big[:200]
    res["nbig"] = len(big)
    res["named"] = sum(1 for h in idautils.Heads(0x7A320, s.end_ea) if idc.get_name(h) and not idc.get_name(h).startswith(("byte_", "word_", "dword_", "unk_", "asc_", "off_", "seg_", "a")))
    res["names_sample"] = [[h, idc.get_name(h)] for h in idautils.Heads(0x7A320, s.end_ea) if idc.get_name(h)][:80]
    res["at_7A320"] = [idc.get_name(0x7A320), ida_bytes.get_item_size(0x7A320), ida_bytes.get_flags(0x7A320)]
    res["xrefs_into_dgroup"] = sum(1 for h in idautils.Heads(0x7A320, s.end_ea) for _ in idautils.XrefsTo(h, 0))
    res["xrefs_into_r69_lo"] = sum(1 for h in idautils.Heads(s.start_ea, 0x7A320) for _ in idautils.XrefsTo(h, 0))
    res["code_in_dgroup"] = [h for h in idautils.Heads(0x7A320, s.end_ea) if ida_bytes.is_code(ida_bytes.get_flags(h))][:20]
    res["funcs_in_r69"] = [f for f in idautils.Functions(s.start_ea, s.end_ea)][:20]


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=0)
idaapi.qexit(0)
