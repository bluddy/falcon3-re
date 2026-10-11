import struct
from pathlib import Path
from collections import Counter

EXE = Path('game/FALCONCD.EXE').read_bytes()
DIR_FILE = 0x1E24F
TAIL_PARA = 0x1FB50

rows = []
for i in range(70):
    o = DIR_FILE + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows.append(dict(idx=i, w0=w0, w2=w2, span=w4, fixups=w5))

OV = {r['w0'] for r in rows} | {0x1D0D, 0x1D31, 0x1EFE}

FAIL = [5, 16, 28, 29, 30, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
        61, 62, 63, 64, 65, 66, 67, 68, 69]

for i in FAIL:
    r = rows[i]
    bases = []
    if r['w2'] >= 0x1000:
        bases = [r['w2'] << 4]
    else:
        bases = [TAIL_PARA + (r['w2'] << 4), 0x1FB51 + r['w2']]
    for b in bases:
        if b + 64 > len(EXE):
            continue
        dws = struct.unpack_from('<16I', EXE, b)
        segs = [v >> 16 for v in dws]
        offs = [v & 0xFFFF for v in dws]
        inov = sum(1 for s in segs if s in OV)
        print('idx%-3d w2=%-6X base=%-8X inOV=%2d/16 segs=%s offs=%s' % (
            i, r['w2'], b, inov,
            ' '.join('%04X' % s for s in segs[:8]),
            ' '.join('%04X' % o for o in offs[:8])))
    # where in window are segs in OV concentrated? scan stride 4 counting runs
    b0 = bases[0]
    best = (0, 0)
    for p in range(b0, min(b0 + r['span'] * 16 + r['fixups'] * 4 + 0x200, len(EXE) - 8), 4):
        s = struct.unpack_from('<I', EXE, p)[0] >> 16
        if s in OV:
            best = (max(best[0], 1), p)
    print()
