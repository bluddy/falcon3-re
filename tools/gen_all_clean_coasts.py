#!/usr/bin/env python3
"""Generate clean coast SVGs - Mediterranean uses all-points Y-sort, others use tile endpoints."""
import struct, glob, os

def get_mediterranean_coast(theater_file):
    """Extract Mediterranean coast: all western points from tiles at X < -5, Y-sorted."""
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
                                coast_tiles[attr20] = (row, col)
    
    # Collect ALL points from these tiles, filter western edge
    all_pts = []
    for coast_off, (row, col) in coast_tiles.items():
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
        
        for px, py in pts:
            wx = tx + px / 65536.0
            wy = ty + py / 65536.0
            if wx < -5:  # Mediterranean western edge
                all_pts.append((wx, wy, coast_off, row, col, px, py))
    
    # Y-sort all points (south to north)
    all_pts.sort(key=lambda p: p[1])
    
    # Deduplicate nearby points
    deduped = []
    for pt in all_pts:
        if deduped:
            last_wx, last_wy, _, _, _, _, _ = deduped[-1]
            if abs(pt[0] - last_wx) < 0.05 and abs(pt[1] - last_wy) < 0.05:
                continue
        deduped.append(pt)
    
    return deduped

def get_clean_coast(theater_file):
    """Original: one west/east point per unique coast tile."""
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
    
    sorted_tiles = sorted(coast_tiles.items(), key=lambda x: x[1][1])
    return [(wx, wy, ex, ey, row, col, west_pt, east_pt) for _, (wx, wy, ex, ey, row, col, west_pt, east_pt) in sorted_tiles]

os.makedirs('analysis/isldat_clean_coasts', exist_ok=True)

for p in glob.glob('game/ISLDAT.*'):
    name = os.path.basename(p).split('.')[-1]
    if name not in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
        continue
    
    if name == 'ISR':
        # Mediterranean coast: all points Y-sorted
        pts = get_mediterranean_coast(p)
        print(f'{name}: {len(pts)} Mediterranean coast points (all pts Y-sorted)')
        for wx, wy, coast_off, row, col, px, py in pts[:10]:
            print(f'  ({wx:7.3f},{wy:7.3f}) Coast {coast_off:#06x}')
        if len(pts) > 10:
            print(f'  ...')
        
        # Determine bounds
        all_x = [p[0] for p in pts]
        all_y = [p[1] for p in pts]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
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
        
        svg = ['<?xml version="1.0"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}">'.format(CANVAS, CANVAS, CANVAS, CANVAS),
               '<rect width="100%" height="100%" fill="#f0f0f0"/>',
               '<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{} ISLDAT Clean Coast (Mediterranean)</text>'.format(name)]
        
        # Draw path
        if pts:
            path = 'M {:.2f} {:.2f}'.format(tx(pts[0][0]), ty(pts[0][1]))
            for wx, wy, _, _, _, _, _ in pts[1:]:
                path += ' L {:.2f} {:.2f}'.format(tx(wx), ty(wy))
            svg.append('<path d="{}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>'.format(path))
        
        # Draw points
        for i, (wx, wy, coast_off, row, col, px, py) in enumerate(pts):
            sx, sy = tx(wx), ty(wy)
            svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="3" fill="#0066cc" opacity="0.8"/>'.format(sx, sy))
            svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="8" fill="black" text-anchor="middle">{}</text>'.format(sx, sy - 5, i))
        
        svg.append('<text x="20" y="50" font-family="monospace" font-size="10" fill="#0066cc">Mediterranean coast (all western pts, Y-sorted)</text>')
        svg.append('<text x="20" y="65" font-family="monospace" font-size="10" fill="#666">{} points</text>'.format(len(pts)))
        svg.append('</svg>')
        
        with open('analysis/isldat_clean_coasts/{}_clean_coast.svg'.format(name), 'w') as f:
            f.write('\n'.join(svg))
        print('  Wrote analysis/isldat_clean_coasts/{}_clean_coast.svg'.format(name))
        print()
        continue
    
    # Other theaters: use tile endpoints
    tiles = get_clean_coast(p)
    if not tiles:
        print(f'{name}: no coast tiles found')
        continue
    
    print(f'{name}: {len(tiles)} unique coast tiles')
    for wx, wy, ex, ey, row, col, west_pt, east_pt in tiles:
        print(f'  Coast Grid[{row},{col:3d}] West=({wx:7.3f},{wy:7.3f}) East=({ex:7.3f},{ey:7.3f})')
    
    all_x = [wx for wx, wy, ex, ey, _, _, _, _ in tiles] + [ex for wx, wy, ex, ey, _, _, _, _ in tiles]
    all_y = [wy for wx, wy, ex, ey, _, _, _, _ in tiles] + [ey for wx, wy, ex, ey, _, _, _, _ in tiles]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
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
    
    svg = ['<?xml version="1.0"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}">'.format(CANVAS, CANVAS, CANVAS, CANVAS),
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           '<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{} ISLDAT Clean Coast</text>'.format(name)]
    
    # Left edge (west)
    left_pts = [(tx(wx), ty(wy)) for wx, wy, ex, ey, _, _, _, _ in tiles]
    if left_pts:
        path = 'M {:.2f} {:.2f}'.format(left_pts[0][0], left_pts[0][1])
        for sx, sy in left_pts[1:]:
            path += ' L {:.2f} {:.2f}'.format(sx, sy)
        svg.append('<path d="{}" fill="none" stroke="#0066cc" stroke-width="2" opacity="0.8"/>'.format(path))
    
    # Right edge (east)
    right_pts = [(tx(ex), ty(ey)) for wx, wy, ex, ey, _, _, _, _ in tiles]
    if right_pts:
        path = 'M {:.2f} {:.2f}'.format(right_pts[0][0], right_pts[0][1])
        for sx, sy in right_pts[1:]:
            path += ' L {:.2f} {:.2f}'.format(sx, sy)
        svg.append('<path d="{}" fill="none" stroke="#cc0000" stroke-width="2" opacity="0.8"/>'.format(path))
    
    for i, (wx, wy, ex, ey, row, col, west_pt, east_pt) in enumerate(tiles):
        sx_w, sy_w = tx(wx), ty(wy)
        sx_e, sy_e = tx(ex), ty(ey)
        svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="4" fill="#0066cc" opacity="0.8"/>'.format(sx_w, sy_w))
        svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="10" fill="black" text-anchor="middle">{}</text>'.format(sx_w, sy_w - 6, i))
        svg.append('<text x="{:.2f}" y="{:.2f}" font-family="monospace" font-size="8" fill="#666" text-anchor="middle">Grid[{},{}]</text>'.format(sx_w, sy_w + 14, row, col))
        svg.append('<circle cx="{:.2f}" cy="{:.2f}" r="4" fill="#cc0000" opacity="0.8"/>'.format(sx_e, sy_e))
    
    svg.append('<text x="20" y="50" font-family="monospace" font-size="10" fill="#0066cc">Left edge (west endpoints)</text>')
    svg.append('<text x="20" y="65" font-family="monospace" font-size="10" fill="#cc0000">Right edge (east endpoints)</text>')
    svg.append('<text x="20" y="80" font-family="monospace" font-size="10" fill="#666">{} tiles</text>'.format(len(tiles)))
    svg.append('</svg>')
    
    with open('analysis/isldat_clean_coasts/{}_clean_coast.svg'.format(name), 'w') as f:
        f.write('\n'.join(svg))
    print('  Wrote analysis/isldat_clean_coasts/{}_clean_coast.svg'.format(name))
    print()

print('Done!')