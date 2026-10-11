"""Apply RTLink fixups to rebuilt overlay segments (validated semantics: word += 0x1000).

Reads analysis/ida_falconcd/fixups_to_apply.json: {row: [[rel, word_before], ...]}
For each placed record: at ida_ea+rel, verify current word == word_before
(guard: if mismatch, record was already applied or drifted -> skip+report),
then patch word += 0x1000 (L, IDA runtime space).
Idempotent via per-segment comment marker.
"""
import json
import traceback

import ida_segment
import ida_bytes
import idaapi
import ida_loader

ROOT = r"C:\Users\yotam\projects\falcon3"
FIXUPS = ROOT + r"\analysis\ida_falconcd\fixups_to_apply.json"
PLACE = ROOT + r"\analysis\ida_falconcd\overlay_placement.json"
LOG = ROOT + r"\analysis\ida_falconcd\apply_fixups.log"
IDB_PATH = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

fixups = {int(k): v for k, v in json.load(open(FIXUPS)).items()}
placements = {p["idx"]: p for p in json.load(open(PLACE))}
log = []


def main():
    applied = skipped_done = mismatch = oob = 0
    samples = []
    for idx, plist in sorted(fixups.items()):
        p = placements.get(idx)
        if not p or p["addr"] == "skip" or not p["ida_len"]:
            continue
        base = p["ida_ea"]
        marker = "RTFIX"
        if ida_bytes.get_cmt(base, 0) and marker in (ida_bytes.get_cmt(base, 0) or ""):
            skipped_done += len(plist)
            continue
        for rel, w_before in plist:
            ea = base + rel
            if ida_segment.getseg(ea) is None:
                oob += 1
                continue
            cur = ida_bytes.get_word(ea)
            if cur != w_before:
                mismatch += 1
                if len(samples) < 6:
                    samples.append("idx%d ea=0x%X expect=0x%04X got=0x%04X" % (
                        idx, ea, w_before, cur))
                continue
            ida_bytes.put_word(ea, (w_before + 0x1000) & 0xFFFF)
            applied += 1
        cmt = ida_bytes.get_cmt(base, 0) or ""
        if marker not in cmt:
            ida_bytes.set_cmt(base, cmt + " | RTFIX applied", 0)

    log.append("applied=%d already_done=%d mismatch=%d oob=%d" % (
        applied, skipped_done, mismatch, oob))
    for s in samples:
        log.append("  MISMATCH %s" % s)

    idaapi.auto_wait()
    ida_loader.save_database(IDB_PATH, 0)
    log.append("saved")


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())
    try:
        ida_loader.save_database(IDB_PATH, 0)
        log.append("saved after error")
    except Exception:
        log.append("save after error failed")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
