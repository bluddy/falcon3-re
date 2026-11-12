"""mainloop_probe.py — read main_frame_update_loop and key callers."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/mainloop_disasm.log")

TARGETS = [
    0x2F5D1,  # main_frame_update_loop (find from naming.yaml)
    # Also check callers of game_frame_pipeline_step
]

log = []

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def callers_of(ea, limit=5):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        nm = idc.get_func_name(fn.start_ea) if fn else "?"
        result.append((hex(xr.frm), nm))
        if len(result) >= limit: break
    return result

try:
    # Find main_frame_update_loop by searching for it
    import idautils
    for fn_ea in idautils.Functions():
        nm = idc.get_func_name(fn_ea)
        if 'main_frame' in nm or 'update_loop' in nm:
            fn = ida_funcs.get_func(fn_ea)
            size = fn.end_ea - fn_ea
            log.append("\n=== 0x%X  %s  %dB  %s ===" % (fn_ea, nm, size, seg_name(fn_ea)))
            a, lim = fn_ea, 60
            while a < fn.end_ea and lim > 0:
                log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
                a += ida_bytes.get_item_size(a)
                lim -= 1
            if a < fn.end_ea:
                log.append("  ... (%dB more)" % (fn.end_ea - a))
            log.append("  Callers: %s" % callers_of(fn_ea))

    # Also get callers of game_frame_pipeline_step = 0x2FD42
    GPF_EA = 0x2FD42
    log.append("\n=== Callers of game_frame_pipeline_step ===")
    for xr in idautils.XrefsTo(GPF_EA, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        nm = idc.get_func_name(fn.start_ea) if fn else "?"
        log.append("  from 0x%X in %s" % (xr.frm, nm))

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
