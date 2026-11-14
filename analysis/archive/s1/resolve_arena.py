"""Host-side: resolve every direct far call/jmp into the shared 0x1E10 arena (R05/R27/R28/R29)
to exactly one variant.  Input farcall_probe.json + segbase.json.  Output arena_resolve.json."""
import json, collections
D = r"C:/Users/ybarnoy/projects/falcon3/analysis/s1/"
C = json.load(open(D + "farcall_probe.json"))["calls"]
S = json.load(open(D + "segbase.json"))["segs"]
anch = collections.defaultdict(set)
for name, s, e, b, sel, bits in S:
    if name[:3] in ("R05", "R27", "R28", "R29"):
        anch[name[:3]].add(int(name[4:8], 16))


def st(v, n):
    s = v[n][1]
    return "F" if s["fs"] else "h" if s["head"] else "c" if s["code"] else "x"


rows, cnt = [], collections.Counter()
for x in C:
    v = x["var"]
    if not v:
        continue
    link = x["seg"] - 0x1000
    own = [n for n in v if link in anch[n]]
    cs = x["cseg"][:3]
    if cs in v and cs in own:
        rule, pick = "intra", cs
    elif len(own) == 1:
        rule, pick = "segword", own[0]
    else:
        pool = own or list(v)
        fs = [n for n in pool if st(v, n) == "F"]
        hd = [n for n in pool if st(v, n) in "Fh"]
        if len(fs) == 1:
            rule, pick = "decode_fs", fs[0]
        elif len(hd) == 1:
            rule, pick = "decode_head", hd[0]
        else:
            rule, pick = "ambiguous", None
    cur = sorted(n for n in v for r in x["refs"] if r[0] == v[n][0])
    tgt = v[pick][0] if pick else None
    k = (rule, pick, st(v, pick) if pick else "-", "ok" if cur == [pick] else "fix")
    cnt[k] += 1
    rows.append({"ea": x["ea"], "op": x["op"], "seg": x["seg"], "off": x["off"], "rule": rule, "pick": pick,
                 "target": tgt, "tstate": st(v, pick) if pick else None, "cur": cur,
                 "cur_eas": [r[0] for r in x["refs"]], "cseg": x["cseg"]})
for k, n in sorted(cnt.items(), key=lambda z: -z[1]):
    print(n, k)
json.dump({"anchors": {k: sorted(v) for k, v in anch.items()}, "rows": rows}, open(D + "arena_resolve.json", "w"))
