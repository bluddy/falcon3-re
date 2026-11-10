"""Register the R29 entries exposed by the variant selector repair (finding 123, step S1b).

After S1a, 2,035 far calls from the menu overlays land on 129 R29 addresses that IDA never decoded
(nothing pointed at them before).  Seeds:
  * every planned S1a cref target inside R29 that is not a function start,
  * R29 far-transfer targets from memdump/*fartrans.jsonl that are not a function start (runtime),
  * transitively, near/far call targets inside R29 found in the newly created functions.
Each seed is registered with flow-based add_func(ea).  A seed covered by orphan (function-less)
misdecoded code is pre-fixed: the orphan code items overlapping the seed's fresh decode are undefined
first (two cases, both directly after a switch jump table).  Far calls in the new code that resolve to
R05 through the shared anchor 0x1E10 get the S1a cref swap (caller is R29 -> R29 image).

Two modes, same script:
  VRMODE=plan   (run on a COPY)  performs the registration, records the exact result (seed order,
                every new function's bounds, pre-fix items, cref swaps, head changes outside R29) in
                registry/r29_register_expected.json, and discards the IDB (DBFL_KILL).
  default       replays the manifest on the IDB: every seed must be fresh, every pre-fix item must hold
                its recorded size; afterwards the function table must equal before + the planned
                functions exactly, and the head changes outside R29 must equal the recorded ones.
                Idempotent; any failure discards the changes (DBFL_KILL).  Never runs auto_wait.

Usage: idat -A -S"tools\\register_r29_entries.py" <idb>     (VRLOG env overrides the log path)
"""
import collections
import glob
import json
import os
import struct
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_idp
import ida_loader
import ida_segment
import ida_ua
import ida_xref
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
S1A = ROOT / "registry/variant_sel_expected.json"
MANIFEST = ROOT / "registry/r29_register_expected.json"
LOG = Path(os.environ.get("VRLOG") or ROOT / "analysis/ida_falconcd/register_r29_entries.log")
PLAN = os.environ.get("VRMODE") == "plan"
R29_BASE, W0, LB = 0x11C3C0, 0x1E10, 0x1F5
FAR_CODE = (ida_xref.fl_CF, ida_xref.fl_JF)

log = []


def r29_range():
    segs = [ida_segment.getseg(s) for s in idautils.Segments()]
    r = [(s.start_ea, s.end_ea) for s in segs if ida_segment.get_segm_name(s).startswith("R29")]
    return r[0][0], r[-1][1]


def is_fs(ea):
    f = ida_funcs.get_func(ea)
    return bool(f and f.start_ea == ea)


def snapshot_funcs():
    return {fs: ida_funcs.get_func(fs).end_ea for fs in idautils.Functions()}


def all_heads():
    return {h for s in idautils.Segments() for h in idautils.Heads(s, ida_segment.getseg(s).end_ea)}


def seeds(lo, hi, s1a):
    out = {}
    for c in s1a["crefs"]:
        if lo <= c["to"] < hi and not is_fs(c["to"]):
            out.setdefault(c["to"], "cref")
    remap = {s["link"] for s in s1a["selectors"]}
    for fn in sorted(glob.glob(str(ROOT / "memdump/*fartrans.jsonl"))):
        for line in open(fn):
            r = json.loads(line)
            link = r["cs"] - LB
            if link in remap:
                t = R29_BASE + (link - W0) * 16 + r["ip"]
                if lo <= t < hi and not is_fs(t):
                    out.setdefault(t, "runtime")
    return out


def orphan_overlap(ea):
    """orphan code items the fresh decode from ea would collide with: [(head, size)]"""
    out, x = set(), ea
    for _ in range(64):
        insn = ida_ua.insn_t()
        n = ida_ua.decode_insn(insn, x)
        if n <= 0:
            break
        if ida_bytes.get_item_head(x) == x and ida_bytes.is_code(ida_bytes.get_flags(x)) \
                and ida_bytes.get_item_size(x) == n:
            break                              # fresh decode re-joined an existing boundary
        for y in range(x, x + n):
            h = ida_bytes.get_item_head(y)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                if ida_funcs.get_func(h):
                    raise RuntimeError("seed 0x%X collides with function code at 0x%X" % (ea, h))
                out.add((h, ida_bytes.get_item_size(h)))
        if insn.get_canon_mnem() in ("retf", "retn", "iret", "jmp"):
            break
        x += n
    return sorted(out)


def far_fixes(new, lo, hi, s1a):
    """far calls in new code resolving through the identity selector of a shared anchor into R05"""
    shared = {W0 + 0x1000}
    remapped = {s["sel"] for s in s1a["selectors"]}
    out = []
    for f in new:
        for h in idautils.FuncItems(f):
            if ida_bytes.get_byte(h) not in (0x9A, 0xEA) or ida_bytes.get_item_size(h) != 5:
                continue
            off, seg = struct.unpack("<HH", idc.get_bytes(h, 5)[1:])
            if seg in remapped:
                continue
            if seg not in shared:
                continue
            want = R29_BASE + (seg - 0x1000 - W0) * 16 + off
            before = sorted((x.to, x.type, bool(x.user)) for x in idautils.XrefsFrom(h, ida_xref.XREF_FAR)
                            if x.iscode and x.type in FAR_CODE)
            if [b[0] for b in before] != [want]:
                out.append({"ea": h, "to": want, "type": ida_xref.fl_CF if ida_bytes.get_byte(h) == 0x9A
                            else ida_xref.fl_JF, "before": before})
    return out


def swap(fixes):
    for c in fixes:
        for to, ty, user in c["before"]:
            if not user and to != c["to"]:
                ida_xref.del_cref(c["ea"], to, 0)
        ida_xref.add_cref(c["ea"], c["to"], c["type"] | ida_xref.XREF_USER)


def plan():
    s1a = json.loads(S1A.read_text())
    lo, hi = r29_range()
    fn0 = snapshot_funcs()
    h0 = {h for h in all_heads() if not lo <= h < hi}
    todo = seeds(lo, hi, s1a)
    log.append("seeds: %s" % sorted(collections.Counter(todo.values()).items()))
    order, prefix, seen, rnd = [], [], set(todo), 0
    while todo and rnd < 10:
        rnd += 1
        added = []
        for ea, why in sorted(todo.items()):
            if ida_funcs.get_func(ea):
                raise RuntimeError("seed 0x%X (%s) is inside function 0x%X" % (ea, why, ida_funcs.get_func(ea).start_ea))
            ov = orphan_overlap(ea)
            for h, sz in ov:
                ida_bytes.del_items(h, ida_bytes.DELIT_SIMPLE, sz)
            if ov:
                prefix.append({"seed": ea, "items": ov})
            if not ida_funcs.add_func(ea) or not is_fs(ea):
                raise RuntimeError("add_func 0x%X (%s) failed" % (ea, why))
            order.append({"ea": ea, "end": ida_funcs.get_func(ea).end_ea, "why": why, "round": rnd})
            added.append(ea)
        nxt = {}
        for ea in added:
            for h in idautils.FuncItems(ea):
                insn = ida_ua.insn_t()
                ida_ua.decode_insn(insn, h)
                if not ida_idp.is_call_insn(insn):
                    continue
                for t in idautils.CodeRefsFrom(h, 0):
                    if lo <= t < hi and t not in seen and not is_fs(t):
                        nxt[t] = "callee"
                        seen.add(t)
        todo = nxt
    if todo:
        raise RuntimeError("closure did not converge")
    fn1 = snapshot_funcs()
    changed = [f for f, e in fn0.items() if fn1.get(f) != e]
    if changed:
        raise RuntimeError("existing functions changed: %s" % ["0x%X" % f for f in changed[:10]])
    new = sorted(set(fn1) - set(fn0))
    fixes = far_fixes(new, lo, hi, s1a)
    swap(fixes)
    h1 = {h for h in all_heads() if not lo <= h < hi}
    doc = {"finding": 123, "step": "S1b", "r29": [lo, hi], "funcs_before": len(fn0),
           "seeds": order, "prefix": prefix, "crefs": fixes,
           "new_funcs": [[f, fn1[f]] for f in new],
           "outside_heads_new": sorted(h1 - h0), "outside_heads_gone": sorted(h0 - h1)}
    MANIFEST.write_text(json.dumps(doc, indent=0))
    log.append("rounds: %d; new functions %d (%d bytes); pre-fixed seeds %s; far cref swaps %d"
               % (rnd, len(new), sum(fn1[f] - f for f in new), ["0x%X" % p["seed"] for p in prefix], len(fixes)))
    log.append("heads outside R29: %d new %s, %d gone %s"
               % (len(h1 - h0), ["0x%X" % h for h in sorted(h1 - h0)][:12], len(h0 - h1),
                  ["0x%X" % h for h in sorted(h0 - h1)][:12]))
    for h in sorted(h0 - h1):
        g = ida_bytes.get_item_head(h)
        log.append("  gone 0x%X: now inside 0x%X (%d B) %s" % (h, g, ida_bytes.get_item_size(g), idc.generate_disasm_line(g, 0)))
    log.append("plan written to %s (IDB discarded)" % MANIFEST.relative_to(ROOT))
    ida_loader.set_database_flag(ida_loader.DBFL_KILL)


def apply():
    doc = json.loads(MANIFEST.read_text())
    lo, hi = doc["r29"]
    fn0 = snapshot_funcs()
    want = {f: e for f, e in doc["new_funcs"]}
    if all(fn0.get(f) == e for f, e in want.items()):
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    problems = []
    if len(fn0) != doc["funcs_before"]:
        problems.append("function count %d != manifest %d" % (len(fn0), doc["funcs_before"]))
    for s in doc["seeds"]:
        if ida_funcs.get_func(s["ea"]):
            problems.append("seed 0x%X already inside a function" % s["ea"])
    for p in doc["prefix"]:
        for h, sz in p["items"]:
            if ida_bytes.get_item_head(h) != h or ida_bytes.get_item_size(h) != sz \
                    or not ida_bytes.is_code(ida_bytes.get_flags(h)) or ida_funcs.get_func(h):
                problems.append("pre-fix item 0x%X (%d B) not as planned" % (h, sz))
    if problems:
        log.extend("  " + p for p in problems[:20])
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    h0 = {h for h in all_heads() if not lo <= h < hi}
    pre = {p["seed"]: p["items"] for p in doc["prefix"]}
    for s in sorted(doc["seeds"], key=lambda s: (s["round"], s["ea"])):
        for h, sz in pre.get(s["ea"], []):
            ida_bytes.del_items(h, ida_bytes.DELIT_SIMPLE, sz)
        if not ida_funcs.add_func(s["ea"]) or not is_fs(s["ea"]) or ida_funcs.get_func(s["ea"]).end_ea != s["end"]:
            f = ida_funcs.get_func(s["ea"])
            raise RuntimeError("seed 0x%X: got %s, planned end 0x%X"
                               % (s["ea"], "0x%X-0x%X" % (f.start_ea, f.end_ea) if f else None, s["end"]))
    for c in doc["crefs"]:
        live = sorted((x.to, x.type, bool(x.user)) for x in idautils.XrefsFrom(c["ea"], ida_xref.XREF_FAR)
                      if x.iscode and x.type in FAR_CODE)
        if live != [tuple(b) for b in c["before"]]:
            raise RuntimeError("cref 0x%X live %s != planned before %s" % (c["ea"], live, c["before"]))
    swap(doc["crefs"])
    fn1 = snapshot_funcs()
    exp = dict(fn0)
    exp.update(want)
    if fn1 != exp:
        diff = sorted(set(fn1.items()) ^ set(exp.items()))
        raise RuntimeError("function table differs from plan: %s" % ["0x%X-0x%X" % d for d in diff[:20]])
    h1 = {h for h in all_heads() if not lo <= h < hi}
    if sorted(h1 - h0) != doc["outside_heads_new"] or sorted(h0 - h1) != doc["outside_heads_gone"]:
        raise RuntimeError("heads outside R29 differ from plan: new %s gone %s"
                           % (["0x%X" % h for h in sorted(h1 - h0)][:12], ["0x%X" % h for h in sorted(h0 - h1)][:12]))
    log.append("registered %d functions (%d bytes), %d pre-fixed seeds, %d far cref swaps; table %d -> %d"
               % (len(want), sum(e - f for f, e in want.items()), len(pre), len(doc["crefs"]), len(fn0), len(fn1)))
    log.append("heads outside R29 as planned: %d new, %d gone" % (len(h1 - h0), len(h0 - h1)))
    ida_loader.save_database(idaapi.get_path(idaapi.PATH_TYPE_IDB), 0)
    log.append("database saved")


try:
    plan() if PLAN else apply()
except Exception:
    ida_loader.set_database_flag(ida_loader.DBFL_KILL)
    log.append("ERROR (not saved):\n" + traceback.format_exc())
LOG.write_text("\n".join(log))
idaapi.qexit(0)
