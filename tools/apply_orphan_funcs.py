"""Register orphan code that is called but belongs to no function (finding 126, S1c-4).

Tier 1 only: a run of code heads that no function owns, entered by a call from code, that decodes from its
start to a terminator (ret/retf/iret or an unconditional jmp) without touching another function.  Runs that
end mid-flow (mov/add/popf ...) or look misdecoded are NOT registered; they are listed in finding 126.

Manifest registry/orphan_funcs_expected.json: {"add_funcs": [{"ea", "end", "last", "callers", "sha256"}]}
  OFMODE=plan   run on a COPY: registers every candidate in ADD (below) with an explicit end, checks each,
                records the result, never saves.
  (default)     replays the manifest: each [ea, end) must hold its recorded bytes and no function (or already be
                exactly the planned function); applies add_func(ea, end); post-check requires the old functions
                to be unchanged (start, end, name, chunks) and the new ones to be exactly the planned ones.
                A failure discards everything (DBFL_KILL).  Never runs auto_wait.
REBASE (finding 130) moves the start of an existing named function up to the call-reached entry in front of it (the
old start was a mid-instruction byte left by a misdecode): del_func, clear, recursive descent, add_func, same name and
far flag, DS range extended.  Manifest key "rebase_funcs".
OFLOG overrides the log path, OFDRY=1 applies and checks without saving.

Usage: idat -A -S"tools\\apply_orphan_funcs.py" <idb>
"""
import hashlib
import json
import os
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_segment
import ida_segregs
import ida_ua
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "registry/orphan_funcs_expected.json"
LOG = Path(os.environ.get("OFLOG") or ROOT / "analysis/ida_falconcd/apply_orphan_funcs.log")
PLAN = os.environ.get("OFMODE") == "plan"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
# (ea, end): chosen from analysis/s1/orphan_t1*.json; every end is the address after a terminator
ADD = [(0x1617C, 0x162DF), (0x162DF, 0x163AD), (0x16284E, 0x162878), (0x12C970, 0x12C9D0),
       (0x12CA0D, 0x12CAEF), (0x12CAEF, 0x12CB27), (0x12C683, 0x12C7C6), (0x12C951, 0x12C970),
       (0x12CCE9, 0x12CE9D), (0x10931E, 0x1093A8), (0x109445, 0x109519), (0x129F7, 0x12B12), (0x12B12, 0x12B62),
       (0x100CA8, 0x100D00)]
# ea -> (clear_lo, clear_hi, seeds): orphan run with a misdecoded stretch that must be cleared and redecoded first
ADD_CLEAR = {0x10931E: (0x109388, 0x1093A6, [0x10931E, 0x109388]), 0x109445: (0x109445, 0x109519, [0x109445]),
             0x129F7: (0x129F7, 0x12B12, [0x129F7]), 0x12B12: (0x12B12, 0x12B62, [0x12B12]), 0x100CA8: (0x100CA8, 0x100D00, [0x100CA8])}
# ea -> (tail chunk, clear ranges, seeds, pad bytes): a function whose second chunk lies after a foreign function that sits
# inside its span (finding 131); pad bytes are single data bytes inside a chunk that no flow reaches
TAILS = {0x100CA8: ([(0x100D0E, 0x100DFA)], [(0x100CA8, 0x100D00), (0x100D0D, 0x100DFA)], [0x100CA8, 0x100D0E, 0x100DF4], [0x100DEC])}
# (old_start, new_start, end, clear_lo, ds_para): existing function whose real entry is new_start (finding 130).
# [clear_lo, end) is cleared and redecoded from new_start; ds_para (or None) extends the DS range down to new_start.
REBASE = [(0x106EEC, 0x106EE2, 0x106F3A, 0x106EE2, 0x706E), (0x10843D, 0x108430, 0x1084A6, 0x10843C, None),
          (0x10CFA6, 0x10CE30, 0x10CFEC, 0x10CFA5, None),
          (0x4335A, 0x4334E, 0x43395, 0x4334E, None)]
# (ea, end): existing functions whose body continues in orphan code (jcc/jmp into it) -> set_func_end
EXTEND = [(0x12C518, 0x12C66A), (0x12C7C6, 0x12C951)]
# (func, run_lo, run_hi): fl_F continuations (finding 129).  If run_lo is the main-chunk end the function is
# lengthened (set_func_end, which also swallows an adjacent tail chunk), else the run is appended as a tail chunk.
EXTEND_RUNS = [(0x10CC60, 0x10CC8E, 0x10CE05), (0x2D31A, 0x2D353, 0x2D375), (0x3F6A9, 0x3F6C7, 0x3F6D6),
               (0x2142E, 0x215FE, 0x21631), (0x2520B, 0x25220, 0x25224)]
DOS_EXIT = {0x2D353}  # run ends in `mov ax,4C00h / int 21h` (terminates the process)
# jmp-reached menu bodies (R20/R21): (base, damaged `call far` head, end).  The key table is `mov bx, tab` with
# `mov cx, n` before the lookup loop; the handler table follows the keys, offsets relative to base.
MENUS = [(0x10B380, 0x10B4E8, 0x10B6DF), (0x10B720, 0x10B888, 0x10BA7B)]
log = []


def descend(seed, lo, hi, made):
    todo = [seed]
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea:
                if ea in made:
                    break
            else:
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
                if ida_ua.create_insn(ea) <= 0:
                    raise RuntimeError("cannot decode 0x%X" % ea)
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and lo <= x.to < hi:
                        todo.append(x.to)
                if m == "jmp":
                    break
            ea += ida_bytes.get_item_size(ea)


def menu_seeds(base, cf):
    mov = cx = None
    a = base
    while a < base + 0x1C0 and mov is None:
        h = ida_bytes.get_item_head(a)
        if (idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "bx" and idc.get_operand_type(h, 1) == idc.o_imm
                and idc.get_operand_value(h, 1) > 0x300):
            mov = h
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(mov is not None, "table load in 0x%X" % base)
    h = mov
    while h > base and cx is None:
        h = idc.prev_head(h, base)
        if idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "cx" and idc.get_operand_type(h, 1) == idc.o_imm:
            cx = idc.get_operand_value(h, 1)
    must(cx, "loop count in 0x%X" % base)
    tab = idc.get_operand_value(mov, 1)
    hands = [ida_bytes.get_word(base + tab + 2 * cx + 2 * i) for i in range(cx)]
    return sorted({base + x for x in hands} | {cf + 5})


def decode_menu(item):
    lo, hi = item["ea"], item["end"]
    if "clear" in item or "clears" in item:
        regs = regions(item)
        orig = set()
        for clo, chi in item.get("clears") or [item["clear"]]:
            a = clo
            while a < chi:
                h = ida_bytes.get_item_head(a)
                if ida_bytes.is_code(ida_bytes.get_flags(h)):
                    orig.add(h)
                a = h + max(ida_bytes.get_item_size(h), 1)
            ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        for sd in item["seeds"]:
            rlo, rhi = next((x, y) for x, y in regs if x <= sd < y)
            descend(sd, rlo, rhi, set())
        for h in sorted(orig):
            if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
                bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not any(x <= r.frm < y for x, y in regs)]
                must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
        return
    else:
        cf = item["redecode"]
        ida_bytes.del_items(cf, ida_bytes.DELIT_SIMPLE, 5)
        must(ida_ua.create_insn(cf) == 5, "re-decode call far at 0x%X" % cf)
    made = set()
    for sd in item["seeds"]:
        descend(sd, lo, hi, made)


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


def sha(ea, end):
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()


def must(ok, what):
    if not ok:
        raise RuntimeError(what + " failed")


def terminated(ea, end):
    last = idc.prev_head(end, ea)
    m = idc.print_insn_mnem(last)
    return m in RETS or (m == "jmp" and idc.get_operand_type(last, 0) in (idc.o_near, idc.o_far))


def callers(ea):
    return sorted(x.frm for x in idautils.XrefsTo(ea, 0)
                  if x.iscode and idc.print_insn_mnem(x.frm).startswith("call") and ida_funcs.get_func(x.frm))


def regions(item):
    return [[item["ea"], item["end"]]] + [list(t) for t in item.get("tails", [])]


def state(item):
    f = ida_funcs.get_func(item["ea"])
    if f and f.start_ea == item["ea"] and f.end_ea == item["end"] and (not item.get("tails") or chunks(item["ea"]) == sorted(regions(item))):
        return "applied"
    if (not any(ida_funcs.get_func(a) for lo, hi in regions(item) for a in range(lo, hi))
            and sha(item["ea"], item["end"]) == item["sha256"]
            and all(sha(lo, hi) == t for (lo, hi), t in zip(item.get("tails", []), item.get("tails_sha256", [])))):
        return "fresh"
    return "mismatch"


def uname(ea):
    return idaapi.get_name(ea) if ida_bytes.has_user_name(ida_bytes.get_flags(ea)) else None


def norm(x):
    """Fill the fields the finding-128 entries lack (they were a single contiguous run appended to a one-chunk function)."""
    x.setdefault("run", [x["before_end"], x["end"]])
    x.setdefault("run_sha256", x["sha256"])
    x.setdefault("chunks_before", [[x["ea"], x["before_end"]]])
    x.setdefault("chunks_after", [[x["ea"], x["end"]]])
    return x


def ext_state(x):
    """Entry: ea, run [lo, hi) of orphan code, run_sha256, chunks_before/after (sorted chunk lists), before_end/end
    (main-chunk end, which is what function_bytes.json sees) and sha256 of the bytes appended to the main chunk."""
    f = ida_funcs.get_func(x["ea"])
    if not f or f.start_ea != x["ea"]:
        return "mismatch"
    if chunks(x["ea"]) == x["chunks_after"] and f.end_ea == x["end"]:
        return "applied"
    lo, hi = x["run"]
    if (chunks(x["ea"]) == x["chunks_before"] and f.end_ea == x["before_end"]
            and not any(ida_funcs.get_func(a) for a in range(lo, hi)) and sha(lo, hi) == x["run_sha256"]):
        return "fresh"
    return "mismatch"


def extend(x):
    lo, hi = x["run"]
    f = ida_funcs.get_func(x["ea"])
    if f.end_ea == lo:
        must(ida_funcs.set_func_end(x["ea"], hi), "set_func_end 0x%X -> 0x%X" % (x["ea"], hi))
    else:
        must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (x["ea"], lo, hi))
    if x["chunks_after"] is None:
        f = ida_funcs.get_func(x["ea"])
        x["end"], x["chunks_after"] = f.end_ea, chunks(x["ea"])
        x["sha256"] = sha(x["before_end"], x["end"]) if x["end"] > x["before_end"] else ""
    must(ext_state(x) == "applied", "extend 0x%X (state %s, chunks %s)" % (x["ea"], ext_state(x), chunks(x["ea"])))


def is_far(ea):
    return bool(ida_funcs.get_func(ea).flags & ida_funcs.FUNC_FAR)


def rb_state(x):
    old, new, end = x["old_ea"], x["ea"], x["end"]
    f = ida_funcs.get_func(new)
    if f and f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]] and uname(new) == x["name"]:
        return "applied"
    f = ida_funcs.get_func(old)
    if (f and f.start_ea == old and f.end_ea == end and chunks(old) == [[old, end]] and uname(old) == x["name"]
            and sha(new, end) == x["sha256"] and not any(ida_funcs.get_func(a) for a in range(new, old))):
        return "fresh"
    return "mismatch"


def rebase(x):
    old, new, end, clo = x["old_ea"], x["ea"], x["end"], x["clear_lo"]
    far = is_far(old)
    must(far == x["far"], "far flag of 0x%X" % old)
    a, orig = clo, set()
    while a < end:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(ida_funcs.del_func(old), "del_func 0x%X" % old)
    ida_name.set_name(old, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, end - clo)
    if x.get("ds") is not None:
        s = ida_segment.setup_selector(x["ds"])
        must(ida_segment.sel2para(s) == x["ds"], "selector for para 0x%X" % x["ds"])
        must(ida_segregs.split_sreg_range(new, idaapi.str2reg("ds"), s, ida_segregs.SR_user), "DS split at 0x%X" % new)
    made = set()
    descend(new, new, end, made)
    a = new
    while a < end:
        must(ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.get_item_head(a) == a, "non-code head 0x%X in rebased 0x%X" % (a, new))
        a += ida_bytes.get_item_size(a)
    lost = sorted(h for h in orig if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h))
    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (new <= r.frm < end)]
        must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    must(ida_funcs.add_func(new, end), "add_func 0x%X..0x%X" % (new, end))
    f = ida_funcs.get_func(new)
    must(f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]], "span of rebased 0x%X" % new)
    if far:
        f.flags |= ida_funcs.FUNC_FAR
        must(ida_funcs.update_func(f), "update_func 0x%X" % new)
    if x["name"]:
        must(ida_name.set_name(new, x["name"], ida_name.SN_NOWARN), "name of 0x%X" % new)
    must(is_far(new) == far, "far flag of rebased 0x%X" % new)
    if x.get("lost_heads") is None:
        x["lost_heads"] = lost
    must(x["lost_heads"] == lost, "stale code heads of 0x%X differ from the manifest: %s" % (new, [hex(h) for h in lost]))
    must(rb_state(x) == "applied", "rebase 0x%X" % new)


def add_all(items, exts=(), rebs=()):
    before = snapshot()
    for x in exts:
        if ext_state(x) == "applied":
            continue
        extend(x)
    for x in rebs:
        if rb_state(x) != "applied":
            rebase(x)
    for it in items:
        if state(it) == "applied":
            continue
        if "seeds" in it:
            decode_menu(it)
        must(ida_funcs.add_func(it["ea"], it["end"]), "add_func 0x%X..0x%X" % (it["ea"], it["end"]))
        f = ida_funcs.get_func(it["ea"])
        must(f.start_ea == it["ea"] and f.end_ea == it["end"], "span of 0x%X" % it["ea"])
        for lo, hi in it.get("tails", []):
            must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (it["ea"], lo, hi))
            f = ida_funcs.get_func(it["ea"])
        must(chunks(it["ea"]) == sorted(regions(it)), "chunks of 0x%X" % it["ea"])
        if "clear" in it or "clears" in it:
            for lo, hi in regions(it):
                must(terminated(lo, hi), "0x%X..0x%X does not end in a terminator" % (lo, hi))
            it["last"] = idc.generate_disasm_line(idc.prev_head(it["end"], it["ea"]), 0)
        if "seeds" in it:
            for lo, hi in regions(it):
                a = lo
                while a < hi:
                    if a in it.get("pad", []):
                        a += 1
                        continue
                    must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                    a += ida_bytes.get_item_size(a)
    after = snapshot()
    new = {it["ea"] for it in items} | {x["ea"] for x in rebs}
    changed = sorted(ea for ea in set(before) if before[ea] != after.get(ea))
    must(set(changed) <= {x["ea"] for x in exts} | {x["old_ea"] for x in rebs},
         "unplanned existing functions changed %s" % [hex(c) for c in changed[:10]])
    for x in exts:
        must(after[x["ea"]][0] == before[x["ea"]][0], "name of 0x%X changed" % x["ea"])
    for x in rebs:
        must(x["old_ea"] not in after and (x["name"] is None or after[x["ea"]][0] == x["name"]), "rebase of 0x%X" % x["old_ea"])
    must(set(after) - set(before) <= new, "unplanned new functions %s" % [hex(c) for c in sorted(set(after) - set(before) - new)][:10])
    log.append("functions added: %s; extended: %s; rebased: %s; table %d -> %d, other existing functions unchanged" % (
        ["0x%X..0x%X" % (it["ea"], it["end"]) for it in items],
        ["0x%X -> 0x%X" % (x["ea"], x["end"]) for x in exts],
        ["0x%X -> 0x%X %s" % (x["old_ea"], x["ea"], x["name"]) for x in rebs], len(before), len(after)))


def main():
    if PLAN:
        items = []
        old = {x["ea"]: x for x in json.loads(MANIFEST.read_text())["add_funcs"]} if MANIFEST.exists() else {}
        for ea, end in ADD:
            if state({"ea": ea, "end": end, "sha256": ""}) == "applied" and ea in old:
                items.append(old[ea])
                continue
            tails = TAILS[ea][0] if ea in TAILS else []
            must(not any(ida_funcs.get_func(a) for lo, hi in [(ea, end)] + tails for a in range(lo, hi)), "0x%X..0x%X already owned" % (ea, end))
            must(ea in ADD_CLEAR or terminated(ea, end), "0x%X..0x%X does not end in a terminator" % (ea, end))
            it = {"ea": ea, "end": end, "last": None, "callers": callers(ea), "sha256": sha(ea, end)}
            if ea in ADD_CLEAR:
                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
            if ea in TAILS:
                it["tails"], it["tails_sha256"] = [list(t) for t in tails], [sha(lo, hi) for lo, hi in tails]
                it["clears"], it["seeds"], it["pad"] = [list(c) for c in TAILS[ea][1]], TAILS[ea][2], TAILS[ea][3]
                del it["clear"]
            items.append(it)
        for base, cf, end in MENUS:
            if state({"ea": base, "end": end, "sha256": ""}) == "applied" and base in old:
                items.append(old[base])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
            must(terminated(base, end), "0x%X..0x%X does not end in a terminator" % (base, end))
            items.append({"ea": base, "end": end, "last": idc.generate_disasm_line(idc.prev_head(end, base), 0),
                          "callers": sorted(x.frm for x in idautils.XrefsTo(base, 0) if x.iscode),
                          "redecode": cf, "seeds": menu_seeds(base, cf), "sha256": sha(base, end)})
        oldx = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("extend_funcs", [])} if MANIFEST.exists() else {}
        exts = []
        for ea, end in EXTEND:
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            if f.end_ea == end and ea in oldx:
                exts.append(norm(oldx[ea]))
                continue
            must(terminated(f.end_ea, end), "0x%X..0x%X does not end in a terminator" % (f.end_ea, end))
            exts.append(norm({"ea": ea, "before_end": f.end_ea, "end": end, "sha256": sha(f.end_ea, end)}))
        for ea, lo, hi in EXTEND_RUNS:
            if ea in oldx and "run" in oldx[ea]:
                exts.append(oldx[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            must(not any(ida_funcs.get_func(a) for a in range(lo, hi)), "run 0x%X..0x%X already owned" % (lo, hi))
            must(terminated(lo, hi) or lo in DOS_EXIT, "run 0x%X..0x%X not terminated" % (lo, hi))
            exts.append({"ea": ea, "run": [lo, hi], "run_sha256": sha(lo, hi), "before_end": f.end_ea,
                         "chunks_before": chunks(ea), "end": None, "sha256": None, "chunks_after": None})
        oldr = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("rebase_funcs", [])} if MANIFEST.exists() else {}
        rebs = []
        for old, new, end, clo, ds in REBASE:
            if new in oldr:
                rebs.append(oldr[new])
                continue
            f = ida_funcs.get_func(old)
            must(f and f.start_ea == old and f.end_ea == end, "0x%X is not the planned function" % old)
            rebs.append({"ea": new, "old_ea": old, "end": end, "clear_lo": clo, "ds": ds, "name": uname(old),
                         "far": is_far(old), "sha256": sha(new, end), "old_sha256": sha(old, end),
                         "prefix_sha256": sha(new, old), "lost_heads": None})
        add_all(items, exts, rebs)
        MANIFEST.write_text(json.dumps({"finding": 131, "step": "S1c-4 orphan code registered as functions (findings 126-131)",
                                        "extend_funcs": exts, "rebase_funcs": rebs, "add_funcs": items},
                                       indent=1).replace("\n", "\r\n"))
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("plan written: %s (not saved)" % MANIFEST.name)
        return
    doc = json.loads(MANIFEST.read_text())
    exts = [norm(x) for x in doc.get("extend_funcs", [])]
    rebs = doc.get("rebase_funcs", [])
    states = [state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs]
    log.append("manifest: %d entries (add + extend); live: %d fresh, %d applied, %d mismatched" % (
        len(states), states.count("fresh"), states.count("applied"), states.count("mismatch")))
    if all(s == "applied" for s in states):
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    if "mismatch" in states:
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    add_all(doc["add_funcs"], exts, rebs)
    if os.environ.get("OFDRY"):
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("dry run (OFDRY): not saved")
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
