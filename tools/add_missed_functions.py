"""Register IDA-missed keyboard-unit functions in the IDB (headless, batch).

Finding 28: contiguous call-displacement arithmetic of the keyboard TU
(0x19BFF..0x1A4CA) exposed 11 functions that IDA's auto-analysis never
created. Each entry: add_func(ea, end_ea) + set_name + save.

This replaces the session-ephemeral _add_missed_fn3.py so the IDB regen
runbook (status.md) is reproducible. sub_19D65 (finding 26) and sub_19F7A/
sub_19F8E (gap batch 2) were registered by _add_missed_fn.py / _add_missed_fn2.py;
re-running add_func over already-registered ranges is a harmless no-op.

Usage: cmd /c "tools\\run_idat.bat tools\\add_missed_functions.py"
"""
import traceback

import ida_funcs
import ida_loader
import ida_name
import idaapi

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc3.log"

# (ea, end_ea, name) -- 11 keyboard-unit gap functions (finding 28)
NEW_FUNCS = [
    (0x19BFF, 0x19C0A, "sub_19BFF"),   # kb_record_base, 11B
    (0x1A00F, 0x1A023, "sub_1A00F"),   # kb_field_set_27_1, 20B
    (0x1A0BC, 0x1A0D2, "sub_1A0BC"),   # kb_clear_28, 22B
    (0x1A123, 0x1A176, "sub_1A123"),   # kb_field_set_2c, 83B
    (0x1A1D6, 0x1A24B, "sub_1A1D6"),   # kb_field_get_31, 117B
    (0x1A2DE, 0x1A348, "sub_1A2DE"),   # kb_array_get_1, 106B
    (0x1A348, 0x1A3B3, "sub_1A348"),   # kb_array_set_1, 107B
    (0x1A3B3, 0x1A423, "sub_1A3B3"),   # kb_array_get_2, 112B
    (0x1A423, 0x1A494, "sub_1A423"),   # kb_array_set_2, 113B
    (0x1A4A2, 0x1A4B6, "sub_1A4A2"),   # kb_flag_set_10_1, 20B
    (0x1A4B6, 0x1A4CA, "sub_1A4B6"),   # kb_flag_set_10_0, 20B
]

log = []
try:
    for ea, end_ea, name in NEW_FUNCS:
        ok = ida_funcs.add_func(ea, end_ea)
        ida_name.set_name(ea, name, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        log.append("%s add_func(0x%X..0x%X)=%s -> %s"
                   % (name, ea, end_ea, ok,
                      (hex(f.start_ea) + "-" + hex(f.end_ea)) if f else "NONE"))
    idaapi.auto_wait()
    ida_loader.save_database(IDB, 0)
    log.append("saved")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
