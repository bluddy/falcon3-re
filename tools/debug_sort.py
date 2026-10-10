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

for i, r in enumerate(sorted_recs):
    if r['id'] == 7:
        print(f"Index {i}: id={r['id']} off={r['off']:#x} A={r['A']}")
        if i + 1 < len(sorted_recs):
            nr = sorted_recs[i + 1]
            gap = nr['off'] - (r['off'] + r['A'])
            print(f"  next: id={nr['id']} off={nr['off']:#x} gap={gap}")
        break

# Also check id5
for i, r in enumerate(sorted_recs):
    if r['id'] == 5:
        print(f"Index {i}: id={r['id']} off={r['off']:#x} A={r['A']}")
        if i + 1 < len(sorted_recs):
            nr = sorted_recs[i + 1]
            gap = nr['off'] - (r['off'] + r['A'])
            print(f"  next: id={nr['id']} off={nr['off']:#x} gap={gap}")
        break

# And id7 in the list with context
print("\nRecords around id7:")
for j in range(max(0, 10), min(len(sorted_recs), 20)):
    r = sorted_recs[j]
    end = r['off'] + r['A']
    print(f"  {j}: id={r['id']:3d} off={r['off']:05x} A={r['A']:5d} end={end:05x}")