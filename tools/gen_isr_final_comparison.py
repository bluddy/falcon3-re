#!/usr/bin/env python3
"""Create comparison: ISLDAT Mediterranean coast vs user traced coastline."""
import struct

# Load ISLDAT ISR
with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_table = body[0x500:]

# Find Mediterranean coast tiles (X < -5)
med_tiles = {}
for row in range(4):
    for col in range(256):
        t1_idx = gridB[row*256 + col]
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
                                med_tiles[(row, col)] = (attr20, tx, ty)

print(f"Mediterranean tiles in grid: {len(med_tiles)}")

# Collect all western points from these tiles
med_west_pts = []
for (row, col), (coast_off, tx, ty) in med_tiles.items():
    pts_off = coast_off + 0x38
    pts = []
    for i in range(200):
        if pts_off + 6 > len(body): break
        px, mid, py = struct.unpack_from('<hhh', body, pts_off)
        if mid != 0: break
        pts.append((px, py))
        pts_off += 6
        if len(pts) > 200: break
    
    for px, py in pts:
        wx = tx + px / 65536.0
        wy = ty + py / 65536.0
        if wx < -5:
            med_west_pts.append((wx, wy, coast_off, row, col))

# Sort by Y (south to north)
med_west_pts.sort(key=lambda p: p[1])

# Dedup
deduped = []
for pt in med_west_pts:
    if deduped:
        if abs(pt[0] - deduped[-1][0]) < 0.05 and abs(pt[1] - deduped[-1][1]) < 0.05:
            continue
    deduped.append(pt)

print(f"ISLDAT Mediterranean west points: {len(deduped)}")

# User traced points (Mediterranean portion only - first ~12 points)
user_med = [
    (1.87, 199.62), (14.92, 187.68), (57.46, 175.36), (94.03, 95.89), (97.38, 95.14),
    (124.62, 32.09), (134.69, -7.84), (141.78, -37.68), (151.48, -111.56), (168.65, -111.19),
    (182.08, -195.51), (205.21, -223.87)
]

# Transform ISLDAT to user SVG coordinates
isldat_x_min, isldat_x_max = -23.5, -8.5
isldat_y_min, isldat_y_max = -39.0, -8.0
svg_x_min, svg_x_max = 1.0, 450.0
svg_y_min, svg_y_max = 199.0, -1900.0

def tx(wx):
    t = (wx - isldat_x_min) / (isldat_x_max - isldat_x_min)
    return svg_x_min + t * (svg_x_max - svg_x_min)

def ty(wy):
    t = (wy - isldat_y_min) / (isldat_y_max - isldat_y_min)
    return svg_y_min + t * (svg_y_max - svg_y_min)

# Generate SVG
svg = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<svg width="1000" height="1200" viewBox="0 -1900 1000 2100" xmlns="http://www.w3.org/2000/svg">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       '<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">ISR Coast: ISLDAT (blue) vs User Traced (green)</text>']

# ISLDAT Mediterranean coast (blue)
if deduped:
    path = f'M {tx(deduped[0][0]):.2f} {ty(deduped[0][1]):.2f}'
    for wx, wy, _, _, _ in deduped[1:]:
        path += f' L {tx(wx):.2f} {ty(wy):.2f}'
    svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="3" opacity="0.8"/>')

# ISLDAT points
for i, (wx, wy, coast_off, row, col) in enumerate(deduped):
    sx, sy = tx(wx), ty(wy)
    svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="4" fill="#0066cc" opacity="0.8"/>')
    svg.append(f'<text x="{sx:.2f}" y="{sy:.2f}-6" font-family="monospace" font-size="10" fill="black" text-anchor="middle">{i}</text>')

# User traced Mediterranean (green dashed)
if user_med:
    path = f'M {user_med[0][0]:.2f} {user_med[0][1]:.2f}'
    for x, y in user_med[1:]:
        path += f' L {x:.2f} {y:.2f}'
    svg.append(f'<path d="{path}" fill="none" stroke="#00cc00" stroke-width="2" opacity="0.8" stroke-dasharray="10,5"/>')

# User points
for i, (x, y) in enumerate(user_med):
    svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#00cc00" opacity="0.8"/>')
    svg.append(f'<text x="{x:.2f}" y="{y:.2f}-6" font-family="monospace" font-size="10" fill="black" text-anchor="middle">{i}</text>')

# Legend
svg.append('<text x="20" y="40" font-family="monospace" font-size="12" fill="#0066cc">ISLDAT Mediterranean ({} pts)'.format(len(deduped)))
svg.append('<text x="20" y="60" font-family="monospace" font-size="12" fill="#00cc00">User traced Mediterranean ({} pts)'.format(len(user_med)))
svg.append('<text x="20" y="80" font-family="monospace" font-size="12" fill="#cc0000">Note: ISLDAT has NO lakes (Dead Sea, Galilee) or borders</text>')
svg.append('<text x="20" y="100" font-family="monospace" font-size="12" fill="#666">Lakes/borders not in ISLDAT - may be in MAPOBJ.ISR or other files</text>')

svg.append('</svg>')

with open('analysis/isldat_isr_comparison_final.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_comparison_final.svg')

print(f'\nISLDAT Mediterranean points ({len(deduped)}):')
for i, (wx, wy, coast_off, row, col) in enumerate(deduped):
    print(f'  {i}: World=({wx:7.3f},{wy:7.3f}) Coast {coast_off:#06x} Grid[{row},{col}]')

print(f'\nUser Mediterranean points ({len(user_med)}):')
for i, (x, y) in enumerate(user_med):
    print(f'  {i}: SVG=({x:.2f},{y:.2f})')