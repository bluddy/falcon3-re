"""Truncation check for a dump_level1 disasm: compare each block's last
insn address against ea+size-4.  Writes <tag>_trunc.json (truncated keys)
and <tag>_full_targets.json (subset targets file for dump_full.py).
Usage: python tools/_trunc_check.py <disasm> <targets> <out_prefix>
"""
import json, re, sys, io

disasm, targets, prefix = sys.argv[1:4]
tg0 = json.load(open(targets, encoding="utf-8"))
tg = [k for v in tg0.values() for k in v] if isinstance(tg0, dict) else list(tg0)
fb = json.load(open("analysis/ida_falconcd/function_bytes.json", encoding="utf-8"))
raw = io.open(disasm, encoding="utf-8", errors="replace").read()

blocks = re.split(r"(?m)^#\d+ ", raw)[1:]
last = {}
for b in blocks:
    m = re.match(r"(\S+)\s+ea=(0x[0-9A-Fa-f]+)", b)
    if not m:
        continue
    name = m.group(1)
    addrs = re.findall(r"(?m)^  (0x[0-9A-Fa-f]+):", b)
    if addrs:
        last[name] = int(addrs[-1], 16)

trunc = []
for k in tg:
    ea = fb[k]["ea"]; size = fb[k]["size"]
    ln = last.get(k)
    if ln is None or ln < ea + size - 4:
        trunc.append(k)
print("blocks=%d targets=%d truncated=%d" % (len(last), len(tg), len(trunc)))
print(trunc)
json.dump(trunc, open(prefix + "_trunc.json", "w"), indent=1)
sub = ({kk: [k for k in vv if k in trunc] for kk, vv in tg0.items()}
       if isinstance(tg0, dict) else [k for k in tg if k in trunc])
json.dump(sub, open(prefix + "_full_targets.json", "w"), indent=1)
print("wrote %s_trunc.json and %s_full_targets.json" % (prefix, prefix))
