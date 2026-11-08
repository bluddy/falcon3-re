#!/usr/bin/env python3
"""Generate SVG variations for tile 0x1478 sub-records."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

quad = 0
col = 133
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

# Sub-record chains (divided by 16)
subrecord_chains = [
    ("subrec_1", [4, 64, 0, 16, 32, 64, 4, 64, 32, 48, 80, 64]),
    ("subrec_2", [4, 96, 112, 144, 128, 96, 5, 128, 144, 160, 176, 192, 128]),
]

# Note: These are LINE TABLE entry indices, not point indices.
# But for visualization, we'll map them to point indices modulo 13
# to show the implied polygon variations.

os.makedirs('analysis/isldat_isr_tiles', exist_ok=True)

for name, chain in subrecord_chains:
    # Map line table indices to point indices (mod 13)
    point_indices = [idx % 13 for idx in chain]
    
    # Build path from point sequence
    path_pts = [world_pts[idx] for idx in point_indices]
    
    # Determine bounds
    xs = [p[0] for p in path_pts]
    ys = [p[1] for p in path_pts]
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
    
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="10" y="25" font-family="monospace" font-size="16" fill="#333">ISR Tile 0x1478 Variation: {name}</text>',
           f'<text x="10" y="45" font-family="monospace" font-size="12" fill="#666">Chain: {chain}</text>',
           f'<text x="10" y="60" font-family="monospace" font-size="10" fill="#666">Point indices (mod 13): {point_indices}</text>']
    
    # Draw polygon from point sequence
    if path_pts:
        path = f'M {tx_s(path_pts[0][0]):.2f} {ty_s(path_pts[0][1]):.2f}'
        for wx, wy in path_pts[1:]:
            path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
        path += ' Z'
        svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>')
    
    # Draw points
    for i, (wx, wy) in enumerate(path_pts):
        sx, sy = tx_s(wx), ty_s(wy)
        svg.append(f'<circle cx="{sx:.2f}" cy="{ty_s(wy):.2f}" r="5" fill="#0066cc" opacity="0.8"/>')
        svg.append(f'<text x="{sx:.2f}" y="{ty_s(wy):.2f}" font-family="monospace" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{i}</text>')
    
    # Also draw all points as reference
    for i, (wx, wy) in enumerate(world_pts):
        sx, sy = tx_s(wx), ty_s(wy)
        svg.append(f'<circle cx="{sx:.2f}" cy="{ty_s(wy):.2f}" r="2" fill="#999999" opacity="0.3"/>')
    
    svg.append('<text x="10" y="25" font-family="monospace" font-size="14" fill="#333">ISR Tile 0x1478 - Sub-record Variation</text>')
    svg.append(f'<text x="10" y="45" font-family="monospace" font-size="10" fill="#666">Chain: {chain}</text>')
    svg.append(f'<text x="10" y="60" font-family="monospace" font-size="10" fill="#666">Point indices (mod 13): {point_indices}</text>')
    
    svg.append('</svg>')
    
    with open(f'analysis/isldat_isr_tiles/tile_0x1478_q0_c133_{name}.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'Wrote analysis/isldat_isr_tiles/tile_0x1478_q0_c133_{name}.svg')

print("Done!")