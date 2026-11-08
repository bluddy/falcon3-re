"""Extract ISLDAT outlines (coastlines, lake shores, river banks) per record (finding 118).

Geometry model (docs/structures.md section ISLDAT):
  every sub-record ring is CONVEX -- a record's rings are a convex
  decomposition of its land/water area, with interior edges shared by two rings.
  So the outline = edges used by exactly ONE ring.

  Coast records (attr 0x14) are TILES: their area is clipped to a local box
  (ISR: x +-4388, z +-5109; IRQ: +-5502), and the clip shows up as unshared,
  axis-aligned edges lying on the record's own bounding box.  Those are the
  tile seams, not shoreline, so they are dropped (for every attr except lakes,
  0x64, which are self-contained and keep every unshared edge).

  The remaining edges are chained into polylines (open = runs from box side to
  box side, closed = islands / lakes).

Coordinates are the record's LOCAL point units ({i16 x, 0, i16 z}).  The
local->world transform (scale/orientation relative to the record's 16.16 nm
X/Y) is still open, so the SVG is a small-multiples sheet: one cell per record,
box outline in grey, outline polylines in the attr colour, +z drawn up.

Output: analysis/isldat_coast_edges/<THEATER>.json + <THEATER>.svg
Usage:  venv\\Scripts\\python tools\\extract_isldat_coast_edges.py
"""
import glob
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path('analysis/isldat_coast_edges')
ATTR_COLORS = {0x14: '#0066cc', 0x32: '#00aa55', 0x64: '#6600cc', 0xC8: '#cc0000'}
CELL = 220


def u16(b, o): return struct.unpack_from('<H', b, o)[0]


def table_extent(body, base, limit):
    """K where min(u16[0..K-1]) == base+2K (same fixed point as parse_isldat.py)."""
    best = 0
    for k in range(1, (limit - base) // 2 + 1):
        if min(u16(body, base + 2 * j) for j in range(k)) == base + 2 * k:
            best = k
    return [u16(body, base + 2 * j) for j in range(best)]


def record_offsets(raw):
    body = raw[9:]
    t1, t2 = struct.unpack_from('<HH', raw, 4)
    recs = set()
    for ptr in table_extent(body, t1, t2) + table_extent(body, t2, len(body)):
        o = ptr
        while u16(body, o) != 0xFFFF:
            recs.add(u16(body, o))
            o += 2
    return body, sorted(recs)


def rings(body, rec):
    """Yield each sub-record ring as a list of point indices (closed: last == first)."""
    o = u16(body, rec + 0x32)
    while u16(body, o) != 0xFFFF:
        sub = u16(body, o)
        o += 2
        chain = u16(body, sub) & 0x1000
        q = sub + 4
        while True:
            cnt = u16(body, q)
            if cnt == 0xFFFF:
                break
            yield [u16(body, q + 2 + 2 * k) // 16 for k in range(cnt + 1)]
            q += 2 + 2 * (cnt + 1)
            if not chain:
                break


def chain_edges(edges):
    """Chain undirected edges into polylines: open runs first, then closed loops."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    used = set()
    out = []

    def walk(start):
        line = [start]
        cur = start
        while True:
            nxt = [n for n in adj[cur] if (min(cur, n), max(cur, n)) not in used]
            if not nxt:
                return line
            n = nxt[0]
            used.add((min(cur, n), max(cur, n)))
            line.append(n)
            cur = n

    for v in [v for v in adj if len(adj[v]) % 2 == 1]:
        if any((min(v, n), max(v, n)) not in used for n in adj[v]):
            out.append(dict(closed=False, idx=walk(v)))
    for v in adj:
        if any((min(v, n), max(v, n)) not in used for n in adj[v]):
            out.append(dict(closed=True, idx=walk(v)))
    return out


def extract(body, rec):
    n = u16(body, rec + 0x2E)
    pts = [struct.unpack_from('<hhh', body, rec + 0x38 + 6 * i) for i in range(n)]
    xs = [p[0] for p in pts]
    zs = [p[2] for p in pts]
    box = (min(xs), max(xs), min(zs), max(zs))
    use = Counter()
    nrings = 0
    for ring in rings(body, rec):
        nrings += 1
        for a, b in zip(ring, ring[1:]):
            use[(min(a, b), max(a, b))] += 1
    attr = u16(body, rec + 0x20)
    outline, seams = [], []
    for e, k in use.items():
        if k != 1:
            continue
        pa, pb = pts[e[0]], pts[e[1]]
        # lakes are self-contained (never clipped): keep every unshared edge
        on_box = attr != 0x64 and (
            (pa[0] == pb[0] and pa[0] in (box[0], box[1])) or
            (pa[2] == pb[2] and pa[2] in (box[2], box[3])))
        (seams if on_box else outline).append(e)
    lines = chain_edges(outline)
    for ln in lines:
        ln['pts'] = [[pts[i][0], pts[i][2]] for i in ln['idx']]
    return dict(off=rec, attr=attr,
                x_nm=struct.unpack_from('<i', body, rec)[0] / 65536.0,
                y_nm=struct.unpack_from('<i', body, rec + 4)[0] / 65536.0,
                box=list(box), rings=nrings, edges=len(use),
                outline_edges=len(outline), seam_edges=len(seams),
                polylines=lines)


def svg(theater, recs):
    cols = 6
    rows = (len(recs) + cols - 1) // cols
    w, h = cols * CELL, rows * CELL
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'font-family="monospace" font-size="10">' % (w, h),
         '<rect width="100%" height="100%" fill="white"/>']
    for i, r in enumerate(recs):
        cx = (i % cols) * CELL + CELL / 2
        cy = (i // cols) * CELL + CELL / 2 + 6
        x0, x1, z0, z1 = r['box']
        k = (CELL - 40) / max(x1 - x0, z1 - z0, 1)
        mx, mz = (x0 + x1) / 2, (z0 + z1) / 2

        def P(x, z):
            return '%.1f,%.1f' % (cx + (x - mx) * k, cy - (z - mz) * k)
        s.append('<polygon points="%s %s %s %s" fill="none" stroke="#ccc"/>'
                 % (P(x0, z0), P(x1, z0), P(x1, z1), P(x0, z1)))
        col = ATTR_COLORS.get(r['attr'], '#000')
        for ln in r['polylines']:
            tag = 'polygon' if ln['closed'] else 'polyline'
            s.append('<%s points="%s" fill="none" stroke="%s" stroke-width="1.5"/>'
                     % (tag, ' '.join(P(x, z) for x, z in ln['pts']), col))
        s.append('<text x="%d" y="%d">%s 0x%X a=0x%02X (%.2f,%.2f)</text>'
                 % ((i % cols) * CELL + 4, (i // cols) * CELL + 12, theater,
                    r['off'], r['attr'], r['x_nm'], r['y_nm']))
    s.append('</svg>')
    return '\n'.join(s)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(glob.glob('game/ISLDAT.*')):
        theater = Path(path).suffix[1:]
        body, offs = record_offsets(Path(path).read_bytes())
        recs = [extract(body, r) for r in offs]
        json.dump(dict(theater=theater, units='record-local point units; '
                       'world transform open (finding 118)', records=recs),
                  open(OUT / ('%s.json' % theater), 'w'), indent=1)
        if recs:
            (OUT / ('%s.svg' % theater)).write_text(svg(theater, recs))
        print('%-4s recs=%3d outline_edges=%4d seam_edges=%3d polylines=%3d (closed %d)' % (
            theater, len(recs), sum(r['outline_edges'] for r in recs),
            sum(r['seam_edges'] for r in recs),
            sum(len(r['polylines']) for r in recs),
            sum(1 for r in recs for ln in r['polylines'] if ln['closed'])))
    print('wrote %s/' % OUT.as_posix())


main()
