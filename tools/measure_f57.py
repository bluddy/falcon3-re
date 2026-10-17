"""Finding 57 outcome metrics (host side, read-only).

(a) graph deltas vs the committed (finding 56) state
(b) where the retargeted/new far-call targets land: the 228 pre-existing
    overlay orphans, other registered fns, fn interiors, or outside every fn
(c) refs landing inside sub_2E2F0 (0x2E2F0..0x3ACAC), which spans the 24
    sub-block anchors (incl. the 0x2F640 name table)

Usage: venv\\Scripts\\python tools\\measure_f57.py
"""
import json
import subprocess
from bisect import bisect_right
from collections import Counter
from pathlib import Path

ROOT = Path(".")
IDA = "analysis/ida_falconcd/"
TR = "analysis/traces/"


def git_json(path):
    r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("cannot read HEAD:%s" % path)
    return json.loads(r.stdout)


cur_cls = json.load(open(IDA + "classification.json", encoding="utf-8"))
hd_cls = git_json(IDA + "classification.json")
cur_refs = json.load(open(IDA + "callgraph_refs.json"))["refs"]
hd_refs = git_json(IDA + "callgraph_refs.json")["refs"]
cur_cg = json.load(open(TR + "callgraph_partial.json"))
hd_cg = git_json(TR + "callgraph_partial.json")

PLACE = json.load(open(IDA + "overlay_placement.json"))
ovl_writes = sorted((p["ida_ea"], p["ida_ea"] + p["ida_len"])
                    for p in PLACE if p.get("ida_ea") is not None and p.get("ida_len"))
THUNK_LO, THUNK_HI = 0x2BD9D, 0x2C973
SUB = ("sub_2E2F0", 0x2E2F0, 0x3ACAC)


def make_index(cls):
    ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k, v.get("overlay", False))
                 for k, v in cls.items() if v.get("bytes", True) is not None)
    starts = [x[0] for x in ivs]
    return ivs, starts


def resolve(ea, ivs, starts):
    i = bisect_right(starts, ea) - 1
    if i >= 0:
        s, e, k, ov = ivs[i]
        if s <= ea < e:
            return k, (ea == s), ov
    return None, False, None


def in_ovl_range(ea):
    i = bisect_right([x[0] for x in ovl_writes], ea) - 1
    return i >= 0 and ovl_writes[i][0] <= ea < ovl_writes[i][1]


def kind(ea, ivs, starts):
    k, exact, ov = resolve(ea, ivs, starts)
    if k is None:
        where = ("thunk" if THUNK_LO <= ea < THUNK_HI
                 else ("overlay-data" if in_ovl_range(ea) else "resident-data"))
        return where
    zone = "overlay-fn" if ov else "resident-fn"
    return "%s/%s" % ("start" if exact else "interior", zone)


cur_ivs, cur_starts = make_index(cur_cls)
hd_ivs, hd_starts = make_index(hd_cls)

# ---------- pre-existing overlay orphans (finding 56 output: 228) ----------
hd_indeg = Counter(b for _a, b in hd_cg["edges"])
hd_orphans = {k for k, v in hd_cls.items() if v.get("overlay") and hd_indeg[k] == 0}
cur_indeg = Counter(b for _a, b in cur_cg["edges"])
cur_orphans = {k for k, v in cur_cls.items() if v.get("overlay") and cur_indeg[k] == 0}

# ================= (a) graph deltas =================
print("== (a) graph ==")
for label, key in (("functions", None), ("static edges", "static"),
                   ("static_unresolved", "static_unresolved"), ("union", "union")):
    if key is None:
        print("   %-18s: %d -> %d" % (label, len(hd_cls), len(cur_cls)))
    else:
        h, c = hd_cg["edge_counts"][key], cur_cg["edge_counts"][key]
        print("   %-18s: %d -> %d  (%+d)" % (label, h, c, c - h))
print("   overlay orphans   : %d -> %d" % (len(hd_orphans), len(cur_orphans)))

# ================= (b) retargeted / new sites =================
print("\n== (b) where the fixed targets land ==")
hd_by_src, cur_by_src = {}, {}
for s, d, c in hd_refs:
    hd_by_src.setdefault((s, c), set()).add(d)
for s, d, c in cur_refs:
    cur_by_src.setdefault((s, c), set()).add(d)

moved = [(k, sorted(hd_by_src[k]), sorted(cur_by_src[k]))
         for k in cur_by_src.keys() & hd_by_src.keys()
         if hd_by_src[k] != cur_by_src[k]]
only_cur = [k for k in cur_by_src.keys() - hd_by_src.keys()]
only_hd = [k for k in hd_by_src.keys() - cur_by_src.keys()]
print("   ref sites: %d -> %d   retargeted %d   new %d   gone %d"
      % (len(hd_by_src), len(cur_by_src), len(moved), len(only_cur), len(only_hd)))


def tally(site_keys, which):
    """which=0 old dsts, 1 new dsts -> Counter of kind()."""
    c = Counter()
    hit_orph = 0
    for k in site_keys:
        ds = (hd_by_src[k] if which == 0 else cur_by_src[k])
        for d in ds:
            c[kind(d, *( (hd_ivs, hd_starts) if which == 0 else (cur_ivs, cur_starts) ))] += 1
            kk, _, _ = resolve(d, *((hd_ivs, hd_starts) if which == 0 else (cur_ivs, cur_starts)))
            if kk in hd_orphans:
                hit_orph += 1
    return c, hit_orph


moved_keys = [m[0] for m in moved]
moved_old, moved_old_orph = tally(moved_keys, 0)
moved_new, moved_new_orph = tally(moved_keys, 1)
new_new, new_orph = tally(only_cur, 1)
print("   -- retargeted sites: OLD dst kinds --")
for k, v in moved_old.most_common():
    print("      %-24s %d" % (k, v))
print("   -- retargeted sites: NEW dst kinds --")
for k, v in moved_new.most_common():
    print("      %-24s %d" % (k, v))
print("   -- brand-new ref sites: dst kinds --")
for k, v in new_new.most_common():
    print("      %-24s %d" % (k, v))
print("   landed on a pre-existing overlay orphan: moved %d, new %d"
      % (moved_new_orph, new_orph))
print("   orphans now orphan: %d   rescued: %d   newly orphaned: %d"
      % (len(cur_orphans), len(hd_orphans - cur_orphans), len(cur_orphans - hd_orphans)))

# ---- (b2) functions that had NO incoming edge at HEAD and now do ----
hd_zero = {k for k in hd_cls if hd_indeg[k] == 0}
reached_now = sorted(k for k in hd_zero if cur_indeg[k] > 0)
print("   functions with zero indegree at HEAD  : %d" % len(hd_zero))
print("   ... now reached by >=1 edge          : %d  (overlay %d / resident %d)"
      % (len(reached_now),
         sum(1 for k in reached_now if hd_cls[k].get("overlay")),
         sum(1 for k in reached_now if not hd_cls[k].get("overlay"))))
# ---- (b3) the data targets: few tables, many call sites ----
data_dsts = Counter()
for k in moved_keys:
    for d in cur_by_src[k]:
        kk, _, _ = resolve(d, cur_ivs, cur_starts)
        if kk is None:
            data_dsts[d] += 1
print("   moved targets landing on data: %d refs -> %d distinct addresses"
      % (sum(data_dsts.values()), len(data_dsts)))
for d, n in data_dsts.most_common(8):
    print("      0x%-7X x%-4d %s" % (d, n,
          "overlay" if in_ovl_range(d) else ("thunk" if THUNK_LO <= d < THUNK_HI else "resident")))

# ================= (c) sub_2E2F0 interior =================
print("\n== (c) inside %s (0x%X..0x%X) ==" % (SUB[0], SUB[1], SUB[2]))


def sub_hits(refs, ivs, starts, exact_only=False):
    hits = []
    for s, d, c in refs:
        if SUB[1] <= d < SUB[2]:
            kk, ex, _ = resolve(d, ivs, starts)
            if exact_only and not ex:
                continue
            hits.append((s, d, c, kk))
    return hits


h0 = sub_hits(hd_refs, hd_ivs, hd_starts)
h1 = sub_hits(cur_refs, cur_ivs, cur_starts)
print("   refs landing in range : %d -> %d" % (len(h0), len(h1)))
for nm, hits in (("HEAD", h0), ("now", h1)):
    ins = sum(1 for x in hits if x[3] is None)
    exacts = [x for x in hits if resolve(x[1], cur_ivs, cur_starts)[1]]
    print("      %-5s total %4d   at a fn start %d   interior %d   outside every fn %d"
          % (nm, len(hits), len(exacts), len(hits) - len(exacts) - ins, ins))
starts_d = sorted({d for _s, d, _c, _k in h1 if resolve(d, cur_ivs, cur_starts)[1]})
print("      distinct fn starts targeted now: %d" % len(starts_d))
print("      0x2F640 (name-table anchor+0xA7) targeted now: %s"
      % any(d == 0x2F640 for _s, d, _c, _k in h1))
# anchors: in IDA space each sub-block anchor is ida_ea + k*0x1000 (+ const),
# so the 4KB block of the target identifies WHICH sub-block it belongs to.
blocks = Counter((d - 0x2E100) >> 12 for _s, d, _c, _k in h1)
print("      distinct 4KB blocks (i.e. sub-block anchors) hit: %d" % len(blocks))
print("      blocks: %s" % ", ".join("0x%X=%d" % (b, n) for b, n in sorted(blocks.items())))
print("      refs whose dst CHANGED into this range: %d"
      % sum(1 for k in moved_keys for d in cur_by_src[k] if SUB[1] <= d < SUB[2]))

# interior -> which functions
who = Counter(k for _s, d, _c, k in h1 if k)
print("      landing inside: %s"
      % ", ".join("%s=%d" % (k, v) for k, v in who.most_common(6)))

# ---- the word-level check: how many patched words sit in a decoded insn ----
print("\n== patched words that are call/jmp operands ==")
fix = {int(k): v for k, v in json.load(open(IDA + "fixups_to_apply.json")).items()}
pl = {p["idx"]: p for p in json.load(open(IDA + "overlay_placement.json"))}
srcmap = {}
for s, d, c in cur_refs:
    srcmap.setdefault(s, (d, c))
heads = sorted(srcmap)
n_call = n_any = 0
sample = []
for idx, plist in fix.items():
    p = pl.get(idx)
    if not p or p["addr"] == "skip" or not p["ida_len"]:
        continue
    for rel, _w in plist:
        ea = p["ida_ea"] + rel
        i = bisect_right(heads, ea) - 1
        if i < 0:
            continue
        hs = heads[i]
        if ea - hs < 6:                       # word inside that head's insn
            n_any += 1
            d, c = srcmap[hs]
            if c:
                n_call += 1
                if len(sample) < 6:
                    sample.append("src=0x%X dst=0x%X word=0x%X" % (hs, d, ea))
print("   patched words inside a ref-emitting instruction: %d (of which CALLs %d)"
      % (n_any, n_call))
for s in sample:
    print("      " + s)
