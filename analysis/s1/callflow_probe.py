"""Read-only (DBFL_KILL): every call into the wrongly no-return functions, and whether the instruction
after the call is reached by flow, owned by the caller's function, or orphaned.
Output: analysis/s1/callflow_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\callflow_probe.json"
TGT = [0x4F7B8, 0x38C91, 0x2FD42, 0x322E5, 0x3F700, 0x33116, 0x331E4, 0x3343E, 0x2F6D0, 0x4FE02, 0x3F7A6,
       0x3F861, 0x3FD66, 0x22DFF]
R = {}
try:
    for t in TGT:
        f = ida_funcs.get_func(t)
        rows = []
        for x in idautils.XrefsTo(t, 0):
            if not x.iscode:
                continue
            m = idc.print_insn_mnem(x.frm)
            nx = x.frm + ida_bytes.get_item_size(x.frm)
            fl = ida_bytes.get_flags(nx)
            cf = ida_funcs.get_func(x.frm)
            nf = ida_funcs.get_func(nx)
            rows.append({"frm": x.frm, "mnem": m, "type": x.type, "caller": cf.start_ea if cf else None,
                         "next": nx, "next_flow": bool(ida_bytes.is_flow(fl)), "next_code": bool(ida_bytes.is_code(fl)),
                         "next_func": nf.start_ea if nf else None,
                         "next_disasm": idc.generate_disasm_line(nx, 0)})
        R["%X" % t] = {"name": idc.get_func_name(t), "noret": bool(f.flags & ida_funcs.FUNC_NORET), "calls": rows}
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
