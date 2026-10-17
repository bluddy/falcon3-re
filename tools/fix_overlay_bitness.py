"""Fix finding 52: overlay segments are decoded as 32-bit in a 16-bit program.

Every R* segment was created by rebuild_overlay_segments.py:61 via add_segm()
without setting bitness, so IDA decoded real-mode overlay code as 32-bit
(`push eax`, `stosd`, `mov ebx 579A000Ch`). The resident loader segments are
16-bit; these must match.

Passes, in order:
  1. record every function currently inside an R* segment (start, end, name)
  2. set bitness = 0 (16-bit) on every R* segment
  3. del_func + del_items per segment so old 32-bit items are gone
  4. re-decode each recorded start as 16-bit and probe its end
     - KEEP the existing end if it still validates (standalone C3/CB/CF on a
       16-bit boundary, before the next recorded start) -> zero churn there
     - otherwise take the probe's end
     - if neither works, keep the old end and flag it
  5. add_func + set_name for every recorded start

GUARD: saves only if every recorded start has a function afterwards, no end
crosses the next start, and no segment kept a 32-bit bitness. Otherwise it
exits without save_database (idat may still persist a dirty DB -- restore
FALCONCD.EXE.i64.bak_bitness if needed).

NO auto_wait() anywhere: finding 37 showed it shrinks registered ranges.

Usage: cmd /c "tools\run_idat.bat tools\fix_overlay_bitness.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_segment
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fix_bitness.log"

TERMS = {0xc3, 0xcb, 0xcf}
log = []
ok_all = False

try:
    cls = json.load(open(CLS))
    n_before = ida_funcs.get_func_qty()

    # ---- 1. record overlay functions -------------------------------------
    rsegs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        if ida_segment.get_segm_name(s).startswith("R"):
            rsegs.append((s.start_ea, s.end_ea, ida_segment.get_segm_name(s)))
    rsegs.sort()
    log.append("R* segments: %d" % len(rsegs))

    recorded = []
    for k, v in sorted(cls.items(), key=lambda kv: kv[1]["ea"]):
        ea = v["ea"]
        if not any(a <= ea < b for a, b, _ in rsegs):
            continue
        f = ida_funcs.get_func(ea)
        if not f or f.start_ea != ea:
            continue
        recorded.append((ea, f.end_ea, idc.get_func_name(ea) or ("sub_%X" % ea)))
    log.append("overlay functions recorded: %d" % len(recorded))
    if not recorded:
        raise SystemExit("nothing recorded -- aborting")

    # next recorded start within the same segment (bound for the probe)
    starts = [r[0] for r in recorded]

    # ---- 2. 16-bit bitness ------------------------------------------------
    changed_bits = 0
    for a, b, nm in rsegs:
        s = ida_segment.getseg(a)
        if s is None:
            continue
        if s.bitness != 0:
            s.bitness = 0
            changed_bits += 1
    log.append("segments switched to 16-bit: %d" % changed_bits)

    # ---- 3. drop old 32-bit items ----------------------------------------
    for ea, end, name in recorded:
        if ida_funcs.get_func(ea):
            ida_funcs.del_func(ea)
    n_del = 0
    for a, b, nm in rsegs:
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, b - a)
        n_del += b - a
    log.append("cleared %d bytes of 32-bit items across %d segments"
               % (n_del, len(rsegs)))

    # ---- 4/5. re-decode, probe end, re-add --------------------------------
    keep = new = flagged = 0
    for idx, (ea, old_end, name) in enumerate(recorded):
        seg = ida_segment.getseg(ea)
        seg_end = seg.end_ea if seg else old_end
        nxt = next((s for s in starts if s > ea), seg_end)
        limit = min(nxt, ea + 4000, seg_end)

        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, min(max(old_end, ea + 8) - ea, 64))
        if not ida_ua.create_insn(ea):
            log.append("  0x%X FAIL create_insn" % ea)
            flagged += 1
            continue

        # probe for a standalone terminator
        pos, probed = ea, None
        while pos < limit:
            n = ida_ua.create_insn(pos)
            if n <= 0:
                break
            if ida_bytes.get_byte(pos) in TERMS and n == 1:
                probed = pos + 1
                break
            pos += n

        # does the OLD end still validate under 16-bit decode?
        old_ok = (ea < old_end <= nxt and old_end <= seg_end
                  and ida_bytes.get_byte(old_end - 1) in TERMS)
        if old_ok:
            end = old_end
            keep += 1
        elif probed:
            end = probed
            new += 1
        else:
            end = old_end
            flagged += 1
            log.append("  0x%X no terminator; keeping old end 0x%X" % (ea, old_end))

        if end > nxt:
            end = nxt
            log.append("  0x%X WARN clamped end to next start 0x%X" % (ea, nxt))

        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 8)
        ida_ua.create_insn(ea)
        ok = ida_funcs.add_func(ea, end)
        if ok:
            ida_funcs.set_func_end(ea, end)
        ida_name.set_name(ea, name, ida_name.SN_CHECK)

    log.append("end kept (already valid under 16-bit): %d" % keep)
    log.append("end re-probed (32-bit artifact)       : %d" % new)
    log.append("flagged (no terminator found)         : %d" % flagged)

    # ---- guard ------------------------------------------------------------
    problems = []
    if ida_funcs.get_func_qty() < len(recorded):
        problems.append("function count %d < recorded %d"
                        % (ida_funcs.get_func_qty(), len(recorded)))
    prev_end = -1
    for ea, old_end, name in recorded:
        f = ida_funcs.get_func(ea)
        if not f:
            problems.append("0x%X lost its function" % ea)
            continue
        if f.start_ea != ea:
            problems.append("0x%X start moved to 0x%X" % (ea, f.start_ea))
        if f.end_ea > prev_end:
            prev_end = f.end_ea
        # no overrun into the next recorded start
        nxt = next((s for s in starts if s > ea), None)
        if nxt is not None and f.end_ea > nxt:
            problems.append("0x%X end 0x%X overruns next 0x%X" % (ea, f.end_ea, nxt))
    for a, b, nm in rsegs:
        s = ida_segment.getseg(a)
        if s is None or s.bitness != 0:
            problems.append("segment %s still bitness=%s"
                            % (nm, s.bitness if s else "?"))
    log.append("functions: %d (was %d, recorded %d)"
               % (ida_funcs.get_func_qty(), n_before, len(recorded)))
    if problems:
        log.append("GUARD FAILED (%d):" % len(problems))
        for p in problems[:20]:
            log.append("   " + p)
        ok_all = False
    else:
        log.append("GUARD PASSED")
        ok_all = True

except SystemExit:
    ok_all = False
except Exception:
    log.append("EXCEPTION (db dirty -- restore FALCONCD.EXE.i64.bak_bitness):")
    log.append(traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_bitness if it looks wrong")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
