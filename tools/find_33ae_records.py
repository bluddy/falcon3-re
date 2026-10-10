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

sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

print(f"{'id':>4} {'seg':>4} {'B':>6} {'first_8_bytes':>20} {'type0':>6} {'type1':>6}")
print("-" * 70)

for r in sorted_recs:
    if r['B'] == 0 or r['A'] < r['B']:
        continue
    fixup_off = r['off'] + r['A'] - r['B']
    fixup_data = t[fixup_off:fixup_off + min(r['B'], 8)]
    if len(fixup_data) >= 4:
        typ0 = struct.unpack_from('<H', fixup_data, 0)[0]
        typ1 = struct.unpack_from('<H', fixup_data, 4)[0] if len(fixup_data) >= 6 else 0
        first_8 = fixup_data[:8].hex()
        print(f"{r['id']:4d} {r['seg']:04x} {r['B']:6d} {first_8:>20} {typ0:04x} {typ1:04x}")

print("\n=== Records with first fixup type = 0x33ae ===")
for r in sorted_recs:
    if r['B'] == 0 or r['A'] < r['B']:
        continue
    fixup_off = r['off'] + r['A'] - r['B']
    fixup_data = t[fixup_off:fixup_off + min(r['B'], 4)]
    if len(fixup_data) >= 2:
        typ0 = struct.unpack_from('<H', fixup_data, 0)[0]
        if typ0 == 0x33ae:
            print(f"id={r['id']:3d} seg={r['seg']:04x} B={r['B']} A={r['A']} code={r['A']-r['B']}")