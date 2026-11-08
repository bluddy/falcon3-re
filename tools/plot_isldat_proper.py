#!/usr/bin/env python3
"""Proper ISLDAT SVG generator with attr filtering and correct scaling."""
import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ATTR_NAMES = {
    0x14: 'coastline',
    0x32: 'river', 
    0x64: 'lake',
    0xC8: 'border',
    0x00: 'unknown',
}
ATTR_COLORS = {
    0x14: '#0066cc',  # blue - coastline
    0x32: '#00cc66',  # green - river
    0x64: '#6600cc',  # purple - lake
    0xC8: '#cc0000',  # red - border
    0x00: '#888888',  # gray
}

VALID_ATTRS = {0x14, 0x32, 0x64, 0xC8}

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
    # grids
    gridB = body[0x000:0x400]
    gridA = body[0x400:0x500]
    
    # scan tables
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
    
    # follow lists
    recs = set()
    for idx in t1 + t2:
        off = idx
        while off + 2 <= len(body):
            v = struct.unpack_from('<H', body, off)[0]
            off += 2
            if v == 0xFFFF:
                break
            recs.add(v)
    
    # parse records
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        # Only process records with valid attr
        if attr not in VALID_ATTRS:
            continue
            
        pts_off = r_off + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        
        # parse sub-records
        sub_off = pts_off
        subs = []
        for _ in range(20):  # safety limit
            if sub_off + 4 > len(body):
                break
            flags, opcode = struct.unpack_from('<HH', body, sub_off)
            sub_off += 4
            nodes = []
            if flags & 0x1000:
                # chain until FFFF
                while sub_off + 2 <= len(body):
                    v = struct.unpack_from('<H', body, sub_off)[0]
                    sub_off += 2
                    if v == 0xFFFF:
                        break
                    nodes.append(v)
            else:
                # single node
                if sub_off + 2 <= len(body):
                    nodes.append(struct.unpack_from('<H', body, sub_off)[0])
                    sub_off += 2
            subs.append((flags, opcode, nodes))
            if sub_off >= len(body) or sub_off > r_off + 500:
                break
        
        if pts:  # only records with points
            records.append((r_off, attr, pts, subs))
    return records

def apply_attr_scale(pts, attr):
    """Apply attr scale factor. attr is a scale divisor."""
    if attr == 0:
        return pts
    # Scale factors: 0x14=1.0, 0x32=2.0, 0x64=4.0, 0xC8=8.0 (approximate)
    # Actually the attr is shifted by attr_scale_shift and used as divisor
    # For visualization, we'll use relative scaling
    scale_map = {0x14: 1.0, 0x32: 0.5, 0x64: 0.25, 0xC8: 0.125}
    scale = scale_map.get(attr, 1.0)
    return [(x * scale, y * scale) for x, y in pts]

def generate_svg(records, theater_name, output_dir='analysis/isldat_svgs_v2'):
    os.makedirs(output_dir, exist_ok=True)
    
    # Group by attr
    by_attr = {}
    all_pts = []
    for r_off, attr, pts, subs in records:
        if attr not in by_attr:
            by_attr[attr] = []
        by_attr[attr].append((r_off, pts, subs))
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
    
    # Combined SVG
    svg = ['<?xml version="1.0"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>',
           f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} ISLDAT - All Features</text>']
    
    for attr, items in sorted(by_attr.items()):
        color = ATTR_COLORS.get(attr, '#888888')
        name = ATTR_NAMES.get(attr, f'unknown_0x{attr:02X}')
        for r_off, pts, subs in items:
            if len(pts) < 2:
                continue
            path = f'M {tx(pts[0][0])} {ty(pts[0][1])}'
            for px, py in pts[1:]:
                path += f' L {tx(px)} {ty(py)}'
            path += ' Z'
            svg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.7" data-attr="0x{attr:02X}" data-name="{name}"/>')
            
            # Draw sub-record node chains
            for flags, opcode, nodes in subs:
                if not nodes:
                    continue
                # nodes are line-table offsets, we'd need to map to actual coordinates
                # For now just mark the record center
                cx = sum(tx(p[0]) for p in pts) / len(pts)
                cy = sum(ty(p[1]) for p in pts) / len(pts)
                svg.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{color}" opacity="0.5"/>')
    
    svg.append('</svg>')
    with open(f'{output_dir}/{theater_name}_combined.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'  Wrote {output_dir}/{theater_name}_combined.svg')
    
    # Per-attr SVGs
    for attr, items in sorted(by_attr.items()):
        color = ATTR_COLORS.get(attr, '#888888')
        name = ATTR_NAMES.get(attr, f'unknown_0x{attr:02X}')
        svg = ['<?xml version="1.0"?>',
               f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
               '<rect width="100%" height="100%" fill="#f0f0f0"/>',
               f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} - {name} (0x{attr:02X})</text>']
        for r_off, pts, subs in items:
            if len(pts) < 2:
                continue
            path = f'M {tx(pts[0][0])} {ty(pts[0][1])}'
            for px, py in pts[1:]:
                path += f' L {tx(px)} {ty(py)}'
            path += ' Z'
            svg.append(f'<path d="{path}" fill="none" stroke="{ATTR_COLORS.get(attr, "#888")}" stroke-width="1.5" opacity="0.7"/>')
        svg.append('</svg>')
        with open(f'{output_dir}/{theater_name}_{ATTR_NAMES.get(attr, f"unknown_{attr:02X}")}.svg', 'w') as f:
            f.write('\n'.join(svg))
        print(f'  Wrote {output_dir}/{theater_name}_{name}.svg')

for p in glob.glob('game/ISLDAT.*'):
    name = os.path.basename(p).split('.')[-1]
    if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):  # skip PAK (empty)
        recs = parse_isldat(p)
        print(f'{name}: {len(recs)} records')
        generate_svg(recs, f'ISLDAT_{name}')

# All-theater combined SVG
all_records = {}
for p in glob.glob('game/ISLDAT.*'):
    name = os.path.basename(p).split('.')[-1]
    if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
        all_records[name] = parse_isldat(p)

if all_records:
    output_dir = 'analysis/isldat_svgs_v2'
    os.makedirs(output_dir, exist_ok=True)
    CANVAS = 4000
    MARGIN = 100
    
    all_pts = []
    for recs in all_records.values():
        for _, _, pts, _ in recs:
            all_pts.extend(pts)
    
    if all_pts:
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        w = maxx - minx
        h = maxy - miny
        scale = (CANVAS - 2 * MARGIN) / max(w, h) if max(w, h) > 0 else 1
        
        def tx(x): return MARGIN + (x - minx) * scale
        def ty(y): return CANVAS - (MARGIN + (y - miny) * scale)
        
        colors = {0x14: '#0066cc', 0x32: '#00cc66', 0x64: '#6600cc', 0xC8: '#cc0000'}
        
        svg = ['<?xml version="1.0"?>',
               f'<svg xmlns="http://www.w3.org/2000/svg" width="4000" height="4000" viewBox="0 0 4000 4000">',
               '<rect width="100%" height="100%" fill="#f0f0f0"/>',
               '<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">ALL THEATERS ISLDAT</text>']
        
        for attr in [0x14, 0x32, 0x64, 0xC8]:
            color = {0x14: '#0066cc', 0x32: '#00cc66', 0x64: '#6600cc', 0xC8: '#cc0000'}[attr]
            for theater, recs in all_records.items():
                for r_off, attr, pts, subs in [r for r in all_records[theater] if r[1] == attr]:
                    if len(pts) < 2: continue
                    path = f'M {tx(pts[0][0])} {ty(pts[0][1])}'
                    for px, py in pts[1:]:
                        path += f' L {tx(px)} {ty(py)}'
                    path += ' Z'
                    svg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1" opacity="0.5" data-theater="{theater}"/>')
        
        svg.append('</svg>')
        with open('analysis/isldat_svgs_v2/ISLDAT_ALL.svg', 'w') as f:
            f.write('\n'.join(svg))
        print('Wrote analysis/isldat_svgs_v2/ISLDAT_ALL.svg')