#!/usr/bin/env python3
"""ISLDAT SVG generator - points only (no connectivity lines) for debugging."""
import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VALID_ATTRS = {0x14, 0x32, 0x64, 0xC8}
ATTR_NAMES = {0x14: 'coastline', 0x32: 'river', 0x64: 'lake', 0xC8: 'border'}
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
            # Valid points ALWAYS have mid=0; sub-record data has non-zero mid
            if mid != 0:
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

def generate_points_only_svg(records, theater_name, output_dir='analysis/isldat_svgs_points_only'):
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
    
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} ISLDAT Points Only</text>']
    
    global_idx = 0
    for attr in (0x14, 0x32, 0x64, 0xC8):
        color = ATTR_COLORS.get(attr, '#888888')
        for r_off, attr_r, pts in records:
            if attr_r != attr:
                continue
            # Draw only points as small circles with index labels
            for i, (px, py) in enumerate(pts):
                svg.append(f'<circle cx="{tx(px)}" cy="{ty(py)}" r="2" fill="{color}" opacity="0.8"/>')
                svg.append(f'<text x="{tx(px)}" y="{ty(py) - 8}" font-family="monospace" font-size="7" fill="black" text-anchor="middle" dominant-baseline="bottom">{global_idx}</text>')
                global_idx += 1
    
    svg.append('</svg>')
    with open(f'{output_dir}/{theater_name}_points.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'  Wrote {output_dir}/{theater_name}_points.svg')

def generate_nel_fixed_svg(records, theater_name, output_dir='analysis/isldat_svgs_final'):
    """NEL-specific: each record as separate closed polygon."""
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
    
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} ISLDAT Coastline (NEL fixed)</text>']
    
    global_idx = 0
    for attr in (0x14, 0x32, 0x64, 0xC8):
        color = ATTR_COLORS.get(attr, '#888888')
        for r_off, attr_r, pts in records:
            if attr_r != attr:
                continue
            if len(pts) < 3:
                continue
            # Each record as separate closed polygon
            path = f'M {tx(pts[0][0])} {ty(pts[0][1])}'
            for i, (px, py) in enumerate(pts[1:], 1):
                path += f' L {tx(px)} {ty(py)}'
            path += ' Z'  # Close each record
            svg.append(f'<path d="{path}" fill="none" stroke="{ATTR_COLORS.get(attr, "#888")}" stroke-width="1.5" opacity="0.7"/>')
            
            # Add point labels with global indices
            for i, (px, py) in enumerate(pts):
                svg.append(f'<text x="{tx(px)}" y="{ty(py)}" font-family="monospace" font-size="8" fill="black" text-anchor="middle" dominant-baseline="middle">{global_idx}</text>')
                global_idx += 1
    
    svg.append('</svg>')
    with open(f'{output_dir}/{theater_name}_coastline.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'  Wrote {output_dir}/{theater_name}_coastline.svg')

if __name__ == '__main__':
    import glob, os
    
    # Generate points-only SVGs for all theaters
    os.makedirs('analysis/isldat_svgs_points_only', exist_ok=True)
    for p in glob.glob('game/ISLDAT.*'):
        name = os.path.basename(p).split('.')[-1]
        if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
            recs = parse_isldat(p)
            print(f'{name}: {len(recs)} valid records, {sum(len(r[2]) for r in recs)} total points')
            generate_points_only_svg(recs, f'ISLDAT_{name}', 'analysis/isldat_svgs_points_only')
    
    # Generate fixed NEL SVG (closed lake loop)
    os.makedirs('analysis/isldat_svgs_final', exist_ok=True)
    for p in glob.glob('game/ISLDAT.*'):
        name = os.path.basename(p).split('.')[-1]
        if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
            recs = parse_isldat(p)
            if name == 'NEL':
                generate_nel_fixed_svg(recs, f'ISLDAT_{name}', 'analysis/isldat_svgs_final')
            else:
                # For other theaters, use the standard polygon approach
                all_pts = []
                for _, _, pts in recs:
                    all_pts.extend(pts)
                if not all_pts:
                    continue
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
                svg = ['<?xml version="1.0"?>',
                       f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
                       '<rect width="100%" height="100%" fill="#f0f0f0"/>',
                       f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{f"ISLDAT_{name}"} ISLDAT Coastline</text>']
                global_idx = 0
                for attr in (0x14, 0x32, 0x64, 0xC8):
                    color = ATTR_COLORS.get(attr, '#888888')
                    for r_off, attr_r, pts in recs:
                        if attr_r != attr:
                            continue
                        if len(pts) < 3:
                            continue
                        path = f'M {tx(pts[0][0])} {ty(pts[0][1])}'
                        for i, (px, py) in enumerate(pts[1:], 1):
                            path += f' L {tx(px)} {ty(py)}'
                        path += ' Z'
                        svg.append(f'<path d="{path}" fill="none" stroke="{ATTR_COLORS.get(attr, "#888")}" stroke-width="1.5" opacity="0.7"/>')
                        for i, (px, py) in enumerate(pts):
                            svg.append(f'<text x="{tx(px)}" y="{ty(py)}" font-family="monospace" font-size="8" fill="black" text-anchor="middle" dominant-baseline="middle">{global_idx}</text>')
                            global_idx += 1
                svg.append('</svg>')
                with open(f'analysis/isldat_svgs_final/ISLDAT_{name}_coastline.svg', 'w') as f:
                    f.write('\n'.join(svg))
                print(f'  Wrote analysis/isldat_svgs_final/ISLDAT_{name}_coastline.svg')