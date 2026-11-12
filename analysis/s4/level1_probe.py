"""level1_probe.py — dump top Level-1 and other high-value unnamed functions."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback, json
from pathlib import Path

LOG  = Path("analysis/s4/level1_disasm.log")

# Top Level-1 by dyn + some named ones we want to understand
TARGET_EAS = [
    0x1016C,  # Level-1, 320K dyn, in=4
    0x24984,  # Level-1, 303K dyn, in=38
    0x256BE,  # Level-1, 228K dyn, in=0  (no static callers!)
    0x260AF,  # Level-1, 192K dyn, in=25
    0x2497C,  # Level-1, 147K dyn, in=29
    0x23D2B,  # Level-1, 109K dyn, in=25
    0x23E57,  # Level-1, 80K dyn, in=1
    0x24992,  # Level-1, 62K dyn, in=2
    0x248CD,  # Level-1, 40K dyn, in=9
    0x25F64,  # Level-1, 38K dyn, in=3
    0x24F03,  # Level-1, 31K dyn
    0x2BFC3,  # Level-1, 31K dyn, in=10
    0x25773,  # Level-1, 20K dyn, in=1
    0x205BF,  # Level-1, 18K dyn, in=8
    0x22996,  # Level-1, 13K dyn, in=3
    # Named Level-1 we want to verify
    0x2257B,  # op_dispatch (named, interesting)
    0x231F0,  # fn_table_dispatch (named)
]

log = []

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def callers_of(ea, limit=5):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        m = idc.print_insn_mnem(xr.frm)
        fn = ida_funcs.get_func(xr.frm)
        fn_name = idc.get_func_name(fn.start_ea) if fn else "?"
        result.append("%s(%s)" % (m, fn_name))
        if len(result) >= limit: break
    return result

try:
    for ea in TARGET_EAS:
        fn = ida_funcs.get_func(ea)
        if fn is None or fn.start_ea != ea:
            log.append("SKIP 0x%X: not a fn start" % ea)
            continue
        name = idc.get_func_name(ea)
        size = fn.end_ea - fn.start_ea
        seg  = seg_name(ea)
        log.append("\n=== 0x%X  %s  %dB  %s ===" % (ea, name, size, seg))
        a = fn.start_ea
        limit = 50
        while a < fn.end_ea and limit > 0:
            log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
            limit -= 1
        if a < fn.end_ea:
            log.append("  ... (%dB more)" % (fn.end_ea - a))
        log.append("  Callers: %s" % callers_of(ea))

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
