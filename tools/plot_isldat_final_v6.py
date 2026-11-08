#!/usr/bin/env python3
"""Proper ISLDAT SVG generator - connect record points as closed polygons."""
import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VALID_ATTRS = {0x14, 0x32, 0x64, 0xC8}
ATTR_COLORS = {0x14: '#0066cc', 0x32: '#00cc66', 0x64: '#6600cc', 0xC8: '#cc0000'}

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, unk, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    records = []
    for r_off in range(0, len(body) - 0x36, 2):
        attr = struct.unpack_from('<H', body, r_off + 0x20)[0]
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(200):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            if mid < -300 or mid > 300:
                break
            pts.append((px, py))
            pts_off += 6
            if len(pts) > 200:
                break
        
        if pts:
            attr = struct.unpack_from('<H', body, r_off + 0x20)[0]
            if attr in (0x14, 0x32, 0x64, 0xC8):
                records.append((r_off, attr, pts))
    return records

def generate_svg(records, theater_name, output_dir='analysis/isldat_svgs_final'):
    os.makedirs(output_dir, exist_ok=True)
    
    all_pts = []
    for _, _, pts in records:
        all_pts.extend(pts)
    if not all_pts:
        return
    
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    
    CANVAS = 4000
    MARGIN = 100
    w = maxx - minx
    h = maxy - miny
    scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
    
    def tx(x): return MARGIN + (x - minx) * scale
    def ty(y): return CANVAS - (MARGIN + (y - miny) * scale)
    
    os.makedirs(output_dir, exist_ok=True)
    
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           '<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{0} ISLDAT Coastline</text>'.format(theater_name)]
    
    for attr in (0x14, 0x32, 0x64, 0xC8):
        color = ATTR_COLORS.get(attr, '#888888')
        for r_off, attr_r, pts in records:
            if attr_r != attr:
                continue
            if len(pts) < 3:
                continue
            path = 'M {0} {1}'.format(tx(pts[0][0]), ty(pts[0][1]))
            for px, py in pts[1:]:
                path += ' L {0} {1}'.format(tx(px), ty(py))
            path += ' Z'
            svg.append('<path d="{0}" fill="none" stroke="{1}" stroke-width="1.5" opacity="0.7"/>'.format(path, ATTR_COLORS.get(attr, '#888')))
    
    svg.append('</svg>')
    with open('{0}/{1}_coastline.svg'.format(output_dir, theater_name), 'w') as f:
        f.write('\n'.join(svg))
    print('  Wrote {0}/{1}_coastline.svg'.format(output_dir, theater_name))

if __name__ == '__main__':
    import glob, os
    os.makedirs('analysis/isldat_svgs_final', exist_ok=True)
    for p in glob.glob('game/ISLDAT.*'):
        name = os.path.basename(p).split('.')[-1]
        if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
            recs = parse_isldat(p)
            print('{0}: {1} valid records'.format(name, len(recs)))
            generate_svg(recs, 'ISLDAT_' + name, 'analysis/isldat_svgs_final')