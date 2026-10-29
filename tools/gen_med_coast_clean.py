#!/usr/bin/env python3
"""Generate clean coastline SVG from Y-sorted western vertices."""
import struct, os, math

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

# Collect ALL Mediterranean tiles
med_tiles = {}
for quad in range(4):
    row_data = gridB[quad*256:(quad+1)*256]
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
                            if tx < -5:
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
                                    if attr20 not in med_tiles:
                                        med_tiles[attr20] = (tx, ty, pts)

# Collect ALL western vertices
all_west = []
for coast_off, (tx, ty, pts) in med_tiles.items():
    for px, py in pts:
        wx = tx + px / 65536.0
        wy = ty + py / 65536.0
        if wx < -5:
            all_west.append((wx, wy, coast_off))

# Sort by Y (south to north) and dedup
all_west.sort(key=lambda p: p[1])
deduped = []
for wx, wy, coast_off in all_west:
    if deduped and abs(wx - deduped[-1][0]) < 0.02 and abs(wy - deduped[-1][1]) < 0.02:
        continue
    deduped.append((wx, wy, coast_off))

print(f"Deduped vertices: {len(deduped)}")

# Resample to 22 points evenly distributed along Y
target_points = 22
if len(deduped) > target_points:
    indices = [int(i * (len(deduped) - 1) / (target_points - 1)) for i in range(target_points)]
    resampled = [deduped[i] for i in indices]
else:
    resampled = deduped

print(f"Resampled to {len(resampled)} points")

# Transform to user SVG coordinates
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

# User traced Mediterranean (first 12 points)
user_med = [
    (1.87, 199.62), (14.92, 187.68), (57.46, 175.36), (94.03, 95.89), (97.38, 95.14),
    (124.62, 32.09), (134.69, -7.84), (141.78, -37.68), (151.48, -111.56), (168.65, -111.19),
    (182.08, -195.51), (205.21, -223.87)
]

CANVAS_W, CANVAS_H = 600, 2100

svg = ['<?xml version="1.0"?>',
       f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="2100" viewBox="0 -1900 600 2100">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       '<text x="10" y="20" font-family="monospace" font-size="14" fill="#333">ISR Mediterranean Coast: ISLDAT (blue) vs User (green dashed)</text>']

# ISLDAT coastline (resampled)
if resampled:
    path = f'M {tx_s(resampled[0][0]):.2f} {ty_s(resampled[0][1]):.2f}'
    for wx, wy, _ in resampled[1:]:
        path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
    svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>')

# ISLDAT points
for i, (wx, wy, coast_off) in enumerate(resampled):
    sx, sy = tx_s(wx), ty_s(wy)
    svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="4" fill="#0066cc" opacity="0.8"/>')
    svg.append(f'<text x="{sx:.2f}" y="{sy - 8:.2f}" font-family="monospace" font-size="10" fill="black" text-anchor="middle">{i}</text>')

# User traced
path = f'M {user_med[0][0]:.2f} {user_med[0][1]:.2f}'
for x, y in user_med[1:]:
    path += f' L {x:.2f} {y:.2f}'
svg.append(f'<path d="{path}" fill="none" stroke="#00cc00" stroke-width="2" opacity="0.8" stroke-dasharray="10,5"/>')

# User points
for i, (x, y) in enumerate(user_med):
    svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#00cc00" opacity="0.8"/>')
    svg.append(f'<text x="{x:.2f}" y="{y - 8:.2f}" font-family="monospace" font-size="10" fill="black" text-anchor="middle">{i}</text>')

# Legend
svg.append('<text x="10" y="20" font-family="monospace" font-size="12" fill="#0066cc">ISLDAT Med coast (resampled 22 pts)</text>')
svg.append('<text x="10" y="35" font-family="monospace" font-size="12" fill="#00cc00">User traced (dashed)</text>')

svg.append('</svg>')

os.makedirs('analysis/isldat_isr_quad3', exist_ok=True)
with open('analysis/isldat_isr_quad3/med_coast_clean.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_quad3/med_coast_clean.svg')

# Also output the points for reference
print("\nClean coastline points (resampled 22):")
for i, (wx, wy, coast_off) in enumerate(resampled):
    print(f"  {i}: ({wx:7.3f}, {wy:7.3f}) Coast {coast_off:#06x}")