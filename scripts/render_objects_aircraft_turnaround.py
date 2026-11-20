import json
import math
import struct
from PIL import Image, ImageDraw, ImageFont

# Load palette
data = json.load(open('analysis/viewer/assets_database.json'))
palette = data['metadata']['palette']

def parse_aircraft(obj_id):
    obj_data = open('game/OBJECTS', 'rb').read()
    first_off = struct.unpack_from('<I', obj_data, 0)[0]
    offsets = struct.unpack(f'<{first_off//4}I', obj_data[:first_off])
    chunk = obj_data[offsets[obj_id] : offsets[obj_id+1]]
    name = chunk[4:12].decode('ascii', errors='ignore').strip()
    
    # Extract LOD 0
    vc, vo_h, to_h = struct.unpack_from('<3H', chunk, 0x0040)
    vo = vo_h + 2
    to = to_h + 2
    
    # find boundary for LOD 0 faces
    # next entry at 0x004a
    n_vc, n_vo, n_to = struct.unpack_from('<3H', chunk, 0x004a)
    if n_vo > vo:
        scan_to = n_vo + 2
    else:
        scan_to = n_to + 2
        
    raw_verts = [struct.unpack_from('<hhh', chunk, vo + i * 6) for i in range(vc)]
    # Authentic Aviation coordinate transform matching REPORT.DAT:
    # X_gl = w1 / 10.0 (Right)
    # Y_gl = -w2 / 10.0 (Up)
    # Z_gl = w3 / 10.0 (Forward)
    verts = [[round(v[0] / 10.0, 2), round(-v[1] / 10.0, 2), round(v[2] / 10.0, 2)] for v in raw_verts]
    
    faces = []
    unique = set()
    for p in range(to, scan_to - 8, 2):
        norm, mode, col, cnt = struct.unpack_from('<4H', chunk, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= scan_to:
            v_words = struct.unpack_from(f'<{cnt+1}H', chunk, p + 8)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                ring = [w // 16 for w in v_words[:-1]]
                k = tuple(sorted(ring))
                if k not in unique:
                    unique.add(k)
                    faces.append({'col': col & 0xFF, 'indices': ring})
                    
    return {'name': name, 'vertices': verts, 'faces': faces}

def project(v, yaw, pitch, scale=8.0, cx=150, cy=150):
    x, y, z = v
    rad_y = math.radians(yaw)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x1 = x * cos_y + z * sin_y
    z1 = -x * sin_y + z * cos_y
    rad_p = math.radians(pitch)
    cos_p, sin_p = math.cos(rad_p), math.sin(rad_p)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    sx = cx + x1 * scale
    sy = cy - y2 * scale
    return sx, sy, z2

def render_aircraft_card(model, size=(300, 300), yaw=45, pitch=-20, scale=6.0, label=""):
    img = Image.new('RGB', size, (22, 25, 32))
    draw = ImageDraw.Draw(img)
    verts = model['vertices']
    faces = model['faces']
    
    proj_faces = []
    for f in faces:
        pts = []
        sum_z = 0
        valid = True
        for idx in f['indices']:
            if idx >= len(verts):
                valid = False; break
            sx, sy, sz = project(verts[idx], yaw, pitch, scale=scale, cx=size[0]//2, cy=size[1]//2)
            pts.append((sx, sy))
            sum_z += sz
        if valid and len(pts) >= 3:
            proj_faces.append((sum_z / len(pts), pts, f['col']))
            
    proj_faces.sort(key=lambda x: x[0])
    for avg_z, pts, col_idx in proj_faces:
        c = palette[col_idx] if col_idx < len(palette) else (160, 160, 160)
        draw.polygon(pts, fill=tuple(c), outline=(35, 38, 48))
        
    draw.text((10, 10), label, fill=(240, 240, 240))
    return img

test_aircraft = [
    (3, 'F-16 Fighting Falcon', 7.0),
    (2, 'F-15 Eagle', 6.0),
    (17, 'MiG-29 Fulcrum', 6.5),
    (57, 'Chengdu J-7 Airguard', 6.0),
    (18, 'Su-27 Flanker', 5.5),
    (27, 'Su-25 Frogfoot', 7.0),
]

card_w, card_h = 300, 300
canvas = Image.new('RGB', (len(test_aircraft) * card_w, 2 * card_h), (14, 16, 20))
draw = ImageDraw.Draw(canvas)

for col_idx, (obj_id, title, sc) in enumerate(test_aircraft):
    m = parse_aircraft(obj_id)
    # Row 0: Perspective
    img_persp = render_aircraft_card(m, size=(card_w, card_h), yaw=45, pitch=-20, scale=sc, label=f"{title}\n[Obj {obj_id}] Persp")
    # Row 1: Profile / Top
    img_side = render_aircraft_card(m, size=(card_w, card_h), yaw=90, pitch=-10, scale=sc, label=f"{title}\nSide View")
    canvas.paste(img_persp, (col_idx * card_w, 0))
    canvas.paste(img_side, (col_idx * card_w, card_h))

canvas.save('analysis/aircraft_objects_calibration_gallery.png')
print("Successfully generated analysis/aircraft_objects_calibration_gallery.png")
