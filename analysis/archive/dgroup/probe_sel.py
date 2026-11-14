"""Read-only: selector table + where DS==0 ranges are -> $OUT"""
import json
import os
import traceback

import ida_segment
import ida_segregs
import idaapi
import idc

OUT = os.environ.get("OUT", r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\probe_sel.json")
res = {}


def main():
    sels = []
    for n in range(ida_segment.get_selector_qty()):
        ok, sel, base = ida_segment.getn_selector(n)
        sels.append([sel, base])
    res["selectors"] = sels
    res["sel0_para"] = ida_segment.sel2para(0)
    DS = idaapi.str2reg("ds")
    rr = ida_segregs.sreg_range_t()
    z = []
    for k in range(ida_segregs.get_sreg_ranges_qty(DS)):
        ida_segregs.getn_sreg_range(rr, DS, k)
        if rr.val == 0:
            p = idc.prev_head(rr.start_ea, 0)
            z.append([rr.start_ea, rr.end_ea, ida_segment.get_segm_name(ida_segment.getseg(rr.start_ea)),
                      idc.generate_disasm_line(p, 0), idc.generate_disasm_line(rr.start_ea, 0)])
    res["ds_zero"] = z
    res["segs"] = [[ida_segment.get_segm_name(s), s.start_ea, s.sel, ida_segment.get_segm_base(s)]
                   for s in (ida_segment.getnseg(i) for i in range(ida_segment.get_segm_qty()))]


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=0)
idaapi.qexit(0)
