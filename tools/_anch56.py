"""Finding 56 step 4b: for R05_1E10's fixup entries, which base is right --
record base (off) or the `seg`-paragraph anchor ((seg-w0)*16 + off)?

Restricted to the dominant anchor (seg = w0+0x154 = 0x1F64) so the comparison
is like-for-like, and checks the anchor against the name table that begins at
exactly that offset.

Usage: venv\\Scripts\\python tools\\_anch56.py
"""
import struct
from collections import Counter
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
DIR = 0x1E24F
IDX = 5
w0, _w1, w2, _w3, span, nfx, _w6, _idf, _ds = struct.unpack_from("<9H", EXE, DIR + IDX * 18)
tpos = w2 << 4

place = {p["idx"]: p for p in __import__("json").load(
    open("analysis/ida_falconcd/overlay_placement.json"))}[IDX]
DATA = place["data_file"]
IDA_EA = place["ida_ea"]
LEN = place["ida_len"]

# windows a +0x1000-adjusted paragraph may legitimately name
import json as _j
places = _j.load(open("analysis/ida_falconcd/overlay_placement.json"))
WIN = [(0x10000, 0x2CF60)]
for p in places:
    if p.get("ida_ea") is not None and p["ida_len"]:
        WIN.append((p["ida_ea"], p["ida_ea"] + p["ida_len"]))


def ok(word):
    if word > 0xFFFF:
        return False
    lin = ((word + 0x1000) & 0xFFFF) << 4
    return any(lo <= lin < hi for lo, hi in WIN)


# the name table at anchor +0 (file DATA+0x1540)
ANCHOR = 0x1540
nt_start = DATA + ANCHOR
nt_head = EXE[nt_start:nt_start + 6]
strings = EXE[nt_start + 6:nt_start + 60]
nt_len = strings.find(b"\x00\x00\x00") + 3 if b"\x00" in strings else 60
print("anchor = record base + 0x%X = file 0x%X = IDA 0x%X"
      % (ANCHOR, nt_start, IDA_EA + ANCHOR))
print("  name table head u16s: %s" % [hex(x) for x in struct.unpack("<3H", nt_head)])
print("  strings: %r" % strings[:60])
print("")

by_anchor = {}
for k in range(nfx):
    off, seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
    by_anchor.setdefault(seg, []).append(off)

print("%-9s %7s %10s %10s   %9s %9s %9s" %
      ("seg", "n", "off min", "off max", "base=off", "base=anch", "anchor>nt?"))
for seg, offs in sorted(by_anchor.items(), key=lambda x: -len(x[1]))[:6]:
    anchor = (seg - w0) * 16
    a_ok = b_ok = past = 0
    for off in offs:
        for base, flag in ((0, "a"), (anchor, "b")):
            pos = DATA + base + off
            if 0 <= pos + 2 <= len(EXE):
                w = struct.unpack_from("<H", EXE, pos)[0]
                if ok(w):
                    if flag == "a":
                        a_ok += 1
                    else:
                        b_ok += 1
        if anchor + off >= ANCHOR + 0x40:      # past the ~0x40B name table
            past += 1
    tag = "  <-- dominant (w0+0x%X)" % ((seg - w0)) if seg != w0 else "  (== w0, delta 0)"
    print("%-9s %7d %10s %10s   %9d %9d %9d%s"
          % (hex(seg), len(offs), hex(min(offs)), hex(max(offs)),
             a_ok, b_ok, past, tag))

# overall verdict restricted to entries whose anchor != 0
tot_a = tot_b = 0
for seg, offs in by_anchor.items():
    if seg == w0:
        continue
    anchor = (seg - w0) * 16
    for off in offs:
        for base, which in ((0, "a"), (anchor, "b")):
            pos = DATA + base + off
            if 0 <= pos + 2 <= len(EXE):
                w = struct.unpack_from("<H", EXE, pos)[0]
                if ok(w):
                    if which == "a":
                        tot_a += 1
                    else:
                        tot_b += 1
print("")
print("entries with a NON-ZERO anchor (seg != w0): base=off -> %d word-ok, "
      "base=anchor -> %d word-ok" % (tot_a, tot_b))

# how far past the name table do the dominant anchor's offs start?
offs = by_anchor.get(0x1F64, [])
offs_sorted = sorted(offs)
in_nt = sum(1 for o in offs_sorted if ANCHOR + o < ANCHOR + 0x40)
print("")
print("dominant anchor (seg=0x1F64): %d entries, off range 0x%X..0x%X"
      % (len(offs), offs_sorted[0], offs_sorted[-1]))
print("  whose absolute position falls INSIDE the 0x40B name table: %d" % in_nt)
print("  first 8 off values: %s" % [hex(x) for x in offs_sorted[:8]])
