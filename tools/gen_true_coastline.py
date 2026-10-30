#!/usr/bin/env python3
"""Generate the true ISR coastline from grid walk vertices."""
import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

# Collect all Mediterranean tiles
all_tiles = {}
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
                                    if attr20 not in all_tiles:
                                        all_tiles[attr20] = (tx, ty, pts)

# Collect all western vertices in grid walk order
all_vertices = []
for quad in range(4):
    row_data = gridB[quad*256:(quad+1)*256]
    for col in range(256):
        t1_idx = row_data[col]
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
                                    for px, py in pts:
                                        wx = tx + px / 65536.0
                                        wy = ty + py / 65536.0
                                        if wx < -5:
                                            all_vertices.append((wx, wy, attr20))

# Sort by Y (south to north)
all_vertices.sort(key=lambda v: v[1])

# Resample to 22 points (matching user's trace)
target_points = 22
if len(all_vertices) > target_points:
    indices = [int(i * (len(all_vertices) - 1) / (target_points - 1)) for i in range(target_points)]
    resampled = [all_vertices[i] for i in indices]
else:
    resampled = all_vertices

print(f"Resampled to {len(resampled)} points:")
for i, (wx, wy, coast_off) in enumerate(resampled):
    print(f"  {i}: ({wx:.3f}, {wy:.3f}) Coast {coast_off:#06x}")

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
       '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="2100" viewBox="0 -1900 600 2100">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       '<text x="10" y="20" font-family="monospace" font-size="14" fill="#333">ISR True Coastline (Grid Walk Vertices)</text>']

# ISLDAT coastline (resampled)
if resampled:
    path = 'M {:.2f} {:.2f}'.format(tx_s(resampled[0][0]), ty_s(resampled[0][1]))
    for wx, wy, _ in resampled[1:]:
        path += ' L {:.2f} {:.2f}'.format(tx_s(wx), ty_s(wy))
    svg.append('<path d="{}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>'.format(path))

# ISLDAT points
for i, (wx, wy, coast_off) in enumerate(resampled):
    sx, sy = tx_s(wx), ty_s(wy)
    svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="3" fill="#0066cc" opacity="0.8"/>'.format(sx, sy))
    svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="8" fill="black" text-anchor="middle">{}</text>'.format(sx, sy - 6, i))

# User traced
path = 'M {:.2f} {:.2f}'.format(user_med[0][0], user_med[0][1])
for x, y in user_med[1:]:
    path += ' L {:.2f} {:.2f}'.format(x, y)
svg.append('<path d="{}" fill="none" stroke="#00cc00" stroke-width="2" opacity="0.8" stroke-dasharray="10,5"/>'.format(path))

for i, (x, y) in enumerate(user_med):
    svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="3" fill="#00cc00" opacity="0.8"/>'.format(x, y))
    svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="8" fill="black" text-anchor="middle">{}</text>'.format(x, y - 6, i))

# Legend
svg.append('<text x="10" y="20" font-family="monospace" font-size="12" fill="#0066cc">ISLDAT Grid Walk (resampled 22 pts)</text>')
svg.append('<text x="10" y="35" font-family="monospace" font-size="12" fill="#00cc00">User Traced (dashed)</text>')

svg.append('</svg>')

with open('analysis/isldat_isr_true_coastline.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_true_coastline.svg')

# Also output the points for reference
print("\nResampled coastline points (22):")
for i, (wx, wy, coast_off) in enumerate(resampled):
    print("  {}: ({:.3f}, {:.3f}) Coast {:06x}".format(i, wx, wy, coast_off))