"""level4567_probe.py — targeted probe for high-value Level 4-7 functions."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/level4567_disasm.log")

TARGETS = [
    # Level-4
    0x257C9,  # clip_pending_apply_gate  18K dyn, 0 static callers
    0x27ED4,  # record_queue_push_guard  14K dyn
    0x25E42,  # angle_quad_norm_far  52K dyn
    0x23AC4,  # vec_transform_scale  8K dyn
    0x208E7,  # math_saturate_store  403B
    0x257B1,  # dual_step_wrap  1.9K dyn
    # Level-5
    0x14BD7,  # farobj_pos_wrap_update  10K dyn  
    0x2589F,  # clip_pending_atomic_apply  7K dyn
    0x1BCC2,  # state_mode_check  104 dyn, 13 callers
    # Level-6
    0x1509E,  # entity_state_load  775B, 11K dyn (KEY!)
    0x22598,  # op_dispatch_far_entry  30B, 54 callers
    0x225B6,  # op_dispatch_far_wide  30B
    0x27703,  # far_op_execute  325B
    0x127D4,  # param_table_init  176B
    0x274E6,  # buffer_callback_api_block  242B
    0x27678,  # buffer_write_entry  31B
    0x275D8,  # buffer_budget_entry_block  113B
    # Level-7
    0x1B8EE,  # mode_slot_index_build  262B
    0x276E9,  # far_op_execute_farptr  26B
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
