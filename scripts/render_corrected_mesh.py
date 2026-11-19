import struct
from pathlib import Path
from PIL import Image, ImageDraw

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
            # In Falcon, vertices are 16 bytes each in transformed table, so index is offset // 16
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

# Render high-res image of all rings
# Scale: local y = p[0], local x = p[2]
# world_x = tx + p[2] / 2000.0
# world_y = ty + p[0] / 2000.0

W, H = 1600, 1600
min_x, max_x = -60.0, 40.0
min_y, max_y = -65.0, 25.0

def to_px(wx, wy):
    sx = (wx - min_x) / (max_x - min_x) * W
    sy = H - (wy - min_y) / (max_y - min_y) * H
    return (sx, sy)

img = Image.new('RGB', (W, H), (15, 23, 42))
draw = ImageDraw.Draw(img)

# Draw grid
for gx in range(int(min_x), int(max_x)+1, 10):
    p0 = to_px(gx, min_y)
    p1 = to_px(gx, max_y)
    draw.line([p0, p1], fill=(30, 41, 59), width=1)
    draw.text((p0[0]+2, H-20), f"{gx}nm", fill=(100, 116, 139))

for gy in range(int(min_y), int(max_y)+1, 10):
    p0 = to_px(min_x, gy)
    p1 = to_px(max_x, gy)
    draw.line([p0, p1], fill=(30, 41, 59), width=1)
    draw.text((10, p0[1]-12), f"{gy}nm", fill=(100, 116, 139))

for rd in records:
    tx, ty = rd['tx'], rd['ty']
    attr = rd['attr']
    pts = rd['pts']
    
    # Color by attribute
    if attr == 0x14: # coast/water tile
        outline_col = (56, 189, 248) # light sky blue
        fill_col = (14, 116, 144)
    elif attr == 0x32: # river/waterway
        outline_col = (52, 211, 153) # emerald
        fill_col = (16, 185, 129)
    elif attr == 0x64: # lake
        outline_col = (129, 140, 248) # indigo
        fill_col = (99, 102, 241)
    else:
        outline_col = (248, 113, 113) # red
        fill_col = (239, 68, 68)

    for ring in rd['rings']:
        poly = []
        for p_idx in ring:
            p = pts[p_idx]
            # local y = p[0], local x = p[2]
            wx = tx + p[2] / 2000.0
            wy = ty + p[0] / 2000.0
            poly.append(to_px(wx, wy))
            
        if len(poly) >= 3:
            # draw polygon outline and slight fill
            draw.polygon(poly, outline=outline_col)

# Also draw centroids
for rd in records:
    cx, cy = to_px(rd['tx'], rd['ty'])
    draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=(255, 255, 255))
    draw.text((cx+5, cy-5), f"0x{rd['r']:04X}", fill=(226, 232, 240))

out_path = Path('temp/israel_corrected_mesh.png')
img.save(out_path)
print(f"Saved {out_path}")
