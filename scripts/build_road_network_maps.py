import struct
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

THEATER_MAP = {
    'BOS': ('BOSNIA.THE', 'BOSNIA.STR', 'Bosnia / Adriatic Sea'),
    'HOK': ('JAPAN.THE', 'JAPAN.STR', 'Hokkaido / Northern Japan'),
    'IRQ': ('KUWAIT.THE', 'KUWAIT.STR', 'Kuwait / Iraq / Persian Gulf'),
    'ISR': ('ISRAEL.THE', 'ISRAEL.STR', 'Israel / Sinai / Levant'),
    'KOR': ('KOREA.THE', 'KOREA.STR', 'Korea / Yellow Sea / Sea of Japan'),
    'NEL': ('NELLIS.THE', 'NELLIS.STR', 'Nellis AFB / Nevada Range'),
    'PAK': ('INDIA.THE', 'INDIA.STR', 'Pakistan / Thar Desert'),
    'PAN': ('PANAMA.THE', 'PANAMA.STR', 'Panama Canal Zone')
}

TARGET_TYPES = {
    0: 'AIRBASE',
    1: 'AIRFIELD',
    2: 'CITY',
    3: 'TOWN',
    4: 'NAVAL TASK FORCE',
    5: 'NAVAL BASE',
    6: 'RADAR SITE',
    7: 'BRIDGE',
    8: 'OIL FIELD',
    9: 'INDUSTRIAL',
    10: 'NUKE POWER STATION',
    11: 'CHEMICAL WEAPONS',
    12: 'BIOLOGICAL WEAPONS',
    13: 'ARMY BASE',
    14: 'RAIL YARD',
    15: 'MISSILE SITE'
}

def parse_theater_roads(the_filename, str_filename):
    tpath = Path('game') / the_filename
    spath = Path('game') / str_filename
    if not tpath.exists():
        return [], []

    names = []
    if spath.exists():
        with open(spath, 'rb') as f:
            sdata = f.read()
        pos = 0
        while pos < len(sdata):
            slen = sdata[pos]
            if slen == 0 or pos + 1 + slen > len(sdata):
                break
            names.append(sdata[pos+1 : pos+1+slen].decode('latin1', errors='ignore'))
            pos += 1 + slen

    with open(tpath, 'rb') as f:
        tdata = f.read()

    num_nodes = struct.unpack_from('<H', tdata, 0)[0]
    nodes = []
    edges = set()

    for i in range(num_nodes):
        rec = tdata[2 + i*78 : 2 + (i+1)*78]
        if len(rec) < 78:
            break
        target_type = rec[0]
        allegiance = rec[2]
        capacity = struct.unpack_from('<H', rec, 4)[0]
        raw_x, raw_y = struct.unpack_from('<hh', rec, 64)
        neighbors = [b for b in rec[68:78] if b != 0xFF]

        name = names[i] if i < len(names) else f"Node {i}"
        type_str = TARGET_TYPES.get(target_type, f"TYPE_{target_type}")
        if 'BRIDGE' in name.upper() or 'TRESTLE' in name.upper():
            type_str = 'BRIDGE'
        elif 'AIRBASE' in name.upper() or 'AIRPORT' in name.upper():
            type_str = 'AIRBASE'
        elif 'RAILYARD' in name.upper() or 'RAILROAD' in name.upper():
            type_str = 'RAIL YARD'

        nodes.append({
            'id': i,
            'name': name,
            'type_code': target_type,
            'type': type_str,
            'allegiance': allegiance,
            'capacity': capacity,
            'x': raw_x,
            'y': raw_y,
            'neighbors': neighbors
        })

        for nb in neighbors:
            if nb < num_nodes:
                edge = tuple(sorted([i, nb]))
                edges.add(edge)

    return nodes, sorted(list(edges))

def render_road_map(code, the_filename, str_filename, title, out_dir):
    nodes, edges = parse_theater_roads(the_filename, str_filename)
    if not nodes:
        print(f"Skipping {code}: No nodes found")
        return None

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    W, H = 1600, 1600

    xs = [n['x'] for n in nodes]
    ys = [n['y'] for n in nodes]
    min_x, max_x = min(xs) - 600, max(xs) + 600
    min_y, max_y = min(ys) - 600, max(ys) + 600
    span = max(max_x - min_x, max_y - min_y)
    mid_x, mid_y = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    min_x = mid_x - span / 2.0
    max_x = mid_x + span / 2.0
    min_y = mid_y - span / 2.0
    max_y = mid_y + span / 2.0

    def to_px(x, y):
        # Y in .THE has +Y South (down), -Y North (up)
        # Direct screen projection:
        sx = (x - min_x) / span * (W - 200) + 100
        sy = (y - min_y) / span * (H - 200) + 100
        return (sx, sy)

    img = Image.new('RGB', (W, H), (15, 23, 42)) # dark slate
    draw = ImageDraw.Draw(img)

    # Grid lines
    grid_step = 2000
    g_start_x = int(min_x // grid_step * grid_step)
    g_end_x = int(max_x // grid_step * grid_step + grid_step)
    g_start_y = int(min_y // grid_step * grid_step)
    g_end_y = int(max_y // grid_step * grid_step + grid_step)

    for gx in range(g_start_x, g_end_x + 1, grid_step):
        p0 = to_px(gx, min_y)
        p1 = to_px(gx, max_y)
        draw.line([p0, p1], fill=(30, 41, 59), width=1)
        draw.text((p0[0] + 4, H - 40), f"{gx}", fill=(100, 116, 139))

    for gy in range(g_start_y, g_end_y + 1, grid_step):
        p0 = to_px(min_x, gy)
        p1 = to_px(max_x, gy)
        draw.line([p0, p1], fill=(30, 41, 59), width=1)
        draw.text((15, p0[1] - 8), f"{gy}", fill=(100, 116, 139))

    # Center axes
    p0x = to_px(0, min_y)
    p1x = to_px(0, max_y)
    draw.line([p0x, p1x], fill=(51, 65, 85), width=2)
    p0y = to_px(min_x, 0)
    p1y = to_px(max_x, 0)
    draw.line([p0y, p1y], fill=(51, 65, 85), width=2)

    # Draw Road/Rail Edges
    for u, v in edges:
        p0 = to_px(nodes[u]['x'], nodes[u]['y'])
        p1 = to_px(nodes[v]['x'], nodes[v]['y'])
        # Draw roadway glow and core
        draw.line([p0, p1], fill=(180, 83, 9), width=4) # dark amber glow
        draw.line([p0, p1], fill=(245, 158, 11), width=2) # bright amber core

    # Draw Nodes
    node_by_id = {n['id']: n for n in nodes}
    for n in nodes:
        px, py = to_px(n['x'], n['y'])
        t = n['type']

        if t == 'BRIDGE':
            # Critical Choke Point: Crimson Red Diamond/Square
            r = 7
            draw.rectangle([px-r, py-r, px+r, py+r], fill=(239, 68, 68), outline=(255, 255, 255), width=2)
            # Crossbar
            draw.line([px-r, py, px+r, py], fill=(255, 255, 255), width=1)
        elif t in ('AIRBASE', 'AIRFIELD'):
            # Royal Blue Circle
            r = 7
            draw.ellipse([px-r, py-r, px+r, py+r], fill=(37, 99, 235), outline=(255, 255, 255), width=2)
        elif t in ('RAIL YARD', 'INDUSTRIAL', 'OIL FIELD'):
            # Emerald Green Diamond
            r = 6
            diamond = [(px, py-r), (px+r, py), (px, py+r), (px-r, py)]
            draw.polygon(diamond, fill=(16, 185, 129), outline=(255, 255, 255))
        elif 'NUKE' in t or 'CHEMICAL' in t or 'BIOLOGICAL' in t:
            # Purple Circle
            r = 6
            draw.ellipse([px-r, py-r, px+r, py+r], fill=(168, 85, 247), outline=(255, 255, 255), width=2)
        else:
            # City / Town: Slate White
            r = 5
            draw.ellipse([px-r, py-r, px+r, py+r], fill=(248, 250, 252), outline=(100, 116, 139), width=1)

        # Label
        label = n['name']
        draw.text((px + 8, py - 5), label, fill=(241, 245, 249))

    # Header
    header_title = f"{code}: {title}"
    draw.text((80, 30), header_title, fill=(248, 250, 252))
    sub = f"Strategic Campaign Road & Logistics Network: {len(nodes)} strategic nodes, {len(edges)} supply route segments"
    draw.text((80, 55), sub, fill=(148, 163, 184))

    # Legend
    legend_y = H - 90
    draw.rectangle([80, legend_y, 750, legend_y + 40], fill=(20, 30, 48), outline=(51, 65, 85))
    
    # Bridge
    draw.rectangle([95, legend_y + 13, 109, legend_y + 27], fill=(239, 68, 68), outline=(255, 255, 255))
    draw.text((118, legend_y + 12), "Bridge (Choke Point)", fill=(226, 232, 240))

    # Airbase
    draw.ellipse([270, legend_y + 13, 284, legend_y + 27], fill=(37, 99, 235), outline=(255, 255, 255))
    draw.text((292, legend_y + 12), "Airbase / Airfield", fill=(226, 232, 240))

    # Industry / Depot
    draw.polygon([(435, legend_y + 13), (442, legend_y + 20), (435, legend_y + 27), (428, legend_y + 20)], fill=(16, 185, 129), outline=(255, 255, 255))
    draw.text((450, legend_y + 12), "Railyard / Depot", fill=(226, 232, 240))

    # City
    draw.ellipse([580, legend_y + 15, 590, legend_y + 25], fill=(248, 250, 252), outline=(100, 116, 139))
    draw.text((598, legend_y + 12), "City / Town", fill=(226, 232, 240))

    png_path = out_dir / f"{code}_roads_map.png"
    img.save(png_path)

    # SVG Export
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="#0f172a"/>',
        f'<text x="80" y="45" font-family="sans-serif" font-size="22" font-weight="bold" fill="#f8fafc">{header_title}</text>',
        f'<text x="80" y="70" font-family="sans-serif" font-size="14" fill="#94a3b8">{sub}</text>'
    ]

    # Grid in SVG
    for gx in range(g_start_x, g_end_x + 1, grid_step):
        p0 = to_px(gx, min_y)
        p1 = to_px(gx, max_y)
        svg_lines.append(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#1e293b" stroke-width="1"/>')
        svg_lines.append(f'<text x="{p0[0]+4:.1f}" y="{H-40}" font-family="sans-serif" font-size="11" fill="#64748b">{gx}</text>')

    for gy in range(g_start_y, g_end_y + 1, grid_step):
        p0 = to_px(min_x, gy)
        p1 = to_px(max_x, gy)
        svg_lines.append(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#1e293b" stroke-width="1"/>')
        svg_lines.append(f'<text x="15" y="{p0[1]-4:.1f}" font-family="sans-serif" font-size="11" fill="#64748b">{gy}</text>')

    # Edges in SVG
    for u, v in edges:
        p0 = to_px(nodes[u]['x'], nodes[u]['y'])
        p1 = to_px(nodes[v]['x'], nodes[v]['y'])
        u_name = nodes[u]['name']
        v_name = nodes[v]['name']
        svg_lines.append(
            f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" '
            f'stroke="#f59e0b" stroke-width="2">'
            f'<title>Route: {u_name} &lt;--&gt; {v_name}</title>'
            f'</line>'
        )

    # Nodes in SVG
    for n in nodes:
        px, py = to_px(n['x'], n['y'])
        t = n['type']
        name = n['name']
        nid = n['id']
        cap = n['capacity']
        tt = f"Node {nid}: {name} | Type: {t} | Capacity: {cap} | Pos: ({n['x']}, {n['y']})"

        if t == 'BRIDGE':
            svg_lines.append(
                f'<rect x="{px-7:.1f}" y="{py-7:.1f}" width="14" height="14" fill="#ef4444" stroke="#ffffff" stroke-width="2">'
                f'<title>{tt}</title></rect>'
            )
        elif t in ('AIRBASE', 'AIRFIELD'):
            svg_lines.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="#2563eb" stroke="#ffffff" stroke-width="2">'
                f'<title>{tt}</title></circle>'
            )
        elif t in ('RAIL YARD', 'INDUSTRIAL', 'OIL FIELD'):
            svg_lines.append(
                f'<polygon points="{px:.1f},{py-7:.1f} {px+7:.1f},{py:.1f} {px:.1f},{py+7:.1f} {px-7:.1f},{py:.1f}" fill="#10b981" stroke="#ffffff" stroke-width="1.5">'
                f'<title>{tt}</title></polygon>'
            )
        else:
            svg_lines.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="#f8fafc" stroke="#64748b" stroke-width="1">'
                f'<title>{tt}</title></circle>'
            )
        svg_lines.append(f'<text x="{px+8:.1f}" y="{py+4:.1f}" font-family="sans-serif" font-size="11" fill="#f1f5f9">{name}</text>')

    svg_lines.append('</svg>')
    svg_path = out_dir / f"{code}_roads_map.svg"
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))

    print(f"Rendered {code} roads: {png_path.name}")
    return img

def main():
    out_dir = Path('analysis/theater_maps')
    out_dir.mkdir(parents=True, exist_ok=True)
    theater_imgs = {}

    for code, (the_file, str_file, title) in sorted(THEATER_MAP.items()):
        im = render_road_map(code, the_file, str_file, title, out_dir)
        if im:
            theater_imgs[code] = im

    # 4 cols x 2 rows master overview sheet
    W_cell, H_cell = 800, 800
    sheet = Image.new('RGB', (W_cell * 4, H_cell * 2), (10, 15, 30))
    order = ['BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAK', 'PAN']
    for idx, code in enumerate(order):
        r = idx // 4
        c = idx % 4
        if code in theater_imgs:
            im = theater_imgs[code].resize((W_cell, H_cell), Image.Resampling.LANCZOS)
            sheet.paste(im, (c * W_cell, r * H_cell))

    overview_path = out_dir / 'all_theaters_roads_overview.png'
    sheet.save(overview_path)
    print(f"Saved master roads overview: {overview_path}")

    # Copy to artifacts directory
    artifact_dir = Path(r'C:\Users\yotam\.gemini\antigravity-cli\brain\55de3f9f-195f-4620-9a3d-ce8463e4c888')
    if artifact_dir.exists():
        for f in ['ISR_roads_map.png', 'IRQ_roads_map.png', 'PAN_roads_map.png', 'all_theaters_roads_overview.png']:
            src = out_dir / f
            if src.exists():
                shutil.copy(src, artifact_dir / f)

if __name__ == '__main__':
    main()
