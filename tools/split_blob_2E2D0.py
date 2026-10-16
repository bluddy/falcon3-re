"""Split the 51,676B blob sub_2E2D0 at its two hot secondary entries (finding 42).

sub_2E2D0 spans 0x2E2D0..0x3ACAC. Verified from raw bytes:
  [0x2E2D0,0x2E2E0) 16B, retf at end  -- far-called 12,106x (blob entry)
  [0x2E2E0,0x2E2F0) 16B, retf at end  -- far-called  8,312x (MID target)
  [0x2E2F0,0x3ACAC) residual, starts at a far-call entry (8,696x)

Split pattern follows apply_trace_functions.py (finding 33): del_func ->
del_items -> create_insn at the new HEADS only -> add_func per range.
NO auto_wait (finding 37: it shrinks explicitly-registered ranges).

GUARD: if any of the 3 add_func/set_func_end calls does not produce exactly
the planned range, the script reports failure and EXITS WITHOUT SAVING, so
the caller can restore <IDB>.bak_before_split. Note idat may still persist a
dirty DB on exit, which is why the host-side backup is mandatory.

Usage: cmd /c "tools\\run_idat.bat tools\\split_blob_2E2D0.py"
"""
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\split_blob.log"

PLAN = [
    (0x2E2D0, 0x2E2E0),   # 16B slot, 12,106 calls
    (0x2E2E0, 0x2E2F0),   # 16B slot,  8,312 calls
    (0x2E2F0, 0x3ACAC),   # residual (starts at 8,696-call entry)
]

log = []
ok_all = False
try:
    f = ida_funcs.get_func(0x2E2D0)
    if not f:
        log.append("FATAL: sub_2E2D0 not found as a function; aborting")
        raise SystemExit(1)
    log.append("before: 0x%X..0x%X (%dB)" % (f.start_ea, f.end_ea, f.end_ea - f.start_ea))

    ida_funcs.del_func(0x2E2D0)
    ida_bytes.del_items(0x2E2D0, ida_bytes.DELIT_SIMPLE, 0x3ACAC - 0x2E2D0)
    log.append("del_func + del_items over 0x2E2D0..0x3ACAC done")

    # decode the three heads only (finding-33 pattern)
    for start, end in PLAN:
        ida_ua.create_insn(start)

    for start, end in PLAN:
        ok = ida_funcs.add_func(start, end)
        if ok:
            ida_funcs.set_func_end(start, end)
        g = ida_funcs.get_func(start)
        good = bool(g) and g.start_ea == start and g.end_ea == end
        log.append("  add_func(0x%X..0x%X)=%s -> %s  %s"
                   % (start, end, ok,
                      ("%s-%s" % (hex(g.start_ea), hex(g.end_ea))) if g else "NONE",
                      "OK" if good else "** MISMATCH **"))
        if not good:
            ok_all = False
            break
    else:
        ok_all = True

    # coverage + naming check
    if ok_all:
        covered = sum(e - s for s, e in PLAN)
        log.append("coverage: %dB vs blob 51676B -> %s"
                   % (covered, "exact" if covered == 51676 else "MISMATCH"))
        ida_name.set_name(0x2E2D0, "sub_2E2D0", ida_name.SN_CHECK)
        ida_name.set_name(0x2E2E0, "sub_2E2E0", ida_name.SN_CHECK)
        ida_name.set_name(0x2E2F0, "sub_2E2F0", ida_name.SN_CHECK)
        for s, e in PLAN:
            g = ida_funcs.get_func(s)
            log.append("    0x%X..0x%X %dB last=%02X"
                       % (g.start_ea, g.end_ea, g.end_ea - g.start_ea,
                          ida_bytes.get_byte(g.end_ea - 1)))

except Exception:
    log.append("EXCEPTION (db left dirty -- restore backup if needed):")
    log.append(traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_before_split if the IDB looks wrong")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
