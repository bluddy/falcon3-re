import struct
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCALE = 8776.0 / (335360.0 / 65536.0) # 1715.0045801526717

THEATER_NAMES = {
    'BOS': 'Bosnia / Adriatic Sea',
    'HOK': 'Hokkaido / Northern Japan',
    'IRQ': 'Kuwait / Iraq / Persian Gulf',
    'ISR': 'Israel / Sinai / Dead Sea',
    'KOR': 'Korea / Yellow Sea / Sea of Japan',
    'NEL': 'Nellis AFB / Nevada',
    'PAK': 'Pakistan / Desert',
    'PAN': 'Panama Canal'
}

def parse_isldat(path):
    with open(path, 'rb') as f:
        raw = f.read()

    body = raw[9:]
    def u16(o): 
        if o + 2 > len(body): return 0xFFFF
        return struct.unpack_from('<H', body, o)[0]
    def i32(o): return struct.unpack_from('<i', body, o)[0]

    records = []
    for offset in range(0, len(body) - 0x38, 2):
        attr = u16(offset + 0x20)
        c24 = u16(offset + 0x24)
        c26 = u16(offset + 0x26)
        c28 = u16(offset + 0x28)
        c2c = u16(offset + 0x2C)
        if attr in [0x14, 0x32, 0x64, 0xC8] and c24 == 0x000B and c26 == 0xFFFF and c28 == 0x0000 and c2c == 0x0004:
            records.append(offset)

    polys = []
    for idx, r in enumerate(records):
        cx = i32(r) / 65536.0
        cy = i32(r+4) / 65536.0
        attr = u16(r+0x20)
        nv = u16(r+0x2E)
        sub = u16(r+0x32)
        pts = [struct.unpack_from('<hhh', body, r + 0x38 + 6 * i) for i in range(nv)]
        
        # local Y = p[0], local Z = p[1], local X = p[2]
        world_pts = [(cx + p[2] / SCALE, cy + p[0] / SCALE) for p in pts]
        
        p = sub
        while p + 2 <= len(body) and u16(p) != 0xFFFF:
            block_ptr = u16(p)
            p += 2
            chain = u16(block_ptr) & 0x1000
            q = block_ptr + 4
            while q + 2 <= len(body):
                cnt = u16(q)
                if cnt == 0xFFFF: break
                ring = [u16(q + 2 + 2 * k) // 16 for k in range(cnt + 1)]
                poly_world = [world_pts[vi] for vi in ring if vi < len(world_pts)]
                if len(poly_world) >= 3:
                    polys.append({
                        'rec_id': idx,
                        'attr': attr,
                        'poly': poly_world
                    })
                q += 2 + 2 * (cnt + 1)
                if not chain: break
                
    return len(records), polys

def render_vector_map(code, n_records, polys, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    W, H = 1600, 1600
    
    if polys:
        all_xs = [pt[0] for p in polys for pt in p['poly']]
        all_ys = [pt[1] for p in polys for pt in p['poly']]
        min_x, max_x = min(all_xs) - 4, max(all_xs) + 4
        min_y, max_y = min(all_ys) - 4, max(all_ys) + 4
    else:
        min_x, max_x = -50.0, 50.0
        min_y, max_y = -50.0, 50.0

    # Ensure square aspect ratio
    span = max(max_x - min_x, max_y - min_y)
    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0
    min_x = mid_x - span / 2.0
    max_x = mid_x + span / 2.0
    min_y = mid_y - span / 2.0
    max_y = mid_y + span / 2.0

    def to_px(wx, wy):
        sx = (wx - min_x) / (max_x - min_x) * (W - 160) + 80
        sy = (H - 160) - (wy - min_y) / (max_y - min_y) * (H - 160) + 80
        return (sx, sy)

    img = Image.new('RGB', (W, H), (15, 23, 42)) # slate-900
    draw = ImageDraw.Draw(img)

    # Grid step
    grid_step = 10 if span > 40 else 5
    g_start_x = int(min_x // grid_step * grid_step)
    g_end_x = int(max_x // grid_step * grid_step + grid_step)
    g_start_y = int(min_y // grid_step * grid_step)
    g_end_y = int(max_y // grid_step * grid_step + grid_step)

    for gx in range(g_start_x, g_end_x + 1, grid_step):
        p0 = to_px(gx, min_y)
        p1 = to_px(gx, max_y)
        draw.line([p0, p1], fill=(30, 41, 59), width=1)
        draw.text((p0[0] + 4, H - 40), f"{gx}nm", fill=(100, 116, 139))

    for gy in range(g_start_y, g_end_y + 1, grid_step):
        p0 = to_px(min_x, gy)
        p1 = to_px(max_x, gy)
        draw.line([p0, p1], fill=(30, 41, 59), width=1)
        draw.text((15, p0[1] - 8), f"{gy}nm", fill=(100, 116, 139))

    # Center axes (0,0)
    p0x = to_px(0, min_y)
    p1x = to_px(0, max_y)
    draw.line([p0x, p1x], fill=(51, 65, 85), width=2)
    p0y = to_px(min_x, 0)
    p1y = to_px(max_x, 0)
    draw.line([p0y, p1y], fill=(51, 65, 85), width=2)

    # 1. First pass: Filled polygons
    poly_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    poly_draw = ImageDraw.Draw(poly_img)

    for item in polys:
        pts_px = [to_px(pt[0], pt[1]) for pt in item['poly']]
        if len(pts_px) < 3: continue
        attr = item['attr']
        if attr in (0x14, 0xC8):
            fill = (14, 116, 144, 180) # deep water teal/cyan
        elif attr == 0x64:
            fill = (2, 132, 199, 180) # lake sky blue
        else: # 0x32
            fill = (16, 185, 129, 180) # inland water emerald
        poly_draw.polygon(pts_px, fill=fill)

    img.paste(poly_img, (0, 0), poly_img)

    # 2. Second pass: Polygon edges / wireframe
    for item in polys:
        pts_px = [to_px(pt[0], pt[1]) for pt in item['poly']]
        if len(pts_px) < 3: continue
        attr = item['attr']
        if attr in (0x14, 0xC8):
            outline = (56, 189, 248) # bright cyan
        elif attr == 0x64:
            outline = (125, 211, 252) # light sky blue
        else:
            outline = (52, 211, 153) # bright green
        draw.polygon(pts_px, outline=outline)

    # 3. Header & Info overlay
    title = f"{code}: {THEATER_NAMES.get(code, 'Unknown')}"
    draw.text((80, 30), title, fill=(248, 250, 252))
    sub = f"ISLDAT: {n_records} records, {len(polys)} convex water polygons | Local scale: 1715.00 local/nm | Range: {span:.1f}x{span:.1f} nm"
    draw.text((80, 52), sub, fill=(148, 163, 184))

    # Save PNG
    png_path = out_dir / f"{code}_vector_map.png"
    img.save(png_path)
    
    # Also save clean SVG
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="#0f172a"/>',
        f'<text x="80" y="40" font-family="sans-serif" font-size="22" font-weight="bold" fill="#f8fafc">{title}</text>',
        f'<text x="80" y="65" font-family="sans-serif" font-size="14" fill="#94a3b8">{sub}</text>'
    ]
    
    # SVG grid
    for gx in range(g_start_x, g_end_x + 1, grid_step):
        p0 = to_px(gx, min_y)
        p1 = to_px(gx, max_y)
        svg_lines.append(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#1e293b" stroke-width="1"/>')
        svg_lines.append(f'<text x="{p0[0]+4:.1f}" y="{H-40}" font-family="sans-serif" font-size="11" fill="#64748b">{gx}nm</text>')

    for gy in range(g_start_y, g_end_y + 1, grid_step):
        p0 = to_px(min_x, gy)
        p1 = to_px(max_x, gy)
        svg_lines.append(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#1e293b" stroke-width="1"/>')
        svg_lines.append(f'<text x="15" y="{p0[1]-4:.1f}" font-family="sans-serif" font-size="11" fill="#64748b">{gy}nm</text>')

    # SVG polygons
    for item in polys:
        pts_px = [to_px(pt[0], pt[1]) for pt in item['poly']]
        if len(pts_px) < 3: continue
        pts_str = " ".join(f"{pt[0]:.1f},{pt[1]:.1f}" for pt in pts_px)
        attr = item['attr']
        if attr in (0x14, 0xC8):
            fill = "rgba(14, 116, 144, 0.7)"
            stroke = "#38bdf8"
        elif attr == 0x64:
            fill = "rgba(2, 132, 199, 0.7)"
            stroke = "#7dd3fc"
        else:
            fill = "rgba(16, 185, 129, 0.7)"
            stroke = "#34d399"
        svg_lines.append(f'<polygon points="{pts_str}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')

    svg_lines.append('</svg>')
    svg_path = out_dir / f"{code}_vector_map.svg"
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))

    print(f"Rendered {code}: {png_path.name} & {svg_path.name}")
    return img

def render_overview_sheet(theater_imgs, out_path):
    # 8 theaters arranged in 2 rows of 4
    W_cell, H_cell = 800, 800
    sheet = Image.new('RGB', (W_cell * 4, H_cell * 2), (10, 15, 30))
    
    order = ['BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAK', 'PAN']
    for idx, code in enumerate(order):
        r = idx // 4
        c = idx % 4
        if code in theater_imgs:
            im = theater_imgs[code].resize((W_cell, H_cell), Image.Resampling.LANCZOS)
            sheet.paste(im, (c * W_cell, r * H_cell))

    sheet.save(out_path)
    print(f"Master overview sheet saved: {out_path}")

def main():
    out_dir = Path('analysis/theater_maps')
    theater_imgs = {}

    for isldat_file in sorted(Path('game').glob('ISLDAT.*')):
        code = isldat_file.suffix[1:]
        n_rec, polys = parse_isldat(isldat_file)
        im = render_vector_map(code, n_rec, polys, out_dir)
        theater_imgs[code] = im

    overview_path = out_dir / 'all_theaters_vector_overview.png'
    render_overview_sheet(theater_imgs, overview_path)

    # Copy key artifacts to artifact directory
    artifact_dir = Path(r'C:\Users\yotam\.gemini\antigravity-cli\brain\55de3f9f-195f-4620-9a3d-ce8463e4c888')
    if artifact_dir.exists():
        for f in ['ISR_vector_map.png', 'all_theaters_vector_overview.png', 'KOR_vector_map.png', 'PAN_vector_map.png']:
            src = out_dir / f
            if src.exists():
                shutil.copy(src, artifact_dir / f)
                print(f"Copied to artifact dir: {f}")

if __name__ == '__main__':
    main()
