"""Dry-run probe: plan the split of the 51,676B blob sub_2E2D0 (finding 42).

sub_2E2D0 = one IDA "function" spanning 0x2E2D0..0x3ACAC (51,676B, the next
largest fn is 4,169B). It is real code with secondary entry points that IDA
never turned into functions — 5 far-call targets land MID inside it, two with
8.3K/8.7K calls (0x2E2E0, 0x2E2F0). Byte pattern shows 16-byte slots each
ending in `retf`.

THIS IS READ-ONLY: disassembles each split candidate to find its terminator,
clipped so it never crosses the next candidate, and prints the plan.
Mutation lives in split_blob_2E2D0.py.

Usage: cmd /c "tools\\run_idat.bat tools\\probe_blob_split.py"
"""
import traceback

import ida_bytes
import ida_funcs
import ida_ua
import idaapi
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\probe_blob_split.log"
BLOB = 0x2E2D0
BLOB_END = 0x2E2D0 + 51676
CANDIDATES = [0x2E2D0, 0x2E2E0, 0x2E2F0, 0x2E37B, 0x2E380, 0x2E6C6]
TERMS = {0xC3: "ret", 0xCB: "retf", 0xCF: "iret"}

log = []
try:
    f = ida_funcs.get_func(BLOB)
    log.append("blob: %s .. %s (%dB) name=%s" %
               (hex(f.start_ea), hex(f.end_ea), f.end_ea - f.start_ea,
                idc.get_func_name(BLOB)))
    log.append("candidates: %s" % ", ".join(hex(c) for c in CANDIDATES))
    log.append("")

    # disassemble WITHOUT deleting: probe on a copy of the byte stream is not
    # possible, so we del_items ONLY over a candidate's own small span and
    # restore nothing -- NO. Instead: use decode over existing code where
    # possible; only del_items the candidate span if it is currently data.
    points = sorted(set(CANDIDATES + [BLOB_END]))
    plan = []
    for i, start in enumerate(points[:-1]):
        limit = points[i + 1]
        # decode forward from `start` looking for a standalone terminator
        pos = start
        end = None
        steps = 0
        while pos < limit and steps < 400:
            # create_insn is safe on already-code spans; on data spans it
            # fails, which we report rather than forcing.
            ok = ida_ua.create_insn(pos)
            if not ok:
                log.append("  [%d] 0x%X: decode FAILED at 0x%X (limit 0x%X)"
                           % (i, start, pos, limit))
                break
            b = ida_bytes.get_byte(pos)
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                log.append("  [%d] 0x%X: zero-size at 0x%X" % (i, start, pos))
                break
            if b in TERMS and sz == 1:
                end = pos + 1
                break
            pos += sz
            steps += 1
        if end:
            residual = limit - end
            log.append("  [%d] start=0x%X -> term=0x%X  %3dB (%s) | residual to 0x%X: %dB"
                       % (i, start, end, end - start, TERMS[ida_bytes.get_byte(end - 1)],
                          limit, residual))
            plan.append((start, end, limit))
        else:
            log.append("  [%d] start=0x%X -> NO TERM before 0x%X  (would register whole span %dB)"
                       % (i, start, limit, limit - start))
            plan.append((start, limit, limit))

    log.append("")
    log.append("PLAN (register these; union must cover 0x%X..0x%X):" % (BLOB, BLOB_END))
    covered = 0
    for start, end, limit in plan:
        gap = start - (plan[plan.index((start, end, limit)) - 1][1] if plan.index((start, end, limit)) else BLOB)
        log.append("   0x%X .. 0x%X  (%dB)" % (start, end, end - start))
        covered += end - start
    log.append("coverage check: next start should equal prev end")
    ok = all(plan[i][1] == plan[i + 1][0] for i in range(len(plan) - 1))
    log.append("  contiguous (no gaps/overlaps): %s" % ok)
    log.append("  total covered: 0x%X vs blob 0x%X" % (covered, BLOB_END - BLOB))

except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
