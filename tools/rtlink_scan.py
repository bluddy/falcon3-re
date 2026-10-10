"""Scan the RTLink/Plus overlay directory embedded in FALCONCD.EXE.

The directory lives inside the resident image and is walked by the overlay
manager at 1aa3:0590 (entry thunks call it with a record id).  Each entry is
18 bytes of little-endian words:

    0  load segment (runtime)
    2  constant (0x12ed here)
    4  tail-relative data offset
    6  constant (0x400 here)
    8  A  - record size in bytes
   10  B  - ? (small subset of A for many entries)
   12  C  - flags / segment-group id
   14  id - overlay record id (matches thunk id)
   16  A2 - duplicate of A
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mzparse import MZ  # noqa: E402


def main():
    m = MZ(sys.argv[1] if len(sys.argv) > 1 else "../game/FALCONCD.EXE")
    # overlay manager data segment + table offset (from the entry thunk path)
    seg, off = 0x1AA3, 0x0C1F
    base = m.file_off(seg, off)
    rows = []
    i = 0
    while True:
        o = base + i * 18
        if o + 18 > len(m.data):
            break
        w = struct.unpack_from("<9H", m.data, o)
        if not (0x100 <= w[0] <= 0x9000):
            break
        rows.append(dict(idx=i, seg=w[0], const1=w[1], off=w[2], const2=w[3],
                         A=w[4], B=w[5], C=w[6], id=w[7], A2=w[8]))
        i += 1
    tail = m.hdr + m.imagesize
    print(f"table file offset {base:#x}, tail start {tail:#x}, {len(rows)} entries")
    print(f"{'#':>3} {'id':>4} {'seg':>5} {'off':>7} {'file':>9} "
          f"{'A':>6} {'B':>6} {'C':>5} {'delta':>7}")
    prev_off = None
    for r in rows:
        fo = tail + r["off"]
        delta = (r["off"] - prev_off) if prev_off is not None else 0
        print(f"{r['idx']:3d} {r['id']:4x} {r['seg']:5x} {r['off']:7x} "
              f"{fo:9x} {r['A']:6d} {r['B']:6d} {r['C']:5x} {delta:7d}")
        prev_off = r["off"]


if __name__ == "__main__":
    main()
