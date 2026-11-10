"""Plan the 0x1E10-arena variant selector repair (finding 123).

Problem: records R05 (real image at 0x2E100), R27, R28 and R29 (synthetic, IDA 0x11C3C0) are alternative
load images of the same RTLink overlay arena (w0 = 0x1E10).  IDA resolves every far operand seg:off through
the identity selector seg -> paragraph seg, i.e. into the R05 image, so ~4,300 far calls from the menu-time
overlays (R29, R30..R68) point into R05 bytes that are mid-instruction or data there.  R29 is the menu /
briefing variant (resident in main_menu/briefing/edit_flights/waypoints/pilots/armament memdumps), R05 the
sim one (opening/flight_takeoff/outside_view).

Host-side.  Input: analysis/s1/farcall_probe.json (tools/export_farcalls.py on a copy of the IDB).
Output: registry/variant_sel_expected.json, consumed by tools/apply_variant_selectors.py.

Resolution of each direct far call/jmp into the arena (first rule that decides wins):
  intra    the caller's segment family is one of the variants and owns the seg word as a segment anchor
  segword  exactly one variant owns the seg word as an anchor
  family   seg 0x3FA8 (link) is no anchor of any variant; all its callers are R29-family / menu overlays
           and the menu memdumps hold R29's bytes (prologues at +0/+43/+83) at runtime 0x3FA8 -> R29
  decode_fs / decode_head   otherwise: the one variant where the target is a function start / code head
  ambiguous                 left alone
Plan:
  selectors  R29-only anchors (+0x3FA8): selector seg+0x1000 -> R29 paragraph (identity -> R29 image).
             Planned only if no R05-family code uses that selector (far operand or segment register).
  crefs      far calls whose current code xrefs differ from [resolved target]: drop the non-user far
             crefs, add a user cref to the resolved target.  No del_items/create_insn (re-creating far
             calls made IDA shrink / drop 7 functions in exp_sel_all).
  drefs      code heads with a direct memory operand addressed through DS/ES holding a remapped selector:
             stale non-user drefs (computed into the R05 image) are dropped and the head re-created.
  func_moves function starting with 0x90 pad bytes whose resolved callers all enter right after the pad:
             start moved past the pad (IDA would otherwise move it itself while the cref is added).

Usage: python tools/plan_variant_selectors.py [--facts PATH]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "analysis/s1/farcall_probe.json"
MANIFEST = ROOT / "registry/variant_sel_expected.json"
W0 = 0x1E10
BASE = {"R05": 0x2E100, "R27": 0x10C9E0, "R28": 0x111530, "R29": 0x11C3C0}
EXTRA = {0x3FA8: "R29"}            # link seg word that is no segment anchor (rule "family")
FL_CF, FL_JF = 16, 18              # ida_xref.fl_CF / fl_JF


def tstate(v, n):
    s = v[n][1]
    return "F" if s["fs"] else "h" if s["head"] else "c" if s["code"] else "x"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", default=str(FACTS))
    a = ap.parse_args()
    F = json.loads(Path(a.facts).read_text())
    anch = collections.defaultdict(set)
    for name, *_ in F["segs"]:
        if name[:3] in BASE:
            anch[name[:3]].add(int(name[4:8], 16))
    r29x = sorted(anch["R29"] - anch["R05"] - anch["R27"] - anch["R28"])
    remap = {l + 0x1000: (BASE["R29"] >> 4) + (l - W0) for l in r29x}
    for l, var in EXTRA.items():
        remap[l + 0x1000] = (BASE[var] >> 4) + (l - W0)
    fam =lambda cseg: cseg[:3] if cseg[:3] in BASE else cseg   # noqa: E731

    rows, cnt = [], collections.Counter()
    for x in F["calls"]:
        v = x["var"]
        if not v:
            continue
        link = x["seg"] - 0x1000
        own = [n for n in v if link in anch[n]]
        cs = fam(x["cseg"])
        if cs in v and cs in own:
            rule, pick = "intra", cs
        elif len(own) == 1:
            rule, pick = "segword", own[0]
        elif link in EXTRA:
            rule, pick = "family", EXTRA[link]
        else:
            pool = own or list(v)
            fs = [n for n in pool if tstate(v, n) == "F"]
            hd = [n for n in pool if tstate(v, n) in "Fh"]
            rule, pick = ("decode_fs", fs[0]) if len(fs) == 1 else \
                ("decode_head", hd[0]) if len(hd) == 1 else ("ambiguous", None)
        cnt[(rule, pick)] += 1
        rows.append((x, rule, pick))

    # selector usage by the R05 family (a remap would mis-render / mis-ref them)
    users = collections.Counter()
    for x, rule, pick in rows:
        if x["seg"] in remap and pick != "R29":
            users[(x["seg"], "farcall", rule, pick)] += 1
    for rn, s, e, val, tag, sname in F["sreg_ranges"]:
        if sname[:3] in ("R05", "R27", "R28"):
            users[(val, "sreg", rn, sname)] += 1
    bad = {k[0] for k in users}
    if bad:
        print("selectors used outside R29 context (not remapped): %s" % sorted(users.items()))
    for s in bad:
        remap.pop(s, None)

    crefs, amb = [], []
    for x, rule, pick in rows:
        if pick is None:
            amb.append({"ea": x["ea"], "seg": x["seg"], "off": x["off"], "cseg": x["cseg"], "refs": x["refs"]})
            continue
        want = x["var"][pick][0]
        if x["seg"] in remap and want != (remap[x["seg"]] << 4) + x["off"]:
            raise SystemExit("0x%X: resolved target 0x%X != remapped selector target" % (x["ea"], want))
        cur = sorted(r[0] for r in x["refs"])
        if cur == [want]:
            continue
        crefs.append({"ea": x["ea"], "op": x["op"], "seg": x["seg"], "off": x["off"], "rule": rule,
                      "pick": pick, "to": want, "type": FL_CF if x["op"] == 0x9A else FL_JF,
                      "before": x["refs"], "tstate": tstate(x["var"], pick), "cseg": x["cseg"]})

    # function starting with nop padding whose callers enter just past it
    by_t = collections.defaultdict(list)
    for c in crefs:
        by_t[c["to"]].append(c)
    func_moves = []
    st = {}
    for x, rule, pick in rows:
        if pick:
            st[x["var"][pick][0]] = x["var"][pick][1]
    for t, cs in sorted(by_t.items()):
        s = st[t]
        if s["fin"] is not None and not s["fs"] and s["head"] and 0 < t - s["fin"] <= 3:
            func_moves.append({"from": s["fin"], "to": t, "callers": len(cs)})

    # data-xref heads
    drefs = []
    dcnt = collections.Counter()
    for h, size, regs, vals, mnem, dr in F["sreg_heads"]:
        if not any(v in remap for v in vals):
            continue
        stale = [d for d in dr if not d[2] and BASE["R05"] <= d[0] < BASE["R05"] + 0x388F0]
        dcnt["heads"] += 1
        dcnt["with_stale_dref"] += bool(stale)
        drefs.append({"ea": h, "size": size, "regs": regs, "mnem": mnem, "before": dr})

    doc = {
        "finding": 123,
        "selectors": [{"sel": s, "before": s, "after": p, "link": s - 0x1000} for s, p in sorted(remap.items())],
        "crefs": crefs,
        "dref_heads": drefs,
        "func_moves": func_moves,
        "ambiguous": amb,
        "rule_counts": {"%s:%s" % k: n for k, n in sorted(cnt.items(), key=lambda z: -z[1])},
    }
    MANIFEST.write_text(json.dumps(doc, indent=0))
    print("rules: %s" % sorted(cnt.items(), key=lambda z: -z[1]))
    print("selectors remapped: %d; cref fixes: %d (%s); ambiguous left: %d"
          % (len(remap), len(crefs), sorted(collections.Counter((c["rule"], c["tstate"]) for c in crefs).items()),
             len(amb)))
    print("dref heads: %s; func moves: %s" % (dict(dcnt), [("%X->%X" % (m["from"], m["to"]), m["callers"])
                                                         for m in func_moves]))
    print("wrote %s" % MANIFEST.relative_to(ROOT))


if __name__ == "__main__":
    main()
