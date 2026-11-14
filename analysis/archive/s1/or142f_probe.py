import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idautils, idaapi
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142f.txt", "w")
BASE = 0x6E0B0
cands = [0x6E76A, 0x6E78D, 0x6E7B3, 0x6E809, 0x6E851, 0x6E7C7]
# retf-ended handlers: find starts = byte after each retf in 6E76A..6E8B7 by sweeping my own decode is hard; just search words
want = {c - BASE: c for c in cands}
hits = []
for a in range(0x6E0B0, 0x6F900):
    w = ida_bytes.get_word(a)
    if w in want: hits.append((a, w, want[w]))
out.write("word hits: %s\n" % [("%X=%04X->%X" % h) for h in hits])
# also E8/E9 rel16 targets landing on candidates, and eb/7x rel8
for a in range(0x6E0B0, 0x6F900):
    b = ida_bytes.get_byte(a)
    if b in (0xE8, 0xE9):
        t = (a + 3 + ida_bytes.get_word(a + 1)) & 0xFFFF
        t += 0  # same segment
        tgt = (a & ~0xFFFF) + t if False else None
    # compute with 64K-aligned wrap is wrong for linear; do signed
    if b in (0xE8, 0xE9):
        d = ida_bytes.get_word(a + 1); d = d - 0x10000 if d & 0x8000 else d
        t = a + 3 + d
        if t in cands: out.write("rel16 %02X at %X -> %X\n" % (b, a, t))
    if (0x70 <= b <= 0x7F) or b in (0xEB, 0xE2, 0xE3):
        d = ida_bytes.get_byte(a + 1); d = d - 256 if d & 0x80 else d
        t = a + 2 + d
        if t in cands: out.write("rel8 %02X at %X -> %X\n" % (b, a, t))
out.close(); idc.qexit(0)
