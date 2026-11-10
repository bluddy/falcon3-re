"""Apply the DS/SS plan in registry/ds_expected.json to the IDB (finding 122).

The manifest is produced on the host by tools/plan_default_ds.py from
tools/export_ds_facts.py output and the memdump far-transfer traces.  This
script only:
  * splits DS/SS segment-register ranges (SR_user) at the planned points,
  * changes segment default DS/SS (R29 split segments: DS 0 -> unknown;
    every CODE segment but the startup ones: SS -> DGROUP),
  * re-creates the code heads whose DS changed and that carry an implicit-DS
    direct memory operand, so their data xrefs follow the new DS (stale
    analysis drefs computed under the old DS are dropped first).
It never runs auto_wait / plan_range: the canonical IDB's auto queue is not
empty, and draining it creates ~94 unrelated functions (finding 122).

Manifest-first: every planned point must hold its recorded "before" value in
the live IDB, otherwise nothing is changed.  Idempotent: if every point
already holds its "after" value as a user range the run is a no-op.  Any
failure discards the in-memory changes (DBFL_KILL).

Usage: idat -A -S"tools\\apply_default_ds.py" <idb>     (DSLOG env overrides the log path)
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
MANIFEST = ROOT / "registry/ds_expected.json"
LOG = Path(os.environ.get("DSLOG") or ROOT / "analysis/ida_falconcd/apply_default_ds.log")
DS, SS = idaapi.str2reg("ds"), idaapi.str2reg("ss")
SREGS = {idaapi.str2reg(r) for r in ("es", "cs", "ss", "ds")}
SREG_WRITERS = {"lds", "les", "lss", "pop", "mov"}

log = []


def para(v):
    if v is None or v in (idaapi.BADSEL, 0xFFFF, 0xFFFFFFFF):
        return None
    return ida_segment.sel2para(v)


def sel(p):
    if p is None:
        return idaapi.BADSEL
    s = ida_segment.setup_selector(p)
    if ida_segment.sel2para(s) != p:
        raise RuntimeError("selector for para %X maps to %X" % (p, ida_segment.sel2para(s)))
    return s


def rng(ea, reg):
    rr = ida_segregs.sreg_range_t()
    return rr if ida_segregs.get_sreg_range(rr, ea, reg) else None


def implicit_mem(ea, insn):
    """direct memory operands addressed through DS (no segment prefix)"""
    for op in insn.ops:
        if op.type == ida_ua.o_void:
            break
        if op.type == ida_ua.o_mem and not any(p in (idc.print_operand(ea, op.n) or "")
                                               for p in ("es:", "cs:", "ss:")):
            return True
    return False


def ds_bad_ops():
    """(implicit-DS operands, of which DS unknown) over all function heads"""
    n = bad = 0
    for fs in idautils.Functions():
        for h in idautils.FuncItems(fs):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, h):
                continue
            k = 0
            for op in insn.ops:
                if op.type == ida_ua.o_void:
                    break
                if op.type not in (ida_ua.o_mem, ida_ua.o_displ, ida_ua.o_phrase):
                    continue
                txt = idc.print_operand(h, op.n) or ""
                if any(p in txt for p in ("es:", "cs:", "ss:")):
                    continue
                if op.type != ida_ua.o_mem and "bp" in txt:
                    continue
                k += 1
            n += k
            if k and para(ida_segregs.get_sreg(h, DS)) is None:
                bad += k
    return n, bad


def snapshot_funcs():
    return [(fs, ida_funcs.get_func(fs).end_ea, idaapi.get_name(fs)) for fs in idautils.Functions()]


def state(doc):
    """'fresh' / 'applied' / problems list"""
    fresh, applied, problems = 0, 0, []
    for p in doc["ds_points"]:
        live = para(ida_segregs.get_sreg(p["ea"], DS))
        r = rng(p["ea"], DS)
        if r and r.start_ea == p["ea"] and r.tag == ida_segregs.SR_user and live == p["after"]:
            applied += 1
        elif live == p["before"]:
            fresh += 1
        else:
            problems.append("DS 0x%X live %s, manifest before %s after %s"
                            % (p["ea"], live, p["before"], p["after"]))
    for p in doc["ss_points"]:
        live = para(ida_segregs.get_sreg(p["ea"], SS))
        r = rng(p["ea"], SS)
        if r and r.start_ea == p["ea"] and r.tag == ida_segregs.SR_user and live == p["after"]:
            applied += 1
        elif live == p["before"]:
            fresh += 1
        else:
            problems.append("SS 0x%X live %s, manifest before %s" % (p["ea"], live, p["before"]))
    for d in doc["seg_defaults"]:
        s = ida_segment.getseg(d["start"])
        if s is None or s.start_ea != d["start"] or ida_segment.get_segm_name(s) != d["seg"]:
            problems.append("segment %s not at 0x%X" % (d["seg"], d["start"]))
            continue
        live = para(ida_segregs.get_sreg(s.start_ea, DS if d["reg"] == "ds" else SS))
        if live == d["after"]:
            applied += 1
        elif live == d["before"]:
            fresh += 1
        else:
            problems.append("segment %s %s live %s, manifest before %s" % (d["seg"], d["reg"], live, d["before"]))
    return fresh, applied, problems


def redecode(heads):
    """re-create code heads so their drefs follow the new DS"""
    n = dropped = 0
    skipped = collections.Counter()
    for h in sorted(heads):
        if not ida_bytes.is_code(ida_bytes.get_flags(h)):
            continue
        sz = ida_bytes.get_item_size(h)
        insn = ida_ua.insn_t()
        if ida_ua.decode_insn(insn, h) != sz:
            skipped["truncated head"] += 1
            continue
        if not implicit_mem(h, insn):
            continue
        if insn.get_canon_mnem() in SREG_WRITERS and insn.ops[0].type == ida_ua.o_reg \
                and insn.ops[0].reg in SREGS:
            skipped["segment load"] += 1   # re-emulating it would redo IDA's own sreg split
            continue
        for x in list(idautils.XrefsFrom(h, ida_xref.XREF_FAR)):
            if x.iscode or x.user:
                continue
            ida_xref.del_dref(h, x.to)
            dropped += 1
        if ida_ua.create_insn(h) != sz:
            raise RuntimeError("create_insn changed item size at 0x%X" % h)
        n += 1
    return n, dropped, skipped


def apply(doc):
    before_funcs = snapshot_funcs()
    if len(before_funcs) != doc["funcs"]:
        raise RuntimeError("function count %d != manifest %d" % (len(before_funcs), doc["funcs"]))
    nops, bad0 = ds_bad_ops()
    log.append("implicit-DS operands %d, DS unknown before: %d" % (nops, bad0))
    # heads of every function touched, with DS before
    touched = {p["func"] for p in doc["ds_points"]}
    ds_before = {}
    for fs in touched:
        if ida_funcs.get_func(fs) is None:
            raise RuntimeError("planned function 0x%X missing" % fs)
        for h in idautils.FuncItems(fs):
            ds_before[h] = para(ida_segregs.get_sreg(h, DS))
    for d in doc["seg_defaults"]:
        s = ida_segment.getseg(d["start"])
        ida_segregs.set_default_sreg_value(s, DS if d["reg"] == "ds" else SS, sel(d["after"]))
    log.append("segment defaults set: %d" % len(doc["seg_defaults"]))
    fails = []
    for p in sorted(doc["ds_points"], key=lambda p: p["ea"]):
        if not ida_segregs.split_sreg_range(p["ea"], DS, sel(p["after"]), ida_segregs.SR_user):
            fails.append(p["ea"])
    for p in doc["ss_points"]:
        if not ida_segregs.split_sreg_range(p["ea"], SS, sel(p["after"]), ida_segregs.SR_user):
            fails.append(p["ea"])
    if fails:
        raise RuntimeError("split_sreg_range failed at %s" % ["0x%X" % e for e in fails[:10]])
    log.append("DS points split: %d, SS points split: %d" % (len(doc["ds_points"]), len(doc["ss_points"])))
    _f, applied, problems = state(doc)
    total = len(doc["ds_points"]) + len(doc["ss_points"]) + len(doc["seg_defaults"])
    if problems or applied != total:
        log.append("  e.g. %s" % problems[:10])
        raise RuntimeError("post-check: %d/%d points hold their planned value" % (applied, total))
    changed = {h for h, v in ds_before.items() if para(ida_segregs.get_sreg(h, DS)) != v}
    n, dropped, skipped = redecode(changed)
    log.append("heads with new DS: %d; re-created %d (dropped %d stale drefs, skipped %s)"
               % (len(changed), n, dropped, sorted(skipped.items())))
    _f, applied, problems = state(doc)
    if problems or applied != total:
        raise RuntimeError("re-decode disturbed %d points: %s" % (total - applied, problems[:10]))
    after_funcs = snapshot_funcs()
    if before_funcs != after_funcs:
        gone = sorted(set(before_funcs) - set(after_funcs))
        new = sorted(set(after_funcs) - set(before_funcs))
        log.append("function table: %d gone %s" % (len(gone), ["0x%X..0x%X %s" % g for g in gone[:20]]))
        log.append("function table: %d new %s" % (len(new), ["0x%X..0x%X %s" % g for g in new[:20]]))
        raise RuntimeError("function table changed")
    log.append("function table unchanged (%d)" % len(after_funcs))
    nops2, bad1 = ds_bad_ops()
    if nops2 != nops:
        raise RuntimeError("implicit-DS operand count changed %d -> %d" % (nops, nops2))
    log.append("DS unknown after: %d (was %d)" % (bad1, bad0))
    drefs = collections.Counter()
    for h in changed:
        for x in idautils.XrefsFrom(h, ida_xref.XREF_FAR):
            if not x.iscode:
                s = ida_segment.getseg(x.to)
                drefs[ida_segment.get_segm_name(s) if s else "none"] += 1
    log.append("data xrefs from re-based heads by target segment: %s" % drefs.most_common(12))


def main():
    doc = json.loads(MANIFEST.read_text())
    log.append("manifest: %d DS points, %d SS points, %d segment defaults"
               % (len(doc["ds_points"]), len(doc["ss_points"]), len(doc["seg_defaults"])))
    fresh, applied, problems = state(doc)
    total = len(doc["ds_points"]) + len(doc["ss_points"]) + len(doc["seg_defaults"])
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
    ida_loader.save_database(idaapi.get_path(idaapi.PATH_TYPE_IDB), 0)
    log.append("database saved")


try:
    main()
except Exception:
    ida_loader.set_database_flag(ida_loader.DBFL_KILL)
    log.append("ERROR (not saved):\n" + traceback.format_exc())
LOG.write_text("\n".join(log))
idaapi.qexit(0)
