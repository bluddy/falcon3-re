"""Pass 2 of the finding-52 fix: re-decode the bodies of overlay functions.

fix_overlay_bitness.py cleared 1,053,376 bytes of 32-bit items across the R*
segments and re-added the 210 functions, but only created the instruction at
each function's start -- so every body reads as `??`. This walks each overlay
function's [start, end) creating 16-bit instructions.

Resident segments are untouched (they were already 16-bit and still are).

GUARD: saves only if every targeted byte in every range became a defined
instruction (zero-size items are the only tolerated gap), and the first/last
instructions of a sample decode as expected.

Usage: cmd /c "tools\run_idat.bat tools\fix_overlay_bodies.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fix_bodies.log"

log = []
ok_all = False

try:
    cls = json.load(open(CLS))
    rsegs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        if ida_segment.get_segm_name(s).startswith("R"):
            rsegs.append((s.start_ea, s.end_ea))

    fns = [(v["ea"], v["ea"] + v["size"]) for v in cls.values()
           if any(a <= v["ea"] < b for a, b in rsegs)]
    fns.sort()
    log.append("overlay functions to re-decode: %d" % len(fns))

    total_bytes = decoded = gap = fail = 0
    for ea, end in fns:
        pos = ea
        while pos < end:
            n = ida_ua.create_insn(pos)
            if n > 0:
                decoded += n
                pos += n
                continue
            # already defined and decodes to something? advance by its size
            sz = ida_bytes.get_item_size(pos)
            if sz > 0 and (idc.print_insn_mnem(pos) or ""):
                pos += sz
                continue
            gap += 1
            if gap <= 10:
                log.append("  UNDECODABLE 0x%X (inside 0x%X..0x%X)" % (pos, ea, end))
            pos += 1
        total_bytes += end - ea

    log.append("bytes in overlay fn ranges : %d" % total_bytes)
    log.append("instruction bytes created  : %d" % decoded)
    log.append("positions that would not decode: %d" % gap)

    # sample sanity checks (16-bit must render, no 32-bit-only registers)
    samples = [0x103087, 0x15CC1A, 0x16BACF, 0x165C80]
    bad32 = 0
    for ea in samples:
        f = ida_funcs.get_func(ea)
        if not f:
            continue
        pos, i, txt = f.start_ea, 0, []
        while pos < f.end_ea and i < 6:
            txt.append("%s %s" % (idc.print_insn_mnem(pos) or "??",
                                  idc.print_operand(pos, 0) or ""))
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                break
            pos += sz
            i += 1
        log.append("0x%X: %s" % (ea, " | ".join(txt)))
        blob = " ".join(txt)
        for reg in ("eax", "ebx", "ecx", "edx", "esi", "edi", "push eax", "stosd"):
            if reg in blob:
                bad32 += 1

    problems = []
    if gap > 0:
        problems.append("%d positions would not decode" % gap)
    if bad32:
        problems.append("32-bit register names still present in samples: %d" % bad32)
    if problems:
        log.append("GUARD FAILED: %s" % "; ".join(problems))
        ok_all = False
    else:
        log.append("GUARD PASSED")
        ok_all = True

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
