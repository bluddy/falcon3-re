#!/usr/bin/env python3
"""Generate SVG for specific tile 0x1874 at quadrant 0, column 150 with point numbering."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

# Tile 0x1874 at quadrant 0, column 150
quad = 0
col = 150
row_data = gridB[quad*256:(quad+1)*256]
t1_idx = row_data[col]
t1_off = t1_idx * 2
rec_off = struct.unpack_from('<H', t1_table, t1_off)[0]
attr20 = struct.unpack_from('<H', body, rec_off + 0x20)[0]

x, y, z = struct.unpack_from('<iii', body, attr20)
tx = x / 65536.0
ty = y / 65536.0

pts_off = attr20 + 0x38
pts = []
for i in range(200):
    if pts_off + 6 > len(body): break
    px, mid, py = struct.unpack_from('<hhh', body, pts_off)
    if mid != 0: break
    pts.append((px, py))
    pts_off += 6
    if len(pts) > 200: break

world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]

# Determine bounds
xs = [p[0] for p in world_pts]
ys = [p[1] for p in world_pts]
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)

# Add padding
pad_x = (max_x - min_x) * 0.15
pad_y = (max_y - min_y) * 0.15
min_x -= pad_x; max_x += pad_x
min_y -= pad_y; max_y += pad_y

CANVAS = 1200
MARGIN = 80
w = max_x - min_x
h = max_y - min_y
scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1

def tx_s(wx): return MARGIN + (wx - min_x) * scale
def ty_s(wy): return CANVAS - (MARGIN + (wy - min_y) * scale)

# Generate SVG
svg = ['<?xml version="1.0"?>',
       f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       f'<text x="10" y="25" font-family="monospace" font-size="16" fill="#333">ISR Tile 0x1874 (Dead Sea) Grid[{0},{150}]</text>',
       f'<text x="10" y="45" font-family="monospace" font-size="12" fill="#666">Tile pos=({tx:.2f},{ty:.2f}) pts={len(pts)}</text>',
       f'<text x="10" y="65" font-family="monospace" font-size="12" fill="#666">Tile coord=({tx:.4f},{ty:.4f})</text>']

# Draw polygon
path = f'M {tx_s(world_pts[0][0]):.2f} {ty_s(world_pts[0][1]):.2f}'
for wx, wy in world_pts[1:]:
    path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
path += ' Z'
svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>')

# Draw points with LARGE numbers
for i, (wx, wy) in enumerate(world_pts):
    sx, sy = tx_s(wx), ty_s(wy)
    # Circle
    svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="6" fill="#0066cc" opacity="0.8"/>')
    # Large number
    svg.append(f'<text x="{sx:.2f}" y="{sy:.2f}" font-family="monospace" font-size="14" fill="black" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{i}</text>')
    # Coordinates label
    wx_raw = pts[i][0]
    wy_raw = pts[i][1]
    svg.append(f'<text x="{sx:.2f}" y="{sy + 20:.2f}" font-family="monospace" font-size="9" fill="#333" text-anchor="middle">{i}: ({wx_raw},{wy_raw}) = ({wx:.3f},{wy:.3f})</text>')

# Legend
svg.append('<text x="10" y="CANVAS-30" font-family="monospace" font-size="12" fill="#333">Tile 0x1874 - Dead Sea candidate</text>'.replace('CANVAS', str(CANVAS)))
svg.append(f'<text x="10" y="{CANVAS-15}" font-family="monospace" font-size="10" fill="#666">Points: 0-{len(pts)-1} | Grid[0,150] | Tile pos=({tx:.2f},{ty:.2f})</text>')

svg.append('</svg>')

os.makedirs('analysis/isldat_isr_tiles', exist_ok=True)
with open('analysis/isldat_isr_tiles/tile_0x1874_q0_c150_deadsea.svg', 'w') as f:
    f.write('\n'.join(svg))

print(f'Wrote analysis/isldat_isr_tiles/tile_0x1874_q0_c150_deadsea.svg')
print(f'Tile: 0x1874 at Grid[0,150], pos=({tx:.2f},{ty:.2f}), {len(pts)} pts')
for i, (wx, wy) in enumerate(world_pts):
    print(f'  {i}: ({wx:.4f},{wy:.4f}) raw=({pts[i][0]},{pts[i][1]})')