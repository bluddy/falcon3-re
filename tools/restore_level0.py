"""Restore the 4 hot Level-0 leaves that a diagnostic's del_items removed.

Root cause: tools/_verify_claims.py called ida_bytes.del_items() on existing
functions just to disassemble them, and the deletion persisted (idat -A
saves a dirty DB on exit). Lesson recorded: diagnostics must never
del_items existing functions.

Known-good boundaries (pre-deletion classification + terminator check):
  sub_112A1 0x112A1..0x112C6  37B  retf   (318K calls)
  sub_2703F 0x2703F..0x27051  18B  retf   (209K)
  sub_2228F 0x2228F..0x222A0  17B  retf   (205K)
  sub_22285 0x22285..0x2228F  10B  retf   (202K)

Uses the fix_trace_functions.py proven pattern (disable autoanalysis,
force-decode, set_func_end, save WITHOUT auto_wait).

Usage: cmd /c "tools\\run_idat.bat tools\\restore_level0.py"
"""
import traceback

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idautils

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\restore_level0.log"

FUNCS = [
    (0x112A1, 0x112C6, "sub_112A1"),
    (0x2703F, 0x27051, "sub_2703F"),
    (0x2228F, 0x222A0, "sub_2228F"),
    (0x22285, 0x2228F, "sub_22285"),
]

log = []
try:
    # report pre-state
    for ea, end, name in FUNCS:
        f = ida_funcs.get_func(ea)
        log.append("BEFORE 0x%X: %s" % (ea, ("%s-%s" % (hex(f.start_ea), hex(f.end_ea))) if f else "NONE"))

    ida_auto.enable_auto(False)
    for ea, end, name in FUNCS:
        if ida_funcs.get_func(ea):
            log.append("%s already present, skip" % name)
            continue
        ida_bytes.del_items(ea, ida_bytes.DELIT_EXPAND, end - ea)
        pos = ea
        bad = None
        while pos < end:
            if not ida_ua.create_insn(pos):
                ida_bytes.del_items(pos, ida_bytes.DELIT_EXPAND, 16)
                if not ida_ua.create_insn(pos):
                    bad = pos
                    break
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                bad = pos
                break
            pos += sz
        if bad is not None or pos != end:
            log.append("%s DECODE MISMATCH bad=%s pos=0x%X -> ABORT"
                       % (name, hex(bad) if bad else "-", pos))
            continue
        ok = ida_funcs.add_func(ea, end)
        ida_name.set_name(ea, name, ida_name.SN_CHECK)
        if ok:
            ida_funcs.set_func_end(ea, end)
        f = ida_funcs.get_func(ea)
        log.append("%s add_func=%s -> %s"
                   % (name, ok, ("%s-%s" % (hex(f.start_ea), hex(f.end_ea))) if f else "NONE"))

    ida_loader.save_database(IDB, 0)
    ida_auto.enable_auto(True)
    log.append("saved; total fns=%d" % len(list(idautils.Functions())))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
