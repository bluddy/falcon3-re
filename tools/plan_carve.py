"""Finding 59 step 1c (host, read-only): turn the seed tests into an exact,
inspectable carve plan -> registry/subblock_split_expected.json.

Boundary rule (finding 58/59, evidence-based):
  accept an address as a function start iff
    (1) it is the blob start (0x2E2F0),
    (2) it is a data-hole END (code resumes where data stops), or
    (3) it is a sub-block ANCHOR that is not the start of a hole (module
        boundary -- those are preceded by padding after a terminator, which
        the backward sweep cannot see as a terminator landing on the address), or
    (4) an instruction DECODES TO END EXACTLY there and is a flow terminator
        (retn/retf/ret/iret/jmp) -- the terminator-backwards rule.

Everything else stays interior of its block (e.g. 0x2E380, which sits 5 bytes
into the prologue that starts at 0x2E37B -- finding 42's "MID target").

The manifest also pins, per old key: the old span + sha256, every data hole
(ea/size/sha256/why) and every planned new function (key/ea/size).  It is
written BEFORE any mutation, so the mutator is a dumb applier: if reality
differs from this file, it does not save.

Usage: venv\\Scripts\\python tools\\plan_carve.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

IDA = Path("analysis/ida_falconcd")
OUT = Path("registry/subblock_split_expected.json")
LO, HI = 0x2E2F0, 0x3ACAC
PARENT = "sub_2E2F0"
MIN_FN = 4


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git_json(path):
    r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, text=True)
    if r.returncode != 0:
        print("FATAL: cannot read HEAD:" + path)
        sys.exit(2)
    return json.loads(r.stdout)


seeds = json.loads((IDA / "carve_seeds.json").read_text())["seeds"]
tests = json.loads((IDA / "seed_tests.json").read_text())["tests"]
amap = json.loads((IDA / "sub2e2f0_map.json").read_text())
holes = [(h["lo"], h["hi"], h["size"]) for h in amap["holes"]]
anchors = sorted(int(k, 16) for k in amap["anchors"] if LO <= int(k, 16) < HI)

old = git_json("analysis/ida_falconcd/function_bytes.json")[PARENT]
assert old["ea"] == LO and old["size"] == HI - LO, old
old_bytes = bytes.fromhex(old["bytes"])

hole_starts = {h[0] for h in holes}
hole_ends = {h[1] for h in holes}
forced = {LO} | hole_ends | {a for a in anchors if a not in hole_starts}

accepted, rejected, reasons = set(), set(), {}
for ea in seeds:
    if ea in forced:
        accepted.add(ea)
        reasons[ea] = "forced"
        continue
    r = tests.get("0x%X" % ea)
    if r and any(p["term"] for p in r["prev"]):
        accepted.add(ea)
        reasons[ea] = "terminator:" + next(p["mnem"] for p in r["prev"] if p["term"])
    else:
        rejected.add(ea)
        reasons[ea] = ("nothing-lands" if r and not r["prev"]
                       else "no-terminator" if r else "untested")

starts = sorted(a for a in accepted if not any(lo <= a < hi for lo, hi, _ in holes))

# ---- boundary sanity vs the EXISTING decode (carve_probe.json) --------------
# An existing instruction crossing a planned boundary means one of two things:
#   * the crossing item is zero padding (the sweep turned `00 00...` before a
#     module boundary into `add`) -> boundary is right, delete that item;
#   * the crossing item is a REAL instruction (first byte != 0) -> the boundary
#     sits inside code, so the seed was a backward-decode artefact and must be
#     dropped (the merge keeps the tiling exact).
# Hole edges are always authoritative (the table really starts there).
probe_path = IDA / "carve_probe.json"
dropped, deleted_items = [], []
if probe_path.exists():
    probe = json.loads(probe_path.read_text())
    cross_at = {}
    for r in probe.get("fns", []):
        for which, edge in (("start", r["ea"]), ("end", r["ea"] + r["size"])):
            st = r[which]
            if st.get("crosses"):
                cross_at.setdefault(edge, st["head"])
    base = old["ea"]

    def first_byte(head):
        o = head - base
        return old_bytes[o] if 0 <= o < len(old_bytes) else None

    for edge, head in sorted(cross_at.items()):
        b0 = first_byte(head)
        at_hole = any(lo == edge or hi == edge for lo, hi, _n in holes)
        if at_hole or b0 == 0:
            deleted_items.append((head, edge, b0))
            continue
        if edge in starts:
            starts.remove(edge)
            dropped.append((edge, head, b0))
            reasons[edge] = ("dropped: existing instruction at 0x%X starts "
                             "with %02X and crosses this boundary"
                             % (head, b0 if b0 is not None else 0))
        else:
            dropped.append((edge, head, b0))
            reasons[edge] = "dropped(end): existing instruction at 0x%X crosses it" % head
print("boundary sanity: %d crossing items -> %d padding/data (deleted later), "
      "%d real instructions (seed dropped)"
      % (len(cross_at), len(deleted_items), len(dropped)))
for edge, head, b0 in dropped:
    print("   DROPPED seed 0x%X: existing instruction at 0x%X starts with %02X"
          % (edge, head, b0 if b0 is not None else 0))

# ---- build pieces: walk the cut points, skipping the holes ------------------
points = sorted(set([LO] + starts + [h[0] for h in holes] +
                    [h[1] for h in holes] + [HI]))
fns, cur, holes_used = [], LO, []
for p in points:
    if p < cur:
        continue
    if any(lo == p for lo, _hi, _n in holes):          # data hole starts here
        if cur < p:
            fns.append((cur, p))
        _lo, hi_h, _n = next(h for h in holes if h[0] == p)
        holes_used.append((p, hi_h))
        cur = hi_h
        continue
    if cur < p:
        fns.append((cur, p))
    cur = p
assert cur == HI, hex(cur)

# ---- validation -------------------------------------------------------------
covered = sum(e - s for s, e in fns)
hole_bytes = sum(h[2] for h in holes)
problems = []
if covered + hole_bytes != HI - LO:
    problems.append("coverage %d + holes %d != %d" % (covered, hole_bytes, HI - LO))
for s, e in fns:
    if e - s < MIN_FN:
        problems.append("fn 0x%X..0x%X is %dB (<%d)" % (s, e, e - s, MIN_FN))
for lo, hi in holes_used:
    for s, e in fns:
        if s < hi and lo < e:
            problems.append("fn 0x%X..0x%X overlaps hole 0x%X..0x%X" % (s, e, lo, hi))
# every accepted start must be a function start (except ones swallowed by holes)
for a in starts:
    if any(lo <= a < hi for lo, hi, _n in holes):
        continue
    if a not in {s for s, _e in fns}:
        problems.append("accepted start 0x%X is not a function start" % a)

dsts = set(amap["in_blob"].get("ext_call", [])) | set(amap["in_blob"].get("thunk", []))
f_starts = {s for s, _e in fns}
in_hole = [d for d in amap["in_blob"].get("internal", [])
           if any(lo <= d < hi for lo, hi, _n in holes)]
at_start = sum(1 for d in amap["in_blob"].get("internal", []) if d in f_starts)

print("seeds              : %d  (forced %d, terminator %d, rejected %d)"
      % (len(seeds), sum(1 for e in reasons.values() if e == "forced"),
         sum(1 for e in reasons.values() if e.startswith("terminator")),
         len(rejected)))
rcount = {}
for v in reasons.values():
    rcount[v.split(":")[0]] = rcount.get(v.split(":")[0], 0) + 1
print("boundary reasons   : ", rcount)
print("functions planned  : %d   (+%d holes = %d pieces)"
      % (len(fns), len(holes_used), len(fns) + len(holes_used)))
print("smallest / largest : %d B / %d B   total code %d B + data %d B"
      % (min(e - s for s, e in fns), max(e - s for s, e in fns), covered, hole_bytes))
print("coverage           : %s" % ("EXACT" if not problems else "PROBLEMS"))
for p in problems[:10]:
    print("   !", p)
print("of the 568 internal ref destinations: %d land on a new function start, "
      "%d inside a hole" % (at_start, len(in_hole)))
print("rejected seeds stay interior (interior -> not a boundary): %d"
      % len(rejected))

if problems:
    print("\nNOT WRITING the manifest until the plan validates")
    sys.exit(1)

entry = {
    "key": PARENT,
    "ea": LO,
    "old_size": HI - LO,
    "old_sha256": sha(old_bytes),
    "reason": ("finding 59 carve of the 51,644 B blob: boundaries from the "
               "terminator-backwards rule over the 372 verified seeds, plus "
               "forced module anchors and data-hole ends."),
    "seeds_total": len(seeds),
    "seeds_accepted": len(accepted),
    "seeds_rejected": len(rejected),
    "data_holes": [
        {"ea": lo, "size": n, "sha256": sha(old_bytes[lo - LO:lo - LO + n]),
         "why": why}
        for (lo, _hi, n), why in zip(
            holes,
            ["object-name table (OBJECTS / FalcObj.Bin / FSXObj.Bin)",
             "RTLink module-name table (global.amo / local.amo / harpoon.dat / "
             "FALCONCOLORADO) -- anchor 0x2F640 with 1,442 fixups",
             "2-byte alignment pad before code at 0x3AB92"])],
    "new_fns": [{"key": "sub_%X" % s, "ea": s, "size": e - s} for s, e in fns],
}
manifest = {"schema": 1, "splits": [entry]}
OUT.write_text(json.dumps(manifest, indent=1))
print("\nwrote %s  (%d functions, %d holes)"
      % (OUT, len(entry["new_fns"]), len(entry["data_holes"])))
print("first pieces:", ", ".join("0x%X:%dB" % (f["ea"], f["size"])
                                 for f in entry["new_fns"][:5]))
print("rejected seeds (interior):", ", ".join("0x%X" % x for x in sorted(rejected)[:12]),
      "..." if len(rejected) > 12 else "")
