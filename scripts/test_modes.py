import struct
from collections import Counter, defaultdict
from pathlib import Path

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]
t1, t2 = struct.unpack_from('<HH', raw, 4)

def u16(o): return struct.unpack_from('<H', body, o)[0]
def i32(o): return struct.unpack_from('<i', body, o)[0]

def table_extent(base, limit):
    best = 0
    for k in range(1, (limit - base) // 2 + 1):
        if min(u16(base + 2 * j) for j in range(k)) == base + 2 * k:
            best = k
    return [u16(base + 2 * j) for j in range(best)]

recs = set()
for ptr in table_extent(t1, t2) + table_extent(t2, len(body)):
    o = ptr
    while o + 2 <= len(body) and u16(o) != 0xFFFF:
        recs.add(u16(o))
        o += 2

# We know the Mediterranean coast in Israel:
# In real geography:
# North: Haifa (~32.8 N), Acre, Rosh HaNikra
# Center: Tel Aviv (~32.1 N)
# South: Ashdod, Ashkelon, Gaza (~31.5 N), Rafah
# The coast runs primarily NORTH-SOUTH!
# Y decreases as you go from North to South!
# X is on the WEST side!

for mode in [1, 2, 3, 4]:
    print(f"\n{'='*30} MODE {mode} {'='*30}")
    # Mode 1: wx = tx + w0/2000, wy = ty + w2/2000 (old)
    # Mode 2: wx = tx + w2/2000, wy = ty + w0/2000 (local axes corrected)
    # Mode 3: wx = ty + w0/2000, wy = tx + w2/2000 (centroids swapped)
    # Mode 4: wx = ty + w2/2000, wy = tx + w0/2000 (centroids swapped + local corrected)
    
    # Check the 4 Gaza/Sinai coast records: 0x1542, 0x15C0, 0x162C, 0x16AA
    for r in [0x1542, 0x15C0, 0x162C, 0x16AA, 0x10F4, 0x19F4]:
        tx = i32(r) / 65536.0
        ty = i32(r+4) / 65536.0
        pts = [struct.unpack_from('<hhh', body, r+0x38+6*i) for i in range(u16(r+0x2E))]
        p0 = pts[0]
        w0, w1, w2 = p0[0]/2000.0, p0[1]/2000.0, p0[2]/2000.0
        if mode == 1: wx, wy = tx + w0, ty + w2
        elif mode == 2: wx, wy = tx + w2, ty + w0
        elif mode == 3: wx, wy = ty + w0, tx + w2
        elif mode == 4: wx, wy = ty + w2, tx + w0
        print(f"Rec 0x{r:04X} (tx={tx:6.2f}, ty={ty:6.2f}) -> (wx={wx:6.2f}, wy={wy:6.2f})")
