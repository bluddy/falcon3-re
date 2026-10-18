"""Finding 71 fix: IDA rejects names with the `seg_` dummy prefix (set_name
returns True but the auto-name survives).  Rename the two affected ledger
entries to `segment_*` equivalents in naming.yaml + routines.yaml +
batch10_names.json, then re-run naming.py apply/push.
"""
import io, json, sys, yaml
sys.stdout.reconfigure(encoding='utf-8')

RENAMES = {"seg_change_debounce_cx": "segment_change_debounce_cx",
           "seg_bitfield_decode": "segment_bitfield_decode"}
IDA_KEYS = {"sub_112F6": "segment_change_debounce_cx",
            "sub_14152": "segment_bitfield_decode"}

# 1) naming.yaml (LF preserved): replace the name: field of the two entries
p = "registry/naming.yaml"
t = io.open(p, encoding="utf-8", newline="").read()
n = 0
for ida_k, new in IDA_KEYS.items():
    old_blk = "  - ida: %s\n    name: " % ida_k
    i = t.index(old_blk)
    j = t.index("\n", i + len(old_blk))
    cur = t[i + len(old_blk):j]
    if cur != new:
        t = t[:i + len(old_blk)] + new + t[j:]
        n += 1
        print("naming.yaml: %s %s -> %s" % (ida_k, cur, new))
io.open(p, "w", encoding="utf-8", newline="").write(t)
d = yaml.safe_load(io.open(p, encoding="utf-8").read())
print("naming.yaml OK, symbols:", len(d["symbols"]))

# 2) routines.yaml (CRLF): hypothesis: field of the two ea entries
p = "registry/routines.yaml"
t = io.open(p, encoding="utf-8", newline="").read()
for ida_k, new in IDA_KEYS.items():
    for old in RENAMES:
        # hypothesis: "old"  (CRLF endings)
        pat = 'hypothesis: "%s"' % old
        # only replace within the entry keyed by this ida_k's ea -- the
        # hypothesis value is unique enough (these two names are unique)
        cnt = t.count(pat)
        if cnt == 1:
            t = t.replace(pat, 'hypothesis: "%s"' % new)
            print("routines.yaml: hypothesis %s -> %s" % (old, new))
        else:
            print("routines.yaml: %s found %d times -- SKIP" % (pat, cnt))
io.open(p, "w", encoding="utf-8", newline="").write(t)
d = yaml.safe_load(io.open(p, encoding="utf-8").read())
print("routines.yaml OK, entries:", len(d.get("routines", [])))

# 3) batch10_names.json
p = "analysis/ida_falconcd/batch10_names.json"
a = json.load(io.open(p, encoding="utf-8"))
c = 0
for k, v in a.items():
    if v[0] in RENAMES:
        v[0] = RENAMES[v[0]]
        c += 1
json.dump(a, io.open(p, "w", encoding="utf-8"), indent=1)
print("batch10_names.json: renamed %d" % c)