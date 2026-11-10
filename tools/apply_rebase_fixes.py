"""Apply the live-IDB function-table repairs in registry/rebase_fixes_expected.json (finding 124).

The manifest is produced on the host by tools/plan_rebase_fixes.py.  In this order the script:
  * swaps the planned far cref (thunk 0x2C969 -> R67_569Fs) to a user cref,
  * removes the planned tail chunks (orphan alias tails, thunk entry chunks, own tails re-added below),
  * deletes the planned fall-in fragment(s), extends the planned function ends (set_func_end),
  * appends the planned tails, registers the planned functions (add_func with an explicit end,
    create_insn first where planned) and their tails,
  * turns the planned byte ranges back into data (byte array), checking their sha256.
It never runs auto_wait / plan_range (finding 122: the canonical IDB's auto queue is not empty).

Manifest-first: every touched function must hold its recorded chunk list ("funcs_before"), the cref its
"drop" target and the to_data range its sha256, otherwise nothing is changed.  Idempotent: if everything
already holds its "after" state the run is a no-op.  After applying, every touched function must hold
"funcs_after" and every other function its old start, end, name and chunks.  Any failure discards the
in-memory changes (DBFL_KILL).

Usage: idat -A -S"tools\\apply_rebase_fixes.py" <idb>     (RBLOG env overrides the log path,
                                                             RBDRY=1 applies and checks without saving)
"""
import hashlib
import json
import os
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import ida_ua
import ida_xref
import idaapi
import idautils

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(os.environ.get("RBMAN") or ROOT / "registry/rebase_fixes_expected.json")
LOG = Path(os.environ.get("RBLOG") or ROOT / "analysis/ida_falconcd/apply_rebase_fixes.log")
FAR_CODE = (ida_xref.fl_CF, ida_xref.fl_JF)

log = []
notes = []


def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return sorted(out)


def norm(ch):
    if ch is None:
        return None
    out = []
    for lo, hi in sorted(ch):
        if out and out[-1][1] == lo:
            out[-1][1] = hi
        else:
            out.append([lo, hi])
    return out


def far_crefs(ea):
    return sorted((x.to, x.type, bool(x.user)) for x in idautils.XrefsFrom(ea, ida_xref.XREF_FAR)
                  if x.iscode and x.type in FAR_CODE)


def sha(ea, n):
    return hashlib.sha256(ida_bytes.get_bytes(ea, n) or b"").hexdigest()


def is_bytes(ea, n):
    """[ea, ea+n) is covered by data items that start inside it and belong to no function"""
    end = ea
    while end < ea + n:
        h = ida_bytes.get_item_head(end)
        if h != end or not ida_bytes.is_data(ida_bytes.get_flags(h)) or ida_funcs.get_func(h):
            return False
        end = h + ida_bytes.get_item_size(h)
    return end == ea + n


def pieces(ea, n):
    """split [ea, ea+n) at segment boundaries (0x6CD90..0x6CDA8 straddles R30_569F / R06_5CD9)"""
    out, end = [], ea + n
    while ea < end:
        s = ida_segment.getseg(ea)
        hi = min(end, s.end_ea) if s else end
        out.append((ea, hi - ea))
        ea = hi
    return out


def snapshot():
    out = {}
    for fs in idautils.Functions():
        out[fs] = (idaapi.get_name(fs), chunks(fs))
    return out


def superseded():
    """{func: chunks} a later manifest (its "follows" names this one) leaves a touched function in"""
    out = {}
    for p in sorted(MANIFEST.parent.glob("rebase_fixes*_expected.json")):
        d = json.loads(p.read_text())
        if d.get("follows") == MANIFEST.name:
            out.update({k: norm(v) for k, v in d["funcs_after"].items()})
    return out


def state(doc):
    """(fresh, applied, problems) over touched functions, crefs and to_data ranges"""
    fresh, applied, problems = 0, 0, []
    notes.clear()
    later = superseded()
    for k, want in doc["funcs_after"].items():
        ea = int(k, 16)
        live = norm(chunks(ea))
        if live == norm(want) or live == later.get(k):
            applied += 1
        elif live == norm(doc["funcs_before"][k]):
            fresh += 1
        else:
            problems.append("0x%s chunks %s, manifest before %s after %s" % (k, live, doc["funcs_before"][k], want))
    for c in doc["crefs"]:
        live = far_crefs(c["ea"])
        if live == [(c["to"], c["type"], True)]:
            applied += 1
        elif live == [(c["drop"], c["type"], False)]:
            fresh += 1
        else:
            problems.append("cref 0x%X live %s" % (c["ea"], [(hex(t), ty, u) for t, ty, u in live]))
    for ea in doc.get("clear_noret", []):
        f = ida_funcs.get_func(ea)
        if not f or f.start_ea != ea:
            problems.append("clear_noret 0x%X: no function" % ea)
        elif f.flags & ida_funcs.FUNC_NORET:
            fresh += 1
        else:
            applied += 1
    for t in doc["to_data"]:
        if sha(t["ea"], t["size"]) != t["sha256"]:
            problems.append("0x%X..+%d bytes changed" % (t["ea"], t["size"]))
        elif is_bytes(t["ea"], t["size"]):
            applied += 1
        else:
            fresh += 1
            notes.append("0x%X..+%d not all free data: %s" % (t["ea"], t["size"], [
                (hex(a), ida_bytes.is_data(ida_bytes.get_flags(a)), bool(ida_funcs.get_func(a)))
                for a in range(t["ea"], t["ea"] + t["size"]) if not is_bytes(a, 1)]))
    return fresh, applied, problems


def must(ok, what):
    if not ok:
        raise RuntimeError(what + " failed")


def apply(doc):
    before = snapshot()
    for c in doc["crefs"]:
        ida_xref.del_cref(c["ea"], c["drop"], 0)
        ida_xref.add_cref(c["ea"], c["to"], c["type"] | ida_xref.XREF_USER)
    log.append("far crefs swapped: %s" % ["0x%X: 0x%X -> 0x%X" % (c["ea"], c["drop"], c["to"]) for c in doc["crefs"]])
    shared = 0
    for r in doc["remove_tails"]:
        f = ida_funcs.get_func(r["owner"])
        must(f and f.start_ea == r["owner"], "owner 0x%X" % r["owner"])
        if not ida_funcs.remove_func_tail(f, r["lo"]):
            # a tail shared by several functions (0x11E1A7) can already be gone with its other parent
            must(not ida_funcs.func_contains(f, r["lo"]), "remove_func_tail 0x%X from 0x%X" % (r["lo"], r["owner"]))
            shared += 1
    log.append("tails removed: %d (%d already detached with a co-parent)" % (len(doc["remove_tails"]), shared))
    for d in doc["del_funcs"]:
        must(ida_funcs.del_func(d["ea"]), "del_func 0x%X" % d["ea"])
    log.append("functions deleted: %s" % ["0x%X" % d["ea"] for d in doc["del_funcs"]])
    for ea in doc.get("clear_noret", []):
        f = ida_funcs.get_func(ea)
        f.flags &= ~ida_funcs.FUNC_NORET
        must(ida_funcs.update_func(f), "update_func 0x%X" % ea)
        must(not ida_funcs.get_func(ea).flags & ida_funcs.FUNC_NORET, "clear FUNC_NORET 0x%X" % ea)
    log.append("no-return flags cleared: %s" % ["0x%X" % ea for ea in doc.get("clear_noret", [])])
    for s in doc["set_ends"]:
        must(ida_funcs.set_func_end(s["ea"], s["end"]), "set_func_end 0x%X -> 0x%X" % (s["ea"], s["end"]))
        must(ida_funcs.get_func(s["ea"]).end_ea == s["end"], "end of 0x%X" % s["ea"])
    log.append("function ends set: %s" % ["0x%X: 0x%X -> 0x%X" % (s["ea"], s["before_end"], s["end"])
                                          for s in doc["set_ends"]])
    for a in doc["append_tails"]:
        must(ida_funcs.append_func_tail(ida_funcs.get_func(a["owner"]), a["lo"], a["hi"]),
             "append_func_tail 0x%X..0x%X to 0x%X" % (a["lo"], a["hi"], a["owner"]))
    log.append("tails appended: %d" % len(doc["append_tails"]))
    for f in doc["add_funcs"]:
        if f["create_insn"]:
            must(ida_ua.create_insn(f["ea"]) > 0, "create_insn 0x%X" % f["ea"])
        must(ida_funcs.add_func(f["ea"], f["end"]), "add_func 0x%X..0x%X" % (f["ea"], f["end"]))
        for lo, hi in f["tails"]:
            must(ida_funcs.append_func_tail(ida_funcs.get_func(f["ea"]), lo, hi),
                 "append_func_tail 0x%X..0x%X to new 0x%X" % (lo, hi, f["ea"]))
    log.append("functions added: %s" % ["0x%X..0x%X%s" % (f["ea"], f["end"], " +%d tails" % len(f["tails"])
                                        if f["tails"] else "") for f in doc["add_funcs"]])
    for t in doc["to_data"]:
        ea, n = t["ea"], t["size"]
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, n)
        for pe, pn in pieces(ea, n):
            must(ida_bytes.create_data(pe, ida_bytes.FF_BYTE, pn, idaapi.BADNODE), "create_data 0x%X,%d" % (pe, pn))
    log.append("ranges made data: %s" % ["0x%X..+%d as %s" % (t["ea"], t["size"], pieces(t["ea"], t["size"]))
                                         for t in doc["to_data"]])

    _f, applied, problems = state(doc)
    total = len(doc["funcs_after"]) + len(doc["crefs"]) + len(doc["to_data"]) + len(doc.get("clear_noret", []))
    if problems or applied != total:
        for p in problems[:20]:
            log.append("  " + p)
        log.extend("  " + n for n in notes)
        raise RuntimeError("post-check: %d/%d items hold their planned value" % (applied, total))
    after = snapshot()
    touched = {int(k, 16) for k in doc["funcs_after"]}
    changed = sorted(ea for ea in set(before) | set(after) if ea not in touched and before.get(ea) != after.get(ea))
    if changed:
        for ea in changed[:20]:
            log.append("  untouched 0x%X: %s -> %s" % (ea, before.get(ea), after.get(ea)))
        raise RuntimeError("%d functions outside the plan changed" % len(changed))
    flags = {"0x%X" % f["ea"]: "far" if ida_funcs.get_func(f["ea"]).flags & ida_funcs.FUNC_FAR else "near"
             for f in doc["add_funcs"]}
    log.append("function table: %d -> %d, untouched functions unchanged; new function kinds %s"
               % (len(before), len(after), flags))


def main():
    doc = json.loads(MANIFEST.read_text())
    total = len(doc["funcs_after"]) + len(doc["crefs"]) + len(doc["to_data"]) + len(doc.get("clear_noret", []))
    log.append("manifest: %d functions touched, %d tail removals, %d new, %d crefs, %d to_data"
               % (len(doc["funcs_after"]), len(doc["remove_tails"]), len(doc["add_funcs"]),
                  len(doc["crefs"]), len(doc["to_data"])))
    fresh, applied, problems = state(doc)
    log.append("live: %d fresh, %d applied, %d mismatched" % (fresh, applied, len(problems)))
    if applied == total:
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    if problems or fresh != total:
        for p in problems[:20]:
            log.append("  " + p)
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    apply(doc)
    if os.environ.get("RBDRY"):
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("dry run (RBDRY): not saved")
        return
    ida_loader.save_database(idaapi.get_path(idaapi.PATH_TYPE_IDB), 0)
    log.append("database saved")


try:
    main()
except Exception:
    ida_loader.set_database_flag(ida_loader.DBFL_KILL)
    log.append("ERROR (not saved):\n" + traceback.format_exc())
LOG.write_text("\n".join(log))
idaapi.qexit(0)
