"""Plan the DS/SS segment-register values to apply to the IDB (finding 122).

Host-side.  Inputs:
  analysis/dgroup/ds_facts.json   tools/export_ds_facts.py run on a copy of the IDB
  memdump/*fartrans.jsonl         runtime far-transfer targets with entry DS (finding 30)
Output:
  registry/ds_expected.json       manifest consumed by tools/apply_default_ds.py

Entry DS of a function, first rule that decides wins:
  1. runtime: every observed far entry (session A, load base 0x1F5) had the same DS.
     A value inside an IDA segment is used as is; mixed or non-segment values
     (heap blocks, PSP) mean DS is not static -> BADSEL.
  2. callers: every call/jump/fall-through into the function arrives with the same
     known DS (iterated to a fixpoint, so it flows down the call graph).
  3. otherwise the current value is kept, unless it is an artifact -- inherited
     linearly from a range opened inside a *different* function (e.g. 303 seg021
     functions inherit 2AA3 from `mov ds,dx` at 0x2B482) or the 0 left by the
     R29 split -- which becomes BADSEL.
Inner ranges (opened inside the function) are re-derived from the entry DS:
  matched `pop ds` = DS at the push; unmatched `pop ds` in an epilogue of a
  function whose prologue pushes ds = entry DS; `mov r,ss; mov ds,r` = DGROUP;
  `mov r,ds|es; mov ds,r` = that register; `mov ds,cs:[slot]` = DGROUP for the
  two slots that hold DGROUP in all 12 memdumps, BADSEL for slots IDA read as 0;
  `lds`/`mov ds,mem` that IDA read as 0 -> BADSEL.  `xor r,r; mov ds,r` keeps 0.
Every point that changes a value is followed by a restore point at the end of
its chunk (if no other break follows) so code after the chunk is untouched.

SS: runtime SS is DGROUP everywhere except startup (initial EXE stack, finding 121),
so every CODE segment except seg021/seg022/R01_1CF6 gets default SS 7A32 and
its inner SS ranges (mostly `pop ss` in misdecoded data) are set to 7A32.

Usage: python tools/plan_default_ds.py [--facts PATH]
"""
import argparse
import bisect
import collections
import glob
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "analysis/dgroup/ds_facts.json"
MANIFEST = ROOT / "registry/ds_expected.json"
EXE = ROOT / "game/FALCONCD.EXE"
PLACEMENT = ROOT / "analysis/ida_falconcd/overlay_placement.json"

DGROUP = 0x7A32
LB = 0x1F5                       # session A image load base (finding 32)
DIR = 0x1E24F                    # RTLink record directory (finding 56)
RESIDENT_PARAS = 0x1CF5
CONST_SLOTS = {0x10842, 0x27470}  # cs-relative words = runtime 6C27 in 12/12 dumps
SS_KEEP = {"seg021", "seg022", "R01_1CF6"}   # startup: SS = initial EXE stack 852C
R29_ZERO = "R29_"                # segments created with default DS 0 by finding 120
EPILOGUE = {"pop", "popa", "popf", "leave"}
RET = {"retf", "retn", "iret"}


def build_evidence(fstarts):
    """{func_start: Counter(ida_para|None -> n)} from the far-transfer traces"""
    exe = EXE.read_bytes()
    place = {p["idx"]: p for p in json.loads(PLACEMENT.read_text())}
    spans = {}
    for idx in place:
        w0, _, _, _, span, _ = struct.unpack_from("<6H", exe, DIR + idx * 18)
        spans[idx] = (w0, span)

    def cands(cs, ip):
        link = cs - LB
        out = []
        if 0 <= link < RESIDENT_PARAS:
            out.append(((link + 0x1000) << 4) + ip)
        for idx, (w0, span) in spans.items():
            p = place[idx]
            if p.get("ida_ea") is None or not p.get("ida_len"):
                continue
            if w0 <= link < w0 + max(1, span):
                ea = p["ida_ea"] + (link - w0) * 16 + ip
                if p["ida_ea"] <= ea < p["ida_ea"] + p["ida_len"]:
                    out.append(ea)
        return out

    ev = collections.defaultdict(collections.Counter)
    for fn in sorted(glob.glob(str(ROOT / "memdump/*fartrans.jsonl"))):
        for line in open(fn):
            if not line.strip():
                continue
            r = json.loads(line)
            c = [e for e in cands(r["cs"], r["ip"]) if e in fstarts]
            if len(c) != 1:
                continue
            for h in r["ds"]:
                v = h["seg"]
                ev[c[0]][None if v is None else v - LB + 0x1000] += h["n"]
    return ev


class Planner:
    def __init__(self, facts):
        self.F = facts["funcs"]
        self.segs = facts["segments"]
        self.ss_ranges = facts["ss_ranges"]
        self.by = {f["start"]: f for f in self.F}
        self.starts = sorted(self.by)
        self.seg_lo = sorted(s["start"] for s in self.segs)
        self.seg_by = {s["start"]: s for s in self.segs}
        self.E = {}           # func -> (value, source); value None = BADSEL
        self.stats = collections.Counter()

    # ---- lookups -------------------------------------------------------
    def func_of(self, ea):
        i = bisect.bisect_right(self.starts, ea) - 1
        if i < 0:
            return None
        f = self.by[self.starts[i]]
        return f if any(a <= ea < b for a, b in f["chunks"]) else None

    def owner(self, ea):
        """function whose chunk contains ea (any function, not just the nearest start)"""
        f = self.func_of(ea)
        if f:
            return f
        for g in self.F:
            if any(a <= ea < b for a, b in g["chunks"]):
                return g
        return None

    def seg_of(self, ea):
        i = bisect.bisect_right(self.seg_lo, ea) - 1
        s = self.seg_by[self.seg_lo[i]] if i >= 0 else None
        return s if s and s["start"] <= ea < s["end"] else None

    def mapped(self, p):
        s = self.seg_of(p * 16)
        return s is not None

    # ---- entry classification ------------------------------------------
    def artifact(self, f):
        """current entry value is a linear-inheritance or split artifact"""
        if f["entry"] == 0:
            return True
        rs = f["entry_rs"]
        if rs >= f["start"]:
            return False
        g = self.func_of(rs) or self.func_of(rs - 1)
        return g is not None and g["start"] != f["start"]

    # ---- value resolution under the current plan -----------------------
    def resolve(self, f, st, seen=None):
        if st == "E":
            v = self.E.get(f["start"])
            return v[0] if v else "?"
        r = f["ranges"].get(st[2:])
        if r is None:
            return "?"
        seen = seen or set()
        if st in seen:
            return "?"
        seen.add(st)
        return self.inner(f, r, seen)[0]

    def inner(self, f, r, seen=None):
        """(value, why) for an inner range; value '?' = undecided, None = BADSEL"""
        k = r["kind"]
        cur = r["val"]
        if k == "pop":
            pr = r.get("push_reg")
            if pr == "ds":
                return self.resolve(f, r["push_state"], seen), "pop-matched"
            if pr == "es":
                return (r["es"] if r.get("es") is not None else cur), "pop-es"
            if pr == "cs":
                return (cur if cur is not None else f["cs"]), "pop-cs"
            nxt = r.get("next") or []
            ok = False
            for m in nxt:
                if m in RET:
                    ok = True
                    break
                if m not in EPILOGUE:
                    break
            if ok and any(p.startswith("push") and p.endswith("ds") for p in f["prologue"]):
                return self.resolve(f, "E", seen), "pop-epilogue"
            return cur, "keep"
        if k == "ss":
            return DGROUP, "ss-copy"
        if k == "copy":
            if r["src"] == "ds":
                return self.resolve(f, r["src_state"], seen), "ds-copy"
            return (cur if cur is not None else r["src_val"]), "keep"
        if k == "slot":
            if r["slot_ea"] in CONST_SLOTS:
                return DGROUP, "slot-dgroup"
            return (None if cur == 0 else cur), ("slot-zero" if cur == 0 else "keep")
        if k == "movreg":
            if cur == 0 and not r.get("zero"):
                return None, "movreg-zero-read"
            return cur, "keep"
        if k in ("movmem", "lds"):
            return (None if cur == 0 else cur), (k + "-zero-read" if cur == 0 else "keep")
        return cur, "keep"

    # ---- entry DS --------------------------------------------------------
    def plan_entries(self, ev):
        for f in self.F:
            c = ev.get(f["start"])
            if c:
                tot = sum(c.values())
                v, n = c.most_common(1)[0]
                if v is not None and n / tot >= 0.99:
                    if self.mapped(v):
                        self.E[f["start"]] = (v, "runtime")
                    elif v == f["entry"]:
                        self.E[f["start"]] = (v, "runtime-keep")
                    else:
                        self.E[f["start"]] = (None, "runtime-dynamic")
                else:
                    self.E[f["start"]] = (None, "runtime-mixed")
        fixed = {fs for fs in self.E}
        for f in self.F:
            if f["start"] not in fixed and f["entry"] is not None and not self.artifact(f):
                self.E[f["start"]] = (f["entry"], "keep")
                fixed.add(f["start"])
        # caller fixpoint over the undecided functions
        todo = [f for f in self.F if f["start"] not in fixed]
        changed = True
        rounds = 0
        while changed:
            changed = False
            rounds += 1
            for f in todo:
                if f["start"] in self.E or not f["calls"]:
                    continue
                vals = set()
                for c in f["calls"]:
                    if c["func"] is None:
                        vals.add(c["ida"] if c["ida"] is not None else "?")
                    else:
                        vals.add(self.resolve(self.by[c["func"]], c["state"]))
                    if "?" in vals or None in vals or len(vals) > 1:
                        break
                if len(vals) == 1 and "?" not in vals and None not in vals:
                    self.E[f["start"]] = (vals.pop(), "callers")
                    changed = True
        self.stats["caller rounds"] = rounds
        for f in self.F:
            if f["start"] not in self.E:
                self.E[f["start"]] = ((None, "artifact") if self.artifact(f) else (f["entry"], "keep-unknown"))

    # ---- points ----------------------------------------------------------
    def plan_points(self):
        pts = {}

        def put(ea, val, before, why, fs, kind):
            old = pts.get(ea)
            if old and old["kind"] != "restore":
                return
            pts[ea] = {"ea": ea, "before": before, "after": val, "why": why, "func": fs, "kind": kind}

        reset_segs = {s["start"] for s in self.segs if s["name"].startswith(R29_ZERO) and s["def_ds"] == 0}
        for f in self.F:
            fs = f["start"]
            mine = []                      # points emitted in this function
            v, why = self.E[fs]
            if v != f["entry"]:
                put(fs, v, f["entry"], why, fs, "entry")
                mine.append(fs)
            self.stats["entry " + why + (" (changed)" if v != f["entry"] else "")] += 1
            for k, r in f["ranges"].items():
                nv, why = self.inner(f, r)
                if nv == "?":
                    nv, why = r["val"], "keep-undecided"
                self.stats["inner %s %s" % (r["kind"], why)] += 1
                if nv != r["val"]:
                    put(int(k), nv, r["val"], why, fs, "inner")
                    mine.append(int(k))
            for k, t in f["tails"].items():
                vals = {self.resolve(f, s) for s in t["states"]}
                if len(vals) == 1:
                    nv = vals.pop()
                    if nv != "?" and nv != t["val"]:
                        put(int(k), nv, t["val"], "tail", fs, "tail")
                        mine.append(int(k))
            # restore the value after each chunk whose last break is ours
            breaks = sorted(set(int(k) for k in f["ranges"]) | set(int(k) for k in f["tails"]) | {fs} | set(mine))
            for (cs_, ce), (ce2, cval, brk) in zip(f["chunks"], f["chunk_ends"]):
                inside = [b for b in breaks if cs_ <= b < ce]
                if not inside or inside[-1] not in mine or brk:
                    continue
                s = self.seg_of(ce - 1)
                if s is None or ce >= s["end"]:
                    continue
                rv = None if (cval == 0 and s["start"] in reset_segs) else cval
                # emitted even when rv == cval: without its own break the
                # range split inside the chunk would run on past ce
                put(ce, rv, cval, "restore", fs, "restore")
        return [pts[k] for k in sorted(pts)]

    def plan_segments(self):
        out = []
        for s in self.segs:
            if s["name"].startswith(R29_ZERO) and s["def_ds"] == 0:
                out.append({"seg": s["name"], "start": s["start"], "reg": "ds", "before": 0, "after": None,
                            "why": "R29 split default 0"})
            if s["class"] == "CODE" and s["name"] not in SS_KEEP and s["def_ss"] != DGROUP:
                out.append({"seg": s["name"], "start": s["start"], "reg": "ss", "before": s["def_ss"],
                            "after": DGROUP, "why": "runtime SS = DGROUP"})
        return out

    def plan_ss(self):
        seg_starts = {s["start"] for s in self.segs}
        out = []
        for start, _end, val, _tag, prev in self.ss_ranges:
            if start in seg_starts or val == DGROUP:
                continue
            s = self.seg_of(start)
            if s is None or s["class"] != "CODE" or s["name"] in SS_KEEP:
                continue
            out.append({"ea": start, "before": val, "after": DGROUP, "why": prev})
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", default=str(FACTS))
    ap.add_argument("--out", default=str(MANIFEST))
    a = ap.parse_args()
    facts = json.loads(Path(a.facts).read_text())
    if facts.get("error"):
        raise SystemExit("facts export failed:\n" + facts["error"])
    P = Planner(facts)
    ev = build_evidence(set(P.by))
    P.plan_entries(ev)
    pts = P.plan_points()
    segs = P.plan_segments()
    ss = P.plan_ss()
    doc = {"finding": 122, "dgroup": DGROUP, "funcs": len(P.F),
           "ds_points": pts, "seg_defaults": segs, "ss_points": ss}
    Path(a.out).write_text(json.dumps(doc, indent=0))
    for k, v in sorted(P.stats.items()):
        print("%-40s %d" % (k, v))
    print("ds points %d (%s)" % (len(pts), dict(collections.Counter(p["kind"] for p in pts))))
    print("seg defaults %d, ss points %d -> %s" % (len(segs), len(ss), a.out))


if __name__ == "__main__":
    main()
