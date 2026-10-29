#!/usr/bin/env python3
"""Generate SVGs for ISR river records."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

river_offsets = [0x08e8, 0x096e, 0x09f4, 0x0a58, 0x0ace, 0x0b32, 0x0ba8, 0x0c0c, 0x0c70, 0x0cd4, 0x0db2]

os.makedirs('analysis/isldat_isr_rivers', exist_ok=True)

for r_off in river_offsets:
    attr = struct.unpack_from('<H', body, r_off + 0x20)[0]
    if attr != 0x32:
        continue
    
    x, y, z = struct.unpack_from('<iii', body, r_off)
    tx = x / 65536.0
    ty = y / 65536.0
    
    pts_off = r_off + 0x38
    pts = []
    for i in range(200):
        if pts_off + 6 > len(body): break
        px, mid, py = struct.unpack_from('<hhh', body, pts_off)
        if mid != 0: break
        pts.append((px, py))
        pts_off += 6
        if len(pts) > 200: break
    
    if not pts:
        continue
    
    world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]
    
    xs = [p[0] for p in world_pts]
    ys = [p[1] for p in world_pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    pad_x = (max_x - min_x) * 0.2
    pad_y = (max_y - min_y) * 0.2
    min_x -= pad_x; max_x += pad_x
    min_y -= pad_y; max_y += pad_y
    
    CANVAS = 1000
    MARGIN = 60
    w = max_x - min_x
    h = max_y - min_y
    scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
    
    def tx_s(wx): return MARGIN + (wx - min_x) * scale
    def ty_s(wy): return CANVAS - (MARGIN + (wy - min_y) * scale)
    
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="10" y="25" font-family="monospace" font-size="14" fill="#333">ISR River 0x{r_off:04x} offset {r_off:#06x}</text>',
           f'<text x="10" y="45" font-family="monospace" font-size="12" fill="#666">Tile=({tx:.2f},{ty:.2f}) pts={len(pts)}</text>']
    
    if len(world_pts) >= 2:
        path = f'M {tx_s(world_pts[0][0]):.2f} {ty_s(world_pts[0][1]):.2f}'
        for wx, wy in world_pts[1:]:
            path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
        svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>')
    
    for i, (wx, wy) in enumerate(world_pts):
        sx, sy = tx_s(wx), ty_s(wy)
        svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="5" fill="#0066cc" opacity="0.8"/>')
        svg.append(f'<text x="{sx:.2f}" y="{sy:.2f}" font-family="monospace" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{i}</text>')
        svg.append(f'<text x="{sx:.2f}" y="{sy + 18:.2f}" font-family="monospace" font-size="8" fill="#333" text-anchor="middle">{i}: ({wx:.2f},{wy:.2f})</text>')
    
    svg.append('</svg>')
    
    filename = f'analysis/isldat_isr_rivers/river_{r_off:#06x}.svg'
    with open(filename, 'w') as f:
        f.write('\n'.join(svg))
    print(f'Wrote {filename}: {len(pts)} pts, Tile=({tx:.2f},{ty:.2f})')

print("Done!")