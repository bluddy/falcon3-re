#!/usr/bin/env python3
"""Proper ISLDAT SVG generator with sub-record boundary detection."""
import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VALID_ATTRS = {0x14, 0x32, 0x64, 0xC8}
ATTR_COLORS = {0x14: '#0066cc', 0x32: '#00cc66', 0x64: '#6600cc', 0xC8: '#cc0000'}

def clamp_slope(q):
    if q > 0x7FFF: return 0x7FFF
    if q < -0x8000: return -0x8000
    return q

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    def scan_table(base):
        ptrs = []
        off = base
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            ptrs.append(v)
        return ptrs
    
    t1 = scan_table(t1_base)
    t2 = scan_table(t2_base)
    
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(off)
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        attr = struct.unpack_from('<H', body, r_off + 0x20)[0]
        if attr not in (0x14, 0x32, 0x64, 0xC8):
            continue
            
        pts_off = r_off + 0x38
        pts = []
        # Read points until sub-record pattern detected
        for i in range(200):  # max 200 points
            if pts_off + 6 > len(body):
                break
            # Check for sub-record pattern: first word has high bits (0x1000, 0x8000, 0xFFFF)
            if pts_off + 2 <= len(body):
                first_word = struct.unpack_from('<H', body, pts_off)[0]
                # Sub-record flags often have bit 12 (0x1000) or 0xFFFF
                if (first_word & 0xF000) != 0:  # high nibble set
                    break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
            if len(pts) > 200:  # safety limit
                break
        
        if pts:
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
           f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} ISLDAT Coastline</text>']
    
    for attr in (0x14, 0x32, 0x64, 0xC8):
        color = ATTR_COLORS.get(attr, '#888888')
        for r_off, attr_r, pts in records:
            if attr_r != attr:
                continue
            if len(pts) < 3:
                continue
            path = f'M {tx(pts[0][0])} {ty(pts[0][1])}'
            for px, py in pts[1:]:
                path += f' L {tx(px)} {ty(py)}'
            path += ' Z'
            svg.append(f'<path d="{path}" fill="none" stroke="{ATTR_COLORS.get(attr, "#888")}" stroke-width="1.5" opacity="0.7"/>')
    
    svg.append('</svg>')
    with open(f'{output_dir}/{theater_name}_coastline.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'  Wrote {output_dir}/{theater_name}_coastline.svg')

if __name__ == '__main__':
    import glob, os, struct
    os.makedirs('analysis/isldat_svgs_final', exist_ok=True)
    for p in glob.glob('game/ISLDAT.*'):
        name = os.path.basename(p).split('.')[-1]
        if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
            recs = parse_isldat(p)
            print(f'{name}: {len(recs)} valid records')
            generate_svg(recs, f'ISLDAT_{name}', 'analysis/isldat_svgs_final')