"""Finding 58 part 2 (host, read-only): map the true structure inside
`sub_2E2F0` (0x2E2F0..0x3ACAC) and the R05 upper half, BEFORE any split.

Sources
  * fixup tables straight from FALCONCD.EXE (same location logic as
    tools/_size57.py)  -> the sub-block paragraph anchors
      abs_off = (seg - w0)*16 + off,  anchor = ida_ea + (seg - w0)*16
  * analysis/ida_falconcd/callgraph_refs.json -> entry evidence: which
    addresses inside the blob are CALLed (is_call) / JMPed to, and whether the
    source is a thunk slot, the blob itself, or another function
  * function_bytes.json sub_2E2F0 -> the exact IDB bytes for string/data runs

Writes analysis/ida_falconcd/sub2e2f0_map.json and prints a partition map.

Usage: venv\\Scripts\\python tools/map_sub2e2f0.py
"""
import json
import struct
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
DIR = 0x1E24F
IDA = Path("analysis/ida_falconcd")
LO, HI = 0x2E2F0, 0x3ACAC          # sub_2E2F0
R05_LO, R05_HI = 0x2E100, 0x669F0  # R05_1E10 segment
THUNK_LO, THUNK_HI = 0x2BD9D, 0x2C973

place = {p["idx"]: p for p in json.loads((IDA / "overlay_placement.json").read_text())}
fb = json.loads((IDA / "function_bytes.json").read_text())
cls = json.loads((IDA / "classification.json").read_text())
refs = json.loads((IDA / "callgraph_refs.json").read_text())["refs"]

ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())
starts = [x[0] for x in ivs]


def owner(ea):
    i = bisect_right(starts, ea) - 1
    return ivs[i][2] if i >= 0 and ivs[i][0] <= ea < ivs[i][1] else None


# ---------------- 1. sub-block anchors straight from the fixup tables ----------
anchors = defaultdict(lambda: {"n_fixups": 0, "idxs": set(), "segs": set()})
pairs_in_range = 0
for idx in sorted(place):
    p = place[idx]
    if p.get("addr") == "skip" or not p.get("data_file") or not p.get("ida_len"):
        continue
    o = DIR + idx * 18
    if o + 18 > len(EXE):
        continue
    w0, _w1, w2, _w3, span, nfx, _w6, _idf, _ds = struct.unpack_from("<9H", EXE, o)
    if idx == 69:
        tpos = 0xFFFA0 + (w2 << 4) + 0x60
    elif 50 <= idx <= 68:
        tpos = 0xFFFA0 + (w2 << 4)
    elif w2 >= 0x1000:
        tpos = w2 << 4
    else:
        continue
    if tpos + nfx * 4 > len(EXE):
        continue
    arena = set(range(w0, w0 + max(1, span))) | {0x1D0D, 0x1D31}
    for k in range(nfx):
        off, seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
        if seg not in arena:
            continue
        abs_off = (seg - w0) * 16 + off
        if not (0 <= abs_off + 2 <= p["ida_len"]):
            continue
        anchor = p["ida_ea"] + (seg - w0) * 16
        if not (R05_LO <= anchor < R05_HI):
            continue
        pairs_in_range += 1
        a = anchors[anchor]
        a["n_fixups"] += 1
        a["idxs"].add(idx)
        a["segs"].add(seg)

anch_in = sorted(a for a in anchors if LO <= a < HI)
anch_up = sorted(a for a in anchors if HI <= a < R05_HI)
print("== sub-block paragraph anchors in R05_1E10 ==")
print("   distinct anchors: %d total   in sub_2E2F0 (0x%X..0x%X): %d   "
      "in upper half (0x%X..0x%X): %d"
      % (len(anchors), LO, HI, len(anch_in), HI, R05_HI, len(anch_up)))
print("   fixup pairs landing in the segment: %d" % pairs_in_range)
print("\n   anchors inside sub_2E2F0 (address, fixups at this anchor, seg ids):")
for a in anch_in:
    print("      0x%-6X  fixups=%-5d  seg=%s  rec=%s"
          % (a, anchors[a]["n_fixups"], sorted(anchors[a]["segs"]),
             sorted(anchors[a]["idxs"])))

# ---------------- 2. entry evidence: who points into the blob -----------------
in_blob = [r for r in refs if LO <= r[1] < HI]


def src_kind(s):
    if THUNK_LO <= s < THUNK_HI:
        return "thunk"
    k = owner(s)
    if k == "sub_2E2F0":
        return "inside-blob"
    return "function:" + k if k else "outside-every-fn"


buckets = Counter()
per_dst = defaultdict(lambda: Counter())
for s, d, c in in_blob:
    kind = src_kind(s)
    key = ("%s/%s" % ("CALL" if c else "JMP", kind.split(":")[0]))
    buckets[key] += 1
    per_dst[d][key] += 1

print("\n== refs landing inside sub_2E2F0 ==")
print("   total refs: %d   distinct destination addresses: %d"
      % (len(in_blob), len(per_dst)))
for k, v in buckets.most_common():
    print("      %-24s %5d" % (k, v))
ext_call = sorted(d for d, cc in per_dst.items()
                  if any(k.startswith("CALL/function") for k in cc))
thunk_t = sorted(d for d, cc in per_dst.items() if any("thunk" in k for k in cc))
internal = sorted(d for d, cc in per_dst.items()
                  if any("inside-blob" in k for k in cc))
print("   distinct addresses CALLED from another function : %d" % len(ext_call))
print("   distinct addresses reached via a thunk slot     : %d" % len(thunk_t))
print("   distinct addresses branched/called from INSIDE  : %d" % len(internal))
print("   how many of those sit at a function start        : %d"
      % sum(1 for d in per_dst if owner(d) == "sub_2E2F0" and
            fb["sub_2E2F0"]["ea"] == d))

# ---------------- 3. data regions inside the blob ----------------------------
blob = bytes.fromhex(fb["sub_2E2F0"]["bytes"])
base = fb["sub_2E2F0"]["ea"]
print("\n== data / string runs inside sub_2E2F0 (len=%d, 0x%X..0x%X) =="
      % (len(blob), base, base + len(blob)))
runs = []
i = 0
while i < len(blob):
    if 0x20 <= blob[i] < 0x7F:
        j = i
        while j < len(blob) and 0x20 <= blob[j] < 0x7F:
            j += 1
        if j - i >= 5 and (j == len(blob) or blob[j] == 0):
            runs.append((base + i, j - i, blob[i:j].decode("ascii")))
            i = j
            continue
    i += 1
print("   printable runs (>=5, NUL/EOF-terminated): %d" % len(runs))
for ea, n, s in runs[:20]:
    print("      0x%-6X %-3d %r" % (ea, n, s))

# ---------------- 4. partition map -------------------------------------------
rows = []
anchors_here = sorted(a for a in anchors if LO <= a < HI)
edges = sorted(set([LO] + anchors_here + [HI]))
for a, b in zip(edges, edges[1:]):
    off_a = a - base
    head = blob[off_a:off_a + 16]
    printable = sum(1 for x in head if 0x20 <= x < 0x7F or x == 0)
    entries = sorted(d for d in per_dst if a <= d < b)
    rows.append({"lo": a, "hi": b, "size": b - a,
                 "head_hex": head.hex(), "head_ascii": "".join(
                     chr(x) if 0x20 <= x < 0x7F else "." for x in head),
                 "printable_head": printable >= 8,
                 "n_entries": len(entries),
                 "first_entries": entries[:6]})
print("\n== partition map of sub_2E2F0 (anchor-delimited blocks) ==")
print("   %-8s %-8s %-7s %-5s %-6s %s"
      % ("lo", "hi", "size", "data?", "entries", "first entry targets"))
for r in rows:
    print("   0x%-6X 0x%-6X %-7d %-5s %-6d %s"
          % (r["lo"], r["hi"], r["size"], "DATA" if r["printable_head"] else "",
             r["n_entries"], " ".join("0x%X" % x for x in r["first_entries"][:5])))
data_bytes = sum(r["size"] for r in rows if r["printable_head"])
print("   blocks whose first 16 B look like data/text: %d (%d bytes)"
      % (sum(1 for r in rows if r["printable_head"]), data_bytes))

print("\n== candidate data holes (data-led block head before its first entry) ==")
holes = []
for r in rows:
    if r["printable_head"] and r["first_entries"]:
        gap = min(r["first_entries"]) - r["lo"]
        holes.append((r["lo"], r["lo"] + gap, gap))
        print("      0x%X..0x%X  %d B   head=%r"
              % (r["lo"], r["lo"] + gap, gap, r["head_ascii"]))
print("   plus the 7 NUL-terminated string runs: %d bytes total"
      % sum(n for _e, n, _s in runs))

print("\n== external entry evidence (the seed list for a carve) ==")
ext_cnt = Counter()
thunk_cnt = Counter()
for s, d, c in in_blob:
    if src_kind(s) == "inside-blob":
        continue
    if src_kind(s) == "thunk":
        thunk_cnt[d] += 1
    else:
        ext_cnt[d] += 1
print("   CALLED from another function (%d distinct):" % len(ext_cnt))
for d, n in ext_cnt.most_common():
    print("      0x%-6X x%-3d %s" % (d, n, " (thunk)" if d in thunk_cnt else ""))
print("   reached via a thunk slot (%d distinct):" % len(thunk_cnt))
for d, n in thunk_cnt.most_common():
    print("      0x%-6X x%-3d" % (d, n))
# internal entry refs that are NOT reachable from outside: dispatch labels
inside_only = sorted(set(per_dst) - set(ext_cnt) - set(thunk_cnt))
print("   only-referenced-from-inside (dispatch labels / local jumps): %d"
      % len(inside_only))

# ---------------- 5. upper half ----------------------------------------------
lst = json.loads((IDA / "dst_list.json").read_text())
up = [r for r in lst if HI <= r["ea"] < R05_HI]
print("\n== R05 upper half 0x%X..0x%X ==" % (HI, R05_HI))
print("   unregistered call/jump destinations there: %d (of %d total) / %d refs"
      % (len(up), len(lst), sum(r["n"] for r in up)))
print("   their zones:", dict(Counter(r["zone"].split(":")[0] for r in up)))
# fixup count in the upper half (rel to R05 ida base)
r05 = next(p for p in place.values() if p.get("ida_ea") == R05_LO)
n_up = 0
o = DIR + r05["idx"] * 18
w0, _a, w2, _b, span, nfx, _c, _d, _e = struct.unpack_from("<9H", EXE, o)
tpos = 0xFFFA0 + (w2 << 4) if 50 <= r05["idx"] <= 68 else (w2 << 4)
arena = set(range(w0, w0 + max(1, span))) | {0x1D0D, 0x1D31}
for k in range(nfx):
    off, seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
    if seg not in arena:
        continue
    abs_off = (seg - w0) * 16 + off
    if HI - R05_LO <= abs_off < R05_HI - R05_LO:
        n_up += 1
print("   fixup pairs whose target offset is in the upper half: %d / %d"
      % (n_up, nfx))

# ---------------- 6. verify_rebuild impact -----------------------------------
print("\n== what a split would have to satisfy ==")
print("   old range 0x%X..0x%X = %d bytes" % (base, base + len(blob), len(blob)))
print("   contiguous anchor blocks: %d   data-led blocks: %d (%d bytes)"
      % (len(rows), sum(1 for r in rows if r["printable_head"]), data_bytes))
print("   SPLIT today requires new fns to tile 100%% of the old range, so the")
print("   %d data bytes would have to become functions (wrong) unless the gate"
      % data_bytes)
print("   learns to accept manifest-listed data holes.")

json.dump({"anchors": {hex(a): {"n_fixups": anchors[a]["n_fixups"],
                                "idxs": sorted(anchors[a]["idxs"]),
                                "segs": sorted(anchors[a]["segs"])}
                       for a in sorted(anchors)},
           "partition": rows,
           "in_blob": {"refs": len(in_blob), "distinct": len(per_dst),
                       "buckets": dict(buckets),
                       "ext_call": ext_call, "thunk": thunk_t,
                       "internal": internal},
           "strings": [{"ea": ea, "len": n, "text": s} for ea, n, s in runs],
           "holes": [{"lo": a, "hi": b, "size": n} for a, b, n in holes],
           "upper_half": {"dsts": len(up), "refs": sum(r["n"] for r in up),
                          "fixup_pairs": n_up, "record_fixups": nfx}},
          open(IDA / "sub2e2f0_map.json", "w"))
print("\nwrote analysis/ida_falconcd/sub2e2f0_map.json")
