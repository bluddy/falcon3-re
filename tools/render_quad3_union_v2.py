#!/usr/bin/env python3
"""Render all Quad 3 Mediterranean tiles as union - fixed coordinate transform."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

quad = 3
row_data = gridB[quad*256:(quad+1)*256]

tiles = []
for col, t1_idx in enumerate(row_data):
    if t1_idx != 0:
        t1_off = t1_idx * 2
        if t1_off < len(t1_table):
            rec_off = struct.unpack_from('<H', t1_table, t1_off)[0]
            if rec_off != 0xFFFF and rec_off < len(body):
                attr20 = struct.unpack_from('<H', body, rec_off + 0x20)[0] if rec_off + 0x20 < len(body) else 0xFFFF
                if attr20 != 0xffff and attr20 < len(body):
                    coast_attr = struct.unpack_from('<H', body, attr20 + 0x20)[0] if attr20 + 0x20 < len(body) else 0xFFFF
                    if coast_attr == 0x14:
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
                        
                        if pts:
                            tiles.append((col, attr20, tx, ty, pts))

print(f"Quadrant 3 tiles: {len(tiles)}")

all_west_pts = []
for col, coast_off, tx, ty, pts in tiles:
    for px, py in pts:
        wx = tx + px / 65536.0
        wy = ty + py / 65536.0
        if wx < -5:
            all_west_pts.append((wx, wy))

xs = [p[0] for p in all_west_pts]
ys = [p[1] for p in all_west_pts]
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)

print(f"ISLDAT bounds: X=[{min_x:.2f},{max_x:.2f}], Y=[{min_y:.2f},{max_y:.2f}]")

# Transform to USER SVG coordinate system
# User SVG: X 1-450, Y 199 to -1900 (Y down)
# ISLDAT: X -23.5 to -9, Y -39 to -8
# Map ISLDAT X [-23.5, -9] -> SVG X [1, 450]
# Map ISLDAT Y [-39, -8] -> SVG Y [199, -1900] (Y down)

isldat_x_min, isldat_x_max = -23.5, -8.5
isldat_y_min, isldat_y_max = -39.0, -8.0
svg_x_min, svg_x_max = 1.0, 450.0
svg_y_min, svg_y_max = 199.0, -1900.0

def tx_s(wx):
    t = (wx - isldat_x_min) / (isldat_x_max - isldat_x_min)
    return svg_x_min + t * (svg_x_max - svg_x_min)

def ty_s(wy):
    t = (wy - isldat_y_min) / (isldat_y_max - isldat_y_min)
    return svg_y_min + t * (svg_y_max - svg_y_min)

# Test transformation
print(f"ISLDAT (-23.5, -39) -> SVG ({tx_s(-23.5):.1f}, {ty_s(-39):.1f})")
print(f"ISLDAT (-8.5, -8) -> SVG ({tx_s(-8.5):.1f}, {ty_s(-8):.1f})")

CANVAS_W = 600
CANVAS_H = 2200
VIEWBOX = f"0 0 {CANVAS_W} {CANVAS_H}"

user_med = [
    (1.87, 199.62), (14.92, 187.68), (57.46, 175.36), (94.03, 95.89), (97.38, 95.14),
    (124.62, 32.09), (134.69, -7.84), (141.78, -37.68), (151.48, -111.56), (168.65, -111.19),
    (182.08, -195.51), (205.21, -223.87)
]

svg = ['<?xml version="1.0"?>',
       f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       '<text x="10" y="20" font-family="monospace" font-size="14" fill="#333">ISR Quad 3: All Mediterranean Tiles (union) - USER COORDS</text>']

for col, coast_off, tx, ty, pts in tiles:
    west_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts if (tx + px/65536.0) < -5]
    if len(west_pts) >= 3:
        path = f'M {tx_s(west_pts[0][0]):.2f} {ty_s(west_pts[0][1]):.2f}'
        for wx, wy in west_pts[1:]:
            path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
        path += ' Z'
        svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="1.5" opacity="0.3"/>')

# User traced
path = f'M {user_med[0][0]:.2f} {user_med[0][1]:.2f}'
for x, y in user_med[1:]:
    path += f' L {x:.2f} {y:.2f}'
svg.append(f'<path d="{path}" fill="none" stroke="#00cc00" stroke-width="2" opacity="0.8" stroke-dasharray="10,5"/>')

# Legend
svg.append('<text x="10" y="20" font-family="monospace" font-size="12" fill="#0066cc">ISLDAT Med tiles (union)</text>')
svg.append('<text x="10" y="35" font-family="monospace" font-size="12" fill="#00cc00">User traced (dashed)</text>')

svg.append('</svg>')

os.makedirs('analysis/isldat_isr_quad3', exist_ok=True)
with open('analysis/isldat_isr_quad3/quad3_union_v2.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_quad3/quad3_union_v2.svg')