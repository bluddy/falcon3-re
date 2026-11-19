import struct
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw

# Parse ISLDAT.ISR completely without any seam dropping:
with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]
t1, t2 = struct.unpack_from('<HH', raw, 4)

def u16(o): return struct.unpack_from('<H', body, o)[0]
def i16(o): return struct.unpack_from('<h', body, o)[0]
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

print(f"Unique records: {len(recs)}")

# Inspect the points of each record
records_data = []
for r in sorted(recs):
    tx = i32(r) / 65536.0
    ty = i32(r + 4) / 65536.0
    attr = u16(r + 0x20)
    pc = u16(r + 0x2E)
    pts = [struct.unpack_from('<hhh', body, r + 0x38 + 6 * i) for i in range(pc)]
    
    # Read sub-record rings
    sub_ptr = u16(r + 0x32)
    sub_rings = []
    o = sub_ptr
    while o + 2 <= len(body) and u16(o) != 0xFFFF:
        sub = u16(o)
        o += 2
        chain = u16(sub) & 0x1000
        q = sub + 4
        while q + 2 <= len(body):
            cnt = u16(q)
            if cnt == 0xFFFF: break
            ring = [u16(q + 2 + 2 * k) // 16 for k in range(cnt + 1)]
            sub_rings.append(ring)
            q += 2 + 2 * (cnt + 1)
            if not chain: break
            
    records_data.append({
        'r': r,
        'attr': attr,
        'tx': tx,
        'ty': ty,
        'pts': pts,
        'rings': sub_rings
    })

# Let's inspect the rings of the coast records (attr == 0x14)
for rd in records_data:
    if rd['attr'] == 0x14:
        print(f"Rec 0x{rd['r']:04X}: tx={rd['tx']:6.2f}, ty={rd['ty']:6.2f}, pts_cnt={len(rd['pts'])}, rings_cnt={len(rd['rings'])}")
        for r_idx, ring in enumerate(rd['rings']):
            print(f"   Ring {r_idx}: {ring}")
