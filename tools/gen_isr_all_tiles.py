#!/usr/bin/env python3
"""Generate individual SVG for each Mediterranean coastline tile in ISR."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

# Collect ALL Mediterranean tiles from all 4 quadrants
med_tiles = []
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
                                    med_tiles.append((attr20, col, quad, tx, ty, pts))

print(f"Total Mediterranean tiles: {len(med_tiles)}")

os.makedirs('analysis/isldat_isr_tiles', exist_ok=True)

for coast_off, col, quad, tx, ty, pts in med_tiles:
    # Convert points to world coordinates
    world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]
    
    # Determine bounds
    xs = [p[0] for p in world_pts]
    ys = [p[1] for p in world_pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Add padding
    pad_x = (max_x - min_x) * 0.1
    pad_y = (max_y - min_y) * 0.1
    min_x -= pad_x; max_x += pad_x
    min_y -= pad_y; max_y += pad_y
    
    CANVAS = 1000
    MARGIN = 50
    w = max_x - min_x
    h = max_y - min_y
    scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
    
    def tx_s(wx): return MARGIN + (wx - min_x) * scale
    def ty_s(wy): return CANVAS - (MARGIN + (wy - min_y) * scale)
    
    # Generate SVG
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="10" y="20" font-family="monospace" font-size="14" fill="#333">ISR Tile {coast_off:#06x} Grid[{quad},{col}]</text>',
           f'<text x="10" y="35" font-family="monospace" font-size="10" fill="#666">Tile pos=({tx:.2f},{ty:.2f}) pts={len(pts)}</text>']
    
    # Draw polygon
    if world_pts:
        path = f'M {tx_s(world_pts[0][0]):.2f} {ty_s(world_pts[0][1]):.2f}'
        for wx, wy in world_pts[1:]:
            path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
        path += ' Z'
        svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>')
        
        # Draw points
        for i, (wx, wy) in enumerate(world_pts):
            svg.append(f'<circle cx="{tx_s(wx):.2f}" cy="{ty_s(wy):.2f}" r="3" fill="#ff0000" opacity="0.8"/>')
            svg.append(f'<text x="{tx_s(wx):.2f}" y="{ty_s(wy):.2f}-5" font-family="monospace" font-size="8" fill="black" text-anchor="middle">{i}</text>')
    
    svg.append('</svg>')
    
    filename = f'analysis/isldat_isr_tiles/tile_{coast_off:#06x}_q{quad}_c{col}.svg'
    with open(filename, 'w') as f:
        f.write('\n'.join(svg))

print(f'Wrote {len(med_tiles)} tile SVGs to analysis/isldat_isr_tiles/')