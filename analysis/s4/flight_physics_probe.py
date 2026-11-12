"""flight_physics_probe.py — aircraft physics and control system functions."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/flight_physics.log")

TARGETS = [
    0x3A3D6,  # mode_frame_step_core — the main per-mode physics step
    0x2FEF2,  # game_frame_update_chain — the update chain
    0x2234B,  # control_axes_read — reads flight control axes
    0x3099C,  # control_axes_record_store — stores axis data
    0x3B338,  # pos_step_chain_engine — position/motion update
    0x49546,  # aircraft_slot_cycle_step — aircraft cycling
    0x4CD1D,  # farobj_move_accumulate_step — farobj motion accumulation
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
        a, lim = fn.start_ea, 55
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
