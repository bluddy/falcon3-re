#!/usr/bin/env python3
"""Proper ISLDAT SVG generator with full pipeline simulation."""
import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VALID_ATTRS = {0x14, 0x32, 0x64, 0xC8}
ATTR_NAMES = {0x14: 'coastline', 0x32: 'river', 0x64: 'lake', 0xC8: 'border'}
ATTR_COLORS = {0x14: '#0066cc', 0x32: '#00cc66', 0x64: '#6600cc', 0xC8: '#cc0000'}

def parse_isldat(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap_flag = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    
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
    
    records = []
    for r_off in sorted(recs):
        if r_off + 0x36 > len(body):
            continue
        x, y, z = struct.unpack_from('<iii', body, r_off)
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r_off + 0x20)
        
        if attr not in (0x14, 0x32, 0x64, 0xC8):
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
        for _ in range(50):  # safety limit
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
            if sub_off >= len(body) or sub_off > r_off + 800:
                break
        
        if pts and subs:
            records.append((r_off, attr, pts, subs))
    return records

def build_line_table(pts):
    """Build implicit line table from points: N points -> N edges (closed loop)."""
    if len(pts) < 2:
        return []
    lines = []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        lines.append((x0, y0, x1, y1))
    return lines

def generate_svg(records, theater_name, output_dir='analysis/isldat_svgs_v3'):
    os.makedirs(output_dir, exist_ok=True)
    
    all_pts = []
    for _, _, pts, _ in records:
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
           f'<text x="20" y="30" font-family="monospace" font-size="16" fill="#333">{theater_name} ISLDAT</text>']
    
    for attr in (0x14, 0x32, 0x64, 0xC8):
        color = ATTR_COLORS.get(attr, '#888888')
        name = ATTR_NAMES.get(attr, f'unknown_0x{attr:02X}')
        for r_off, attr, pts, subs in records:
            if attr != attr:
                continue
            # Build line table from points (closed loop)
            line_table = build_line_table(pts)
            
            for flags, opcode, nodes in subs:
                if not nodes:
                    continue
                # Follow node chain - nodes are indices into line table (0x10 stride = index)
                poly_pts = []
                for node_offset in nodes:
                    idx = node_offset // 0x10  # convert byte offset to entry index
                    if 0 <= idx < len(line_table):
                        x0, y0, x1, y1 = line_table[idx]
                        if not poly_pts:
                            poly_pts.append((x0, y0))
                        poly_pts.append((x1, y1))
                
                if len(poly_pts) >= 3:
                    path = f'M {tx(poly_pts[0][0])} {ty(poly_pts[0][1])}'
                    for px, py in poly_pts[1:]:
                        path += f' L {tx(px)} {ty(py)}'
                    path += ' Z'
                    svg.append(f'<path d="{path}" fill="none" stroke="{ATTR_COLORS.get(attr, "#888")}" stroke-width="1.5" opacity="0.7" data-attr="0x{attr:02X}"/>')
    
    svg.append('</svg>')
    with open(f'{output_dir}/{theater_name}_proper.svg', 'w') as f:
        f.write('\n'.join(svg))
    print(f'  Wrote {output_dir}/{theater_name}_proper.svg ({len(records)} records)')

if __name__ == '__main__':
    import glob, os
    os.makedirs('analysis/isldat_svgs_v3', exist_ok=True)
    for p in glob.glob('game/ISLDAT.*'):
        name = os.path.basename(p).split('.')[-1]
        if name in ('BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN'):
            recs = parse_isldat(p)
            print(f'{name}: {len(recs)} valid records')
            generate_svg(recs, f'ISLDAT_{name}', 'analysis/isldat_svgs_v3')