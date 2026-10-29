#!/usr/bin/env python3
"""Generate SVG for tile 0x1874 showing CORRECT connectivity (outer boundary)."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

quad = 0
col = 150
row_data = gridB[quad*256:(quad+1)*256]
t1_idx = row_data[col]
t1_off = row_data[col] * 2
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

# CORRECT connectivity: outer boundary of main body (0-11) and small body (12-17)
# Main body outer ring: 0->1->2->3->4->5->6->7->8->9->10->11->0
main_edges = [(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11),(11,0)]
# Small body: 12->13->14->15->16->17->12
small_edges = [(12,13),(13,14),(14,15),(15,16),(16,17),(17,12)]

# Determine bounds
xs = [p[0] for p in world_pts]
ys = [p[1] for p in world_pts]
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
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

os.makedirs('analysis/isldat_isr_tiles', exist_ok=True)

world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]

svg = ['<?xml version="1.0"?>',
       f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
       f'<text x="10" y="25" font-family="monospace" font-size="16" fill="#333">ISR Tile 0x1874 - CORRECT Polygon Connectivity</text>',
       f'<text x="10" y="45" font-family="monospace" font-size="12" fill="#666">Grid[0,150] Tile=({tx:.2f},{ty:.2f}) 18 pts</text>']

# Draw main body edges (blue) - OUTER BOUNDARY ONLY
for a,b in main_edges:
    wx1, wy1 = world_pts[a]
    wx2, wy2 = world_pts[b]
    svg.append(f'<line x1="{tx_s(world_pts[a][0]):.2f}" y1="{ty_s(world_pts[a][1]):.2f}" x2="{tx_s(world_pts[b][0]):.2f}" y2="{ty_s(world_pts[b][1]):.2f}" stroke="#0066cc" stroke-width="3" opacity="0.9"/>')

# Draw small body edges (red)
for a,b in small_edges:
    svg.append(f'<line x1="{tx_s(world_pts[a][0]):.2f}" y1="{ty_s(world_pts[a][1]):.2f}" x2="{tx_s(world_pts[b][0]):.2f}" y2="{ty_s(world_pts[b][1]):.2f}" stroke="#cc0000" stroke-width="3" opacity="0.9"/>')

# Draw points with numbers
for i, (wx, wy) in enumerate(world_pts):
    sx, sy = tx_s(wx), ty_s(wy)
    color = "#0066cc" if i <= 11 else "#cc0000"
    svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="6" fill="{color}" opacity="0.8"/>')
    svg.append(f'<text x="{sx:.2f}" y="{sy:.2f}" font-family="monospace" font-size="14" fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{i}</text>')
    svg.append(f'<text x="{sx:.2f}" y="{sy + 20:.2f}" font-family="monospace" font-size="9" fill="#333" text-anchor="middle">{i}: ({wx:.3f},{wy:.3f})</text>')

# Legend
svg.append('<text x="10" y="25" font-family="monospace" font-size="14" fill="#333">ISR Tile 0x1874 - CORRECT Polygon Connectivity</text>')
svg.append('<text x="10" y="45" font-family="monospace" font-size="12" fill="#0066cc">Main body (blue): 0-1-2-3-4-5-6-7-8-9-10-11-0</text>')
svg.append('<text x="10" y="60" font-family="monospace" font-size="12" fill="#cc0000">Small body (red): 12-13-14-15-16-17-12</text>')
svg.append(f'<text x="10" y="75" font-family="monospace" font-size="10" fill="#666">Chain has interior diagonals; outer boundary is outer ring</text>')

svg.append('</svg>')

with open('analysis/isldat_isr_tiles/tile_0x1874_q0_c150_correct.svg', 'w') as f:
    f.write('\n'.join(svg))

print('Wrote analysis/isldat_isr_tiles/tile_0x1874_q0_c150_correct.svg')
print("Main body edges:", main_edges)
print("Small body edges:", small_edges)