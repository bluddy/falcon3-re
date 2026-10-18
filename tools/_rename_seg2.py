"""Fix the two leftover renames: batch9_names.json (sub_112F6) and the
corrupted hypothesis inside routines.yaml's ea=0x14152 entry."""
import io, json, sys, yaml, re
sys.stdout.reconfigure(encoding='utf-8')

# 1) batch9_names.json
p = "analysis/ida_falconcd/batch9_names.json"
a = json.load(io.open(p, encoding="utf-8"))
if a.get("sub_112F6", [None])[0] != "segment_change_debounce_cx":
    a["sub_112F6"][0] = "segment_change_debounce_cx"
    json.dump(a, io.open(p, "w", encoding="utf-8"), indent=1)
    print("batch9_names.json: sub_112F6 -> segment_change_debounce_cx")

# 2) routines.yaml: find the entry with ea: 0x14152 and set its hypothesis
p = "registry/routines.yaml"
t = io.open(p, encoding="utf-8", newline="").read()
m = re.search(r"  - ea: 0x14152\r?\n((?:    .*\r?\n)*)", t)
assert m, "ea=0x14152 entry not found"
block = m.group(1)
fixed = re.sub(r'hypothesis: "[^"]*"',
               'hypothesis: "segment_bitfield_decode"', block, count=1)
assert fixed != block, "hypothesis not changed"
t = t[:m.start(1)] + fixed + t[m.end(1):]
io.open(p, "w", encoding="utf-8", newline="").write(t)
print("routines.yaml: ea=0x14152 hypothesis -> segment_bitfield_decode")

d = yaml.safe_load(io.open(p, encoding="utf-8").read())
# verify both hypotheses
bad = [r for r in d["routines"]
       if r.get("ea") in (0x112F6, 0x14152)
       and r.get("hypothesis") not in ("segment_change_debounce_cx",
                                       "segment_bitfield_decode")]
print("routines.yaml OK; bad hypotheses:", len(bad))