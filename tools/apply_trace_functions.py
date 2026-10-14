"""Register trace-verified functions + split mis-merged functions (headless).

v2: forces chunk conversion (del_items + create_insn) before add_func —
most v1 failures were "not a code chunk" (seg000 startup area, PSP-adjacent
data chunks, data-table-adjacent fns).

Input: analysis/traces/boundary_report.json (tools/verify_boundaries.py).
Usage: cmd /c "tools\\run_idat.bat tools\\apply_trace_functions.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc_trace2.log"
REPORT = r"C:\Users\yotam\projects\falcon3\analysis\traces\boundary_report.json"


def force_code(ea, size):
    """Clear whatever IDA thinks is there, decode one insn, mark chunk code."""
    ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, size)
    ida_ua.create_insn(ea)


def try_add(ea, end_ea):
    force_code(ea, min(end_ea - ea, 8))
    ok = ida_funcs.add_func(ea, end_ea)
    return ok


rep = json.load(open(REPORT))
log = []
added = 0
split = 0
skipped = 0

try:
    # 1) split mis-merged functions
    for e in rep["mid"]:
        if e.get("region") != "resident" or not e.get("ida_ea"):
            continue
        fn_ea, cand = e["fn_ea"], e["ida_ea"]
        fn_end = fn_ea + e["fn_size"]
        if not (fn_ea < cand < fn_end):
            skipped += 1
            continue
        if ida_funcs.get_func(cand):
            skipped += 1  # already split in a previous pass
            continue
        ida_funcs.del_func(fn_ea)
        # force the whole original range back to raw bytes
        ida_bytes.del_items(fn_ea, ida_bytes.DELIT_SIMPLE, fn_end - fn_ea)
        ida_ua.create_insn(fn_ea)
        ida_ua.create_insn(cand)
        ok_l = ida_funcs.add_func(fn_ea, cand)
        ok_r = ida_funcs.add_func(cand, fn_end)
        ida_name.set_name(cand, "sub_%X" % cand, ida_name.SN_CHECK)
        log.append("SPLIT %s: 0x%X..0x%X + 0x%X..0x%X (L=%s R=%s) calls=%d"
                   % (e["fn"], fn_ea, cand, cand, fn_end, ok_l, ok_r, e["calls"]))
        split += 1 if (ok_l and ok_r) else 0

    # 2) register missed functions (UNKNOWN targets)
    for e in rep["unknown"]:
        if e.get("region") == "other" or not e.get("ida_ea"):
            continue
        ea = e["ida_ea"]
        span = e.get("span_to_next_fn") or 0
        if span < 2:
            skipped += 1
            continue
        if ida_funcs.get_func(ea):
            skipped += 1
            continue
        end_ea = ea + span
        ok = try_add(ea, end_ea)
        ida_name.set_name(ea, "sub_%X" % ea, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        log.append("ADD %s 0x%X..0x%X ok=%s span=%#x calls=%d -> %s"
                   % (e["region"], ea, end_ea, ok, span, e["calls"],
                      (hex(f.start_ea) + "-" + hex(f.end_ea)) if f else "NONE"))
        added += 1 if f else 0

    idaapi.auto_wait()
    ida_loader.save_database(IDB, 0)
    log.append("saved; added=%d split=%d skipped=%d" % (added, split, skipped))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
