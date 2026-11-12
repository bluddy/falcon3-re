"""toplevel_probe.py — probe the high-level game systems."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/toplevel_disasm.log")

TARGETS = [
    0x2FD42,  # game_frame_pipeline_step  Level-18 (THE main frame function)
    0x20BDB,  # view_projection  282K dyn, Level-9  (core 3D)
    0x1AB34,  # event_state_machine  2266B, 42K dyn, Level-10
    0x2131C,  # farobj_sort_and_step  55K dyn
    0x270E0,  # viewobj_project_advance  63K dyn
    0x12B62,  # viewobj_project_select  59K dyn (tiny!)
    0x1655A,  # entity_update_batch  11K dyn (tiny!)
    0x1CEA3,  # entity_counters_update  453B, 11K dyn, Level-10
    0x153A5,  # terrain_frame_update_driver  11K dyn, Level-14
    0x121C2,  # entity_setup_step  Level-15
    0x24FB9,  # flag_bits_dispatch  Level-18, 21K dyn
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
        result.append(nm)
        if len(result) >= limit: break
    return result

try:
    for ea in TARGETS:
        fn = ida_funcs.get_func(ea)
        if fn is None or fn.start_ea != ea:
            log.append("SKIP 0x%X" % ea)
            continue
        name = idc.get_func_name(ea)
        size = fn.end_ea - fn.start_ea
        log.append("\n=== 0x%X  %s  %dB  %s ===" % (ea, name, size, seg_name(ea)))
        a, lim = fn.start_ea, 60
        while a < fn.end_ea and lim > 0:
            log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
            lim -= 1
        if a < fn.end_ea:
            log.append("  ... (%dB more)" % (fn.end_ea - a))
        log.append("  Callers: %s" % callers_of(ea))

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
