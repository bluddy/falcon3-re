"""Apply the 0x1E10-arena variant selector repair in registry/variant_sel_expected.json (finding 123).

The manifest is produced on the host by tools/plan_variant_selectors.py from tools/export_farcalls.py
output.  This script only:
  * maps the R29-only selectors (identity seg -> R05 image) to their R29 paragraphs (set_selector),
  * moves the start of the planned nop-padded functions past the pad (set_func_start),
  * swaps far code xrefs: drops the planned non-user far crefs, adds a user cref to the resolved target
    (no del_items / create_insn on far calls: re-creating them shrinks or drops 7 functions),
  * re-creates the code heads whose DS/ES holds a remapped selector, after dropping their non-user drefs,
    so their data xrefs land in the R29 image instead of R05.
It never runs auto_wait / plan_range (finding 122: the canonical IDB's auto queue is not empty).

Manifest-first: every planned item must hold its recorded "before" state in the live IDB, otherwise
nothing is changed.  Idempotent: if every item already holds its "after" state the run is a no-op.
Any failure discards the in-memory changes (DBFL_KILL).

Usage: idat -A -S"tools\\apply_variant_selectors.py" <idb>     (VSLOG env overrides the log path)
"""
import collections
import json
import os
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import ida_segregs
import ida_ua
import ida_xref
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "registry/variant_sel_expected.json"
LOG = Path(os.environ.get("VSLOG") or ROOT / "analysis/ida_falconcd/apply_variant_selectors.log")
SREGS = {idaapi.str2reg(r) for r in ("es", "cs", "ss", "ds")}
SREG_WRITERS = {"lds", "les", "lss", "pop", "mov"}
FAR_CODE = (ida_xref.fl_CF, ida_xref.fl_JF)

log = []


def far_crefs(ea):
    return sorted((x.to, x.type, bool(x.user)) for x in idautils.XrefsFrom(ea, ida_xref.XREF_FAR)
                  if x.iscode and x.type in FAR_CODE)


def snapshot_funcs():
    return [(fs, ida_funcs.get_func(fs).end_ea, idaapi.get_name(fs)) for fs in idautils.Functions()]


def sreg_counts():
    return {r: ida_segregs.get_sreg_ranges_qty(r) for r in sorted(SREGS)}


def state(doc):
    """(fresh, applied, problems) over selectors, func moves and crefs"""
    fresh, applied, problems = 0, 0, []
    for s in doc["selectors"]:
        p = ida_segment.sel2para(s["sel"])
        if p == s["after"]:
            applied += 1
        elif p == s["before"]:
            fresh += 1
        else:
            problems.append("selector %X -> %X, manifest before %X after %X" % (s["sel"], p, s["before"], s["after"]))
    for m in doc["func_moves"]:
        f = ida_funcs.get_func(m["to"])
        if f and f.start_ea == m["to"]:
            applied += 1
        elif f and f.start_ea == m["from"]:
            fresh += 1
        else:
            problems.append("function at 0x%X: start %s" % (m["from"], hex(f.start_ea) if f else None))
    for c in doc["crefs"]:
        live = far_crefs(c["ea"])
        if live == [(c["to"], c["type"], True)]:
            applied += 1
        elif live == sorted((t, ty, bool(u)) for t, ty, u in c["before"]):
            fresh += 1
        else:
            problems.append("cref 0x%X live %s, manifest before %s to 0x%X"
                            % (c["ea"], [(hex(t), ty, u) for t, ty, u in live], c["before"], c["to"]))
    return fresh, applied, problems


def redecode(heads):
    """drop non-user drefs and re-create the head so its drefs follow the new selector"""
    n = dropped = 0
    skipped = collections.Counter()
    for h in heads:
        ea, sz = h["ea"], h["size"]
        if not ida_bytes.is_code(ida_bytes.get_flags(ea)) or ida_bytes.get_item_head(ea) != ea \
                or ida_bytes.get_item_size(ea) != sz:
            raise RuntimeError("planned code head 0x%X (size %d) is not one" % (ea, sz))
        insn = ida_ua.insn_t()
        if ida_ua.decode_insn(insn, ea) != sz:
            skipped["truncated head"] += 1
            continue
        if insn.get_canon_mnem() in SREG_WRITERS and insn.ops[0].type == ida_ua.o_reg \
                and insn.ops[0].reg in SREGS:
            skipped["segment load"] += 1   # re-emulating it would redo IDA's own sreg split
            continue
        for x in list(idautils.XrefsFrom(ea, ida_xref.XREF_FAR)):
            if x.iscode or x.user:
                continue
            ida_xref.del_dref(ea, x.to)
            dropped += 1
        if ida_ua.create_insn(ea) != sz:
            raise RuntimeError("create_insn changed item size at 0x%X" % ea)
        n += 1
    return n, dropped, skipped


def apply(doc):
    before_funcs = snapshot_funcs()
    sr0 = sreg_counts()
    for s in doc["selectors"]:
        if not ida_segment.set_selector(s["sel"], s["after"]):
            raise RuntimeError("set_selector %X -> %X failed" % (s["sel"], s["after"]))
    log.append("selectors remapped: %d" % len(doc["selectors"]))
    for m in doc["func_moves"]:
        rc = ida_funcs.set_func_start(m["from"], m["to"])
        if rc != ida_funcs.MOVE_FUNC_OK:
            raise RuntimeError("set_func_start 0x%X -> 0x%X failed (%d)" % (m["from"], m["to"], rc))
    log.append("function starts moved past pad: %s" % ["0x%X->0x%X" % (m["from"], m["to"]) for m in doc["func_moves"]])
    dropped = added = 0
    for c in doc["crefs"]:
        for to, ty, user in c["before"]:
            if not user and to != c["to"]:
                ida_xref.del_cref(c["ea"], to, 0)
                dropped += 1
        ida_xref.add_cref(c["ea"], c["to"], c["type"] | ida_xref.XREF_USER)
        added += 1
    log.append("far crefs: %d dropped, %d user crefs set" % (dropped, added))
    _f, applied, problems = state(doc)
    total = len(doc["selectors"]) + len(doc["func_moves"]) + len(doc["crefs"])
    if problems or applied != total:
        log.append("  e.g. %s" % problems[:10])
        raise RuntimeError("post-check: %d/%d items hold their planned value" % (applied, total))
    n, ddrop, skipped = redecode(doc["dref_heads"])
    log.append("dref heads: %d planned; re-created %d (dropped %d stale drefs, skipped %s)"
               % (len(doc["dref_heads"]), n, ddrop, sorted(skipped.items())))
    _f, applied, problems = state(doc)
    if problems or applied != total:
        raise RuntimeError("re-decode disturbed %d items: %s" % (total - applied, problems[:10]))
    if sreg_counts() != sr0:
        raise RuntimeError("segment-register range counts changed %s -> %s" % (sr0, sreg_counts()))
    after_funcs = snapshot_funcs()
    moved = {m["from"]: m["to"] for m in doc["func_moves"]}
    want = [(moved.get(fs, fs), end, idaapi.get_name(moved[fs]) if fs in moved else nm)
            for fs, end, nm in before_funcs]
    if sorted(want) != after_funcs:
        gone = sorted(set(want) - set(after_funcs))
        new = sorted(set(after_funcs) - set(want))
        log.append("function table: %d gone %s" % (len(gone), ["0x%X..0x%X %s" % g for g in gone[:20]]))
        log.append("function table: %d new %s" % (len(new), ["0x%X..0x%X %s" % g for g in new[:20]]))
        raise RuntimeError("function table changed beyond the planned moves")
    log.append("function table: %d, unchanged except the planned moves" % len(after_funcs))
    drefs, crefs = collections.Counter(), collections.Counter()
    for h in doc["dref_heads"]:
        for x in idautils.XrefsFrom(h["ea"], ida_xref.XREF_FAR):
            if not x.iscode:
                s = ida_segment.getseg(x.to)
                drefs[ida_segment.get_segm_name(s)[:3] if s else "none"] += 1
    for c in doc["crefs"]:
        fl = ida_bytes.get_flags(c["to"])
        f = ida_funcs.get_func(c["to"])
        crefs["func start" if f and f.start_ea == c["to"] else "code head" if ida_bytes.is_code(fl)
              and ida_bytes.get_item_head(c["to"]) == c["to"] else "inside item" if ida_bytes.is_code(fl)
              or ida_bytes.is_data(fl) else "unexplored"] += 1
    log.append("data xrefs from re-created heads by target segment family: %s" % drefs.most_common(8))
    log.append("far cref targets now: %s" % sorted(crefs.items()))


def main():
    doc = json.loads(MANIFEST.read_text())
    log.append("manifest: %d selectors, %d func moves, %d crefs, %d dref heads"
               % (len(doc["selectors"]), len(doc["func_moves"]), len(doc["crefs"]), len(doc["dref_heads"])))
    fresh, applied, problems = state(doc)
    total = len(doc["selectors"]) + len(doc["func_moves"]) + len(doc["crefs"])
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
    if os.environ.get("VSDRY"):
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("dry run (VSDRY): not saved")
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
