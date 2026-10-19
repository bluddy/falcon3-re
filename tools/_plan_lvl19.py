import sys, json, io
sys.stdout.reconfigure(encoding='utf-8')
targets = json.load(open('analysis/ida_falconcd/level19_targets.json'))
keys = [k for v in targets.values() for k in v]
trunc = json.load(open('analysis/ida_falconcd/level19_trunc.json'))
tr = set(trunc['truncated']) if isinstance(trunc, dict) else set(trunc)
fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
cg = json.load(open('analysis/traces/callgraph_partial.json'))

# block line offsets in full.txt (truncated fns) and disasm.txt (non-trunc)
def block_offsets(path):
    import re
    lines = io.open(path, encoding='utf-8', errors='replace').read().split('\n')
    offs = {}
    for i, l in enumerate(lines):
        m = re.match(r'^(?:#\d+\s+)?([A-Za-z_][\w@]+)\s+ea=0x', l)
        if m:
            offs[m.group(1)] = i + 1
    return offs, len(lines)

fo, fl = block_offsets('analysis/ida_falconcd/level19_full.txt')
do, dl = block_offsets('analysis/ida_falconcd/level19_disasm.txt')

nfb = {k: fb[k] for k in keys}
order = sorted(keys, key=lambda k: (-nfb[k]['size'], k))
B = 6
batches = [order[i::B] for i in range(B)]
print("total %d  trunc %d  nontrunc %d" % (len(keys), len(tr), len(keys)-len(tr)))
print("full.txt %d lines, disasm.txt %d lines" % (fl, dl))
for bi, batch in enumerate(batches, 1):
    tsz = sum(nfb[k]['size'] for k in batch)
    nt = sum(1 for k in batch if k in tr)
    print("\n=== BATCH %d: %d fns, %d truncated, %d bytes ===" % (bi, len(batch), nt, tsz))
    for k in batch:
        path = 'full' if k in tr else 'disasm'
        o = fo.get(k) if k in tr else do.get(k)
        print("  %-12s size=%5d off=%s %s" % (k, nfb[k]['size'], o, path))
json.dump({b: batches[i] for i, b in enumerate(range(1, B+1))},
          open('analysis/ida_falconcd/level19_batches.json', 'w'), indent=1)
print("\nwrote level19_batches.json")
