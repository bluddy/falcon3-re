"""level3_probe.py — op_dispatch targets + key Level-3 functions."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/level3_disasm.log")

# op_dispatch table entries 0-15
OP_TARGETS = [0x2F34, 0x2F66, 0x2FD9, 0x2FF6, 0x301F, 0x3028,
              0x3052, 0x307C, 0x30A0, 0x30D7, 0x30F4, 0x30FF,
              0x3108, 0x3158, 0x3113, 0x312C]

# Level-3 key functions  
LVL3 = [
    0x23C9B,  # angle_xy_far  87K dyn
    0x27EE6,  # record_queue_push  71K dyn
    0x23B8A,  # angle_xy_near  30K dyn
    0x14CC6,  # farobj_rect_ratio_build  2.1K dyn (entity rendering)
    0x178D4,  # channel_note_seq_write  4.9K dyn (audio)
    0x276C1,  # farptr_table_invoke  40B
    0x2C58B,  # (unnamed L3)
]

log = []

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def callers_of(ea, limit=4):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        nm = idc.get_func_name(fn.start_ea) if fn else "?"
        result.append(nm)
        if len(result) >= limit: break
    return result

def dump(ea, max_lines=50):
    fn = ida_funcs.get_func(ea)
    if fn is None or fn.start_ea != ea:
        return ["  SKIP: not a fn start"]
    name = idc.get_func_name(ea)
    size = fn.end_ea - fn.start_ea
    out = ["\n=== 0x%X  %s  %dB  %s ===" % (ea, name, size, seg_name(ea))]
    a, lim = fn.start_ea, max_lines
    while a < fn.end_ea and lim > 0:
        out.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
        a += ida_bytes.get_item_size(a)
        lim -= 1
    if a < fn.end_ea:
        out.append("  ... (%dB more)" % (fn.end_ea - a))
    out.append("  Callers: %s" % callers_of(ea))
    return out

try:
    log.append("=== op_dispatch table targets (BX=0..15) ===")
    for i, ea in enumerate(OP_TARGETS):
        lines = dump(ea, max_lines=20)
        log.append("--- BX=%d (0x%X) ---" % (i, ea))
        log.extend(lines)

    log.append("\n=== Level-3 key functions ===")
    for ea in LVL3:
        log.extend(dump(ea, max_lines=50))

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
