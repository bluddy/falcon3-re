import json, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment
OUT = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/probe_misc2.json"
R = {}
def ctx(ea, nb=3, na=14):
    out = []; x = ea
    for _ in range(nb):
        p = idc.prev_head(x, 0)
        if p == idaapi.BADADDR: break
        x = p
    for _ in range(nb + na + 1):
        f = ida_funcs.get_func(x); fl = ida_bytes.get_flags(x)
        out.append("%X %s sz%d %s | %s" % (x, "C" if ida_bytes.is_code(fl) else "D" if ida_bytes.is_data(fl) else "U", ida_bytes.get_item_size(x),
                   idc.generate_disasm_line(x, 0), ("%X-%X" % (f.start_ea, f.end_ea)) if f else "-"))
        x = idc.next_head(x, idaapi.BADADDR)
    return out
try:
    for ea in (0x127E5A, 0x128AA6):
        R["%X" % ea] = {"ctx": ctx(ea), "bytes": idc.get_bytes(ea, 24).hex(), "flags": "%X" % ida_bytes.get_flags(ea)}
    lo, hi = 0x11C3C0, 0x154CB0
    R["outside_heads"] = sorted(h for s in idautils.Segments() for h in idautils.Heads(s, ida_segment.getseg(s).end_ea) if not lo <= h < hi)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
