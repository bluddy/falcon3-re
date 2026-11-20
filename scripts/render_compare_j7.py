import json
import math
import struct
from PIL import Image, ImageDraw, ImageFont

# Load palette
data = json.load(open('analysis/viewer/assets_database.json'))
palette = data['metadata']['palette']

def parse_objects_j7():
    obj_data = open('game/OBJECTS', 'rb').read()
    first_off = struct.unpack_from('<I', obj_data, 0)[0]
    offsets = struct.unpack(f'<{first_off//4}I', obj_data[:first_off])
    j7_obj = obj_data[offsets[57] : offsets[58]]
    
    vc = 71
    vo = 0x0068
    to = 0x0212
    next_to = 0x070e
    
    raw_verts = [struct.unpack_from('<hhh', j7_obj, vo + i * 6) for i in range(vc)]
    # In OpenGL: x = w1 / 10, y = -w2 / 10, z = w3 / 10
    verts = [[v[0] / 10.0, -v[1] / 10.0, v[2] / 10.0] for v in raw_verts]
    
    faces = []
    unique = set()
    for p in range(to, next_to - 8, 2):
        norm, mode, col, cnt = struct.unpack_from('<4H', j7_obj, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt+1)*2 <= next_to:
            v_words = struct.unpack_from(f'<{cnt+1}H', j7_obj, p + 8)
            if all(w % 16 == 0 and w // 16 < vc for w in v_words) and v_words[0] == v_words[-1]:
                ring = [w // 16 for w in v_words[:-1]]
                k = tuple(sorted(ring))
                if k not in unique:
                    unique.add(k)
                    faces.append({'col': col & 0xFF, 'indices': ring})
    return {'name': 'OBJECTS Obj 57 (J7)', 'vertices': verts, 'faces': faces}

def parse_report_j7():
    rep_data = open('game/REPORT.DAT', 'rb').read()
    sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
    s_off = sec_offsets[0]
    rel = struct.unpack_from('<I', rep_data, s_off + 2 + 21 * 4)[0]
    abs_off = s_off + rel
    sz = struct.unpack_from('<H', rep_data, abs_off)[0]
    j7_rep = rep_data[abs_off+2 : abs_off+2+sz]
    rec_off = struct.unpack_from('<H', j7_rep, 4)[0]
    vc, vo, to = struct.unpack_from('<3H', j7_rep, rec_off + 50)
    
    raw_verts = [struct.unpack_from('<hhh', j7_rep, vo + i * 6) for i in range(vc)]
    # Scale by 1/1.3 to match OBJECTS scale for visual parity
    verts = [[(v[0] / 1.30) / 10.0, (-v[1] / 1.30) / 10.0, (v[2] / 1.30) / 10.0] for v in raw_verts]
    
    def parse_node(data, node_off):
        col = data[node_off + 2]
        cnt = struct.unpack_from('<H', data, node_off + 4)[0]
        fcs = []
        if 3 <= cnt <= 16 and node_off + 6 + (cnt+1)*2 <= len(data):
            v_words = struct.unpack_from(f'<{cnt+1}H', data, node_off + 6)
            if all(w % 16 == 0 and w // 16 < vc for w in v_words) and v_words[0] == v_words[-1]:
                fcs.append({'col': col, 'indices': [w // 16 for w in v_words[:-1]]})
        return fcs
    
    faces = []
    unique = set()
    for octant in range(8):
        ptr = struct.unpack_from('<H', j7_rep, to + octant * 2)[0]
        if ptr == 0xffff or ptr >= len(j7_rep): break
        p = ptr
        while p + 2 <= len(j7_rep):
            node = struct.unpack_from('<H', j7_rep, p)[0]
            p += 2
            if node == 0xffff: break
            for f in parse_node(j7_rep, node):
                k = tuple(sorted(f['indices']))
                if k not in unique:
                    unique.add(k)
                    faces.append(f)
    return {'name': 'REPORT.DAT Item 21 (J-7)', 'vertices': verts, 'faces': faces}

def project(v, yaw, pitch, scale=8.0, cx=200, cy=200):
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

def render_view(model, yaw, pitch, scale=7.0, size=(300, 300), title=""):
    img = Image.new('RGB', size, (25, 28, 35))
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
        c = palette[col_idx] if col_idx < len(palette) else (180, 180, 180)
        draw.polygon(pts, fill=tuple(c), outline=(30, 30, 30))
        
    draw.text((10, 10), title, fill=(220, 220, 220))
    return img

m_rep = parse_report_j7()
m_obj = parse_objects_j7()

views = [
    ('Perspective (45, -20)', 45, -20),
    ('Side Profile (90, 0)', 90, 0),
    ('Top Down (0, -90)', 0, -90),
    ('Front View (0, 0)', 0, 0)
]

canvas = Image.new('RGB', (1200, 650), (15, 17, 22))
draw = ImageDraw.Draw(canvas)
draw.text((20, 15), "AUTHENTIC CALIBRATION COMPARISON: REPORT.DAT (Top) vs game/OBJECTS (Bottom)", fill=(255, 215, 0))

for col_idx, (vname, yaw, pitch) in enumerate(views):
    img_rep = render_view(m_rep, yaw, pitch, scale=5.0, size=(290, 280), title=f"REPORT: {vname}")
    img_obj = render_view(m_obj, yaw, pitch, scale=5.0, size=(290, 280), title=f"OBJECTS: {vname}")
    canvas.paste(img_rep, (10 + col_idx * 295, 50))
    canvas.paste(img_obj, (10 + col_idx * 295, 345))

canvas.save('analysis/compare_j7_turnaround.png')
print("Successfully generated analysis/compare_j7_turnaround.png")
