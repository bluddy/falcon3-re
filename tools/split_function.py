"""Split one IDA function at an internal address (finding 50).

Generalises the one-off `split_blob_2E2D0.py` (finding 42) into a reusable
tool, because pass 2 of the graph cleanup needs the same guarded sequence
for every boundary error.

Method (finding-33/42 pattern):
    del_func -> del_items(DELIT_SIMPLE) -> create_insn(new heads only)
    -> add_func + set_func_end per planned range.
NO auto_wait (finding 37: it shrinks explicitly-registered ranges).

GUARD: if any add_func/set_func_end does not yield exactly the planned
range, or the ranges do not tile the original span exactly, the script does
NOT call ida_loader.save_database(). idat may still persist a dirty DB on
exit, so the host-side backup taken immediately before is mandatory --
verify with tools/verify_idb.py + tools/verify_rebuild.py afterwards.

Usage:
  SPLIT_EA=0x23962 SPLIT_AT=0x23966 cmd /c "tools\\run_idat.bat tools\\split_function.py"

SPLIT_EA must be the current function start; SPLIT_AT must be a valid item
head strictly inside it whose preceding instruction is a terminator.
"""
import os
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\split_function.log"
TERM = {"retn", "retf", "ret", "iret", "jmp"}

ea = int(os.environ.get("SPLIT_EA", "0"), 16)
at = int(os.environ.get("SPLIT_AT", "0"), 16)
name1 = os.environ.get("SPLIT_NAME1") or ("sub_%X" % ea)
name2 = os.environ.get("SPLIT_NAME2") or ("sub_%X" % at)

log = []
ok_all = False

try:
    if ea == 0 or at == 0:
        raise SystemExit("SPLIT_EA / SPLIT_AT not set")

    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        log.append("FATAL: no function starting at 0x%X" % ea)
        raise SystemExit(1)
    orig_start, orig_end = f.start_ea, f.end_ea
    orig_size = orig_end - orig_start
    log.append("before: 0x%X..0x%X (%dB)" % (orig_start, orig_end, orig_size))

    if not (orig_start < at < orig_end):
        log.append("FATAL: SPLIT_AT 0x%X not strictly inside 0x%X..0x%X"
                   % (at, orig_start, orig_end))
        raise SystemExit(1)

    # Precondition: an item head at `at`, and the instruction before it must
    # terminate flow -- otherwise `at` is only a branch target and the range
    # must not be split (this check is what turned 10 candidates into 1).
    if idc.get_item_head(at) != at:
        log.append("FATAL: 0x%X is not an item head" % at)
        raise SystemExit(1)
    prev = idc.prev_head(at, orig_start)
    prev_mn = (idc.print_insn_mnem(prev) or "").lower()
    prev_end = prev + ida_bytes.get_item_size(prev) if prev != idc.BADADDR else -1
    if prev_mn not in TERM or prev_end != at:
        log.append("FATAL: instruction before 0x%X is '%s' (ends 0x%X); "
                   "terminator ending exactly there required" % (at, prev_mn, prev_end))
        raise SystemExit(1)
    log.append("precondition OK: '%s' @0x%X ends exactly at split point" % (prev_mn, prev))

    plan = [(orig_start, at), (at, orig_end)]

    ida_funcs.del_func(ea)
    ida_bytes.del_items(orig_start, ida_bytes.DELIT_SIMPLE, orig_size)
    log.append("del_func + del_items over 0x%X..0x%X done" % (orig_start, orig_end))

    for s, e in plan:
        ida_ua.create_insn(s)

    ok_all = True
    for s, e in plan:
        ok = ida_funcs.add_func(s, e)
        if ok:
            ida_funcs.set_func_end(s, e)
        g = ida_funcs.get_func(s)
        good = bool(g) and g.start_ea == s and g.end_ea == e
        log.append("  add_func(0x%X..0x%X)=%s -> %s  %s"
                   % (s, e, ok,
                      ("%s..%s" % (hex(g.start_ea), hex(g.end_ea))) if g else "NONE",
                      "OK" if good else "** MISMATCH **"))
        if not good:
            ok_all = False
            break

    if ok_all:
        covered = sum(e - s for s, e in plan)
        log.append("coverage: %dB vs original %dB -> %s"
                   % (covered, orig_size, "exact" if covered == orig_size else "MISMATCH"))
        if covered != orig_size:
            ok_all = False

    if ok_all:
        ida_name.set_name(plan[0][0], name1, ida_name.SN_CHECK)
        ida_name.set_name(plan[1][0], name2, ida_name.SN_CHECK)
        for s, e in plan:
            g = ida_funcs.get_func(s)
            log.append("    0x%X..0x%X %dB  name=%s  last=%02X"
                       % (g.start_ea, g.end_ea, g.end_ea - g.start_ea,
                          idc.get_func_name(g.start_ea),
                          ida_bytes.get_byte(g.end_ea - 1)))

except SystemExit:
    ok_all = False
except Exception:
    log.append("EXCEPTION (db left dirty -- restore the pre-split backup):")
    log.append(traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_presplit if the IDB looks wrong")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
