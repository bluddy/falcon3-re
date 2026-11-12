"""farobj_type_probe.py — read farobj_type_field_get and key nearby functions."""
import idc, ida_funcs, ida_bytes, idautils, idaapi
import traceback
from pathlib import Path

LOG  = Path("analysis/s4/farobj_type.log")
log = []

TARGET_EAS = [
    0x2647E,  # farobj_type_field_get
    0x24980,  # stub_to_24980
    0x24988,  # stub_to_24988
    0x34C31,  # mode_axis_state_select (accesses [DI+1])
    0x44352,  # farobj_entity_attr_setup (accesses [DI+6,7,22])
    0x34193,  # farobj_scan_74_clear_b
    0x49A5B,  # sub_49A5B (accesses [DI+22,26])
    0x2E8F4,  # farptr_table_field20_get  
    0x2E902,  # farptr_table_field_store
]

try:
    for ea in TARGET_EAS:
        fn = ida_funcs.get_func(ea)
        if fn is None:
            log.append("SKIP 0x%X: no function" % ea)
            continue
        name = idc.get_func_name(ea)
        log.append("\n=== 0x%X  %s  %dB ===" % (ea, name, fn.end_ea - fn.start_ea))
        a = fn.start_ea
        limit = 60
        while a < fn.end_ea and limit > 0:
            log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
            limit -= 1
        if a < fn.end_ea:
            log.append("  ... truncated")

    LOG.write_text("\n".join(log))
except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
