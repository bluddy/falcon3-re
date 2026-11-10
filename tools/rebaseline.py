#!/usr/bin/env python3
"""Re-baseline the committed ground truth on the repaired live IDB (finding 124).

The live IDB is canonical: function_bytes.json (tools/extract_ida_bytes.py on a copy of it) is the new
truth, and the gates' committed inputs are re-derived from it instead of the IDB being pushed back
towards an older extract.  Two steps, both host side and idempotent:

  python tools/rebaseline.py plan     registry/rebaseline_expected.json  (HEAD -> live record: LOST with
                                      the live functions now covering the old span, CHANGED with exact
                                      old/new size + sha256, SPLIT, retired register ranges and holes)
                                      + the three register manifests re-derived where the live IDB
                                      contradicts them (DRY=1: report only)
  python tools/rebaseline.py ledger   registry/naming.yaml + registry/routines.yaml follow the live
                                      names: entries whose function is gone or whose name the IDB no
                                      longer carries are dropped, IDB user names win conflicts, IDB
                                      user names missing from the ledger are added (DRY=1: report only)

Register ranges are re-derived as follows.  A range the live functions no longer tile (a function grew
across its edge, shrank inside it, or absorbed a planned function) is widened to every live function
that overlaps it, merged with any other contradicted range it then meets, and cut into maximal gap-free
runs of live functions (the manifests tile exactly; gaps live between ranges).  A function keeps its
new/keep role; functions that are new to the range are 'new' when HEAD did not have them.  A pending
range whose planned function now starts mid-body of a live function is retired, as is any hole a live
function now covers (verified code: 0x6DF27 is the rest of r06_trig_accum_6de83, 0x161B10 is the
`enter 18h,0` head of a 1,423 B routine with 37 callers).
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FB = ROOT / "analysis/ida_falconcd/function_bytes.json"
OUT = ROOT / "registry/rebaseline_expected.json"
REGMANS = [ROOT / "registry" / n for n in
           ("upper_register_expected.json", "resident_register_expected.json", "overlays_register_expected.json")]
LEDGER = ROOT / "registry/naming.yaml"
ROUTINES = ROOT / "registry/routines.yaml"
TODAY = "2026-11-10"
DRY = bool(os.environ.get("DRY"))


def git_show(path):
    r = subprocess.run(["git", "show", "HEAD:" + path], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode:
        sys.exit("cannot read HEAD:%s: %s" % (path, r.stderr[:300]))
    return r.stdout


def sha(hexstr):
    return hashlib.sha256(bytes.fromhex(hexstr or "")).hexdigest()


def write_json(path, doc):
    """indent=1 + CRLF, the committed format of the registry manifests"""
    text = json.dumps(doc, indent=1).replace("\n", "\r\n")
    if DRY:
        print("  (dry) would write %s" % path.relative_to(ROOT))
    else:
        path.write_bytes(text.encode("utf-8"))


def write_yaml(path, doc):
    text = yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)
    if DRY:
        print("  (dry) would write %s" % path.relative_to(ROOT))
    else:
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def spans(fb):
    return sorted((v["ea"], v["ea"] + v["size"], k) for k, v in fb.items())


def covering(fns, lo, hi):
    return [(k, a, b - a) for a, b, k in fns if a < hi and b > lo]


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
    base = {o["range"][0]: o["name"] for o in origs}
    for i, r in enumerate(out):
        r["name"] = base.get(r["range"][0]) or (origs[0]["name"] if i == 0 else "%s.%d" % (origs[0]["name"], i))
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


def plan():
    head = json.loads(git_show("analysis/ida_falconcd/function_bytes.json"))
    now = json.loads(FB.read_text(encoding="utf-8"))
    fns = spans(now)
    led_head = {e["ida"]: e.get("name") for e in yaml.safe_load(git_show("registry/naming.yaml"))["symbols"]}

    lost, changed, split = [], [], []
    for k in sorted(set(head) - set(now), key=lambda k: head[k]["ea"]):
        a = head[k]
        lost.append({"key": k, "ea": a["ea"], "size": a["size"], "sha256": sha(a["bytes"]),
                     "ledger_name": led_head.get(k),
                     "now_in": [{"key": kk, "ea": ea, "size": s}
                                for kk, ea, s in covering(fns, a["ea"], a["ea"] + a["size"])]})
    for k in sorted(set(head) & set(now), key=lambda k: head[k]["ea"]):
        a, b = head[k], now[k]
        if a["ea"] == b["ea"] and a["bytes"] == b["bytes"]:
            continue
        rec = {"key": k, "ea": a["ea"], "old_size": a["size"], "new_size": b["size"],
               "old_sha256": sha(a["bytes"]), "new_sha256": sha(b["bytes"])}
        # a shrink whose old span is tiled by live functions passes verify_rebuild's SPLIT rule as is
        if b["size"] < a["size"] and a["ea"] == b["ea"]:
            pos, n = a["ea"], 0
            starts = {v["ea"]: v["size"] for v in now.values()}
            while pos in starts and pos < a["ea"] + a["size"]:
                pos += starts[pos]
                n += 1
            if pos == a["ea"] + a["size"] and n > 1:
                split.append(dict(rec, tiled_by=n))
                continue
        changed.append(rec)
    names = {"adopted": [], "dropped": []}
    for k in sorted(set(head) & set(now), key=lambda k: now[k]["ea"]):
        old, new = led_head.get(k), now[k].get("name")
        if old != new and (old or new):
            (names["adopted"] if new else names["dropped"]).append({"key": k, "ea": now[k]["ea"],
                                                                     "ledger_name": old, "idb_name": new})

    docs, register = plan_registers(head, now, load_gaps())
    touched = {r["manifest"] for k in ("retired_ranges", "rewrites") for r in register[k]}
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    if not touched and prev.get("register"):
        register = prev["register"]          # manifests already re-derived by an earlier run
    for g in register["untiled_gaps"]:
        if not g["sha256"]:
            sys.exit("gap 0x%X (%d B) of %s not probed -- add it to analysis/s1/gap_probe_in.json and run "
                     "analysis/s1/gap_probe.py" % (g["ea"], g["size"], g["range_name"]))
    doc = {
        "finding": 124,
        "step": "S1c re-baseline: committed ground truth follows the repaired live IDB",
        "head": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip(),
        "counts": {"head_functions": len(head), "live_functions": len(now), "lost": len(lost),
                   "changed": len(changed), "split": len(split), "added": len(set(now) - set(head)),
                   "names_adopted": len(names["adopted"]), "names_dropped": len(names["dropped"]),
                   "retired_ranges": len(register["retired_ranges"]),
                   "retired_holes": len(register["retired_holes"]),
                   "rewritten_ranges": sum(len(r["before"]) for r in register["rewrites"]),
                   "untiled_gaps": len(register["untiled_gaps"])},
        "lost": lost, "changed": changed, "split": split, "names": names, "register": register,
    }
    print(json.dumps(doc["counts"]))
    for r in register["retired_ranges"]:
        print("  retire range %s %s 0x%X..0x%X: %s" % (r["manifest"][:5], r["name"], r["range"][0], r["range"][1], r["why"]))
    for h in register["retired_holes"]:
        print("  retire hole 0x%X (%d B, %s) now in %s" % (h["ea"], h["size"], h["range_name"], h["now_in"]))
    for rw in register["rewrites"]:
        print("  %s: %s -> %s  (keep-only runs dropped: %d)" % (
            rw["manifest"][:5], ["%s 0x%X..0x%X" % (o["name"], o["range"][0], o["range"][1]) for o in rw["before"]],
            ["%s 0x%X..0x%X n%d k%d h%d" % (r["name"], r["range"][0], r["range"][1], len(r["new_fns"]),
                                           len(r["keep_fns"]), len(r["data_holes"])) for r in rw["after"]],
            len(rw["dropped_keep_only"])))
    for g in register["untiled_gaps"]:
        print("  gap 0x%X %d B (%s) %s" % (g["ea"], g["size"], g["range_name"], g["class"]))
    write_json(OUT, doc)
    for p, d in zip(REGMANS, docs):
        if p.name not in touched:
            continue
        d["rebaseline"] = ("finding 124: ranges the repaired live IDB contradicts were re-derived from it; "
                           "registry/rebaseline_expected.json records before/after, retired holes and the "
                           "untiled gaps between the re-derived runs")
        write_json(p, d)


# ------------------------------------------------------------------ naming ledger + routines
def ledger():
    now = json.loads(FB.read_text(encoding="utf-8"))
    by_ea = {v["ea"]: (k, v) for k, v in now.items()}
    led = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    rout = yaml.safe_load(ROUTINES.read_text(encoding="utf-8"))
    syms, dropped, renamed = [], [], []
    for e in led["symbols"]:
        if e.get("kind", "function") != "function":
            syms.append(e)
            continue
        v = now.get(e["ida"])
        if v is None:
            dropped.append((e["ida"], e.get("name"), "function gone (inside a live function)"))
            continue
        if v.get("name") == e.get("name"):
            syms.append(e)
        elif v.get("name"):
            renamed.append((e["ida"], e.get("name"), v["name"]))
            e["name"] = v["name"]
            e["notes"] = ("%s Previous ledger name %s; the live IDB name wins (finding 124)."
                          % ((e.get("notes") or "").rstrip(), renamed[-1][1])).strip()
            syms.append(e)
        else:
            dropped.append((e["ida"], e.get("name"), "the live IDB carries no user name (%d B now)" % v["size"]))
    have = {e["ida"] for e in syms}
    added = []
    for k, v in sorted(now.items(), key=lambda kv: kv[1]["ea"]):
        if v.get("name") and k not in have:
            added.append({"ida": k, "name": v["name"], "kind": "function",
                          "notes": "User name in the live IDB (%d B at 0x%X), adopted into the ledger "
                                   "(finding 124). conf: idb" % (v["size"], v["ea"])})
    last_fn = max(i for i, e in enumerate(syms) if e.get("kind", "function") == "function")
    syms[last_fn + 1:last_fn + 1] = added
    led["symbols"] = syms

    gone_r, resized, rehyp = [], [], []
    led_name = {e["ida"]: e.get("name") for e in syms if e.get("kind", "function") == "function"}
    dropped_keys = {d[0] for d in dropped}
    keep_r = []
    for r in rout["routines"]:
        hit = by_ea.get(r["ea"])
        if hit is None:
            gone_r.append((r["ea"], r.get("hypothesis"), r.get("port_status")))
            if r.get("port_status") not in (None, "unported"):
                sys.exit("routine 0x%X (%s) is %s but its function is gone" % (r["ea"], r.get("hypothesis"),
                                                                             r.get("port_status")))
            continue
        k, v = hit
        touched = False
        if r.get("size") != v["size"]:
            if r.get("port_status") not in (None, "unported"):
                sys.exit("routine 0x%X (%s) is %s but its size changed" % (r["ea"], r.get("hypothesis"),
                                                                        r.get("port_status")))
            resized.append((r["ea"], r["size"], v["size"]))
            r["size"] = v["size"]
            touched = True
        want = led_name.get(k)
        if k in dropped_keys and r.get("hypothesis"):
            rehyp.append((r["ea"], r["hypothesis"], None))
            r["notes"] = ("%s Hypothesis %s dropped: the live IDB carries no name (finding 124)."
                          % ((r.get("notes") or "").rstrip(), r["hypothesis"])).strip()
            r["hypothesis"] = None
            touched = True
        elif want and r.get("hypothesis") and r["hypothesis"] != want:
            rehyp.append((r["ea"], r["hypothesis"], want))
            r["hypothesis"] = want
            touched = True
        if touched:
            r["updated"] = TODAY
        keep_r.append(r)
    rout["routines"] = keep_r

    print("ledger: %d -> %d symbols (%d dropped, %d renamed to the IDB name, %d added)"
          % (len(yaml.safe_load(LEDGER.read_text(encoding="utf-8"))["symbols"]), len(syms), len(dropped),
             len(renamed), len(added)))
    for d in dropped:
        print("  drop   %-14s %-36s %s" % d)
    for r in renamed:
        print("  rename %-14s %s -> %s" % r)
    for a in added:
        print("  add    %-14s %s" % (a["ida"], a["name"]))
    print("routines: %d removed (function gone), %d resized, %d hypotheses changed"
          % (len(gone_r), len(resized), len(rehyp)))
    for ea, old, new in rehyp:
        print("  hypothesis 0x%X %s -> %s" % (ea, old, new))
    write_yaml(LEDGER, led)
    write_yaml(ROUTINES, rout)


if __name__ == "__main__":
    {"plan": plan, "ledger": ledger}[sys.argv[1]]()
