"""Read-only: dump DS/ES/SS sreg ranges + segment defaults -> $OUT (default probe_ranges.json)"""
import json
import os
import traceback

import ida_funcs
import ida_segment
import ida_segregs
import idaapi
import idc

OUT = os.environ.get("OUT", r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\probe_ranges.json")
res = {}


def main():
    for name in ("ds", "es", "ss"):
        reg = idaapi.str2reg(name)
        rr = ida_segregs.sreg_range_t()
        out = []
        for k in range(ida_segregs.get_sreg_ranges_qty(reg)):
            ida_segregs.getn_sreg_range(rr, reg, k)
            f = ida_funcs.get_func(rr.start_ea)
            prev = idc.prev_head(rr.start_ea, 0)
            out.append([rr.start_ea, rr.end_ea, rr.val, rr.tag,
                        f.start_ea if f else None,
                        idc.generate_disasm_line(prev, 0) if prev != idaapi.BADADDR else ""])
        res[name] = out
    segs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        segs.append([ida_segment.get_segm_name(s), s.start_ea, s.end_ea, s.sel,
                     [s.defsr[k] for k in range(len(s.defsr)) if True] if False else
                     [ida_segregs.get_sreg(s.start_ea, idaapi.str2reg(r)) for r in ("es", "ss", "ds")]])
    res["segs"] = segs


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"))
idaapi.qexit(0)
