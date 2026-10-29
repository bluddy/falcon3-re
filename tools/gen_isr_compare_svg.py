#!/usr/bin/env python3
"""Generate ISLDAT coastline SVG in user's coordinate system for comparison."""
import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_table = body[0x500:]

# Collect unique coastline records from GridB
coast_records = {}
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
                            coast_records[attr20] = (row, col)

# For each coastline record, get tile position and points
all_world_pts = []
for coast_off, (row, col) in coast_records.items():
    tx_raw, ty_raw, tz_raw = struct.unpack_from('<iii', body, coast_off)
    tx = tx_raw / 65536.0
    ty = ty_raw / 65536.0
    
    pts_off = coast_off + 0x38
    pts = []
    for i in range(200):
        if pts_off + 6 > len(body): break
        px, mid, py = struct.unpack_from('<hhh', body, pts_off)
        if mid != 0: break
        pts.append((px, py))
        pts_off += 6
        if len(pts) > 200: break
    
    # Convert to world (interpretation 1: points are 16.16 offsets)
    for px, py in pts:
        wx = tx + px / 65536.0
        wy = ty + py / 65536.0
        all_world_pts.append((coast_off, row, col, wx, wy, px, py))

# Filter western edge points (X < -5) - Mediterranean coast
west_pts = [p for p in all_world_pts if p[3] < -5]
print(f'Western edge points: {len(west_pts)}')

# Sort by Y (south to north = more negative to less negative)
west_pts.sort(key=lambda p: p[4])

print('Western coast points (south to north):')
for p in west_pts:
    print(f'  Coast {p[0]:#06x} Grid[{p[1]},{p[2]}] World=({p[3]:.3f},{p[4]:.3f}) RawPt=({p[5]},{p[6]})')

# Now transform to user's SVG coordinate system
# User SVG: X 1.87-451, Y 199 to -1884 (Y down)
# ISLDAT west coast: X -23 to -9, Y -38 to -9
# Map ISLDAT X [-23, -9] -> SVG X [1, 125] (west coast)
# Map ISLDAT Y [-38, -9] -> SVG Y [199, -7] (south to north, but SVG Y down so flip)

isldat_x_min, isldat_x_max = -23.5, -8.5
isldat_y_min, isldat_y_max = -39.0, -8.0  # south to north

svg_x_min, svg_x_max = 1.0, 130.0
svg_y_min, svg_y_max = 199.0, -10.0  # SVG Y: 199=south (bottom), -10=north (top)

def transform_x(wx):
    # ISLDAT X: -23.5 (west) to -8.5 (east) -> SVG X: 1 to 130
    t = (wx - isldat_x_min) / (isldat_x_max - isldat_x_min)
    return svg_x_min + t * (svg_x_max - svg_x_min)

def transform_y(wy):
    # ISLDAT Y: -39 (south) to -8 (north) -> SVG Y: 199 (south/bottom) to -10 (north/top)
    # Note: SVG Y increases downward, ISLDAT Y increases northward
    t = (wy - isldat_y_min) / (isldat_y_max - isldat_y_min)
    return svg_y_min + t * (svg_y_max - svg_y_min)

# Generate SVG
svg = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<svg width="500" height="600" viewBox="0 -200 500 600" xmlns="http://www.w3.org/2000/svg">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       '<text x="10" y="20" font-family="monospace" font-size="12" fill="#333">ISLDAT ISR Coastline (transformed to user SVG coords)</text>']

# Draw all coastline points as small circles
for coast_off, row, col, wx, wy, px, py in all_world_pts:
    sx = transform_x(wx)
    sy = transform_y(wy)
    color = '#0066cc' if wx < -5 else '#666666'
    svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="1.5" fill="{color}" opacity="0.7"/>')
    # Label with coast offset
    svg.append(f'<text x="{sx:.2f}" y="{sy - 3:.2f}" font-family="monospace" font-size="6" fill="black" text-anchor="middle">{coast_off:#06x}</text>')

# Draw western coast as connected path (sorted by Y)
if west_pts:
    path = f'M {transform_x(west_pts[0][3]):.2f} {transform_y(west_pts[0][4]):.2f}'
    for p in west_pts[1:]:
        path += f' L {transform_x(p[3]):.2f} {transform_y(p[4]):.2f}'
    svg.append(f'<path d="{path}" fill="none" stroke="#ff0000" stroke-width="2" opacity="0.8"/>')

# Draw user's coastline points for reference (from their SVG)
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
svg.append('<text x="10" y="40" font-family="monospace" font-size="10" fill="#0066cc">ISLDAT coast pts</text>')
svg.append('<text x="10" y="55" font-family="monospace" font-size="10" fill="#ff0000">ISLDAT west coast (Y-sorted)</text>')
svg.append('<text x="10" y="70" font-family="monospace" font-size="10" fill="#00ff00">User traced coast (dashed)</text>')

svg.append('</svg>')

with open('analysis/isldat_isr_coast_compare.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_coast_compare.svg')