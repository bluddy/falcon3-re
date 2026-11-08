#!/usr/bin/env python3
"""Generate SVGs for MAPOBJ political border records (attr 0xC8)."""
import struct, os

with open('game/MAPOBJ.ISR', 'rb') as f:
    data = f.read()

os.makedirs('analysis/mapobj_isr_borders', exist_ok=True)

# Search for ISLDAT-like blocks in MAPOBJ with attr 0xC8
for i in range(len(data) - 9):
    if data[i+1] == 0:
        body_len = struct.unpack_from('<H', data, i)[0]
        t1_base = struct.unpack_from('<H', data, i+4)[0]
        if t1_base == 0x500 and body_len > 100 and i + 9 + body_len <= len(data):
            body = data[i+9:i+9+body_len]
            for r_off in range(0, len(body) - 0x36, 2):
                attr = struct.unpack_from('<H', body, r_off + 0x20)[0] if r_off + 0x20 < len(body) else 0xFFFF
                if attr == 0xC8:
                    x, y, z = struct.unpack_from('<iii', body, r_off)
                    tx = x / 65536.0
                    ty = y / 65536.0
                    
                    pts_off = r_off + 0x38
                    pts = []
                    for j in range(200):
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
                    def ty_s(wy): return 1000 - (MARGIN + (wy - min_y) * scale)
                    
                    svg = ['<?xml version="1.0"?>',
                           '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">',
                           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
                           f'<text x="10" y="25" font-family="monospace" font-size="14" fill="#333">MAPOBJ Border 0xC8 at file offset {i:#x}</text>',
                           f'<text x="10" y="45" font-family="monospace" font-size="12" fill="#666">Tile=({tx:.2f},{ty:.2f}) pts={len(pts)}</text>']
                    
                    if len(world_pts) >= 2:
                        path = f'M {tx_s(world_pts[0][0]):.2f} {ty_s(world_pts[0][1]):.2f}'
                        for wx, wy in world_pts[1:]:
                            path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
                        svg.append(f'<path d="{path}" fill="none" stroke="#cc0000" stroke-width="2" opacity="0.8"/>')
                    
                    for j, (wx, wy) in enumerate(world_pts):
                        sx, sy = tx_s(wx), ty_s(wy)
                        svg.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="5" fill="#cc0000" opacity="0.8"/>')
                        svg.append(f'<text x="{sx:.2f}" y="{sy:.2f}" font-family="monospace" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{j}</text>')
                        svg.append(f'<text x="{sx:.2f}" y="{sy + 18:.2f}" font-family="monospace" font-size="8" fill="#333" text-anchor="middle">{j}: ({wx:.2f},{wy:.2f})</text>')
                    
                    svg.append('</svg>')
                    
                    filename = f'analysis/mapobj_isr_borders/border_{i:#x}.svg'
                    with open(filename, 'w') as f:
                        f.write('\n'.join(svg))
                    print(f'Wrote {filename}: {len(pts)} pts, Tile=({tx:.2f},{ty:.2f})')

print("Done!")