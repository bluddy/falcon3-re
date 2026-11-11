"""Read-only (DBFL_KILL): every maximal run of code heads that belong to no function.  For each run: size, the
function ending just before it, whether it ends in a ret/jmp, the xrefs into it (code and data) and the first
and last disassembly lines.  Output: analysis/s1/orphan_scan138.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_scan138.json"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
R = {"runs": []}
try:
    for si in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(si)
        if s.type not in (ida_segment.SEG_CODE,):
            continue
        ea = s.start_ea
        run = None
        while ea < s.end_ea:
            h = ida_bytes.get_item_head(ea)
            fl = ida_bytes.get_flags(h)
            sz = max(ida_bytes.get_item_size(h), 1)
            orphan = ida_bytes.is_code(fl) and not ida_funcs.get_func(h)
            if orphan:
                if run is None:
                    run = [h, h]
                run[1] = h + sz
            else:
                if run is not None:
                    R["runs"].append((run[0], run[1], s.start_ea))
                    run = None
            ea = h + sz
        if run is not None:
            R["runs"].append((run[0], run[1], s.start_ea))
    rows = []
    for lo, hi, sg in R["runs"]:
        pf = ida_funcs.get_func(lo - 1) if lo > 0 else None
        nf = ida_funcs.get_func(hi) if True else None
        heads = []
        a = lo
        while a < hi:
            heads.append(a)
            a += ida_bytes.get_item_size(a)
        last = heads[-1]
        xin = []
        for h in heads:
            for x in idautils.XrefsTo(h, 0):
                if x.frm >= lo and x.frm < hi:
                    continue
                xin.append([x.frm, h, x.type, bool(ida_bytes.is_code(ida_bytes.get_flags(x.frm)))])
        rows.append({"lo": lo, "hi": hi, "size": hi - lo, "seg": ida_segment.get_segm_name(ida_segment.getseg(lo)), "heads": len(heads),
                     "prev_func": pf.start_ea if pf else None, "prev_name": idc.get_func_name(pf.start_ea) if pf else None,
                     "prev_end": pf.end_ea if pf else None, "next_func": nf.start_ea if nf else None,
                     "last_mnem": idc.print_insn_mnem(last), "xin": xin[:12], "n_xin": len(xin),
                     "first": idc.generate_disasm_line(lo, 0), "lastdis": idc.generate_disasm_line(last, 0)})
    R["runs"] = rows
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
