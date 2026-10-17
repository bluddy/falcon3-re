"""Finding 56: is R05_1E10's fixup `off` indexed from the record base, or from
`w0 + 0x154` paras (= +0x1540 bytes, IDA 0x2E100 + 0x1540 = 0x2F640)?

For every fixup pair (off, seg) of a record, read the word at BOTH candidate
bases and ask the only question that matters: after `word + 0x1000` does it
name a real IDA paragraph (i.e. does `((word+0x1000) << 4)` land in a segment
we actually wrote / in the resident image)?  A word that is not a segment at
either base means the pair is something else.

Record 30 is the control: finding 55 measured its far-operands aligning at
delta 0.

Usage: venv\\Scripts\\python tools\\_hyp56.py
"""
import json
import struct
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
DIR = 0x1E24F
place = {p["idx"]: p for p in json.load(open("analysis/ida_falconcd/overlay_placement.json"))}

# every linear range the IDB actually has bytes in (resident image + placements)
WINDOWS = [(0x10000, 0x2CF60, "resident")]
for p in place.values():
    if p.get("ida_ea") is not None and p["ida_len"]:
        WINDOWS.append((p["ida_ea"], p["ida_ea"] + p["ida_len"], p["seg_name"]))


def para_ok(word):
    """Is `word` a link-time paragraph whose +0x1000 form lands in a real window?"""
    if word > 0xFFFF:
        return False
    lin = ((word + 0x1000) & 0xFFFF) << 4
    return any(lo <= lin < hi for lo, hi, _ in WINDOWS)


print("candidate sub-segment offsets inside a record (w0 -> code para):")
for idx in (5, 29, 27, 28, 30, 1):
    if idx not in place:
        continue
    o = DIR + idx * 18
    w0, _, w2, _, span, nfx, _, _, _ = struct.unpack_from("<9H", EXE, o)
    tpos = (0xFFFA0 + (w2 << 4)) if idx >= 50 else (w2 << 4)
    segs = [struct.unpack_from("<H", EXE, tpos + k * 4 + 2)[0] for k in range(nfx)]
    from collections import Counter
    c = Counter(segs)
    top = [(hex(s), n) for s, n in c.most_common(4)]
    extra = "  <-- top seg = w0+0x%X (%d paras)" % (c.most_common(1)[0][0] - w0,
                                                    c.most_common(1)[0][0] - w0) \
        if c.most_common(1) else ""
    print("  idx=%-3d w0=0x%04X nfx=%-5d distinct_segs=%-3d top=%s%s"
          % (idx, w0, nfx, len(c), top, extra))

print("")
print("fixup word read at each candidate base: does word+0x1000 name a real window?")
print("%-5s %-13s %7s %14s %14s %14s" % ("idx", "seg_name", "nfx",
                                        "base=data_file", "base=+0x1540", "neither"))
for idx in (5, 29, 30, 27, 1, 3):
    if idx not in place:
        continue
    p = place[idx]
    if p["addr"] == "skip" or not p["data_file"]:
        continue
    o = DIR + idx * 18
    _w0, _, w2, _, span, nfx, _, _, _ = struct.unpack_from("<9H", EXE, o)
    tpos = (0xFFFA0 + (w2 << 4)) if idx >= 50 else (w2 << 4)
    if tpos + nfx * 4 > len(EXE):
        continue
    a = b = neither = oob = 0
    for k in range(nfx):
        off, _seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
        f0 = p["data_file"] + off
        f1 = p["data_file"] + 0x1540 + off
        ok0 = f0 + 2 <= len(EXE) and para_ok(struct.unpack_from("<H", EXE, f0)[0])
        ok1 = f1 + 2 <= len(EXE) and para_ok(struct.unpack_from("<H", EXE, f1)[0])
        if ok0 and ok1:
            a += 1
            b += 1
        elif ok0:
            a += 1
        elif ok1:
            b += 1
        else:
            neither += 1
    print("%-5d %-13s %7d %14d %14d %14d"
          % (idx, p["seg_name"], nfx, a, b, neither))

# the far-operand cross-check: for record 5, the fixups that DO point at a far
# call's segment word -- which base are their offs consistent with?
print("")
print("record 5 far-operand cross-check (finding 55's 398/412):")
p = place[5]
_o, _, w2, _, _sp, nfx, _, _, _ = struct.unpack_from("<9H", EXE, DIR + 5 * 18)
tpos = w2 << 4
offs = [struct.unpack_from("<H", EXE, tpos + k * 4)[0] for k in range(nfx)]
off_set = set(offs)
blob = EXE[p["data_file"]:p["data_file"] + p["ida_len"]]
far_rel = []
i = 0
while i < len(blob) - 5:
    if blob[i] in (0x9A, 0xEA):
        far_rel.append(i + 3)
        i += 5
    else:
        i += 1
hit0 = sum(1 for r in far_rel if r in off_set)
hit1 = sum(1 for r in far_rel if (r - 0x1540) in off_set)
print("  far segword rels=%d ; off == rel        -> %d" % (len(far_rel), hit0))
print("                       off == rel - 0x1540 -> %d" % hit1)
