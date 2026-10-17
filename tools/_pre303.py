"""Pre-flight for registering the 303 .RTLink thunk slots as functions.

  - which slots already are functions, and with what span
  - which slots are NOT functions
  - is any slot inside a LARGER existing function (would become a split)
  - is any slot's [slot, slot+8) overlapping an existing function partially

Usage: venv\\Scripts\\python tools\\_pre303.py
"""
import json
from bisect import bisect_right

fb = json.load(open("analysis/ida_falconcd/function_bytes.json"))
THUNK_LO, THUNK_HI, STRIDE = 0x2BD9D, 0x2C973, 10
n = (THUNK_HI - THUNK_LO) // STRIDE   # 0x2C973 is one-past-last
slots = [THUNK_LO + i * STRIDE for i in range(n)]
print("slots: %d  (0x%X .. 0x%X)" % (len(slots), slots[0], slots[-1]))

ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in fb.items())
starts = [a for a, _, _ in ivs]


def containing(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i]
    return None


is_fn = {}
sizes = {}
overlap_big = []
partial = []
for s in slots:
    hit = containing(s)
    if hit:
        is_fn[s] = hit[2]
        sizes[s] = hit[1] - hit[0]
        if hit[0] != s:
            overlap_big.append((s, hit[2], hit[0], hit[1]))
    else:
        # does [s, s+8) hit an existing function that starts inside it?
        h2 = containing(s + 7)
        if h2 and h2[0] != s:
            partial.append((s, h2[2], h2[0], h2[1]))

print("")
print("slots already functions : %d" % len(is_fn))
print("   span==8 (matches target end slot+8): %d" % sum(1 for v in sizes.values() if v == 8))
print("   span!=8:", sorted({v for v in sizes.values() if v != 8}))
from collections import Counter
print("   span histogram:", dict(sorted(Counter(sizes.values()).items())))
print("slots NOT a function    : %d" % (len(slots) - len(is_fn)))
print("")
print("slots sitting INSIDE a larger function (would be a SPLIT): %d" % len(overlap_big))
for s, k, a, b in overlap_big[:20]:
    print("   slot 0x%X inside %s (0x%X..0x%X, %d B)" % (s, k, a, b, b - a))
print("slots whose [slot,slot+8) is partially covered by a fn starting inside: %d"
      % len(partial))
for s, k, a, b in partial[:20]:
    print("   slot 0x%X  overlap fn %s starts 0x%X (0x%X..0x%X)" % (s, k, a, a, b))

# gaps in the table: any registered function that starts before a slot and ends after
print("")
print("first 6 not-a-function slots:", ["0x%X" % s for s in slots if s not in is_fn][:6])
print("last  6 not-a-function slots:", ["0x%X" % s for s in slots if s not in is_fn][-6:])
