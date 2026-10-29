#!/usr/bin/env python3
"""Generate clean ISLDAT Mediterranean coast (7 tile segments) in user SVG coords."""
import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_table = body[0x500:]

# Collect unique coastline records (by coast_off) with their westernmost point
coast_tiles = {}
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
                            
                            if pts:
                                west_pt = min(pts, key=lambda p: p[0])
                                wx = tx + west_pt[0] / 65536.0
                                wy = ty + west_pt[1] / 65536.0
                                if wx < -5:
                                    if attr20 not in coast_tiles or wx < coast_tiles[attr20][0]:
                                        coast_tiles[attr20] = (wx, wy, row, col, west_pt)

# Sort by Y (south to north)
sorted_tiles = sorted(coast_tiles.items(), key=lambda x: x[1][1])

# Also get easternmost points for completeness (to show tile extent)
east_tiles = {}
for coast_off, (wx, wy, row, col, west_pt) in coast_tiles.items():
    x, y, z = struct.unpack_from('<iii', body, coast_off)
    tx = x / 65536.0
    ty = y / 65536.0
    pts_off = coast_off + 0x38
    pts = []
    for i in range(200):
        if pts_off + 6 > len(body): break
        px, mid, py = struct.unpack_from('<hhh', body, pts_off)
        if mid != 0: break
        pts.append((px, py))
        pts_off += 6
        if len(pts) > 200: break
    if pts:
        east_pt = max(pts, key=lambda p: p[0])
        ex = tx + east_pt[0] / 65536.0
        ey = ty + east_pt[1] / 65536.0
        east_tiles[coast_off] = (ex, ey, east_pt)

print(f'Unique Mediterranean coast tiles: {len(sorted_tiles)}')
for coast_off, (wx, wy, row, col, west_pt) in sorted_tiles:
    ex, ey, east_pt = east_tiles[coast_off]
    print(f'  Coast {coast_off:#06x} Grid[{row},{col:3d}] West=({wx:7.3f},{wy:7.3f}) East=({ex:7.3f},{ey:7.3f})')

# Transform to user SVG coordinates
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
       '<text x="10" y="20" font-family="monospace" font-size="12" fill="#333">ISLDAT ISR Mediterranean Coast (7 tile segments)</text>']

# Draw tile segments as thick lines (west to east)
for coast_off, (wx, wy, row, col, west_pt) in sorted_tiles:
    ex, ey, east_pt = east_tiles[coast_off]
    sx1, sy1 = tx(wx), ty(wy)
    sx2, sy2 = tx(ex), ty(ey)
    svg.append(f'<line x1="{sx1:.2f}" y1="{sy1:.2f}" x2="{sx2:.2f}" y2="{sy2:.2f}" stroke="#0066cc" stroke-width="3" opacity="0.7"/>')
    # Mark west endpoint
    svg.append(f'<circle cx="{sx1:.2f}" cy="{sy1:.2f}" r="4" fill="#ff0000" opacity="0.8"/>')
    svg.append(f'<text x="{sx1:.2f}" y="{sy1 - 8:.2f}" font-family="monospace" font-size="8" fill="black" text-anchor="middle">{coast_off:#06x}</text>')

# Draw connected path through west endpoints (clean coast)
west_pts = [(tx(wx), ty(wy)) for coast_off, (wx, wy, _, _, _) in sorted_tiles]
if west_pts:
    path = f'M {west_pts[0][0]:.2f} {west_pts[0][1]:.2f}'
    for sx, sy in west_pts[1:]:
        path += f' L {sx:.2f} {sy:.2f}'
    svg.append(f'<path d="{path}" fill="none" stroke="#ff0000" stroke-width="2" opacity="0.8"/>')

# User's traced coast (Mediterranean portion only - first ~8 points)
user_med = [
    (1.87, 199.62), (14.92, 187.68), (57.46, 175.36), (94.03, 95.89), (97.38, 95.14),
    (124.62, 32.09), (134.69, -7.84), (141.78, -37.68)
]
path = f'M {user_med[0][0]:.2f} {user_med[0][1]:.2f}'
for x, y in user_med[1:]:
    path += f' L {x:.2f} {y:.2f}'
svg.append(f'<path d="{path}" fill="none" stroke="#00ff00" stroke-width="1.5" opacity="0.6" stroke-dasharray="5,5"/>')

# Legend
svg.append('<text x="10" y="40" font-family="monospace" font-size="10" fill="#0066cc">ISLDAT tile segments (west-east)</text>')
svg.append('<text x="10" y="55" font-family="monospace" font-size="10" fill="#ff0000">ISLDAT clean coast (west endpoints)</text>')
svg.append('<text x="10" y="70" font-family="monospace" font-size="10" fill="#00ff00">User Mediterranean coast (dashed)</text>')

svg.append('</svg>')

with open('analysis/isldat_isr_med_coast.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_isr_med_coast.svg')

# Output clean coast points
print('\\nClean Mediterranean coast (7 tile segments, south to north):')
for i, (coast_off, (wx, wy, row, col, west_pt)) in enumerate(sorted_tiles):
    sx, sy = tx(wx), ty(wy)
    print(f'  {i}: Coast {coast_off:#06x} ISLDAT=({wx:7.3f},{wy:7.3f}) SVG=({sx:.1f},{sy:.1f})')