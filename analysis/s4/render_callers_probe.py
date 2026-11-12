"""render_callers_probe.py — view_projection callers + farobj_batch_build_project."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/render_callers.log")
log = []

VIEW_PROJ = 0x20BDB

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def callers_of(ea, limit=5):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        nm = idc.get_func_name(fn.start_ea) if fn else "?"
        result.append(nm)
        if len(result) >= limit: break
    return result

try:
    # Find all callers of view_projection and their containing functions
    seen = set()
    log.append("=== Callers of view_projection (0x%X) ===" % VIEW_PROJ)
    for xr in idautils.XrefsTo(VIEW_PROJ, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        if fn is None: continue
        fn_ea = fn.start_ea
        if fn_ea in seen: continue
        seen.add(fn_ea)
        nm = idc.get_func_name(fn_ea)
        size = fn.end_ea - fn_ea
        log.append("\n--- Caller: 0x%X  %s  %dB  %s ---" % (fn_ea, nm, size, seg_name(fn_ea)))
        # Dump just 40 lines
        a, lim = fn_ea, 40
        while a < fn.end_ea and lim > 0:
            log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
            lim -= 1
        if a < fn.end_ea:
            log.append("  ... (%dB more)" % (fn.end_ea - a))
        log.append("  My callers: %s" % callers_of(fn_ea))

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
