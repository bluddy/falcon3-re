import struct
from pathlib import Path
from PIL import Image, ImageDraw

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

records = []
for r in sorted(recs):
    tx = i32(r) / 65536.0
    ty = i32(r + 4) / 65536.0
    attr = u16(r + 0x20)
    pc = u16(r + 0x2E)
    pts = [struct.unpack_from('<hhh', body, r + 0x38 + 6 * i) for i in range(pc)]
    
    sub_ptr = u16(r + 0x32)
    rings = []
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
            rings.append(ring)
            q += 2 + 2 * (cnt + 1)
            if not chain: break
            
    records.append({
        'r': r,
        'attr': attr,
        'tx': tx,
        'ty': ty,
        'pts': pts,
        'rings': rings
    })

W, H = 2000, 2000
min_x, max_x = -60.0, 40.0
min_y, max_y = -65.0, 25.0

def to_px(x, y):
    sx = (x - min_x) / (max_x - min_x) * W
    sy = H - (y - min_y) / (max_y - min_y) * H
    return (sx, sy)

img = Image.new('RGB', (W, H), (15, 23, 42))
draw = ImageDraw.Draw(img)

colors = [
    (230, 25, 75), (60, 180, 75), (255, 225, 25), (67, 99, 216),
    (245, 130, 49), (145, 30, 180), (70, 240, 240), (240, 50, 230),
    (188, 246, 12), (250, 190, 212), (0, 128, 128), (230, 190, 255),
    (154, 99, 36), (255, 250, 200), (128, 0, 0), (170, 255, 195),
    (128, 128, 0), (255, 216, 177), (0, 0, 117), (128, 128, 128),
    (255, 255, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0),
    (0, 255, 0), (255, 128, 128), (128, 255, 128), (128, 128, 255),
    (255, 128, 255), (128, 255, 255), (255, 255, 128), (255, 0, 128)
]

for idx, rd in enumerate(records):
    col = colors[idx % len(colors)]
    tx, ty = rd['tx'], rd['ty']
    pts = rd['pts']
    
    # Draw centroid
    cx, cy = to_px(tx, ty)
    draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=col)
    draw.text((cx+6, cy-6), f"#{idx} 0x{rd['r']:04X}", fill=col)
    
    # Draw rings
    for ring in rd['rings']:
        poly = []
        for p_idx in ring:
            px, _, pz = pts[p_idx]
            wx = tx + px / 2000.0
            wy = ty + pz / 2000.0
            poly.append(to_px(wx, wy))
        if len(poly) >= 2:
            draw.line(poly, fill=col, width=2)

out_p = Path('temp/israel_all_rings.png')
img.save(out_p)
print(f"Saved {out_p}")
