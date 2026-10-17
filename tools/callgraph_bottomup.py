#!/usr/bin/env python3
"""Build a PARTIAL call graph and traverse it bottom-up (leaves -> roots).

Rationale (agreed method): the dynamic trace is incomplete by nature (elapsed
time, plane configs, campaign, null-modem paths may never be exercised), so we
do NOT aim for full coverage. Instead:

    1. endpoints = functions that ARE called but (in our data) call nothing
    2. step back  = their callers
    3. repeat upward until no new nodes / roots reached

Edges = union of:
  * static  : IDA call/jump refs  (tools/export_callrefs.py)
  * dynamic : runtime indirect-far CALL/JMP (caller -> target) from FALCON_TRACE

Both ends resolved to functions via classification.json intervals; targets
landing MID-function are flagged (tail-jumps / dispatch labels).

Output:
  analysis/traces/callgraph_partial.json   full edge set + levels
  readable report on stdout
"""
from __future__ import annotations

import json
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDA = ROOT / "analysis" / "ida_falconcd"
TRACES = ROOT / "analysis" / "traces"
DUMP = ROOT / "memdump"

CLS = IDA / "classification.json"
REFS = IDA / "callgraph_refs.json"
OUT = TRACES / "callgraph_partial.json"

# runtime cs:ip -> ida_ea (finding 32, same as verify_boundaries.py)
IDA_BASE_LINEAR = 0x10000
IMAGE_PARA = 0x1F5
RESIDENT_LO = IMAGE_PARA
RESIDENT_HI = IMAGE_PARA + (0x1CF51 >> 4)


def build_intervals(cls: dict):
    """-> (starts, list of (start, end, key, info)) sorted by start."""
    ivs = sorted(
        (v["ea"], v["ea"] + max(v["size"], 1), k, v) for k, v in cls.items()
    )
    return [iv[0] for iv in ivs], ivs


def resolve(ea: int, starts, ivs):
    """Return (fn_key, is_exact) for an address, or (None, False)."""
    i = bisect_right(starts, ea) - 1
    if i >= 0:
        s, e, k, _ = ivs[i]
        if s <= ea < e:
            return k, (ea == s)
    return None, False


def load_static(cls, starts, ivs):
    edges = set()
    unresolved = 0
    if not REFS.exists():
        return edges, unresolved
    data = json.loads(REFS.read_text())
    for src, dst, _is_call in data["refs"]:
        s, s_exact = resolve(src, starts, ivs)
        d, d_exact = resolve(dst, starts, ivs)
        if s is None or d is None:
            unresolved += 1
            continue
        if s != d:
            edges.add((s, d))
    return edges, unresolved


def rt_to_ida(cs: int, ip: int):
    if RESIDENT_LO <= cs < RESIDENT_HI:
        return (cs << 4) + ip + (IDA_BASE_LINEAR - (IMAGE_PARA << 4))
    return None  # overlay targets handled below via rtlink_loads


def load_dynamic(cls, starts, ivs):
    """caller -> callee edges from indirect_far events."""
    edges = set()
    n_events = 0
    unresolved = 0
    seg_to_rec = defaultdict(list)
    rt_p = TRACES / "rtlink_loads.json"
    placement_p = IDA / "overlay_placement.json"
    placement = {}
    if rt_p.exists() and placement_p.exists():
        placement = {p["idx"]: p for p in json.loads(placement_p.read_text())}
        for rec in json.loads(rt_p.read_text()).get("records", []):
            for seg in rec["segments"]:
                seg_to_rec[seg].append(rec["record_idx"])

    # finding 60 P1: content-validated runtime map (runtime CS = link seg +
    # 0x1F5, addressed record-relative; two variant records can claim the same
    # paragraphs and the loader-swap is decided by terminator evidence).
    # Built by tools/map_runtime_segments.py -> analysis/traces/runtime_seg_map.json
    rmap = {}
    rt_map_p = TRACES / "runtime_seg_map.json"
    if rt_map_p.exists() and placement:
        for cs_s, info in json.loads(rt_map_p.read_text()).get("map", {}).items():
            if info.get("chosen"):
                idx, base = info["chosen"]
                rec = placement.get(idx)
                end = (rec["ida_ea"] + rec["ida_len"]) if rec else None
                rmap[int(cs_s)] = (base, end)

    def to_ida(cs, ip):
        ea = rt_to_ida(cs, ip)
        if ea is not None:
            return ea
        hit = rmap.get(cs)
        if hit:
            base, end = hit
            ea = base + ip
            if end is None or ea < end:
                return ea
            return None          # past the proved record -- never guess
        if cs in seg_to_rec:
            rec = placement.get(seg_to_rec[cs][0])
            if rec and rec.get("ida_ea") is not None:
                return rec["ida_ea"] + ip
        return None

    for path in sorted(DUMP.glob("*_fileio.jsonl")):
        for line in path.open():
            if '"indirect_far"' not in line:
                continue
            r = json.loads(line)
            n_events += 1
            try:
                ccs, cip = (int(x, 16) for x in r["caller"].split(":"))
                tcs, tip = (int(x, 16) for x in r["target"].split(":"))
            except Exception:
                unresolved += 1
                continue
            src_ea, dst_ea = to_ida(ccs, cip), to_ida(tcs, tip)
            if src_ea is None or dst_ea is None:
                unresolved += 1
                continue
            s, _ = resolve(src_ea, starts, ivs)
            d, _ = resolve(dst_ea, starts, ivs)
            if s is None or d is None:
                unresolved += 1
                continue
            if s != d:
                edges.add((s, d))
    return edges, n_events, unresolved


def main():
    cls = json.loads(CLS.read_text())
    starts, ivs = build_intervals(cls)

    st_edges, st_unres = load_static(cls, starts, ivs)
    dy_edges, dy_events, dy_unres = load_dynamic(cls, starts, ivs)

    # dynamic call-frequency for ranking (fartrans is target-keyed -> per target)
    dyn_target_calls = defaultdict(int)
    for path in sorted(DUMP.glob("*_fartrans.jsonl")):
        for line in path.open():
            r = json.loads(line)
            ea = None
            cs, ip = r["cs"], r["ip"]
            e = rt_to_ida(cs, ip)
            if e is None:
                continue
            k, _ = resolve(e, starts, ivs)
            if k:
                dyn_target_calls[k] += r["calls"] + r["jumps"]

    all_edges = st_edges | dy_edges

    # adjacency
    outgoing = defaultdict(set)   # caller -> callees
    incoming = defaultdict(set)   # callee -> callers
    for a, b in all_edges:
        outgoing[a].add(b)
        incoming[b].add(a)

    known = set(cls)
    # endpoints: called (has caller) but calls nothing observed
    endpoints = sorted(
        (k for k in known if incoming.get(k) and not outgoing.get(k)),
        key=lambda k: -dyn_target_calls.get(k, 0),
    )

    # bottom-up BFS
    visited = set()
    levels = []
    frontier = endpoints
    while frontier:
        frontier = [k for k in frontier if k not in visited]
        if not frontier:
            break
        visited.update(frontier)
        levels.append(frontier)
        nxt = set()
        for k in frontier:
            nxt.update(incoming.get(k, ()))
        frontier = sorted(
            (k for k in nxt if k not in visited),
            key=lambda k: -dyn_target_calls.get(k, 0),
        )

    out = {
        "edge_counts": {
            "static": len(st_edges), "static_unresolved": st_unres,
            "dynamic": len(dy_edges), "dynamic_events": dy_events,
            "dynamic_unresolved": dy_unres, "union": len(all_edges),
        },
        "endpoints": endpoints,
        "levels": levels,
        "edges": [list(e) for e in sorted(all_edges)],
        "dyn_target_calls": dict(dyn_target_calls),
    }
    json.dump(out, OUT.open("w"), indent=1)

    # ---- report ----
    ec = out["edge_counts"]
    print("edges: static=%d (+%d unresolved)  dynamic=%d/%d events "
          "(+%d unresolved)  union=%d"
          % (ec["static"], ec["static_unresolved"], ec["dynamic"],
             ec["dynamic_events"], ec["dynamic_unresolved"], ec["union"]))
    print("functions: %d   endpoints (called, calls nothing): %d"
          % (len(cls), len(endpoints)))
    print("levels reached: %d   nodes covered: %d\n"
          % (len(levels), len(visited)))

    for i, lvl in enumerate(levels[:6]):
        print("=== LEVEL %d : %d fns ===" % (i, len(lvl)))
        for k in lvl[:18]:
            info = cls[k]
            dc = dyn_target_calls.get(k, 0)
            print("  %-13s %5dB %-6s in=%-3d dyn=%-8d ea=0x%X"
                  % (k, info["size"], info["class"],
                     len(incoming.get(k, ())), dc, info["ea"]))
        if len(lvl) > 18:
            print("  ... +%d more" % (len(lvl) - 18))
        print()
    if len(levels) > 6:
        print("(%d more levels)" % (len(levels) - 6))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
