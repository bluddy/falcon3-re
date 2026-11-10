"""Repair call flow cut by wrong FUNC_NORET flags (finding 125, S1c-3).

Functions that contain a ret/retf/iret were flagged no-return, so IDA never connected the instruction after
a call into them: (a) the return address was left as alignment padding or data (5 sites, re-decoded here)
and (b) the other return addresses are code in the same function but lack the fall-through (fl_F) edge.
Clearing a flag does not re-flow the callers, and this script never runs auto_wait (the auto queue is not
empty, finding 122).

Two modes, one script:
  FFMODE=plan   run on a COPY of the IDB.  Computes the plan from the live state, applies it, checks it and
                records the exact result in registry/flow_fixes_expected.json.  Never saves.
  (default)     replays the manifest: every item must hold its "before" state (or already its "after" state;
                a run with everything applied is a no-op), then applies, then checks "after" and that the
                function table (start, end, name, chunks) is unchanged.  A failure discards the changes
                (DBFL_KILL).
RBLOG overrides the log path; FFDRY=1 applies and checks without saving.

Usage: idat -A -S"tools\\apply_flow_fixes.py" <idb>
"""
import hashlib
import json
import os
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_ua
import ida_xref
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "registry/flow_fixes_expected.json"
LOG = Path(os.environ.get("FFLOG") or ROOT / "analysis/ida_falconcd/apply_flow_fixes.log")
PLAN = os.environ.get("FFMODE") == "plan"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
# earlier S1c-2 targets: their flags are already clear, their callers still lack the flow edge
CLEARED_EARLIER = [0x4F7B8, 0x38C91, 0x2FD42, 0x322E5, 0x3F700]
# return addresses that are not code: [lo, hi) re-decoded sequentially from lo
RECODE = [(0x2F99E, 0x2F9AC), (0x326FF, 0x32700), (0x3273E, 0x32740), (0x32A43, 0x32A44), (0x32AA1, 0x32AA2)]

log = []


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


def snapshot():
    return {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}


def kind(ea):
    fl = ida_bytes.get_flags(ea)
    if ida_bytes.is_code(fl):
        return "code"
    return "align" if ida_bytes.is_align(fl) else "data"


def layout(lo, hi):
    out, ea = [], ida_bytes.get_item_head(lo)
    while ea < hi:
        out.append([ea, ida_bytes.get_item_size(ea), kind(ea)])
        ea += ida_bytes.get_item_size(ea)
    return out


def has_flow(frm, to):
    return any(x.to == to and x.type == ida_xref.fl_F for x in idautils.XrefsFrom(frm, ida_xref.XREF_ALL))


def has_ret(ea):
    return any(idc.print_insn_mnem(h) in RETS for h in idautils.FuncItems(ea))


def must(ok, what):
    if not ok:
        raise RuntimeError(what + " failed")


def recode(lo, hi):
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    ea = lo
    while ea < hi:
        n = ida_ua.create_insn(ea)
        must(n > 0, "create_insn 0x%X" % ea)
        ea += n
    must(ea == hi, "re-decode 0x%X..0x%X ends at 0x%X" % (lo, hi, ea))


def plan_doc():
    """computed on the live state, before anything is changed"""
    noret = [fs for fs in idautils.Functions()
             if ida_funcs.get_func(fs).flags & ida_funcs.FUNC_NORET and has_ret(fs)]
    recodes = []
    for lo, hi in RECODE:
        recodes.append({"ea": lo, "end": hi, "sha256": hashlib.sha256(ida_bytes.get_bytes(lo, hi - lo)).hexdigest(),
                        "owner": ida_funcs.get_func(lo).start_ea, "before": layout(lo, hi), "after": None})
    return noret, recodes


def call_sites(targets):
    """[(call, return address)] of every direct call into the targets"""
    out = []
    for t in sorted(targets):
        for x in idautils.XrefsTo(t, 0):
            if x.iscode and idc.print_insn_mnem(x.frm).startswith("call"):
                out.append((x.frm, x.frm + ida_bytes.get_item_size(x.frm)))
    return sorted(set(out))


def apply(doc):
    before = snapshot()
    for ea in doc["clear_noret"]:
        f = ida_funcs.get_func(ea)
        must(f and f.start_ea == ea, "function 0x%X" % ea)
        f.flags &= ~ida_funcs.FUNC_NORET
        must(ida_funcs.update_func(f), "update_func 0x%X" % ea)
    log.append("no-return flags cleared: %d" % len(doc["clear_noret"]))
    for r in doc["recode"]:
        if r["after"] is None or layout(r["ea"], r["end"]) != r["after"]:
            recode(r["ea"], r["end"])
    log.append("ranges re-decoded: %s" % ["0x%X..0x%X" % (r["ea"], r["end"]) for r in doc["recode"]])
    for frm, to in doc["flow_crefs"]:
        if not has_flow(frm, to):
            must(ida_xref.add_cref(frm, to, ida_xref.fl_F), "add_cref 0x%X -> 0x%X" % (frm, to))
    log.append("fall-through edges: %d" % len(doc["flow_crefs"]))
    after = snapshot()
    if before != after:
        diff = sorted(ea for ea in set(before) | set(after) if before.get(ea) != after.get(ea))
        for ea in diff[:20]:
            log.append("  function 0x%X: %s -> %s" % (ea, before.get(ea), after.get(ea)))
        raise RuntimeError("%d functions changed" % len(diff))
    log.append("function table unchanged (%d functions)" % len(after))


def check(doc):
    """(fresh, applied, problems)"""
    fresh = applied = 0
    problems = []
    for ea in doc["clear_noret"]:
        f = ida_funcs.get_func(ea)
        if not f or f.start_ea != ea:
            problems.append("no function 0x%X" % ea)
        elif f.flags & ida_funcs.FUNC_NORET:
            fresh += 1
        else:
            applied += 1
    for r in doc["recode"]:
        live = layout(r["ea"], r["end"])
        if live == r["after"]:
            applied += 1
        elif live == r["before"] and hashlib.sha256(ida_bytes.get_bytes(r["ea"], r["end"] - r["ea"])).hexdigest() == r["sha256"]:
            fresh += 1
        else:
            problems.append("0x%X..0x%X layout %s" % (r["ea"], r["end"], live))
    for frm, to in doc["flow_crefs"]:
        if has_flow(frm, to):
            applied += 1
        else:
            fresh += 1
    return fresh, applied, problems


def main():
    if PLAN:
        noret, recodes = plan_doc()
        sites = call_sites(set(noret) | set(CLEARED_EARLIER))
        doc = {"finding": 125, "step": "S1c-3 call flow cut by wrong no-return flags",
               "clear_noret": noret, "recode": recodes,
               "flow_crefs": [[c, n] for c, n in sites]}
        for r in doc["recode"]:
            recode(r["ea"], r["end"])
            r["after"] = layout(r["ea"], r["end"])
        # all sites are checked after the apply; each return address must be code owned by the caller
        doc["sites"] = [[c, n] for c, n in sites]
        apply(doc)
        problems = []
        for c, n in sites:
            cf, nf = ida_funcs.get_func(c), ida_funcs.get_func(n)
            if not ida_bytes.is_code(ida_bytes.get_flags(n)) or not (cf and nf and cf.start_ea == nf.start_ea):
                problems.append("0x%X return address 0x%X not code in the caller" % (c, n))
            elif not has_flow(c, n):
                problems.append("0x%X no flow edge to 0x%X" % (c, n))
        must(not problems, "sites: %s" % problems[:10])
        doc["clear_noret_names"] = {"0x%X" % ea: idc.get_func_name(ea) for ea in noret}
        doc["recode_disasm"] = {"0x%X" % r["ea"]: [idc.generate_disasm_line(a, 0) for a, _s, _k in r["after"]]
                                for r in doc["recode"]}
        MANIFEST.write_text(json.dumps(doc, indent=1).replace("\n", "\r\n"))
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("plan written: %s (not saved)" % MANIFEST.name)
        return
    doc = json.loads(MANIFEST.read_text())
    total = len(doc["clear_noret"]) + len(doc["recode"]) + len(doc["flow_crefs"])
    fresh, applied, problems = check(doc)
    log.append("manifest: %d no-return flags, %d re-decodes, %d fall-through edges" %
               (len(doc["clear_noret"]), len(doc["recode"]), len(doc["flow_crefs"])))
    log.append("live: %d fresh, %d applied, %d mismatched" % (fresh, applied, len(problems)))
    if applied == total:
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    if problems:
        for p in problems[:20]:
            log.append("  " + p)
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    apply(doc)
    fresh, applied, problems = check(doc)
    if problems or applied != total:
        raise RuntimeError("post-check: %d/%d hold, problems %s" % (applied, total, problems[:10]))
    if os.environ.get("FFDRY"):
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("dry run (FFDRY): not saved")
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
