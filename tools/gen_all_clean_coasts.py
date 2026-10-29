#!/usr/bin/env python3
"""Generate clean coast SVGs for all theaters (left/right edges connected separately)."""
import struct, glob, os

def get_clean_coast(theater_file):
    with open(theater_file, 'rb') as f:
        data = f.read()
    body = data[9:]
    t1_base = struct.unpack_from('<H', data, 4)[0]
    gridB = body[0x000:0x000+4*256]
    t1_table = body[t1_base:]
    
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
                                    east_pt = max(pts, key=lambda p: p[0])
                                    wx = tx + west_pt[0] / 65536.0
                                    wy = ty + west_pt[1] / 65536.0
                                    ex = tx + east_pt[0] / 65536.0
                                    ey = ty + east_pt[1] / 65536.0
                                    if attr20 not in coast_tiles or wx < coast_tiles[attr20][0]:
                                        coast_tiles[attr20] = (wx, wy, ex, ey, row, col, west_pt, east_pt)
    
    sorted_tiles = sorted(coast_tiles.items(), key=lambda x: x[1][1])  # sort by wy (south to north)
    return sorted_tiles

os.makedirs('analysis/isldat_clean_coasts', exist_ok=True)

for p in glob.glob('game/ISLDAT.*'):
    name = os.path.basename(p).split('.')[-1]
    if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
        tiles = get_clean_coast(p)
        if not tiles:
            print(f'{name}: no coast tiles found')
            continue
        
        print(f'{name}: {len(tiles)} unique coast tiles')
        for coast_off, (wx, wy, ex, ey, row, col, west_pt, east_pt) in tiles:
            print(f'  Coast {coast_off:#06x} Grid[{row},{col:3d}] World=({wx:7.3f},{wy:7.3f}) East=({ex:7.3f},{ey:7.3f})')
        
        # Determine coordinate bounds for SVG
        all_x = [wx for _, (wx, wy, ex, ey, _, _, _, _) in tiles] + [ex for _, (wx, wy, ex, ey, _, _, _, _) in tiles]
        all_y = [wy for _, (wx, wy, ex, ey, _, _, _, _) in tiles] + [ey for _, (wx, wy, ex, ey, _, _, _, _) in tiles]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        # Add padding
        pad_x = (max_x - min_x) * 0.1
        pad_y = (max_y - min_y) * 0.1
        min_x -= pad_x; max_x += pad_x
        min_y -= pad_y; max_y += pad_y
        
        CANVAS = 4000
        MARGIN = 100
        w = max_x - min_x
        h = max_y - min_y
        scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
        
        def tx(x): return MARGIN + (x - min_x) * scale
        def ty(y): return CANVAS - (MARGIN + (y - min_y) * scale)
        
        # Generate SVG
        svg = ['<?xml version="1.0"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}">'.format(CANVAS, CANVAS, CANVAS, CANVAS),
               '<rect width="100%" height="100%" fill="#f0f0f0"/>',
               '<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{} ISLDAT Clean Coast</text>'.format(name)]
        
        # Draw LEFT edge (west endpoints) - south to north
        left_pts = [(tx(wx), ty(wy)) for _, (wx, wy, ex, ey, _, _, _, _) in tiles]
        if left_pts:
            path = 'M {:.2f} {:.2f}'.format(left_pts[0][0], left_pts[0][1])
            for sx, sy in left_pts[1:]:
                path += ' L {:.2f} {:.2f}'.format(sx, sy)
            svg.append('<path d="{}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>'.format(path))
        
        # Draw RIGHT edge (east endpoints) - south to north
        right_pts = [(tx(ex), ty(ey)) for _, (wx, wy, ex, ey, _, _, _, _) in tiles]
        if right_pts:
            path = 'M {:.2f} {:.2f}'.format(right_pts[0][0], right_pts[0][1])
            for sx, sy in right_pts[1:]:
                path += ' L {:.2f} {:.2f}'.format(sx, sy)
            svg.append('<path d="{}" fill="none" stroke="#cc0000" stroke-width="2" opacity="0.8"/>'.format(path))
        
        # Draw points with indices
        for i, (coast_off, (wx, wy, ex, ey, row, col, west_pt, east_pt)) in enumerate(tiles):
            sx_w, sy_w = tx(wx), ty(wy)
            sx_e, sy_e = tx(ex), ty(ey)
            # West point
            svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="4" fill="#0066cc" opacity="0.8"/>'.format(sx_w, sy_w))
            svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="10" fill="black" text-anchor="middle">{}</text>'.format(sx_w, sy_w - 6, i))
            svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="8" fill="#666" text-anchor="middle">{:#06x}</text>'.format(sx_w, sy_w + 14, coast_off))
            # East point
            svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="4" fill="#cc0000" opacity="0.8"/>'.format(sx_e, sy_e))
        
        # Legend
        svg.append('<text x="20" y="50" font-family="monospace" font-size="10" fill="#0066cc">Left edge (west endpoints)</text>')
        svg.append('<text x="20" y="65" font-family="monospace" font-size="10" fill="#cc0000">Right edge (east endpoints)</text>')
        svg.append('<text x="20" y="80" font-family="monospace" font-size="10" fill="#666">{} tiles</text>'.format(len(tiles)))
        
        svg.append('</svg>')
        
        with open('analysis/isldat_clean_coasts/{}_clean_coast.svg'.format(name), 'w') as f:
            f.write('\n'.join(svg))
        print('  Wrote analysis/isldat_clean_coasts/{}_clean_coast.svg'.format(name))
        print()

print('Done!')