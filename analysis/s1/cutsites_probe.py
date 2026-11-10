"""Read-only (DBFL_KILL): every call site of the (to be) un-NORETed functions whose fall-through flow is cut,
with what sits at the return address.  Output: analysis/s1/cutsites.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\cutsites.json"
TGT = [0x4F7B8, 0x38C91, 0x2FD42, 0x322E5, 0x3F700, 0x22DFF, 0x33116, 0x331E4, 0x3343E, 0x3F7A6, 0x4FE02, 0x3FD66]
R = {"sites": []}
try:
    for t in TGT:
        for x in idautils.XrefsTo(t, 0):
            if not x.iscode:
                continue
            m = idc.print_insn_mnem(x.frm)
            if not m.startswith("call"):
                continue
            nx = x.frm + ida_bytes.get_item_size(x.frm)
            fl = ida_bytes.get_flags(nx)
            cf = ida_funcs.get_func(x.frm)
            nf = ida_funcs.get_func(nx)
            R["sites"].append({"target": t, "frm": x.frm, "caller": cf.start_ea if cf else None, "next": nx,
                               "flow": bool(ida_bytes.is_flow(fl)), "code": bool(ida_bytes.is_code(fl)),
                               "head": ida_bytes.get_item_head(nx) == nx,
                               "owner": nf.start_ea if nf else None,
                               "prev_ok": bool(cf and nf and cf.start_ea == nf.start_ea),
                               "dis": idc.generate_disasm_line(nx, 0)})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
