#!/usr/bin/env python3
"""Generate clean ISLDAT western coast (deduped, south-to-north) in user SVG coords."""
import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_table = body[0x500:]

# Collect ALL coastline points from ALL tiles
all_coast_pts = []
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
                            
                            pts_off = attr20 + 0x38
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
                                if wx < -5:  # Mediterranean coast
                                    all_coast_pts.append((wx, wy, attr20, row, col, px, py))

# Sort by Y (south to north)
all_coast_pts.sort(key=lambda p: p[1])

# Deduplicate with larger threshold for clean polyline
deduped = []
for wx, wy, coast_off, row, col, px, py in all_coast_pts:
    if deduped:
        last_wx, last_wy, _, _, _, _, _ = deduped[-1]
        if abs(wx - last_wx) < 0.1 and abs(wy - last_wy) < 0.1:
            continue
    deduped.append((wx, wy, coast_off, row, col, px, py))

print(f'Clean coast points: {len(deduped)}')

# Transform to user SVG coordinates
# ISLDAT west coast: X -23.5 to -9, Y -39 to -8
# User SVG west coast: X 1 to 130, Y 199 to -10 (Y down)
isldat_x_min, isldat_x_max = -23.5, -8.5
isldat_y_min, isldat_y_max = -39.0, -8.0
svg_x_min, svg_x_max = 1.0, 130.0
svg_y_min, svg_y_max = 199.0, -10.0

def tx(wx):
    t = (wx - isldat_x_min) / (isldat_x_max - isldat_x_min)
    return svg_x_min + t * (svg_x_max - svg_x_min)

def ty(wy):
    t = (wy - isldat_y_min) / (isldat_y_max - isldat_y_min)
    return svg_y_min + t * (svg_y_max - svg_y_min)

# Generate SVG
svg = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<svg width="500" height="600" viewBox="0 -200 500 600" xmlns="http://www.w3.org/2000/svg">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       '<text x="10" y="20" font-family="monospace" font-size="12" fill="#333">ISLDAT ISR Clean Western Coast (deduped, south-to-north)</text>']

# Draw points
for i, (wx, wy, coast_off, row, col, px, py) in enumerate(deduped):
    sx = tx(wx)
    sy = ty(wy)
    svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="2" fill="#0066cc" opacity="0.8"/>')
    svg.append(f'<text x="{sx:.2f}" y="{sy:.2f}-4" font-family="monospace" font-size="7" fill="black" text-anchor="middle">{i}</text>')

# Draw connected path
if deduped:
    path = f'M {tx(deduped[0][0]):.2f} {ty(deduped[0][1]):.2f}'
    for wx, wy, _, _, _, _, _ in deduped[1:]:
        path += f' L {tx(wx):.2f} {ty(wy):.2f}'
    svg.append(f'<path d="{path}" fill="none" stroke="#ff0000" stroke-width="2" opacity="0.8"/>')

# User's traced coast
user_pts = [
    (1.87, 199.62), (14.92, 187.68), (57.46, 175.36), (94.03, 95.89), (97.38, 95.14),
    (124.62, 32.09), (134.69, -7.84), (141.78, -37.68), (151.48, -111.56), (168.65, -111.19),
    (182.08, -195.51), (205.21, -223.87), (254.84, -386.92), (263.79, -467.14),
    (261.93, -514.53), (295.51, -515.65), (324.24, -594.00), (298.87, -626.46),
    (322.74, -671.61), (358.56, -701.08), (451.47, -807.42)
]
path = f'M {user_pts[0][0]:.2f} {user_pts[0][1]:.2f}'
for x, y in user_pts[1:]:
    path += f' L {x:.2f} {y:.2f}'
svg.append(f'<path d="{path}" fill="none" stroke="#00ff00" stroke-width="1.5" opacity="0.6" stroke-dasharray="5,5"/>')

# Legend
svg.append('<text x="10" y="40" font-family="monospace" font-size="10" fill="#0066cc">ISLDAT clean coast pts</text>')
svg.append('<text x="10" y="55" font-family="monospace" font-size="10" fill="#ff0000">ISLDAT clean coast (connected)</text>')
svg.append('<text x="10" y="70" font-family="monospace" font-size="10" fill="#00ff00">User traced coast (dashed)</text>')

svg.append('</svg>')

with open('analysis/isldat_isr_clean_coast.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_clean_coast.svg')

# Also output clean coast points for reference
print('\\nClean coast points (south to north):')
for i, (wx, wy, coast_off, row, col, px, py) in enumerate(deduped):
    sx = tx(wx)
    sy = ty(wy)
    print(f'  {i:3d}: ISLDAT=({wx:7.3f},{wy:7.3f}) SVG=({sx:.1f},{sy:.1f}) Coast {coast_off:#06x}')