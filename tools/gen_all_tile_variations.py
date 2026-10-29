#!/usr/bin/env python3
"""Generate variation SVGs for all tiles with chain sub-records."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

os.makedirs('analysis/isldat_isr_tile_variations', exist_ok=True)

variations_generated = 0

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
                                
                                if not pts:
                                    continue
                                
                                world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]
                                
                                # Read sub-records
                                pts_off = attr20 + 0x38 + len(pts) * 6
                                subrecs = []
                                for sr in range(5):
                                    if pts_off + 4 > len(body): break
                                    flags = struct.unpack_from('<H', body, pts_off)[0]
                                    opcode = struct.unpack_from('<H', body, pts_off + 2)[0]
                                    subrecs.append((pts_off, flags, opcode))
                                    pts_off += 4
                                    if flags & 0x1000:
                                        chain = []
                                        while pts_off + 2 <= len(body):
                                            node = struct.unpack_from('<H', body, pts_off)[0]
                                            if node == 0xFFFF:
                                                pts_off += 2
                                                break
                                            chain.append(node)
                                            pts_off += 2
                                        subrecs[-1] = (subrecs[-1][0], subrecs[-1][1], subrecs[-1][2], chain)
                                    else:
                                        if pts_off + 2 <= len(body):
                                            node = struct.unpack_from('<H', body, pts_off)[0]
                                            subrecs[-1] = (subrecs[-1][0], subrecs[-1][1], subrecs[-1][2], [node])
                                            pts_off += 2
                                
                                # Check if any sub-record has chain mode
                                has_chain = any(flags & 0x1000 for _, flags, _, _ in subrecs)
                                if not has_chain:
                                    continue
                                
                                # Generate variation SVG for each chain sub-record
                                for sr, (off, flags, opcode, chain) in enumerate(subrecs):
                                    if not (flags & 0x1000):
                                        continue
                                    
                                    # Map chain indices to point indices (mod num_points)
                                    point_indices = [idx % len(pts) for idx in chain]
                                    path_pts = [world_pts[idx] for idx in point_indices]
                                    
                                    if len(path_pts) < 2:
                                        continue
                                    
                                    # Determine bounds
                                    xs = [p[0] for p in path_pts]
                                    ys = [p[1] for p in path_pts]
                                    min_x, max_x = min(xs), max(xs)
                                    min_y, max_y = min(ys), max(ys)
                                    pad_x = (max_x - min_x) * 0.15
                                    pad_y = (max_y - min_y) * 0.15
                                    min_x -= pad_x; max_x += pad_x
                                    min_y -= pad_y; max_y += pad_y
                                    
                                    CANVAS = 1000
                                    MARGIN = 60
                                    w = max_x - min_x
                                    h = max_y - min_y
                                    scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
                                    
                                    def tx_s(wx): return MARGIN + (wx - min_x) * scale
                                    def ty_s(wy): return CANVAS - (MARGIN + (wy - min_y) * scale)
                                    
                                    # Generate SVG
                                    svg = ['<?xml version="1.0"?>',
                                           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
                                           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
                                           f'<text x="10" y="20" font-family="monospace" font-size="12" fill="#333">ISR Coast {attr20:#06x} Grid[{quad},{col}] Subrec {sr}</text>',
                                           f'<text x="10" y="35" font-family="monospace" font-size="10" fill="#666">Chain (/16): {chain}</text>',
                                           f'<text x="10" y="50" font-family="monospace" font-size="10" fill="#666">Point indices: {point_indices}</text>']
                                    
                                    # Draw path
                                    if path_pts:
                                        path = f'M {tx_s(path_pts[0][0]):.2f} {ty_s(path_pts[0][1]):.2f}'
                                        for wx, wy in path_pts[1:]:
                                            path += f' L {tx_s(wx):.2f} {ty_s(wy):.2f}'
                                        path += ' Z'
                                        svg.append(f'<path d="{path}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>')
                                    
                                    # Draw points
                                    for i, (wx, wy) in enumerate(path_pts):
                                        sx, sy = tx_s(wx), ty_s(wy)
                                        svg.append(f'<circle cx="{sx:.2f}" cy="{ty_s(wy):.2f}" r="4" fill="#0066cc" opacity="0.8"/>')
                                        svg.append(f'<text x="{sx:.2f}" y="{ty_s(wy):.2f}" font-family="monospace" font-size="10" fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{i}</text>')
                                    
                                    # All points reference
                                    for i, (wx, wy) in enumerate(world_pts):
                                        sx, sy = tx_s(wx), ty_s(wy)
                                        svg.append(f'<circle cx="{sx:.2f}" cy="{ty_s(wy):.2f}" r="2" fill="#999999" opacity="0.2"/>')
                                    
                                    svg.append(f'<text x="10" y="70" font-family="monospace" font-size="10" fill="#666">Chain: {chain}</text>')
                                    svg.append(f'<text x="10" y="85" font-family="monospace" font-size="10" fill="#666">Point indices: {point_indices}</text>')
                                    
                                    svg.append('</svg>')
                                    
                                    filename = f'analysis/isldat_isr_tile_variations/tile_{attr20:#06x}_q{quad}_c{col}_sr{sr}.svg'
                                    with open(filename, 'w') as f:
                                        f.write('\n'.join(svg))
                                    variations_generated += 1
                                    
                                    # Print progress
                                    if variations_generated % 10 == 0:
                                        print(f'Generated {variations_generated} variations...')

print(f'Total variations generated: {variations_generated}')