import struct
import json
import math
from PIL import Image, ImageDraw

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

def decode_multipart_vehicle(obj):
    all_verts = []
    all_faces = []
    v_base = 0
    
    p_row = 0x0036
    parts = []
    while p_row + 14 <= len(obj):
        row = struct.unpack_from('<7H', obj, p_row)
        flags, r_mat, trans_ptr, vc, vo_h, w5, part_table_ptr = row
        if vc == 0 or vc > 100 or vo_h >= len(obj):
            break
        vo = vo_h + 2
        to = struct.unpack_from('<H', obj, part_table_ptr + 6)[0] if part_table_ptr + 8 <= len(obj) else vo + vc * 6
        parts.append((vc, vo, to, trans_ptr))
        p_row += 14
        if len(parts) >= 4:
            break
            
    if not parts:
        return [], []
        
    for part_idx, (vc, vo, to, trans_ptr) in enumerate(parts):
        tx, ty, tz = struct.unpack_from('<3h', obj, trans_ptr) if (trans_ptr and trans_ptr + 6 <= len(obj)) else (0, 0, 0)
        raw_verts = [struct.unpack_from('<3h', obj, vo + i * 6) for i in range(vc)]
        for rx, ry, rz in raw_verts:
            all_verts.append([
                round((rx + tx) / 10.0, 2),
                round(-(ry + ty) / 10.0, 2),
                round((rz + tz) / 10.0, 2)
            ])
            
        next_boundary = parts[part_idx+1][1] - 2 if part_idx + 1 < len(parts) else (0x01ea if len(obj) > 0x01ea else len(obj))
        unique = set()
        for p in range(to, next_boundary, 2):
            if p + 8 <= next_boundary:
                norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
                if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_boundary:
                    v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
                    if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                        indices = [w // 16 + v_base for w in v_words[:-1]]
                        key = tuple(sorted(indices))
                        if key not in unique:
                            unique.add(key)
                            all_faces.append({'color': col, 'indices': indices})
        v_base += vc
        
    return all_verts, all_faces

def decode_singlepiece_aircraft(obj):
    lod_table_off = -1
    for p in range(0x0030, min(0x0200, len(obj) - 10), 2):
        vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, p)
        if 10 <= vc <= 250 and vo < len(obj) and to < len(obj) and vo + vc * 6 <= to and w3 == 0 and w4 == 0:
            lod_table_off = p
            break
    if lod_table_off == -1:
        return [], []
        
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, lod_table_off)
    next_to = len(obj)
    if lod_table_off + 20 <= len(obj):
        n_vc, n_vo, n_to, n_w3, n_w4 = struct.unpack_from('<5H', obj, lod_table_off + 10)
        if 4 <= n_vc <= 250 and n_to < len(obj):
            next_to = n_to
            
    raw_verts = [struct.unpack_from('<3h', obj, vo + i * 6) for i in range(vc)]
    all_verts = [[round(v[1] / 10.0, 2), round(v[2] / 10.0, 2), round(v[0] / 10.0, 2)] for v in raw_verts]
    
    all_faces = []
    unique = set()
    for p in range(to, next_to - 8, 2):
        norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_to:
            v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                indices = [w // 16 for w in v_words[:-1]]
                key = tuple(sorted(indices))
                if key not in unique:
                    unique.add(key)
                    all_faces.append({'color': col, 'indices': indices})
                    
    return all_verts, all_faces

m113_verts, m113_faces = decode_multipart_vehicle(data[offs[36]:offs[37]])
print(f"M113 decoded: {len(m113_verts)} verts, {len(m113_faces)} faces")

m60_verts, m60_faces = decode_multipart_vehicle(data[offs[34]:offs[35]])
print(f"M60 decoded: {len(m60_verts)} verts, {len(m60_faces)} faces")

f16_verts, f16_faces = decode_singlepiece_aircraft(data[offs[3]:offs[4]])
print(f"F-16 decoded: {len(f16_verts)} verts, {len(f16_faces)} faces")

def project(v, yaw, pitch, scale=18.0, cx=150, cy=150):
    x, y, z = v
    rad_y = math.radians(yaw)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x1 = x * cos_y + z * sin_y
    z1 = -x * sin_y + z * cos_y
    rad_p = math.radians(pitch)
    cos_p, sin_p = math.cos(rad_p), math.sin(rad_p)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    return cx + x1 * scale, cy - y2 * scale, z2

def render_model_strip(name, verts, faces, palette, scale=12.0):
    angles = [(45, 20), (135, 20), (225, 20), (315, 20), (0, 90)]
    w, h = 250, 250
    img = Image.new('RGB', (w * len(angles), h), (22, 26, 32))
    draw = ImageDraw.Draw(img)
    for a_idx, (yaw, pitch) in enumerate(angles):
        ox = a_idx * w
        proj_faces = []
        for f in faces:
            pts = [project(verts[idx], yaw, pitch, scale=scale, cx=ox + w//2, cy=h//2) for idx in f['indices']]
            avg_z = sum(p[2] for p in pts) / len(pts)
            col_idx = f['color'] % len(palette)
            rgb = tuple(palette[col_idx])
            proj_faces.append((avg_z, [(p[0], p[1]) for p in pts], rgb))
        proj_faces.sort(key=lambda x: x[0])
        for avg_z, pts, rgb in proj_faces:
            draw.polygon(pts, fill=rgb, outline=(255, 255, 255))
        draw.text((ox + 10, 10), f"{name} ({yaw},{pitch})", fill=(255, 255, 255))
    return img

palette = json.load(open('analysis/viewer/assets_database.json'))['metadata']['palette']
im_m113 = render_model_strip("M113 (OBJECTS Authentic)", m113_verts, m113_faces, palette, scale=15.0)
im_m60 = render_model_strip("M60 (OBJECTS Authentic)", m60_verts, m60_faces, palette, scale=12.0)
im_f16 = render_model_strip("F-16 (OBJECTS Authentic)", f16_verts, f16_faces, palette, scale=7.0)

final_img = Image.new('RGB', (im_m113.width, im_m113.height * 3))
final_img.paste(im_m113, (0, 0))
final_img.paste(im_m60, (0, im_m113.height))
final_img.paste(im_f16, (0, im_m113.height * 2))
final_img.save('analysis/test_authentic_calibration.png')
print("Saved analysis/test_authentic_calibration.png")
