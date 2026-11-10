#!/usr/bin/env python3
"""Plan the live-IDB function-table repairs that precede the integrity re-baseline (finding 124).

The repaired canonical IDB is the source of truth; these fixes remove the defects the S1 audit found in
it (not differences from the old function_bytes.json):

  * 18 orphan alias chunks: wrong-variant far targets that IDA attached as tails of thunks and of the
    R27/R28/3F70s copies (R05 0x2E1xx, R06/R30 0x6CD9x, R14 0x6E7xx/0x6E8Bx, R29_1E19s 0x11DCxx..)
    -> remove_func_tail (the items stay as they are);
  * 10 thunk entry chunks: the correct-variant overlay entry absorbed as a tail of its RTLink thunk
    slot -> removed from the thunk and registered as its own function (8 functions, 2 with a tail);
  * 0x11DA04: one `enter 1Ch .. leave/retf` routine split at the fall-in 0x11DC2A and interleaved with
    R29 alias tails -> delete the fall-in fragment, drop its own tail, extend it to 0x11E1AB;
  * 0x6DE83 r06_trig_accum_6de83 ends mid-body at 0x6DF27 (finding 64 turned the rest into a hole)
    -> extend to its retf (0x6DFCB);
  * 0x15AFD: the switch body 0x15BEB..0x15EAB between its two chunks has no function -> one chunk;
  * sprite_clip_bounds_check (0x2E20A) flows into 0x2E292..0x2E2D0, owned by the R28 copy 0x4E14C as
    an alias tail -> attach to 0x2E20A;
  * 0x161945 (far jmp target from thunk 0x2C487): first byte undefined, no function -> create both;
  * 0x6CD90..0x6CDA8: the R06 word table at seg base+0 (data hole of finding 64), partly decoded as
    alias-tail code -> bytes again;
  * thunk 0x2C969 (rec 67, 669F:173F) far cref resolved into R30 (0x6812F) -> R67_569Fs 0x1AA05F.

Two steps (host side; the probe is read-only):
  python tools/plan_rebase_fixes.py probe-in      -> analysis/s1/chunks_probe_in.json
  idat -A -S"analysis/s1/chunks_probe.py" <copy of the IDB>
  python tools/plan_rebase_fixes.py plan          -> registry/rebase_fixes_expected.json
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "analysis/s1/xseg_tails_draft.json"
PROBE_IN = ROOT / "analysis/s1/chunks_probe_in.json"
PROBE = ROOT / "analysis/s1/chunks_probe.json"
OUT = ROOT / "registry/rebase_fixes_expected.json"

FALLIN = {"keep": 0x11DA04, "drop": 0x11DC2A, "own_tails": [[0x11E0A9, 0x11E1A7], [0x11E1A7, 0x11E1AB]],
          "end": 0x11E1AB}
SET_ENDS = [{"ea": 0x6DE83, "end": 0x6DFCB, "why": "body continues to its retf at 0x6DFCA (finding 64 hole)"},
            {"ea": 0x15AFD, "end": 0x15EC2, "why": "switch body 0x15BEB..0x15EAB reached only by its jmp 0x15B15",
             "own_tail": [0x15EAB, 0x15EC2]}]
APPEND = [{"owner": 0x2E20A, "lo": 0x2E292, "hi": 0x2E296}, {"owner": 0x2E20A, "lo": 0x2E297, "hi": 0x2E2D0}]
NEW_FUNC = {"ea": 0x161945, "end": 0x161978, "create_insn": True, "tails": [],
            "why": "far jmp target of thunk 0x2C487; push bp .. retf"}
TO_DATA = {"ea": 0x6CD90, "size": 24, "why": "R06 word table at seg base+0 (call cs:[bx+10h] at 0x6CDA8)"}
CREF = {"ea": 0x2C96C, "type": 18, "drop": 0x6812F, "to": 0x1AA05F,
        "why": "thunk 0x2C969 rec 67 669F:173F -> R67_569Fs+0x173F (was R30)"}


def norm(chunks):
    out = []
    for lo, hi in sorted(chunks):
        if out and out[-1][1] == lo:
            out[-1][1] = hi
        else:
            out.append([lo, hi])
    return out


def draft():
    return json.loads(DRAFT.read_text())


def probe_in():
    d = draft()
    funcs = {t["owner"] for t in d} | {FALLIN["keep"], FALLIN["drop"], NEW_FUNC["ea"], APPEND[0]["owner"],
                                        CREF["drop"], CREF["to"]} | {s["ea"] for s in SET_ENDS}
    funcs |= {t["lo"] for t in d if t["action"] == "entry"}
    ranges = [[FALLIN["keep"], FALLIN["end"]], [NEW_FUNC["ea"], NEW_FUNC["end"]],
              [TO_DATA["ea"], TO_DATA["ea"] + TO_DATA["size"]]]
    ranges += [[t["lo"], t["hi"]] for t in d if t["action"] != "orphan"]
    ranges += [[a["lo"], a["hi"]] for a in APPEND]
    ranges += [[0x6DF27, 0x6DFCB], [0x15BEB, 0x15EAB]]          # SET_ENDS growth
    PROBE_IN.write_text(json.dumps({"funcs": sorted(funcs), "ranges": ranges}))
    print("wrote %s: %d funcs, %d ranges" % (PROBE_IN, len(funcs), len(ranges)))


def plan():
    d = draft()
    pr = json.loads(PROBE.read_text())
    if "error" in pr:
        sys.exit("probe error: " + pr["error"])
    chunks = {int(k): v for k, v in pr["funcs"].items()}
    ranges = {int(k): v for k, v in pr["ranges"].items()}
    errs = []

    def need_func(ea):
        if not chunks.get(ea):
            errs.append("no function at 0x%X" % ea)
            return []
        return chunks[ea]

    before = {}
    after = {}

    def touch(ea):
        if ea not in before:
            before[ea] = sorted(need_func(ea))
            after[ea] = [list(c) for c in before[ea]]
        return after[ea]

    remove_tails, add_funcs, freed = [], [], {}
    for t in d:
        if t["action"] == "entry_chunk":
            continue
        remove_tails.append({"owner": t["owner"], "lo": t["lo"], "hi": t["hi"], "seg": t["seg"], "kind": t["action"]})
        if t["action"] == "entry":
            tails = [[c["lo"], c["hi"]] for c in d if c["action"] == "entry_chunk" and c["owner"] == t["owner"]]
            for lo, hi in tails:
                remove_tails.append({"owner": t["owner"], "lo": lo, "hi": hi, "seg": t["seg"], "kind": "entry_chunk"})
            add_funcs.append({"ea": t["lo"], "end": t["hi"], "create_insn": False, "tails": tails,
                              "why": "overlay entry of thunk 0x%X (%s)" % (t["owner"], t["seg"])})
    for lo, hi in FALLIN["own_tails"]:
        remove_tails.append({"owner": FALLIN["keep"], "lo": lo, "hi": hi, "seg": "R29_1E19s", "kind": "own_tail"})
    for s in SET_ENDS:
        if "own_tail" in s:
            remove_tails.append({"owner": s["ea"], "lo": s["own_tail"][0], "hi": s["own_tail"][1],
                                 "seg": "", "kind": "own_tail"})
    add_funcs.append(NEW_FUNC)

    for r in remove_tails:
        a = touch(r["owner"])
        if [r["lo"], r["hi"]] not in a or r["lo"] == r["owner"]:
            errs.append("0x%X has no tail chunk 0x%X..0x%X (chunks %s)" % (r["owner"], r["lo"], r["hi"], a))
        else:
            a.remove([r["lo"], r["hi"]])
            freed[r["lo"]] = r["hi"]
    if chunks.get(FALLIN["drop"]) is None:
        errs.append("fall-in fragment 0x%X missing" % FALLIN["drop"])
    del_funcs = [{"ea": FALLIN["drop"], "chunks": chunks.get(FALLIN["drop"]),
                  "why": "fall-in of 0x%X (only inref: flow from 0x11DC25)" % FALLIN["keep"]}]
    set_ends = [{"ea": FALLIN["keep"], "end": FALLIN["end"],
                 "why": "enter 1Ch at 0x11DA04 .. leave/retf at 0x11E1A9, one routine"}] + \
               [{"ea": s["ea"], "end": s["end"], "why": s["why"]} for s in SET_ENDS]
    for s in set_ends:
        a = touch(s["ea"])
        main = [c for c in a if c[0] == s["ea"]]
        if not main:
            continue
        s["before_end"] = main[0][1]
        main[0][1] = s["end"]
        if any(c is not main[0] and c[0] < s["end"] and c[1] > s["ea"] for c in a):
            errs.append("extending 0x%X to 0x%X overlaps its own chunks %s" % (s["ea"], s["end"], a))
        after[s["ea"]] = norm(a)
    for ap in APPEND:
        a = touch(ap["owner"])
        a.append([ap["lo"], ap["hi"]])
        after[ap["owner"]] = norm(a)
    for f in add_funcs:
        if chunks.get(f["ea"]) is not None:
            errs.append("0x%X is already a function start" % f["ea"])
        before[f["ea"]] = None
        after[f["ea"]] = norm([[f["ea"], f["end"]]] + f["tails"])
    before[FALLIN["drop"]] = sorted(chunks.get(FALLIN["drop"]) or [])
    after[FALLIN["drop"]] = None
    for k in after:
        if after[k] is not None:
            after[k] = norm(after[k])

    # every byte a function will newly cover must be code owned by nobody, or by a chunk this plan frees
    dropped = set(c[0] for c in (chunks.get(FALLIN["drop"]) or []))
    gained = []
    for ea, a in after.items():
        if a is None:
            continue
        old = before.get(ea) or []
        for lo, hi in a:
            gained.append((ea, lo, hi, old))
    owner_of = {}
    for t in remove_tails:
        owner_of[(t["lo"], t["hi"])] = t["owner"]
    rows_all = [r for rows in ranges.values() for r in rows]
    for fea, lo, hi, old in gained:
        for h, cls, sz, fn in rows_all:
            if not (lo <= h < hi) or any(o_lo <= h < o_hi for o_lo, o_hi in old):
                continue
            if cls != "C" and not (fea == NEW_FUNC["ea"] and h == NEW_FUNC["ea"]):
                errs.append("0x%X (for 0x%X) is %s, not code" % (h, fea, cls))
            if fn is not None and fn != fea:
                ok = fn == FALLIN["drop"] or any(t_lo <= h < t_hi and o == fn for (t_lo, t_hi), o in owner_of.items())
                if not ok:
                    errs.append("0x%X (for 0x%X) is owned by 0x%X, not freed by the plan" % (h, fea, fn))
    for lo, hi in [[f["ea"], f["end"]] for f in add_funcs] + [[a["lo"], a["hi"]] for a in APPEND]:
        if lo not in ranges:
            errs.append("range 0x%X..0x%X was not probed" % (lo, hi))
    td = ranges.get(TO_DATA["ea"], [])
    for h, cls, sz, fn in td:
        if fn is not None and not any(t_lo <= h < t_hi for t_lo, t_hi in owner_of):
            errs.append("to_data head 0x%X owned by 0x%X, not freed by the plan" % (h, fn))
    if errs:
        for e in errs:
            print("  " + e)
        sys.exit("plan FAILED: %d problems" % len(errs))
    doc = {
        "finding": 124,
        "step": "S1c live-IDB function-table repairs before the integrity re-baseline",
        "remove_tails": remove_tails,
        "del_funcs": del_funcs,
        "set_ends": set_ends,
        "append_tails": APPEND,
        "add_funcs": add_funcs,
        "to_data": [dict(TO_DATA, sha256="cc7cc411e8f8259f494a13f4b2d67438c3177c6cb61e56bdd83e9e335499c0a9")],
        "crefs": [CREF],
        "funcs_before": {"%X" % k: v for k, v in sorted(before.items())},
        "funcs_after": {"%X" % k: v for k, v in sorted(after.items())},
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print("wrote %s: %d tail removals, %d deleted, %d ends, %d appends, %d new functions, %d to_data, %d crefs; "
          "%d functions touched" % (OUT, len(remove_tails), len(del_funcs), len(set_ends), len(APPEND),
                                    len(add_funcs), 1, 1, len(after)))


if __name__ == "__main__":
    {"probe-in": probe_in, "plan": plan}[sys.argv[1]]()
