"""Apply RTLink fixups to the IDB: word += 0x1000 at the anchor-corrected
absolute offset (finding 57).

Reads analysis/ida_falconcd/fixups_to_apply.json: {row: [[abs_off, word_before]]}
where abs_off = (seg - w0) * 16 + off (finding 56's paragraph anchor).

Per-entry guard: patch only when the current word still equals the recorded
link-time value.  A word that already equals `+0x1000` is counted as
`already_done` (pass 1 applied it at the same address for every `seg == w0`
pair, and those must stay untouched); anything else is `mismatch` and is NOT
written.

Finding 56/57 also removes the old per-segment blanket skip: the `RTFIX` marker
skipped a whole record, which would have prevented these sub-block fixups from
ever reaching records pass 1 already touched. Idempotency now comes from the
per-entry word guard, which is exact.

After patching, any patched word that sits inside an instruction has its
instruction head re-created so the decoded operands are fresh -- no auto_wait
(finding 37).  Saves only if every patch verifies AND no word mismatched.

Usage: cmd /c "tools\\run_idat.bat tools\\apply_overlay_fixups.py"
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

ROOT = r"C:\Users\yotam\projects\falcon3"
FIXUPS = ROOT + r"\analysis\ida_falconcd\fixups_to_apply.json"
PLACE = ROOT + r"\analysis\ida_falconcd\overlay_placement.json"
LOG = ROOT + r"\analysis\ida_falconcd\apply_fixups.log"
IDB_PATH = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

fixups = {int(k): v for k, v in json.load(open(FIXUPS)).items()}
placements = {p["idx"]: p for p in json.load(open(PLACE))}
log = []


def main():
    # ---- build the work list, skipping placements we cannot address ----
    jobs = []                       # (idx, ea, w_before)
    oob = 0
    for idx, plist in sorted(fixups.items()):
        p = placements.get(idx)
        if not p or p["addr"] == "skip" or not p["ida_len"]:
            continue
        base = p["ida_ea"]
        for rel, w_before in plist:
            ea = base + rel
            if ida_segment.getseg(ea) is None:
                oob += 1
                continue
            jobs.append((idx, ea, w_before))
    planned = len(jobs)

    # ---- remember the spans of every function we are about to touch, and
    # ---- which patched bytes already live inside a decoded instruction ----
    touched = sorted({ea for _, ea, _ in jobs})
    spans = {}
    insn_heads = set()
    for ea in touched:
        f = ida_funcs.get_func(ea)
        if f is not None:
            spans[(f.start_ea, f.end_ea)] = name_of(f.start_ea)
        h = ida_bytes.get_item_head(ea)
        if h is not None and (idc.print_insn_mnem(h) or ""):
            insn_heads.add(h)
    log.append("planned=%d  oob=%d  functions to touch=%d  pre-existing insn heads=%d"
               % (planned, oob, len(spans), len(insn_heads)))

    # ---- apply ----
    applied = already = mismatch = 0
    samples = []
    heads_to_refresh = set()
    for idx, ea, w_before in jobs:
        cur = ida_bytes.get_word(ea)
        expect = (w_before + 0x1000) & 0xFFFF
        if cur == w_before:
            ida_bytes.put_word(ea, expect)
            applied += 1
            heads_to_refresh.add(ida_bytes.get_item_head(ea))
        elif cur == expect:
            already += 1                 # pass 1 already did exactly this
        else:
            mismatch += 1
            if len(samples) < 8:
                samples.append("idx%d ea=0x%X expect_before=0x%04X got=0x%04X"
                               % (idx, ea, w_before, cur))

    # ---- refresh ONLY pre-existing instruction heads whose operand we changed.
    #      Re-decoding a byte IDA had as data would invent an instruction and
    #      can move a function boundary (finding 57 guard caught that).
    #      No auto_wait (finding 37).
    refreshed = 0
    for h in sorted(insn_heads & heads_to_refresh):
        if ida_ua.create_insn(h):
            refreshed += 1
    log.append("applied=%d already_done=%d mismatch=%d  heads re-decoded=%d"
               % (applied, already, mismatch, refreshed))
    for s in samples:
        log.append("  MISMATCH %s" % s)

    # ---- guard 1: every patch landed ----
    bad_patch = 0
    for idx, ea, w_before in jobs:
        if ida_bytes.get_word(ea) != ((w_before + 0x1000) & 0xFFFF):
            bad_patch += 1
    # ---- guard 2: no function span moved ----
    moved = []
    for (s, e), nm in spans.items():
        f = ida_funcs.get_func(s)
        if not f or f.start_ea != s or f.end_ea != e:
            moved.append("%s 0x%X was %X..%X now %s" % (
                nm, s, s, e, ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))

    # A mismatch is a location we REFUSED to write (cur matched neither the
    # recorded link value nor the already-patched value) -- exactly what pass 1
    # did with those, so it is reported but not fatal: we never write unverified.
    if mismatch:
        log.append("note: %d word mismatches left untouched (pass 1 reported 177)"
                   % mismatch)
    if bad_patch:
        log.append("GUARD FAILED: %d patches did not verify" % bad_patch)
    elif moved:
        log.append("GUARD FAILED: %d function spans moved" % len(moved))
        for m in moved[:10]:
            log.append("   %s" % m)
    else:
        log.append("GUARD PASSED: %d applied, %d already present, 0 mismatch, "
                   "%d function spans unchanged"
                   % (applied, already, len(spans)))
        ida_loader.save_database(IDB_PATH, 0)
        log.append("SAVED")
        return
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_f57_fixups if needed")


def name_of(ea):
    return idc.get_func_name(ea) or ("0x%X" % ea)


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_f57_fixups if needed")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
