# ------------------------------------------------------------------ register manifests
def overlaps(a, b, lo, hi):
    return a < hi and b > lo


def reg_state(rng, fns):
    lo, hi = rng["range"]
    keep = {(f["key"], f["ea"], f["size"]) for f in rng["keep_fns"]}
    want = keep | {(f["key"], f["ea"], f["size"]) for f in rng["new_fns"]}
    have = {(k, a, b - a) for a, b, k in fns if lo <= a < hi}
    crossed = any(overlaps(a, b, lo, hi) and (a < lo or b > hi) for a, b, k in fns)
    holes_hit = any(overlaps(a, b, h["ea"], h["ea"] + h["size"]) for h in rng["data_holes"] for a, b, k in fns)
    if (have == want or have == keep) and not crossed and not holes_hit:
        if have == keep and rng["new_fns"]:
            starts = {a for a, b, k in fns}
            if any(f["ea"] not in starts and any(a < f["ea"] < b for a, b, k in fns) for f in rng["new_fns"]):
                return "vanished"
        return "ok"
    return "violated"


def rederive(origs, elo, ehi, fns, head):
    """live functions + still-free original holes over [elo, ehi), cut into gap-free runs"""
    role = {}
    for o in origs:
        role.update({f["key"]: "keep" for f in o["keep_fns"]})
        role.update({f["key"]: "new" for f in o["new_fns"]})
    items = [(a, b, "fn", k) for a, b, k in fns if overlaps(a, b, elo, ehi)]
    retired = []
    for o in origs:
        for h in o["data_holes"]:
            hlo, hhi = h["ea"], h["ea"] + h["size"]
            cov = covering(fns, hlo, hhi)
            if cov:
                retired.append(dict(h, range_name=o["name"],
                                    now_in=[{"key": k, "ea": a, "size": s} for k, a, s in cov]))
            else:
                items.append((hlo, hhi, "hole", h))
    items.sort(key=lambda t: t[0])
    runs = []
    for it in items:
        if runs and runs[-1][-1][1] == it[0]:
            runs[-1].append(it)
        elif runs and runs[-1][-1][1] > it[0]:
            sys.exit("overlap at 0x%X while re-deriving %s" % (it[0], origs[0]["name"]))
        else:
            runs.append([it])
    gaps = [(runs[i][-1][1], runs[i + 1][0][0]) for i in range(len(runs) - 1)]
    out, dropped = [], []
    for run in runs:
        r = {"name": None, "range": [run[0][0], run[-1][1]], "keep_fns": [], "new_fns": [], "data_holes": []}
        for a, b, kind, x in run:
            if kind == "hole":
                r["data_holes"].append(x)
            else:
                r[(role.get(x) or ("keep" if x in head else "new")) + "_fns"].append(
                    {"key": x, "ea": a, "size": b - a})
        # a range of keep functions only is always 'pending' and pins nothing: leave it out
        (out if r["new_fns"] or r["data_holes"] else dropped).append(r)
    for i, r in enumerate(out):
        r["name"] = origs[0]["name"] if i == 0 else "%s.%d" % (origs[0]["name"], i)
    return out, dropped, retired, gaps


def plan_registers(head, now, gap_sha):
    fns = spans(now)
    docs = [json.loads(p.read_text(encoding="utf-8")) for p in REGMANS]
    retired_ranges, retired_holes, rewrites, gaps_out = [], [], [], []
    for p, doc in zip(REGMANS, docs):
        groups, state = [], {}
        for i, rng in enumerate(doc["ranges"]):
            st = state[i] = reg_state(rng, fns)
            if st == "vanished":
                f = rng["new_fns"][0]
                retired_ranges.append({"manifest": p.name, "name": rng["name"], "range": rng["range"],
                                       "new_fns": rng["new_fns"], "keep_fns": rng["keep_fns"],
                                       "why": "planned %s starts mid-body of live %s" % (
                                           f["key"], [{"key": k, "ea": a, "size": b - a}
                                                      for a, b, k in fns if a < f["ea"] < b])})
            elif st == "violated":
                lo, hi = rng["range"]
                cov = covering(fns, lo, hi)
                groups.append([min([lo] + [a for _k, a, _s in cov]), max([hi] + [a + s for _k, a, s in cov]), [i]])
        groups.sort(key=lambda g: g[0])
        merged = []
        for g in groups:
            if merged and g[0] < merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], g[1])
                merged[-1][2] += g[2]
            else:
                merged.append(g)
        slot = {}
        for elo, ehi, idxs in merged:
            origs = [doc["ranges"][i] for i in idxs]
            for j, o in enumerate(doc["ranges"]):
                if state[j] == "ok" and overlaps(o["range"][0], o["range"][1], elo, ehi):
                    sys.exit("re-derived 0x%X..0x%X (%s) meets intact range %s" % (elo, ehi, origs[0]["name"], o["name"]))
            new, dropped, retired, gaps = rederive(origs, elo, ehi, fns, head)
            for h in retired:
                retired_holes.append(dict(h, manifest=p.name))
            for glo, ghi in gaps:
                gaps_out.append({"manifest": p.name, "range_name": origs[0]["name"], "ea": glo, "size": ghi - glo,
                                 "sha256": gap_sha.get((glo, ghi)), "class": GAP_CLASS.get((glo, ghi))})
            rewrites.append({"manifest": p.name, "before": origs, "after": new, "dropped_keep_only": dropped})
            slot[min(idxs)] = new
        ranges = []
        for i, rng in enumerate(doc["ranges"]):
            if state[i] == "ok":
                ranges.append(rng)
            elif i in slot:
                ranges += slot[i]
        doc["ranges"] = ranges
        doc["n_new_fns"] = sum(len(r["new_fns"]) for r in ranges)
        doc["n_keep_fns"] = sum(len(r["keep_fns"]) for r in ranges)
        doc["n_holes"] = sum(len(r["data_holes"]) for r in ranges)
        doc["hole_bytes"] = sum(h["size"] for r in ranges for h in r["data_holes"])
    return docs, {"retired_ranges": retired_ranges, "retired_holes": retired_holes,
                  "rewrites": rewrites, "untiled_gaps": gaps_out}


GAP_CLASS = {}


def load_gaps():
    """sha256 + item classes of the gaps between re-derived runs (analysis/s1/gap_probe.py on the live IDB)"""
    p = ROOT / "analysis/s1/gap_probe.json"
    out = {}
    if p.exists():
        for g in json.loads(p.read_text(encoding="utf-8")):
            out[(g["lo"], g["hi"])] = g["sha256"]
            cls = sorted({h[1] for h in g["heads"]})
            GAP_CLASS[(g["lo"], g["hi"])] = "%s: %s" % ("/".join(cls), g["heads"][0][4].split(";")[0].strip())
    return out
