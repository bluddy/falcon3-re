"""Finding 61 step P2 (read-only IDA): forward-chain sweep of the evidence-rich
upper-half ranges, producing the registration plan.

For each scope range:
  * keep   = functions already registered there (never touched),
  * holes  = candidate data holes from tools/map_upper.py (live sha256),
  * gaps   = range minus keep minus holes,
  * sweep  = walk each gap instruction-by-instruction:
        - an EXISTING code item wins (its size/mnemonic are adopted -- finding
          60's "never contradict a valid decode"),
        - where there is no item, a fresh decode fills in,
        - stop on: undecodable byte, overrun of the gap end (which flags the
          boundary hole as suspect), arrival inside an existing item (stream
          disagreement), an existing data item, or padding after a terminator
          (module end -- never guess past it),
  * seeds  = unresolved call destinations + RTLink entry_eas inside the gap:
        accepted only if they land EXACTLY on a sweep boundary whose previous
        instruction is a terminator (or on the gap start itself).

Emits analysis/ida_falconcd/upper_sweep.json: contiguous covered ranges (with
keep_fns / holes / new_fns), uncovered spans with stop reasons, and stats.
NO mutation, always idaapi.qexit(0).

Usage: cmd /c "tools\\run_idat.bat tools\\sweep_upper.py"
"""
import hashlib
import json
import traceback
from collections import Counter

import ida_bytes
import ida_funcs
import ida_idp
import ida_ua
import idaapi
import idautils
import idc

ROOT = r"C:\Users\yotam\projects\falcon3"
IDA = ROOT + r"\analysis\ida_falconcd"
OUT = IDA + r"\upper_sweep.json"
LOG = IDA + r"\upper_sweep.log"

SCOPE = [
    {"name": "i_3B830", "lo": 0x3B830, "hi": 0x43AE0},
    {"name": "ii_43AE0", "lo": 0x43AE0, "hi": 0x48DB0},
    {"name": "iii_4E520", "lo": 0x4E520, "hi": 0x4FD20},
    {"name": "iv_54AF0_UI", "lo": 0x54AF0, "hi": 0x669F0},
]
TERMS = {"retn", "retf", "ret", "iret", "jmp"}
MIN_FN = 3
MAX_GAP_INSNS = 40000

log = []


def mnem_at(ea):
    return (idc.print_insn_mnem(ea) or "").lower()


def is_term_mnem(m):
    return m in TERMS


# entry-like mnemonics -- used to authorise continuing past an alignment `00`
# run (decode fails on `00` in this IDB, and padding is otherwise
# indistinguishable from data). Prologue-shaped for 16-bit DOS code.
ENTRY_AFTER_PAD = {
    "push", "pusha", "pushad", "pop", "popa", "popad", "enter", "sub", "mov",
    "xor", "and", "or", "add", "adc", "inc", "dec", "cmp", "test", "call",
    "les", "lds", "lea", "movs", "stos", "lods", "scas", "cmps", "cld", "std",
    "cli", "sti", "clc", "stc", "cmc", "nop", "xchg", "sal", "shl", "shr",
    "sar", "rol", "ror", "rcl", "rcr", "cbw", "cwd", "int", "int3", "bound",
    "hlt", "wait", "fld", "fst", "fild", "fist", "fistp", "fnstsw", "fldcw",
    "fnstcw", "in", "out", "ins", "outs", "loop", "loope", "loopne", "jecxz",
    "sahf", "lahf", "xlat", "mul", "imul", "div", "idiv", "neg", "not",
}


def decode_at(ea):
    """(size, mnem, src): an existing IDA code item wins, else a fresh decode.
    src in {'data','mid','fail'} means do not walk here."""
    h = ida_bytes.get_item_head(ea)
    if h != ea:
        return 0, "", "mid"                       # inside an existing item
    fl = ida_bytes.get_flags(ea)
    if ida_bytes.is_code(fl):
        return ida_bytes.get_item_size(ea), mnem_at(ea), "ida"
    if ida_bytes.is_data(fl):
        return 0, "", "data"
    insn = ida_ua.insn_t()
    n = ida_ua.decode_insn(insn, ea)
    if n <= 0:
        return 0, "", "fail"
    return n, (insn.get_canon_mnem() or "").lower(), "fresh"


def sweep_gap(a, b, holes_lo_set):
    """Walk [a,b). Returns (insns, stop_reason, stop_pos, lead_padding) with
    insns = [(ea, size, mnem, is_term, src, prev_is_term)].  An existing decode
    always wins over a fresh one (finding 60's rule), `00` runs are skipped
    only when what follows looks like an entry, and a stop position < b is
    reported so the caller can mark the rest uncovered."""
    insns = []
    cur = a
    lead = None
    prev_term = False
    gap_start = a

    def trial_close(q):
        """walk from q; True if a terminator is reached within the window
        (used only to authorise bridging over a small non-code island)."""
        cur2, steps = q, 0
        while cur2 < b and steps < 160:
            n, m, s = decode_at(cur2)
            if s == "mid":
                h = ida_bytes.get_item_head(cur2)
                isz = max(ida_bytes.get_item_size(h), 1)
                if h + isz <= cur2:
                    return False
                if is_term_mnem(mnem_at(h)):
                    return True
                cur2 = h + isz
                steps += 1
                continue
            if s == "data":
                isz = max(ida_bytes.get_item_size(cur2), 1)
                if isz >= 16:
                    return False
                cur2 += isz
                continue
            if n <= 0 or cur2 + n > b:
                return False
            if is_term_mnem(m):
                return True
            cur2 += n
            steps += 1
        return False

    def try_bridge(from_at):
        """mid-body only: find q in (from_at, from_at+64] where a chain
        re-starts and closes on a terminator.  The island bytes stay inside
        the function body (tables inside code), never inside a seed."""
        for q in range(from_at + 1, min(from_at + 64, b) + 1):
            if ida_bytes.get_byte(q) == 0:
                continue
            if ida_bytes.get_item_head(q) != q:
                continue
            if trial_close(q):
                return q
        return None

    while cur < b:
        if len(insns) >= MAX_GAP_INSNS:
            return insns, "insn-limit", cur, lead
        if ida_bytes.get_byte(cur) == 0:
            z = 0
            while cur + z < b and ida_bytes.get_byte(cur + z) == 0 and z < 64:
                z += 1
            pad_from = gap_start if not insns else insns[-1][0] + insns[-1][1]
            if cur + z >= b or z >= 64:
                return insns, "zero-run", pad_from, lead
            nz = cur + z
            n2, m2, _s2 = decode_at(nz)
            if n2 <= 0 or m2 not in ENTRY_AFTER_PAD:
                # mid-body (last insn open): try to bridge past the island
                if insns and not is_term_mnem(insns[-1][2]):
                    q = try_bridge(cur)
                    if q:
                        cur = q
                        continue
                return insns, "pad-then-nonentry@0x%X" % nz, pad_from, lead
            if not insns:
                lead = (a, nz)          # leading padding: uncovered [a, nz)
                gap_start = nz
            cur = nz                    # prev_term survives the padding
            continue
        n, m, src = decode_at(cur)
        if src == "data":
            # a small existing data item in the middle of decodable code is a
            # stale label (a 2-byte `dw` here blocked 19 KB of block ii); a
            # real data blob (>= 16 B) stops the sweep unless we are mid-body
            # and can bridge to where a chain closes again
            isz = max(ida_bytes.get_item_size(cur), 1)
            if isz >= 16:
                if insns:
                    q = try_bridge(cur)
                    if q:
                        cur = q
                        continue
                return insns, "data-item@0x%X" % cur, cur, lead
            cur += isz
            continue
        if src == "mid":
            # an existing item disagrees with our stream: IDA wins -- adopt its
            # item wholesale and resync to its end (never contradict a valid
            # decode, never walk backwards)
            h = ida_bytes.get_item_head(cur)
            isz = max(ida_bytes.get_item_size(h), 1)
            mend = h + isz
            if mend <= cur:
                return insns, "conflict-mid-item@0x%X" % cur, cur, lead
            mm = mnem_at(h)
            insns.append((h, isz, mm, is_term_mnem(mm), "ida", False))
            prev_term = is_term_mnem(mm)
            cur = mend
            continue
        if src == "data":
            return insns, "data-item@0x%X" % cur, cur, lead
        if n <= 0:
            if insns:                       # mid-body island (bad bytes,
                q = try_bridge(cur)          # jump tables, stale labels)
                if q:
                    cur = q
                    continue
            return insns, "undecodable@0x%X" % cur, cur, lead
        if cur + n > b:
            reason = ("overrun-hole@0x%X" % b) if b in holes_lo_set else \
                     ("overrun-gap-end@0x%X" % cur)
            return insns, reason, cur, lead
        insns.append((cur, n, m, is_term_mnem(m), src, prev_term))
        prev_term = is_term_mnem(m)
        cur += n
    return insns, "end", cur, lead


def main():
    dsts = json.load(open(IDA + r"\dst_list.json"))
    up = json.load(open(IDA + r"\upper_map.json"))
    entries = json.load(open(IDA + r"\overlay_entries.json"))
    entry_eas = sorted(e["entry_ea"] for e in entries
                       if e.get("entry_ea") is not None)

    out_ranges, uncovered_all, all_stats = [], [], {}
    suspect_holes = set()

    for attempt in range(3):                 # retries drop suspect holes
        out_ranges, uncovered_all, all_stats = [], [], {}
        suspect_this = set()
        for sc in SCOPE:
            lo, hi = sc["lo"], sc["hi"]
            # keys MUST be the ground-truth keys (extract_ida_bytes keeps the
            # previous key for an EA, which can differ from the display name)
            ea2key = {v["ea"]: k for k, v in
                      json.load(open(IDA + r"\function_bytes.json")).items()}
            keep = [{"key": ea2key.get(f) or idc.get_func_name(f) or ("sub_%X" % f),
                     "ea": f, "size": ida_funcs.get_func(f).end_ea - f}
                    for f in idautils.Functions(lo, hi)]
            holes = [dict(h) for h in up["holes"]
                     if lo <= h["lo"] < hi and h["lo"] not in suspect_holes]
            holes.sort(key=lambda h: h["lo"])
            hole_spans = [(h["lo"], h["hi"], h) for h in holes]

            def gaps_of():
                # range minus keep fns minus holes (the range itself is NOT in
                # this list -- it would swallow every gap)
                spans = [(f["ea"], f["ea"] + f["size"], "k") for f in keep] + \
                        [(s, e, "h") for s, e, _ in hole_spans]
                spans.sort(key=lambda x: (x[0], x[1]))
                out, cur = [], lo
                for s, e, _t in spans:
                    if s > cur:
                        out.append((cur, min(s, hi)))
                    cur = max(cur, min(e, hi))
                    if cur >= hi:
                        break
                if cur < hi:
                    out.append((cur, hi))
                return [(a, b) for a, b in out if b - a > 0]

            gaps = gaps_of()
            hole_lo_set = {h["lo"] for h in holes}
            gap_res, uncovered = [], []
            stats = {"insns": 0, "seeds_ok": 0, "seeds_rej": 0, "stops": Counter()}
            dst_in = [d for d in dsts if lo <= d["ea"] < hi]
            new_fns = []
            for a, b in gaps:
                insns, stop, stop_pos, lead = sweep_gap(a, b, hole_lo_set)
                stats["insns"] += len(insns)
                stats["stops"][stop] += 1
                gap_start = a
                # what precedes this gap: keep-fn end, hole end or the range
                # start itself (all authoritative boundaries)
                if any(kf["ea"] + kf["size"] == a for kf in keep):
                    gk = "keep_end"
                elif any(h["hi"] == a for h in holes):
                    gk = "hole_end"
                else:
                    gk = "range"
                if lead:
                    uncovered.append({"lo": a, "hi": lead[1],
                                      "why": "lead-padding", "block": sc["name"]})
                    gap_start = lead[1]
                if stop_pos < b:
                    uncovered.append({"lo": stop_pos, "hi": b, "why": stop,
                                      "block": sc["name"]})
                    if stop.startswith("overrun-hole"):
                        suspect_this.add(b)
                # accepted boundaries: the gap start, plus every instruction
                # preceded by a terminator (padding-aware: a `00` run after a
                # terminator is attributed to the previous instruction)
                acc = {gap_start}
                for (ea, n, m, term, s, pt) in insns:
                    if pt:
                        acc.add(ea)
                inside = lambda x: any(ea <= x < ea + n
                                       for (ea, n, _m, _t, _s, _p) in insns)
                seeds_ok = [gap_start]
                seeds_rej = []
                for d in dst_in:
                    if not (gap_start <= d["ea"] < stop_pos) or d["ea"] == gap_start:
                        continue
                    if d["ea"] in acc:
                        seeds_ok.append(d["ea"])
                    elif inside(d["ea"]):
                        seeds_rej.append((d["ea"], "no-terminator-before"))
                    else:
                        seeds_rej.append((d["ea"], "not-a-sweep-boundary"))
                for ee in entry_eas:
                    if not (gap_start < ee < stop_pos):
                        continue
                    if ee in acc:
                        seeds_ok.append(ee)
                    elif inside(ee):
                        seeds_rej.append((ee, "entry: no-terminator-before"))
                    else:
                        seeds_rej.append((ee, "entry: not-a-sweep-boundary"))
                starts = sorted(set(seeds_ok))
                # greedy partition: never leave a hole -- if a piece would be
                # smaller than MIN_FN, drop the *next* start instead (merge
                # forward), so [gap_start, stop_pos) stays fully tiled
                pieces = []
                if starts and stop_pos > starts[0]:
                    cur_s = starts[0]
                    for s in starts[1:]:
                        if s - cur_s >= MIN_FN:
                            pieces.append((cur_s, s))
                            cur_s = s
                        else:
                            seeds_rej.append((s, "resulting-fn-too-small"))
                    if stop_pos - cur_s >= MIN_FN:
                        pieces.append((cur_s, stop_pos))
                    else:
                        if cur_s != starts[0]:
                            seeds_rej.append((cur_s, "resulting-fn-too-small"))
                        if stop_pos > cur_s:
                            uncovered.append({"lo": cur_s, "hi": stop_pos,
                                              "why": "piece-smaller-than-%d" % MIN_FN,
                                              "block": sc["name"]})
                # emission evidence: a piece must contain a real seed beyond its
                # own start, or include an instruction IDA already decoded as
                # code -- pure fresh decode of undefined bytes is never enough
                seedset = set(seeds_ok) - {gap_start}
                dst_eas_all = [d["ea"] for d in dst_in]

                def closed(s, e):
                    """the sweep's last instruction ENDS exactly at e and is a
                    terminator (the chain closed at an authoritative boundary)"""
                    return any(ea + n == e and term
                               for (ea, n, _m, term, _s, _p) in insns)

                fns = []
                for (s, e) in pieces:
                    has_seed = any(s <= x < e for x in seedset)
                    has_ida = any(s <= ea < e and src == "ida"
                                  for (ea, _n, _m, _t, src, _p) in insns)
                    # a first piece that starts at a keep/hole/range boundary
                    # and whose chain closes on a terminator is also evidence
                    chain = (s == gap_start and closed(s, e))
                    # an interior reference (rejected as a start, but INSIDE
                    # the piece) still proves somebody calls/jumps into code
                    has_ref = any(s <= x < e for x in dst_eas_all)
                    if has_seed or has_ida or chain or has_ref:
                        fns.append({"key": "sub_%X" % s, "ea": s, "size": e - s})
                    else:
                        seeds_rej.append((s, "no-evidence-fresh-decode-only"))
                        uncovered.append({"lo": s, "hi": e, "why": "no-evidence",
                                          "block": sc["name"]})
                gap_res.append({"a": a, "b": b, "covered_to": stop_pos,
                                "stop": stop, "insns": len(insns),
                                "seeds_ok": len(starts),
                                "seeds_rej": seeds_rej[:40],
                                "n_rej": len(seeds_rej), "fns": fns})
                stats["seeds_ok"] += len(starts)
                stats["seeds_rej"] += len(seeds_rej)
                new_fns.extend(fns)

            # contiguous covered ranges: [lo,hi) minus uncovered
            cov, cur = [], lo
            for u in sorted(uncovered, key=lambda x: x["lo"]):
                if u["lo"] > cur:
                    cov.append((cur, u["lo"]))
                cur = max(cur, u["hi"])
            if cur < hi:
                cov.append((cur, hi))
            for (rl, rh) in cov:
                ks = [f for f in keep if rl <= f["ea"] and f["ea"] + f["size"] <= rh]
                hs = [h for h in holes if rl <= h["lo"] and h["hi"] <= rh]
                ns = [f for f in new_fns if rl <= f["ea"] and f["ea"] + f["size"] <= rh]
                for h in hs:
                    raw = idc.get_bytes(h["lo"], h["size"])
                    h["sha256"] = (hashlib.sha256(raw).hexdigest()
                                    if raw and len(raw) == h["size"] else None)
                    h["in_function"] = bool(
                        ida_funcs.get_func(h["lo"]) or ida_funcs.get_func(h["hi"] - 1))
                    h["is_data"] = bool(ida_bytes.is_data(
                        ida_bytes.get_flags(h["lo"])))
                out_ranges.append({"name": sc["name"], "range": [rl, rh],
                                   "keep_fns": ks, "holes_in_range": hs,
                                   "new_fns": ns, "gap_res": [
                                       g for g in gap_res
                                       if rl <= g["a"] and g["covered_to"] <= rh]})
            # ---- stage 2: self-contained seed chains for dsts the gap sweep
            # could not reach (block ii's 38 dsts live beyond an undecodable
            # byte).  Evidence per chain: a terminator BEHIND the seed (the
            # finding-59 rule) and the chain closing on a terminator, bounded
            # to 4 KB, never overlapping a covered range / keep fn / hole.
            taken = [(rl, rh) for (rl, rh) in cov]
            taken += [(f["ea"], f["ea"] + f["size"]) for f in keep]
            taken += [(h["lo"], h["hi"]) for h in holes]
            planned = [(f["ea"], f["ea"] + f["size"]) for f in new_fns]

            def overlaps(a2, b2):
                return any(a2 < y and x < b2 for x, y in taken + planned)

            def prev_term_ok(ea):
                ph = ida_bytes.get_item_head(ea - 1) if ea else None
                if ph is not None and ida_bytes.is_code(ida_bytes.get_flags(ph)):
                    if ph + ida_bytes.get_item_size(ph) == ea and \
                            is_term_mnem(mnem_at(ph)):
                        return True
                for back in range(1, 7):
                    c = ea - back
                    if c < 0:
                        break
                    insn = ida_ua.insn_t()
                    n = ida_ua.decode_insn(insn, c)
                    if n > 0 and c + n == ea:
                        if is_term_mnem((insn.get_canon_mnem() or "").lower()):
                            return True
                return False

            stage2, stage2_rej = [], []
            for d in dst_in:
                ea = d["ea"]
                if any(s <= ea < e for s, e in taken + planned):
                    continue
                if any(h["lo"] <= ea < h["hi"] for h in holes):
                    continue
                h = ida_bytes.get_item_head(ea)
                if h != ea and ida_bytes.is_head(ida_bytes.get_flags(h)):
                    stage2_rej.append((ea, "inside-existing-item"))
                    continue
                if not prev_term_ok(ea):
                    stage2_rej.append((ea, "no-terminator-behind"))
                    continue
                ins, stop, stop_pos, lead = sweep_gap(ea, min(ea + 4096, hi),
                                                      hole_lo_set)
                if lead:
                    stage2_rej.append((ea, "lead-padding-at-seed"))
                elif not ins or ins[0][0] != ea:
                    stage2_rej.append((ea, "chain-would-not-start"))
                elif not ins[-1][3]:
                    stage2_rej.append((ea, "chain-open@0x%X" % stop_pos))
                elif stop_pos - ea < MIN_FN:
                    stage2_rej.append((ea, "chain-too-short"))
                elif overlaps(ea, stop_pos):
                    stage2_rej.append((ea, "overlaps-planned"))
                else:
                    stage2.append({"key": "sub_%X" % ea, "ea": ea,
                                   "size": stop_pos - ea})
                    taken.append((ea, stop_pos))
            for f in stage2:
                out_ranges.append({
                    "name": "seed_0x%X" % f["ea"],
                    "range": [f["ea"], f["ea"] + f["size"]],
                    "keep_fns": [], "holes_in_range": [], "new_fns": [f],
                    "gap_res": [{"a": f["ea"], "b": f["ea"] + f["size"],
                                 "covered_to": f["ea"] + f["size"],
                                 "stop": "stage2-closed", "insns": 0,
                                 "seeds_ok": 1, "seeds_rej": [], "n_rej": 0,
                                 "fns": [f]}]})
            stats["stage2_ok"] = len(stage2)
            stats["stage2_rej"] = len(stage2_rej)
            uncovered_all.extend(uncovered)
            all_stats[sc["name"]] = dict(insns=stats["insns"],
                                         seeds_ok=stats["seeds_ok"],
                                         seeds_rej=stats["seeds_rej"],
                                         stops={k: v for k, v in
                                                stats["stops"].most_common()},
                                         gaps=len(gaps),
                                         covered_b=sum(e - s for s, e in cov),
                                         scope_b=hi - lo,
                                         stage2=stats.get("stage2_ok", 0),
                                         stage2_rej=stats.get("stage2_rej", 0),
                                         stage2_why=dict(Counter(
                                             r for _e, r in stage2_rej)))
        if not suspect_this:
            break
        log.append("attempt %d: dropping suspect holes %s"
                   % (attempt + 1, [hex(h) for h in sorted(suspect_this)]))
        suspect_holes |= suspect_this

    # live hashes for EVERY candidate hole from tools/map_upper.py (68 of them,
    # 6,278 B) so UI strings stay pinned even outside the registered ranges
    all_holes = []
    for h in up["holes"]:
        raw = idc.get_bytes(h["lo"], h["size"])
        all_holes.append({
            "ea": h["lo"], "size": h["size"], "block": h.get("block"),
            "why": (h.get("why") or "")[:160],
            "sha256": (hashlib.sha256(raw).hexdigest()
                       if raw and len(raw) == h["size"] else None),
            "in_function": bool(ida_funcs.get_func(h["lo"])
                                or ida_funcs.get_func(h["hi"] - 1)),
            "is_data": bool(ida_bytes.is_data(ida_bytes.get_flags(h["lo"]))),
        })
    spans_r = [(r["range"][0], r["range"][1]) for r in out_ranges]
    standalone = [h for h in all_holes
                  if not any(lo <= h["ea"] < hi for lo, hi in spans_r)]
    log.append("all candidate holes hashed live: %d (%d B), standalone(out of "
               "any range): %d" % (len(all_holes),
                                   sum(h["size"] for h in all_holes),
                                   len(standalone)))
    json.dump({"scope": SCOPE, "ranges": out_ranges,
               "uncovered": uncovered_all, "suspect_holes": sorted(suspect_holes),
               "all_holes": all_holes, "standalone_holes": standalone,
               "stats": all_stats}, open(OUT, "w"))

    log.append("scope blocks: %d   covered ranges emitted: %d"
               % (len(SCOPE), len(out_ranges)))
    tot_ins = 0
    for name, s in all_stats.items():
        tot_ins += s["insns"]
        log.append("  %-12s scope %6d B  covered %6d B  gaps %3d  insns %5d  "
                   "seeds ok %3d / rej %3d  stage2 %2d/%2d  stops %s"
                   % (name, s["scope_b"], s["covered_b"], s["gaps"], s["insns"],
                      s["seeds_ok"], s["seeds_rej"], s.get("stage2", 0),
                      s.get("stage2_rej", 0), s["stops"]))
    log.append("total instructions walked: %d" % tot_ins)
    log.append("uncovered spans: %d (%d B)"
               % (len(uncovered_all), sum(u["hi"] - u["lo"] for u in uncovered_all)))
    log.append("suspect holes dropped: %s" % [hex(h) for h in sorted(suspect_holes)])
    n_fn = sum(len(r["new_fns"]) for r in out_ranges)
    n_h = sum(len(r["holes_in_range"]) for r in out_ranges)
    n_k = sum(len(r["keep_fns"]) for r in out_ranges)
    s2r = Counter()
    for _n, s in all_stats.items():
        for k2, v2 in s.get("stage2_why", {}).items():
            s2r[k2] += v2
    log.append("stage2 rejected by reason: %s" % dict(s2r.most_common()))
    log.append("plan: ranges=%d  new_fns=%d  keep=%d  holes_in_range=%d"
               % (len(out_ranges), n_fn, n_k, n_h))
    log.append("wrote " + OUT)


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
