import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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

# Create an SVG with every record drawn as full rings (polygons), colored by record index
# Canvas size: 2400 x 2400
# Coordinates: X in [-60..40], Y in [-65..25] -> span 100 x 90 nm
W, H = 2400, 2400
min_x, max_x = -60.0, 40.0
min_y, max_y = -65.0, 25.0

def to_svg(x, y):
    sx = (x - min_x) / (max_x - min_x) * W
    sy = H - (y - min_y) / (max_y - min_y) * H
    return f"{sx:.1f},{sy:.1f}"

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="background:#111;">',
]

colors = [
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6',
    '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3',
    '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#00ffff', '#ff00ff', '#ffff00',
    '#00ff00', '#ff8080', '#80ff80', '#8080ff', '#ff80ff', '#80ffff', '#ffff80', '#ff0080'
]

for idx, rd in enumerate(records):
    col = colors[idx % len(colors)]
    tx, ty = rd['tx'], rd['ty']
    pts = rd['pts']
    
    # Draw centroid
    cx, cy = to_svg(tx, ty).split(',')
    svg.append(f'  <circle cx="{cx}" cy="{cy}" r="5" fill="{col}"/>')
    svg.append(f'  <text x="{float(cx)+8}" y="{float(cy)+4}" fill="{col}" font-family="monospace" font-size="14">#{idx} 0x{rd["r"]:04X} a=0x{rd["attr"]:02X} ({tx:.1f},{ty:.1f})</text>')
    
    # Draw every ring
    for ring in rd['rings']:
        world_ring = []
        for p_idx in ring:
            px, _, pz = pts[p_idx]
            # test standard scale 2000.0
            wx = tx + px / 2000.0
            wy = ty + pz / 2000.0
            world_ring.append(to_svg(wx, wy))
        svg.append(f'  <polygon points="{" ".join(world_ring)}" fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-width="2"/>')

svg.append('</svg>')
out_p = Path('temp/israel_all_rings.svg')
out_p.write_text('\n'.join(svg))
print(f"Saved {out_p}")
