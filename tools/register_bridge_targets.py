"""Register the bridge targets exposed by finding 56 (step 3).

Candidates, in priority order (origin is tracked so the log can say which
group actually succeeded):
  THUNK  -- JMP FAR destinations of the .RTLink thunk slots (the overlay
            entries finding 55 could only count);
  UNRES  -- any static ref whose SOURCE lies inside a registered function but
            whose DESTINATION lies inside none;
  ENTRY  -- overlay_entries.json rows covered by a record window with no fn.

NOTE: membership is tested against function *ranges* [ea, ea+size), not against
the set of function start addresses -- a call almost always targets an
instruction head in the MIDDLE of its callee, so an address-set test silently
reports ~0 unresolved destinations.

Guards (finding 54's proven set + region + no-overrun):
  a. no function already covers the address (get_func is range-based, correct);
  b. the address lies on bytes we wrote: resident image 0x10000..0x2CF60 or an
     overlay segment (name starts with R) -- 7 thunk targets sit in no segment
     at all and cannot be registered;
  c. first byte is a known 16-bit prologue (CODE_START);
  d. 16-bit decode reaches a standalone C3/CB/CF before the next registered
     function, the segment end, and ea+600;
  e. decoded length >= 6;
  f. candidates nesting inside another candidate are dropped.

Verification accepts IDA's own end when the function starts exactly at the
candidate and stops before our computed limit (IDA may pull the end forward by
a byte when it owns the decode -- that is not drift).

NO auto_wait (finding 37). Saves only if every planned registration verifies.
Backup: <IDB>.bak_targets.

Usage: cmd /c "tools\\run_idat.bat tools\\register_bridge_targets.py"
"""
import json
import traceback
from bisect import bisect_right
from collections import Counter

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_segment
import ida_ua
import idautils
import idaapi

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"
REFS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\callgraph_refs.json"
ENT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\overlay_entries.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\register_targets.log"

THUNK_LO, STRIDE, N = 0x2BD9D, 10, 303
RES_LO, RES_HI = 0x10000, 0x2CF60

CODE_START = {0x55, 0x56, 0x57, 0x53, 0x51, 0x52, 0x50, 0x1e, 0x06, 0x07,
              0xb8, 0xb9, 0xba, 0xbb, 0xbf, 0xbe, 0x33, 0x2e, 0x3e, 0x8b,
              0x8c, 0x8e, 0xc7, 0x83, 0x81, 0xe8, 0x9a, 0xb4, 0x31, 0xc8, 0x9c}
TERMS = {0xc3, 0xcb, 0xcf}

log = []
ok_all = False

try:
    cls = json.load(open(CLS))
    refs = json.load(open(REFS))["refs"]
    ent = json.load(open(ENT))

    live = sorted(idautils.Functions())          # LIVE, not classification.json
    ivs = [(s, ida_funcs.get_func(s).end_ea) for s in live]
    starts = list(live)

    def in_fn(addr):
        i = bisect_right(starts, addr) - 1
        return i >= 0 and ivs[i][0] <= addr < ivs[i][1]

    # ---- candidate assembly (tagged by origin) ------------------------------
    origin = {}

    def add(ea, tag):
        if ea not in origin:
            origin[ea] = tag

    n_thunk = 0
    for i in range(N):
        s = THUNK_LO + i * STRIDE
        f = ida_funcs.get_func(s)
        if not f or f.start_ea != s:
            continue
        for d in idautils.CodeRefsFrom(s + 3, 0):
            if not in_fn(d):
                n_thunk += 1
                add(d, "THUNK")
    unres = sorted({d for s, d, _ in refs if in_fn(s) and not in_fn(d)})
    for d in unres:
        add(d, "UNRES")

    for e in ent:
        if e.get("covered_seg") and not in_fn(e["entry_ea"]):
            add(e["entry_ea"], "ENTRY")

    ordered = sorted(origin, key=lambda a: ({"THUNK": 0, "UNRES": 1, "ENTRY": 2}[origin[a]], a))
    log.append("candidates: %d   (unresolved dsts %d; thunk JMP targets %d; "
               "overlay entries added %d)"
               % (len(ordered), len(unres), n_thunk,
                  sum(1 for e in ent if e.get("covered_seg") and not in_fn(e["entry_ea"]))))

    # ---- guard b: on written bytes -----------------------------------------
    keep, skipped = [], Counter()
    for ea in ordered:
        seg = ida_segment.getseg(ea)
        if seg is None:
            skipped["b no segment"] += 1
            continue
        if RES_LO <= ea < RES_HI:
            keep.append((ea, seg, "resident"))
        elif ea >= RES_LO and ida_segment.get_segm_name(seg).startswith("R"):
            keep.append((ea, seg, "overlay"))
        elif ea >= RES_LO:
            keep.append((ea, seg, "other"))
        else:
            skipped["b below image"] += 1
    log.append("on written bytes: %d   skipped %d" % (len(keep), sum(skipped.values())))

    # ---- guards a/c/d/e -----------------------------------------------------
    registered = list(live)   # stale classification would mis-compute nxt
    rejected = Counter()
    cands = []
    for ea, seg, kind in keep:
        if ida_funcs.get_func(ea):
            rejected[("a already covered", origin[ea])] += 1
            continue
        if ida_bytes.get_byte(ea) not in CODE_START:
            rejected[("c no 16-bit prologue", origin[ea])] += 1
            continue
        nxt = next((x for x in registered if x > ea), ea + 600)
        limit = min(nxt, seg.end_ea, ea + 600)
        ins = ida_ua.insn_t()
        pos, end = ea, None
        while pos < limit:
            n = ida_ua.decode_insn(ins, pos)
            if n <= 0:
                rejected[("d decode failed", origin[ea])] += 1
                break
            if ida_bytes.get_byte(pos) in TERMS and n == 1:
                end = pos + 1
                break
            pos += n
        else:
            rejected[("d no terminator", origin[ea])] += 1
        if end is None:
            continue
        if end > limit:
            rejected[("d overrun", origin[ea])] += 1
            continue
        if end - ea < 6:
            rejected[("e too small", origin[ea])] += 1
            continue
        cands.append((ea, end, kind, limit, origin[ea]))

    log.append("passing a/c/d/e: %d" % len(cands))
    for (why, org), v in sorted(rejected.items()):
        log.append("    rejected %-22s %-6s %d" % (why, org, v))

    # ---- guard f: nest-drop -------------------------------------------------
    plan = []
    for ea, end, kind, limit, org in sorted(cands):
        if any(not (end <= s2 or ea >= e2) for s2, e2, _, _, _ in plan):
            rejected[("f nested", org)] += 1
            continue
        plan.append((ea, end, kind, limit, org))
    log.append("after nest-drop: %d" % len(plan))

    # ---- register -----------------------------------------------------------
    done = []
    for ea, end, kind, limit, org in plan:
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 8)
        if not ida_ua.create_insn(ea):
            log.append("  0x%X FAIL create_insn" % ea)
            continue
        ida_funcs.add_func(ea, end)
        ida_funcs.set_func_end(ea, end)
        ida_name.set_name(ea, "sub_%X" % ea, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        if f and f.start_ea == ea and ea < f.end_ea <= limit:
            done.append((ea, f.end_ea, org))
        else:
            log.append("  0x%X (%s) add_func(%dB) did not verify -> %s"
                       % (ea, org, end - ea,
                          ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))
    log.append("registered: %d / %d planned" % (len(done), len(plan)))
    by_org = Counter(o for _, _, o in done)
    plan_org = Counter(o for *_, o in plan)
    for o in ("THUNK", "UNRES", "ENTRY"):
        if plan_org[o] or by_org[o]:
            log.append("    %-6s planned %d -> registered %d" % (o, plan_org[o], by_org[o]))

    problems = []
    if len(done) != len(plan):
        problems.append("%d of %d failed" % (len(plan) - len(done), len(plan)))
    for ea, end, kind, limit, org in plan:
        f = ida_funcs.get_func(ea)
        if not f or f.start_ea != ea or not (ea < f.end_ea <= limit):
            problems.append("0x%X span drift" % ea)
    if problems:
        log.append("GUARD FAILED: %s" % "; ".join(problems[:10]))
    else:
        log.append("GUARD PASSED: %d registrations verified" % len(done))
        ok_all = True

    if ok_all:
        ida_loader.save_database(IDB, 0)
        log.append("SAVED")
    else:
        log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_targets if needed")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
