"""Read-only (DBFL_KILL): context dumps for S1a planning."""
import json, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_xref
OUT = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/probe_misc.json"
R = {}
def ctx(ea, nb=4, na=8):
    out = []; x = ea
    for _ in range(nb):
        p = idc.prev_head(x, 0)
        if p == idaapi.BADADDR: break
        x = p
    for _ in range(nb + na + 1):
        f = ida_funcs.get_func(x)
        out.append("%X %s %s | %s" % (x, "C" if ida_bytes.is_code(ida_bytes.get_flags(x)) else "D",
                   idc.generate_disasm_line(x, 0), ("%X-%X" % (f.start_ea, f.end_ea)) if f else "-"))
        x = idc.next_head(x, idaapi.BADADDR)
    return out
try:
    for ea in (0x13DD40, 0x13DD83, 0x13DDC3, 0x4FA80, 0x4FAC3, 0x4FB03, 0x13DB55, 0x11C3C0, 0x2E100):
        R["%X" % ea] = {"ctx": ctx(ea), "bytes": idc.get_bytes(ea, 16).hex(),
                        "xto": [["%X" % x.frm, x.type, x.user] for x in list(idautils.XrefsTo(ea, 0))[:12]]}
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
