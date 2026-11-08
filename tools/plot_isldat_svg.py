#!/usr/bin/env python3
import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def parse_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    body_len, _, t1_base, t2_base, swap = struct.unpack('<HHHHB', data[:9])
    body = data[9:]
    t1 = []
    off = t1_base
    while off + 2 <= len(body):
        v = struct.unpack_from('<H', body, off)[0]
        off += 2
        if v == 0xFFFF:
            break
        t1.append(v)
    t2 = []
    off = t2_base
    while off + 2 <= len(body):
        v = struct.unpack_from('<H', body, off)[0]
        off += 2
        if v == 0xFFFF:
            break
        t2.append(v)
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
    for r in sorted(recs):
        if r + 0x36 > len(body):
            continue
        attr, ptr26, const000b, const_ffff_a, const_0_b, ptr2e, const4, pc, pts_ptr, op_ptr = struct.unpack_from('<HHHHHHHHHH', body, r + 0x20)
        pts_off = r + 0x38
        pts = []
        for i in range(pc):
            if pts_off + 6 > len(body):
                break
            px, mid, py = struct.unpack_from('<hhh', body, pts_off)
            pts.append((px, py))
            pts_off += 6
        records.append((r, attr, pts))
    return records

all_pts = []
for p in glob.glob('game/ISLDAT.*'):
    recs = parse_file(p)
    for _, _, pts in recs:
        all_pts.extend(pts)
if not all_pts:
    print('no points')
    sys.exit(1)
xs = [p[0] for p in all_pts]
ys = [p[1] for p in all_pts]
minx, maxx = min(xs), max(xs)
miny, maxy = min(ys), max(ys)
print('Global bounds:', minx, maxx, miny, maxy)

os.makedirs('analysis/isldat_svgs', exist_ok=True)
for p in glob.glob('game/ISLDAT.*'):
    name = os.path.basename(p).split('.')[-1]
    recs = parse_file(p)
    w = maxx - minx
    h = maxy - miny
    margin = max(w, h) * 0.1
    canvas_w = w + 2 * margin
    canvas_h = h + 2 * margin
    def tx(x): return (x - minx + margin)
    def ty(y): return canvas_h - (y - miny + margin)
    svg = ['<?xml version="1.0"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(int(canvas_w)) + '" height="' + str(int(canvas_h)) + '" viewBox="0 0 ' + str(int(canvas_w)) + ' ' + str(int(canvas_h)) + '">',
           '<rect width="100%" height="100%" fill="#f0f0f0"/>']
    colors = ['#0066cc', '#cc0000', '#00cc66', '#cc6600', '#6600cc', '#cc00cc']
    for i, (r, attr, pts) in enumerate(recs):
        if len(pts) < 2:
            continue
        c = colors[i % len(colors)]
        path = 'M ' + str(tx(pts[0][0])) + ' ' + str(ty(pts[0][1]))
        for px, py in pts[1:]:
            path += ' L ' + str(tx(px)) + ' ' + str(ty(py))
        path += ' Z'
        svg.append('<path d="' + path + '" fill="none" stroke="' + c + '" stroke-width="2" opacity="0.7"/>')
        cx = sum(tx(p[0]) for p in pts) / len(pts)
        cy = sum(ty(p[1]) for p in pts) / len(pts)
        svg.append('<text x="' + str(cx) + '" y="' + str(cy) + '" font-size="8" fill="' + c + '">' + format(r, '04X') + '</text>')
    svg.append('</svg>')
    with open('analysis/isldat_svgs/ISLDAT_' + name + '.svg', 'w') as f:
        f.write('\n'.join(svg))
    print('Wrote analysis/isldat_svgs/ISLDAT_' + name + '.svg', len(recs), 'records')

# Combined SVG
svg = ['<?xml version="1.0"?>',
       '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(int(canvas_w)) + '" height="' + str(int(canvas_h)) + '" viewBox="0 0 ' + str(int(canvas_w)) + ' ' + str(int(canvas_h)) + '">',
       '<rect width="100%" height="100%" fill="#f0f0f0"/>']
colors = ['#0066cc', '#cc0000', '#00cc66', '#cc6600', '#6600cc', '#cc00cc', '#00cccc', '#990000']
for p in glob.glob('game/ISLDAT.*'):
    name = os.path.basename(p).split('.')[-1]
    recs = parse_file(p)
    c = colors[len(svg) % len(colors)]
    for i, (r, attr, pts) in enumerate(recs):
        if len(pts) < 2:
            continue
        path = 'M ' + str(tx(pts[0][0])) + ' ' + str(ty(pts[0][1]))
        for px, py in pts[1:]:
            path += ' L ' + str(tx(px)) + ' ' + str(ty(py))
        path += ' Z'
        svg.append('<path d="' + path + '" fill="none" stroke="' + c + '" stroke-width="1" opacity="0.5"/>')
svg.append('</svg>')
with open('analysis/isldat_svgs/ISLDAT_ALL.svg', 'w') as f:
    f.write('\n'.join(svg))
print('Wrote analysis/isldat_svgs/ISLDAT_ALL.svg')