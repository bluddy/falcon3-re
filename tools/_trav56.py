"""Which thunk slots emit their JMP FAR (slot+3) today, and which don't?

Breaks finding 55's "27 of 303" down by the shape of the covering function, so
we know whether splitting sub_2BFCD / sub_2BE83 is actually required.

Usage: venv\\Scripts\\python tools\\_trav56.py
"""
import json
from bisect import bisect_right
from collections import Counter

fb = json.load(open("analysis/ida_falconcd/function_bytes.json"))
refs = json.load(open("analysis/ida_falconcd/callgraph_refs.json"))["refs"]
THUNK_LO, STRIDE, N = 0x2BD9D, 10, 303
slots = [THUNK_LO + i * STRIDE for i in range(N)]
srcs = {r[0] for r in refs}
dsts = {r[1] for r in refs}

ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in fb.items())
starts = [a for a, _, _ in ivs]


def containing(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i]
    return None


shape = Counter()
emit = Counter()
for s in slots:
    hit = containing(s)
    if hit is None:
        kind = "no-fn (unregistered slot)"
    elif hit[0] == s and (hit[1] - hit[0]) == 8:
        kind = "fn-start, span 8"
    elif hit[0] == s:
        kind = "fn-start, span %d" % (hit[1] - hit[0])
    else:
        kind = "INSIDE %s (span %d)" % (hit[2], hit[1] - hit[0])
    shape[kind] += 1
    emit[(kind, (s + 3) in srcs)] += 1

print("slot shape distribution:")
for k, v in shape.most_common():
    print("  %-34s %d" % (k, v))
print("")
print("%-34s %8s %8s" % ("shape", "emits+3", "silent"))
for kind, _ in shape.most_common():
    print("%-34s %8d %8d" % (kind, emit[(kind, True)], emit[(kind, False)]))

tot_e = sum(v for (k, b), v in emit.items() if b)
print("")
print("slots emitting a ref from slot+3: %d / %d" % (tot_e, N))

# for silent ones: is slot+3 even a decoded head? (no -- we can't tell host-side)
silent = [s for s in slots if (s + 3) not in srcs]
print("silent slots: %d ; of those not covered by any fn: %d"
      % (len(silent), sum(1 for s in silent if containing(s) is None)))

# incoming refs into the table, by covering function
into = [r for r in refs if THUNK_LO <= r[1] <= THUNK_LO + (N - 1) * STRIDE + 10]
res_in = Counter()
for r in into:
    hit = containing(r[1])
    res_in["resolves -> %s" % hit[2] if hit else "UNRESOLVED"] += 1
print("")
print("refs INTO the thunk table: %d" % len(into))
for k, v in res_in.most_common(8):
    print("   %-34s %d" % (k, v))
