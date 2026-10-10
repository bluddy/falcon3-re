from pathlib import Path
import struct

d = Path('game/FALCONCD.EXE').read_bytes()
tail = 0x1fb51
t = d[tail:]

base = 0x2c00 + 0x1AA3 * 16 + 0x0C1F
recs = []
for i in range(100):
    o = base + i * 18
    if o + 18 > len(d):
        break
    w = struct.unpack_from('<9H', d, o)
    if not (0x100 <= w[0] <= 0x9000):
        break
    recs.append(dict(id=w[7], seg=w[0], off=w[2], A=w[4], B=w[5], C=w[6]))

recs_sorted = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])
print('Record gaps (sorted by tail offset):')
for i in range(len(recs_sorted) - 1):
    r1, r2 = recs_sorted[i], recs_sorted[i + 1]
    gap = r2['off'] - (r1['off'] + r1['A'])
    if gap > 0:
        gb = bytes(d[tail + r1['off'] + r1['A']:tail + r2['off']])
        print(f"id{r1['id']:3d}->id{r2['id']:3d} gap={gap:4d} B={r1['B']:4d} C={r1['C']:04x} seg={r1['seg']:04x}  {gb[:32].hex()}")
    elif gap < 0:
        print(f"id{r1['id']:3d}->id{r2['id']:3d} OVERLAP={-gap}")