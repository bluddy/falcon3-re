#!/usr/bin/env python3
"""Build a PARTIAL call graph and assign TRUE bottom-up topological depth.

Finding 64 (part 2) upgrades the original reachability BFS to a rigorous
leveling suitable for resuming naming from Level 0 globally:

  1. True Bottom-Up Topological Depth (max-callee depth after SCC
     condensation):
         Level(u) = 0  iff u has 0 outgoing calls to other functions
                           (and in_degree >= 1)
         Level(u) = 1 + max(Level(v) for v in callees(u))
     Mutual-recursion SCCs are condensed first so every cycle shares a single
     level.  Guarantees: when we reach Level k, 100% of u's callees are at
     Levels < k and already named.

  2. Transparent .RTLink Thunk Slots (0x2BD9D..0x2C968) & NEARTHUNK stubs:
     - Exclude the thunk -> sub_2AFBD loader-trap edge from level calculation
       (it would otherwise give every thunk an artificial callee).
     - Treat thunk slots as zero-cost pass-through bridges:
       Level(thunk) = Level(target).  The thunk contributes no level of its
       own; its callers see the target's level directly.

  3. Dual-Tier Ranking within Each Level:
       rank = (dyn_calls DESC, static_in_degree DESC)
     Many newly registered overlay functions have dyn == 0 (not reached in
     the short trace) but high static fan-in, so in_degree is the tie-break.

Edges = union of:
  * static  : IDA call/jump refs  (tools/export_callrefs.py)
  * dynamic : runtime indirect-far CALL/JMP (caller -> target) from FALCON_TRACE

Output:
  analysis/traces/callgraph_partial.json   full edge set + levels + ranking
  readable report on stdout
"""
from __future__ import annotations

import json
from bisect import bisect_right
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDA = ROOT / "analysis" / "ida_falconcd"
TRACES = ROOT / "analysis" / "traces"
DUMP = ROOT / "memdump"

CLS = IDA / "classification.json"
REFS = IDA / "callgraph_refs.json"
# finding 64 audit: named detection joins function_bytes.json (integer ea ->
# applied semantic name), NOT a sub_* string match.  function_bytes[key].name
# is non-null exactly for the 265 ledger-named functions.
FB = IDA / "function_bytes.json"
OUT = TRACES / "callgraph_partial.json"

# runtime cs:ip -> ida_ea (finding 32, same as verify_boundaries.py)
IDA_BASE_LINEAR = 0x10000
IMAGE_PARA = 0x1F5
RESIDENT_LO = IMAGE_PARA
RESIDENT_HI = IMAGE_PARA + (0x1CF51 >> 4)

# finding 64 part 2: RTLink thunk slots + the loader-trap target to exclude
THUNK_LO, THUNK_HI = 0x2BD9D, 0x2C968
LOADER_TRAP = "sub_2AFBD"


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

    # finding 60 P1: content-validated runtime map
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


def is_thunk(cls, key):
    ea = cls[key]["ea"]
    return THUNK_LO <= ea < THUNK_HI


def compute_levels(cls, edges):
    """True bottom-up topological depth after SCC condensation.

    Uses Kosaraju's algorithm (two DFS passes) for SCCs, then a longest-path
    DP on the condensation DAG.  Returns (levels, thunk_levels, scc_of,
    n_scc).  Thunks are pass-through: their level equals their (non-trap)
    target's level; the loader-trap edge is excluded from the DAG.
    """
    known = set(cls)
    thunks = {k for k in known if is_thunk(cls, k)}

    # effective DAG: drop thunk->loader_trap edges
    dag_out = defaultdict(set)
    dag_rev = defaultdict(set)
    for a, b in edges:
        if a in thunks and b == LOADER_TRAP:
            continue
        if b in thunks and a == LOADER_TRAP:
            continue
        dag_out[a].add(b)
        dag_rev[b].add(a)

    # ---- Kosaraju: pass 1 = DFS order on dag_out, pass 2 = DFS on dag_rev ----
    visited = set()
    order = []
    for start in known:
        if start in visited:
            continue
        # iterative DFS (post-order)
        stack = [(start, False)]
        while stack:
            v, processed = stack.pop()
            if processed:
                order.append(v)
                continue
            if v in visited:
                continue
            visited.add(v)
            stack.append((v, True))          # post-order marker
            for w in dag_out.get(v, ()):
                if w not in visited:
                    stack.append((w, False))

    # pass 2: process in reverse order on the reversed graph
    scc_of = {}
    visited2 = set()
    scc_id = 0
    for start in reversed(order):
        if start in visited2:
            continue
        # DFS on dag_rev from start -> this is one SCC
        stack = [start]
        visited2.add(start)
        while stack:
            v = stack.pop()
            scc_of[v] = scc_id
            for w in dag_rev.get(v, ()):
                if w not in visited2:
                    visited2.add(w)
                    stack.append(w)
        scc_id += 1
    n_scc = scc_id

    # group nodes by SCC
    scc_members = defaultdict(list)
    for node, sid in scc_of.items():
        scc_members[sid].append(node)

    # condensation DAG: SCC -> SCC (ignore self-loops)
    cond_out = defaultdict(set)
    for a, b in edges:
        if a in thunks and b == LOADER_TRAP:
            continue
        sa, sb = scc_of.get(a), scc_of.get(b)
        if sa is None or sb is None or sa == sb:
            continue
        cond_out[sa].add(sb)

    # longest-path DP on the (acyclic) condensation:
    #   level(s) = 0 if no outgoing, else 1 + max(level(t))
    level_scc = {}
    visiting = set()

    def scc_level(s):
        if s in level_scc:
            return level_scc[s]
        if s in visiting:
            return 0   # shouldn't happen (condensation is acyclic), guard
        visiting.add(s)
        outs = cond_out.get(s, ())
        lvl = 0 if not outs else 1 + max(scc_level(t) for t in outs)
        visiting.discard(s)
        level_scc[s] = lvl
        return lvl

    for s in scc_members:
        scc_level(s)

    # node level = its SCC's level
    levels = {}
    for node, sid in scc_of.items():
        levels[node] = level_scc[sid]

    # ---- Thunk pass-through: Level(thunk) = Level(target) ----
    thunk_levels = {}
    for t in thunks:
        real_targets = [b for a, b in edges if a == t and b != LOADER_TRAP]
        if real_targets:
            tgt_lvls = [levels.get(b, 0) for b in real_targets]
            thunk_levels[t] = max(tgt_lvls) if tgt_lvls else 0
        else:
            thunk_levels[t] = 0   # pure loader stub (trap-only) -> level 0
    for t, lvl in thunk_levels.items():
        levels[t] = lvl

    return levels, thunk_levels, scc_of, n_scc


def main():
    cls = json.loads(CLS.read_text())
    starts, ivs = build_intervals(cls)

    st_edges, st_unres = load_static(cls, starts, ivs)
    dy_edges, dy_events, dy_unres = load_dynamic(cls, starts, ivs)

    # dynamic call-frequency for ranking
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

    # static in-degree (number of distinct callers)
    static_in = defaultdict(int)
    for a, b in st_edges:
        static_in[b] += 1

    # adjacency (raw, for reporting)
    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    for a, b in all_edges:
        outgoing[a].add(b)
        incoming[b].add(a)

    known = set(cls)
    # endpoints: called (has caller) but calls nothing observed
    endpoints = sorted(
        (k for k in known if incoming.get(k) and not outgoing.get(k)),
        key=lambda k: (-dyn_target_calls.get(k, 0), -static_in.get(k, 0)),
    )

    # ---- TRUE topological depth (finding 64 part 2) ----
    levels, thunk_levels, scc_of, n_scc = compute_levels(cls, all_edges)

    # group nodes by level, rank within level by (dyn DESC, in_degree DESC)
    by_level = defaultdict(list)
    for k in known:
        by_level[levels.get(k, 0)].append(k)
    for lvl in by_level:
        by_level[lvl].sort(
            key=lambda k: (-dyn_target_calls.get(k, 0),
                           -static_in.get(k, 0),
                           cls[k]["ea"]))
    # levels list for the report: level 0, 1, 2, ... (sorted keys)
    ordered_levels = [by_level[lvl] for lvl in sorted(by_level)]

    # finding 64 audit fix: named = function_bytes[key].name is non-null.
    # This joins on the integer ea (fb entry carries ea) and equals exactly the
    # 265 ledger-named functions.  The old `sub_*` regex miscounted RTLink
    # r##_e## names as "named" and real-named fns like input_status_pack as
    # "unnamed".
    fb = json.loads(FB.read_text())
    named = {k for k in known if fb.get(k, {}).get("name")}
    unnamed = known - named
    # finding 64 audit: exclude .RTLink thunk slots from the naming queue --
    # they are 8B jmp-far trampolines, not nameable functions.  (Kept in the
    # graph + levels as pass-through bridges.)
    thunk_keys = {k for k in known if is_thunk(cls, k)}
    # naming_queue = unnamed functions MINUS thunk slots
    naming_queue = unnamed - thunk_keys

    out = {
        "edge_counts": {
            "static": len(st_edges), "static_unresolved": st_unres,
            "dynamic": len(dy_edges), "dynamic_events": dy_events,
            "dynamic_unresolved": dy_unres, "union": len(all_edges),
        },
        "endpoints": endpoints,
        "levels": ordered_levels,
        "node_levels": levels,
        "thunk_levels": thunk_levels,
        "scc_of": scc_of,
        "n_scc": n_scc,
        "edges": [list(e) for e in sorted(all_edges)],
        "dyn_target_calls": dict(dyn_target_calls),
        "static_in_degree": dict(static_in),
        "named": sorted(named),
        "unnamed": sorted(unnamed),
        "naming_queue": sorted(naming_queue),
        "thunk_keys": sorted(thunk_keys),
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
    print("SCCs: %d   thunks pass-through: %d   loader-trap edges excluded: %d"
          % (n_scc, len(thunk_levels),
             sum(1 for a, b in all_edges
                 if a in thunk_levels and b == LOADER_TRAP)))
    max_lvl = max(levels.values()) if levels else 0
    print("topological levels: 0..%d   nodes covered: %d"
          % (max_lvl, len(known)))

    # level summary  (named = fb join; to_name = unnamed minus thunk slots)
    print("\n=== LEVEL SUMMARY (true topological depth) ===")
    print("(named = function_bytes.name join; to_name = unnamed minus %d thunk slots)"
          % len(thunk_keys))
    print("%-8s %8s %8s %8s %8s" % ("level", "total", "named", "unnamed", "to_name"))
    for lvl in sorted(by_level):
        nodes = by_level[lvl]
        n_nm = sum(1 for k in nodes if k in named)
        n_un = len(nodes) - n_nm
        n_tq = sum(1 for k in nodes if k in naming_queue)
        print("%-8d %8d %8d %8d %8d" % (lvl, len(nodes), n_nm, n_un, n_tq))

    # top 30 unnamed global Level-0 leaves (thunk slots excluded from queue)
    lvl0 = by_level.get(0, [])
    lvl0_queue = [k for k in lvl0 if k in naming_queue]
    print("\n=== TOP 30 UNNAMED GLOBAL LEVEL-0 LEAVES (naming queue) ===")
    print("(ranked dyn_calls DESC, static_in_degree DESC; thunk slots excluded)")
    for i, k in enumerate(lvl0_queue[:30], 1):
        info = cls[k]
        dc = dyn_target_calls.get(k, 0)
        si = static_in.get(k, 0)
        print("  %2d. %-13s %5dB %-6s in=%-3d dyn=%-8d ea=0x%X"
              % (i, k, info["size"], info["class"], si, dc, info["ea"]))
    if len(lvl0_queue) > 30:
        print("  ... +%d more unnamed Level-0 in queue" % (len(lvl0_queue) - 30))

    # audit totals
    print("\n=== AUDIT TOTALS ===")
    print("functions: %d   named (fb join): %d   unnamed: %d   thunk slots: %d"
          % (len(known), len(named), len(unnamed), len(thunk_keys)))
    print("naming_queue (unnamed - thunks): %d   Level-0 queue: %d"
          % (len(naming_queue), len(lvl0_queue)))

    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()