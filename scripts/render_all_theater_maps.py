#!/usr/bin/env python3
"""
Falcon 3.0 Theater Map Renderer
Interprets and renders:
1. *.MAP (240x200 8-bit elevation/terrain raster) with ALTPAL.<EXT> VGA palette
2. ISLDAT.<EXT> (Vector spatial index + convex polygon rings -> outline polylines)
3. Generates high-resolution PNGs and SVGs for all theaters:
   - BOS (Bosnia)
   - HOK (Hokkaido / Japan)
   - IRQ (Kuwait / Iraq)
   - ISR (Israel)
   - KOR (Korea)
   - NEL (Nellis)
   - PAK (Pakistan / India)
   - PAN (Panama)
"""

import os
import struct
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path('analysis/theater_maps')
GAME_DIR = Path('game')

THEATERS = {
    'BOS': {'name': 'Bosnia-Herzegovina', 'map': 'BOSNIA.MAP', 'isl': 'ISLDAT.BOS', 'pal': 'ALTPAL.BOS'},
    'HOK': {'name': 'Hokkaido (Japan)',   'map': 'JAPAN.MAP',  'isl': 'ISLDAT.HOK', 'pal': 'ALTPAL.HOK'},
    'IRQ': {'name': 'Kuwait / Iraq',      'map': 'KUWAIT.MAP', 'isl': 'ISLDAT.IRQ', 'pal': 'ALTPAL.IRQ'},
    'ISR': {'name': 'Israel / Sinai',     'map': 'ISRAEL.MAP', 'isl': 'ISLDAT.ISR', 'pal': 'ALTPAL.ISR'},
    'KOR': {'name': 'Korea',              'map': 'KOREA.MAP',  'isl': 'ISLDAT.KOR', 'pal': 'ALTPAL.KOR'},
    'NEL': {'name': 'Nellis (Red Flag)',  'map': 'NELLIS.MAP', 'isl': 'ISLDAT.NEL', 'pal': 'ALTPAL.NEL'},
    'PAK': {'name': 'Pakistan / India',   'map': 'INDIA.MAP',  'isl': 'ISLDAT.PAK', 'pal': 'ALTPAL.PAK'},
    'PAN': {'name': 'Panama',             'map': 'PANAMA.MAP', 'isl': 'ISLDAT.PAN', 'pal': 'ALTPAL.PAN'},
}

ATTR_STYLE = {
    0x14: {'name': 'Coastline', 'color': (30, 136, 229),  'hex': '#1e88e5', 'width': 3},
    0x32: {'name': 'River',     'color': (0, 191, 165),   'hex': '#00bfa5', 'width': 2},
    0x64: {'name': 'Lake',      'color': (57, 73, 171),   'hex': '#3949ab', 'width': 2},
    0xC8: {'name': 'Border',    'color': (229, 57, 53),   'hex': '#e53935', 'width': 3},
}

def load_altpal(pal_path):
    raw = pal_path.read_bytes()
    pal = []
    # 280 colors in 6-bit VGA DAC (0..63) -> convert to 8-bit (0..255)
    for i in range(256):
        if (i + 1) * 3 <= len(raw):
            r = min(255, raw[i * 3] * 4 + raw[i * 3] // 16)
            g = min(255, raw[i * 3 + 1] * 4 + raw[i * 3 + 1] // 16)
            b = min(255, raw[i * 3 + 2] * 4 + raw[i * 3 + 2] // 16)
        else:
            r, g, b = (i, i, i)
        pal.extend([r, g, b])
    return pal

def parse_isldat(isl_path):
    raw = isl_path.read_bytes()
    if len(raw) < 18:
        return []
    body = raw[9:]
    t1, t2 = struct.unpack_from('<HH', raw, 4)
    def u16(b, o): return struct.unpack_from('<H', b, o)[0]
    
    def table_extent(base, limit):
        best = 0
        for k in range(1, (limit - base) // 2 + 1):
            if min(u16(body, base + 2 * j) for j in range(k)) == base + 2 * k:
                best = k
        return [u16(body, base + 2 * j) for j in range(best)]
    
    recs = set()
    for ptr in table_extent(t1, t2) + table_extent(t2, len(body)):
        o = ptr
        while o + 2 <= len(body) and u16(body, o) != 0xFFFF:
            recs.add(u16(body, o))
            o += 2

    def rings(rec):
        o = u16(body, rec + 0x32)
        while u16(body, o) != 0xFFFF:
            sub = u16(body, o)
            o += 2
            chain = u16(body, sub) & 0x1000
            q = sub + 4
            while True:
                cnt = u16(body, q)
                if cnt == 0xFFFF: break
                yield [u16(body, q + 2 + 2 * k) // 16 for k in range(cnt + 1)]
                q += 2 + 2 * (cnt + 1)
                if not chain: break

    def chain_edges(edges):
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
                if not nxt: return line
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

    features = []
    for rec in sorted(recs):
        if rec + 0x38 > len(body): continue
        n = u16(body, rec + 0x2E)
        if rec + 0x38 + 6 * n > len(body): continue
        pts = [struct.unpack_from('<hhh', body, rec + 0x38 + 6 * i) for i in range(n)]
        xs = [p[0] for p in pts]
        zs = [p[2] for p in pts]
        box = (min(xs), max(xs), min(zs), max(zs))
        use = Counter()
        for ring in rings(rec):
            for a, b in zip(ring, ring[1:]):
                use[(min(a, b), max(a, b))] += 1
        attr = u16(body, rec + 0x20)
        outline = []
        for e, k in use.items():
            if k != 1: continue
            pa, pb = pts[e[0]], pts[e[1]]
            on_box = attr != 0x64 and (
                (pa[0] == pb[0] and pa[0] in (box[0], box[1])) or
                (pa[2] == pb[2] and pa[2] in (box[2], box[3])))
            if not on_box:
                outline.append(e)
        lines = chain_edges(outline)
        tx = struct.unpack_from('<i', body, rec)[0] / 65536.0
        ty = struct.unpack_from('<i', body, rec + 4)[0] / 65536.0
        
        # Scale local points to NM: px / 2000.0, pz / 2000.0
        for ln in lines:
            world_pts = []
            for idx in ln['idx']:
                px, _, pz = pts[idx]
                wx = tx + px / 2000.0
                wy = ty + pz / 2000.0
                world_pts.append((wx, wy))
            ln['world_pts'] = world_pts

        features.append({
            'rec': rec,
            'attr': attr,
            'tx': tx,
            'ty': ty,
            'polylines': lines
        })
    return features

def render_vector_svg(code, info, features, out_svg_path):
    all_pts = [pt for f in features for ln in f['polylines'] for pt in ln['world_pts']]
    if not all_pts:
        return
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    pad_x = max(1.0, (max_x - min_x) * 0.05)
    pad_y = max(1.0, (max_y - min_y) * 0.05)
    box_x0, box_x1 = min_x - pad_x, max_x + pad_x
    box_y0, box_y1 = min_y - pad_y, max_y + pad_y
    
    W = 1200
    H = int(W * (box_y1 - box_y0) / (box_x1 - box_x0))
    H = max(600, min(1400, H))
    
    def to_svg(wx, wy):
        sx = (wx - box_x0) / (box_x1 - box_x0) * W
        # Invert Y so North (+Y) is UP
        sy = H - (wy - box_y0) / (box_y1 - box_y0) * H
        return f"{sx:.1f},{sy:.1f}"

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="background:#0f172a; font-family:system-ui, sans-serif;">',
        f'  <defs>',
        f'    <radialGradient id="bgGrad" cx="50%" cy="50%" r="75%">',
        f'      <stop offset="0%" stop-color="#1e293b"/>',
        f'      <stop offset="100%" stop-color="#090d16"/>',
        f'    </radialGradient>',
        f'  </defs>',
        f'  <rect width="100%" height="100%" fill="url(#bgGrad)"/>',
        f'  <!-- Theater Title -->',
        f'  <text x="30" y="50" fill="#f8fafc" font-size="28" font-weight="bold">{info["name"]} ({code})</text>',
        f'  <text x="30" y="80" fill="#94a3b8" font-size="16">ISLDAT Vector Features • Bounds: X [{min_x:.1f} .. {max_x:.1f} nm], Y [{min_y:.1f} .. {max_y:.1f} nm]</text>',
    ]
    
    # Draw grid lines
    grid_step = 10.0 # nm
    gx = int(box_x0 // grid_step) * grid_step
    while gx <= box_x1:
        p0 = to_svg(gx, box_y0)
        p1 = to_svg(gx, box_y1)
        lines.append(f'  <line x1="{p0.split(",")[0]}" y1="{p0.split(",")[1]}" x2="{p1.split(",")[0]}" y2="{p1.split(",")[1]}" stroke="#334155" stroke-width="1" stroke-dasharray="4,4"/>')
        lines.append(f'  <text x="{p0.split(",")[0]}" y="{H-15}" fill="#64748b" font-size="12" text-anchor="middle">{gx:.0f} nm</text>')
        gx += grid_step

    gy = int(box_y0 // grid_step) * grid_step
    while gy <= box_y1:
        p0 = to_svg(box_x0, gy)
        p1 = to_svg(box_x1, gy)
        lines.append(f'  <line x1="{p0.split(",")[0]}" y1="{p0.split(",")[1]}" x2="{p1.split(",")[0]}" y2="{p1.split(",")[1]}" stroke="#334155" stroke-width="1" stroke-dasharray="4,4"/>')
        lines.append(f'  <text x="25" y="{p0.split(",")[1]}" fill="#64748b" font-size="12" dominant-baseline="middle">{gy:.0f}</text>')
        gy += grid_step

    # Draw features grouped by attribute
    for attr, style in ATTR_STYLE.items():
        attr_feats = [f for f in features if f['attr'] == attr]
        if not attr_feats:
            continue
        lines.append(f'  <!-- Attribute {style["name"]} (0x{attr:02X}) -->')
        lines.append(f'  <g stroke="{style["hex"]}" stroke-width="{style["width"]}" fill="none" stroke-linecap="round" stroke-linejoin="round">')
        for f in attr_feats:
            for ln in f['polylines']:
                pts = [to_svg(p[0], p[1]) for p in ln['world_pts']]
                tag = 'polygon' if ln['closed'] else 'polyline'
                lines.append(f'    <{tag} points="{" ".join(pts)}"/>')
        lines.append('  </g>')

    # Legend
    lines.append(f'  <!-- Legend -->')
    lines.append(f'  <g transform="translate({W-220}, 30)">')
    lines.append(f'    <rect width="190" height="{len(ATTR_STYLE)*26 + 20}" rx="8" fill="#1e293b" stroke="#475569" opacity="0.9"/>')
    lines.append(f'    <text x="15" y="20" fill="#f1f5f9" font-size="13" font-weight="bold">Vector Layers</text>')
    ly = 42
    for attr, style in ATTR_STYLE.items():
        has_layer = any(f['attr'] == attr for f in features)
        if has_layer:
            lines.append(f'    <line x1="15" y1="{ly}" x2="40" y2="{ly}" stroke="{style["hex"]}" stroke-width="3"/>')
            lines.append(f'    <text x="48" y="{ly+4}" fill="#e2e8f0" font-size="12">{style["name"]}</text>')
            ly += 24
    lines.append('  </g>')

    lines.append('</svg>')
    out_svg_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"  -> Generated SVG: {out_svg_path}")

def render_vector_png(code, info, features, out_png_path):
    all_pts = [pt for f in features for ln in f['polylines'] for pt in ln['world_pts']]
    if not all_pts:
        return
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    pad_x = max(1.0, (max_x - min_x) * 0.05)
    pad_y = max(1.0, (max_y - min_y) * 0.05)
    box_x0, box_x1 = min_x - pad_x, max_x + pad_x
    box_y0, box_y1 = min_y - pad_y, max_y + pad_y
    
    W = 1200
    H = int(W * (box_y1 - box_y0) / (box_x1 - box_x0))
    H = max(600, min(1400, H))
    
    img = Image.new('RGB', (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    def to_px(wx, wy):
        sx = (wx - box_x0) / (box_x1 - box_x0) * W
        sy = H - (wy - box_y0) / (box_y1 - box_y0) * H
        return (sx, sy)

    # Draw grid lines
    grid_step = 10.0
    gx = int(box_x0 // grid_step) * grid_step
    while gx <= box_x1:
        p0 = to_px(gx, box_y0)
        p1 = to_px(gx, box_y1)
        draw.line([p0, p1], fill=(51, 65, 85), width=1)
        gx += grid_step

    gy = int(box_y0 // grid_step) * grid_step
    while gy <= box_y1:
        p0 = to_px(box_x0, gy)
        p1 = to_px(box_x1, gy)
        draw.line([p0, p1], fill=(51, 65, 85), width=1)
        gy += grid_step

    # Draw polylines
    for attr, style in ATTR_STYLE.items():
        attr_feats = [f for f in features if f['attr'] == attr]
        color = style['color']
        width = style['width']
        for f in attr_feats:
            for ln in f['polylines']:
                pts = [to_px(p[0], p[1]) for p in ln['world_pts']]
                if len(pts) >= 2:
                    if ln['closed']:
                        draw.polygon(pts, outline=color, width=width)
                    else:
                        draw.line(pts, fill=color, width=width)

    # Save PNG
    img.save(out_png_path)
    print(f"  -> Generated Vector PNG: {out_png_path}")

def render_raster_map(code, info, out_png_path):
    map_p = GAME_DIR / info['map']
    pal_p = GAME_DIR / info['pal']
    if not map_p.exists() or not pal_p.exists():
        return
    
    data = map_p.read_bytes()
    w, h = struct.unpack_from('<HH', data, 0)
    pixels = data[4:4+w*h]
    
    img = Image.frombytes('P', (w, h), pixels)
    palette = load_altpal(pal_p)
    img.putpalette(palette)
    
    # Scale up using Nearest Neighbor for crisp tile pixels
    scale = 6
    img_scaled = img.resize((w * scale, h * scale), Image.Resampling.NEAREST).convert('RGB')
    
    # Add title bar
    title_h = 50
    final_img = Image.new('RGB', (w * scale, h * scale + title_h), (15, 23, 42))
    final_img.paste(img_scaled, (0, title_h))
    
    draw = ImageDraw.Draw(final_img)
    draw.text((20, 15), f"Falcon 3.0 • {info['name']} ({code}) Strategic Elevation Map • 240x200 Tiles", fill=(248, 250, 252))
    
    final_img.save(out_png_path)
    print(f"  -> Generated Raster Map PNG: {out_png_path}")

def render_composite_overview():
    """Build a multi-theater composite sheet comparing all 8 theater raster maps."""
    cards = []
    for code, info in sorted(THEATERS.items()):
        map_p = GAME_DIR / info['map']
        pal_p = GAME_DIR / info['pal']
        if map_p.exists() and pal_p.exists():
            data = map_p.read_bytes()
            w, h = struct.unpack_from('<HH', data, 0)
            pixels = data[4:4+w*h]
            img = Image.frombytes('P', (w, h), pixels)
            img.putpalette(load_altpal(pal_p))
            # Resize each to 480x400
            s_img = img.resize((480, 400), Image.Resampling.NEAREST).convert('RGB')
            # Add label
            card = Image.new('RGB', (480, 435), (20, 30, 48))
            card.paste(s_img, (0, 35))
            draw = ImageDraw.Draw(card)
            draw.text((15, 10), f"{code} — {info['name']}", fill=(240, 245, 255))
            cards.append(card)
            
    # 4 columns, 2 rows
    cols, rows = 4, 2
    cw, ch = 480, 435
    grid_img = Image.new('RGB', (cols * cw + 30, rows * ch + 80), (10, 15, 26))
    draw = ImageDraw.Draw(grid_img)
    draw.text((25, 20), "Falcon 3.0 — The Eight Battle Theaters (Tactical Elevation & Hydrography Matrix)", fill=(255, 255, 255))
    
    for idx, card in enumerate(cards):
        r = idx // cols
        c = idx % cols
        grid_img.paste(card, (15 + c * cw, 60 + r * ch))
        
    comp_path = OUTPUT_DIR / 'all_theaters_overview.png'
    grid_img.save(comp_path)
    print(f"==> Generated Master Multi-Theater Overview: {comp_path}")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("RENDERING ALL FALCON 3.0 THEATERS (RASTER & ISLDAT VECTORS)")
    print("=" * 70)

    theater_summary = []
    for code, info in sorted(THEATERS.items()):
        print(f"\nProcessing {code} ({info['name']})...")
        # 1. Render raster map
        raster_png = OUTPUT_DIR / f"{code}_raster_map.png"
        render_raster_map(code, info, raster_png)

        # 2. Parse ISLDAT and render vector map
        isl_p = GAME_DIR / info['isl']
        if isl_p.exists() and isl_p.stat().st_size > 18:
            features = parse_isldat(isl_p)
            poly_cnt = sum(len(f['polylines']) for f in features)
            pt_cnt = sum(len(ln['world_pts']) for f in features for ln in f['polylines'])
            if poly_cnt > 0:
                vector_svg = OUTPUT_DIR / f"{code}_vector_map.svg"
                vector_png = OUTPUT_DIR / f"{code}_vector_map.png"
                render_vector_svg(code, info, features, vector_svg)
                render_vector_png(code, info, features, vector_png)
                theater_summary.append({
                    'code': code,
                    'name': info['name'],
                    'records': len(features),
                    'polylines': poly_cnt,
                    'points': pt_cnt,
                    'has_vector': True
                })
            else:
                theater_summary.append({
                    'code': code,
                    'name': info['name'],
                    'records': len(features),
                    'polylines': 0,
                    'points': 0,
                    'has_vector': False
                })
        else:
            theater_summary.append({
                'code': code,
                'name': info['name'],
                'records': 0,
                'polylines': 0,
                'points': 0,
                'has_vector': False
            })

    # 3. Master overview composite
    render_composite_overview()
    print("\nAll theater renders complete!")

if __name__ == '__main__':
    main()
