"""Mark overlay entry points as functions - content-driven row assignment.

For each thunk (word w, target T):
  candidate rows = rows r whose runtime block [real_ea(r), real_ea(r)+span)
                   contains T, tried in priority order:
                     1) r == w          (index interpretation, finding 18)
                     2) r == w - 2      (id-field interpretation)
                     3) any other containing row
  entry_ea = r.ida_ea + (T - r.real_ea); must be inside r's written bytes.
  Candidate accepted iff create_insn succeeds there (bytes decode as code).
  del_items first to clear data flags.

Results: per-row assignment counts (validates/refines finding 18 mapping),
functions created, save, report.
"""
import json
import traceback
from collections import Counter

import ida_segment
import ida_bytes
import ida_funcs
import ida_ua
import idaapi
import ida_loader
import ida_name
import idautils

ROOT = r"C:\Users\yotam\projects\falcon3"
ENTRIES = ROOT + r"\analysis\ida_falconcd\overlay_entries.json"
PLACE = ROOT + r"\analysis\ida_falconcd\overlay_placement.json"
LOG = ROOT + r"\analysis\ida_falconcd\mark_entries.log"
IDB_PATH = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

entries = json.load(open(ENTRIES))
placements = {p["idx"]: p for p in json.load(open(PLACE))}
log = []


def candidates(word, target):
    cont = []
    for idx, p in placements.items():
        if not p["ida_len"] or p["addr"] == "skip":
            continue
        base = p["real_ea"]
        if base <= target < base + p["span_bytes"]:
            rel = target - base
            if rel < p["ida_len"]:
                cont.append((idx, p, rel))
    ordered = []
    for r in (word, word - 2):
        for c in cont:
            if c[0] == r and c not in ordered:
                ordered.append(c)
    for c in cont:
        if c not in ordered:
            ordered.append(c)
    return ordered


def main():
    # start clean: drop functions left by previous partial attempts
    removed = 0
    for f in list(idautils.Functions(0x2CF60, 0x200000)):
        ida_funcs.del_func(f)
        removed += 1
    log.append("removed %d stale overlay funcs" % removed)

    created = covered = nomatch = 0
    assign = Counter()
    fail_samples = []
    n = 0
    for e in entries:
        word = e["row"]
        target = e["target_linear"]
        placed = False
        for idx, p, rel in candidates(word, target):
            ea = p["ida_ea"] + rel
            if ida_segment.getseg(ea) is None:
                continue
            f = ida_funcs.get_func(ea)
            if f is not None:
                if f.start_ea <= ea < f.end_ea:
                    assign[idx] += 1
                    placed = True
                    covered += 1
                    break
            ida_bytes.del_items(ea, 0, 16)
            ida_ua.create_insn(ea)
            if ida_funcs.add_func(ea):
                n += 1
                ida_name.set_name(ea, "r%02d_e%02d" % (idx, n), ida_name.SN_CHECK)
                ida_bytes.set_cmt(ea, "thunk entry word=%d target=0x%X row=%d" % (
                    word, target, idx), 0)
                assign[idx] += 1
                placed = True
                created += 1
                break
        if not placed:
            nomatch += 1
            if len(fail_samples) < 8:
                fail_samples.append("word=%d target=0x%X" % (word, target))

    log.append("created=%d covered=%d nomatch=%d" % (created, covered, nomatch))
    log.append("row assignments: %s" % dict(sorted(assign.items())))
    for s in fail_samples:
        log.append("  FAIL %s" % s)

    idaapi.auto_wait()
    ida_loader.save_database(IDB_PATH, 0)
    log.append("saved")

    count = 0
    for i in range(ida_segment.get_segm_qty()):
        seg = ida_segment.getnseg(i)
        if seg.start_ea >= 0x2CF60:
            funcs = list(idautils.Functions(seg.start_ea, seg.end_ea))
            count += len(funcs)
    log.append("total overlay funcs: %d" % count)


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
