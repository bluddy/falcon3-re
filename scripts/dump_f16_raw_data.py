import struct
from pathlib import Path

# Load game/OBJECTS
with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

# F-16 is Chunk 3
f16_off = offsets[3]
next_off = offsets[4]
f16_bytes = data[f16_off:next_off]

out_dir = Path('analysis/viewer')
out_dir.mkdir(parents=True, exist_ok=True)

# Parse LOD 0 Header
sig_pos = f16_bytes.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16_bytes, lod_table_pos)

# -------------------------------------------------------------
# 1. Dump Header & BSP Pointer Table
# -------------------------------------------------------------
with open(out_dir / 'f16_raw_header_and_bsp.txt', 'w') as f:
    f.write(f"=== F-16 CHUNK 3 HEADER & BSP POINTER TABLE ===\n")
    f.write(f"Archive Chunk Index: 3\n")
    f.write(f"Chunk File Offset: 0x{f16_off:06X} ({f16_off})\n")
    f.write(f"Chunk Size: {len(f16_bytes)} bytes\n")
    name = f16_bytes[4:12].decode('ascii', errors='ignore').strip('\x00 ')
    f.write(f"Name Tag: '{name}'\n")
    f.write(f"Signature '\\xFF\\xFF\\x00\\x40' found at chunk offset: 0x{sig_pos:04X}\n")
    f.write(f"LOD 0 Table Offset: 0x{lod_table_pos:04X}\n")
    f.write(f"  vc (Vertex Count): {vc}\n")
    f.write(f"  vo (Vertex Table Offset): 0x{vo:04X} ({vo})\n")
    f.write(f"  to (Pointer Table Offset): 0x{to:04X} ({to})\n")
    f.write(f"  w3: 0x{w3:04X} ({w3})\n")
    f.write(f"  w4: 0x{w4:04X} ({w4})\n\n")

    f.write("--- Pointer Table at 'to' (0x0222) ---\n")
    ptr = to
    entry_idx = 0
    while ptr + 2 <= len(f16_bytes):
        node_off = struct.unpack_from('<H', f16_bytes, ptr)[0]
        f.write(f"  [{entry_idx:2d}] at 0x{ptr:04X}: -> 0x{node_off:04X}")
        ptr += 2
        entry_idx += 1
        if node_off == 0xFFFF:
            f.write(" (TERMINATOR 0xFFFF)\n")
            break
        if node_off < len(f16_bytes):
            w0 = struct.unpack_from('<H', f16_bytes, node_off)[0]
            if w0 == 0xFFFF:
                # Group
                sub_list = []
                sub_p = node_off + 2
                while sub_p + 2 <= len(f16_bytes):
                    tgt = struct.unpack_from('<H', f16_bytes, sub_p)[0]
                    sub_p += 2
                    if tgt == 0xFFFF or tgt == 0:
                        break
                    sub_list.append(f"0x{tgt:04X}")
                f.write(f" [GROUP/BSP NODE: {len(sub_list)} targets: {', '.join(sub_list[:8])}{'...' if len(sub_list)>8 else ''}]\n")
            else:
                norm, mode, col, cnt = struct.unpack_from('<4H', f16_bytes, node_off)
                f.write(f" [DIRECT POLY: col={col}, {cnt} verts]\n")
        else:
            f.write(" (OUT OF BOUNDS)\n")

# -------------------------------------------------------------
# 2. Dump Raw Vertices
# -------------------------------------------------------------
with open(out_dir / 'f16_raw_vertices.txt', 'w') as f:
    f.write("=== F-16 CHUNK 3 RAW VERTICES ===\n")
    f.write(f"Vertex array starts at chunk offset: 0x{vo:04X} (file offset: 0x{f16_off + vo:06X})\n")
    f.write(f"Vertex count: {vc} (6 bytes per vertex: <hhh = x, y, z)\n\n")
    f.write(f"{'ID':3s} | {'Chunk Off':9s} | {'File Off':8s} | {'Raw Bytes':17s} | {'Falcon (X, Y, Z)':23s} | {'Hex (X, Y, Z)':23s} | {'OpenGL (X, Y, Z)'}\n")
    f.write("-" * 115 + "\n")

    for vi in range(vc):
        c_off = vo + vi * 6
        abs_off = f16_off + c_off
        raw = f16_bytes[c_off:c_off+6]
        x, y, z = struct.unpack_from('<hhh', raw)
        raw_hex = " ".join(f"{b:02x}" for b in raw)
        hex_xyz = f"0x{x&0xffff:04x}, 0x{y&0xffff:04x}, 0x{z&0xffff:04x}"
        dec_xyz = f"({x:5d}, {y:5d}, {z:5d})"
        gl_xyz = f"[{y/10.0:6.2f}, {-z/10.0:6.2f}, {-x/10.0:6.2f}]"
        f.write(f"v{vi:02d} | 0x{c_off:04X}    | 0x{abs_off:06X} | {raw_hex:17s} | {dec_xyz:23s} | {hex_xyz:23s} | {gl_xyz}\n")

# -------------------------------------------------------------
# 3. Dump Raw Faces / Polygons
# -------------------------------------------------------------
ptr = to
poly_offsets = set()
while ptr + 2 <= len(f16_bytes):
    node_off = struct.unpack_from('<H', f16_bytes, ptr)[0]
    ptr += 2
    if node_off == 0xFFFF:
        break
    if node_off >= len(f16_bytes):
        continue
    w0 = struct.unpack_from('<H', f16_bytes, node_off)[0]
    if w0 == 0xFFFF:
        sub_p = node_off + 2
        while sub_p + 2 <= len(f16_bytes):
            tgt = struct.unpack_from('<H', f16_bytes, sub_p)[0]
            sub_p += 2
            if tgt == 0xFFFF or tgt == 0:
                break
            if tgt < len(f16_bytes):
                poly_offsets.add(tgt)
    else:
        poly_offsets.add(node_off)

sorted_polys = sorted(list(poly_offsets))

valid_polys = []
for p in sorted_polys:
    if p + 8 <= len(f16_bytes):
        norm, mode, col, cnt = struct.unpack_from('<4H', f16_bytes, p)
        if 3 <= cnt <= 20 and p + 8 + (cnt+1)*2 <= len(f16_bytes):
            v_words = struct.unpack_from(f'<{cnt+1}H', f16_bytes, p + 8)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                valid_polys.append((p, norm, mode, col, cnt, v_words))

with open(out_dir / 'f16_raw_faces.txt', 'w') as f:
    f.write("=== F-16 CHUNK 3 RAW FACES / POLYGONS ===\n")
    f.write(f"Total authentic polygon records found: {len(valid_polys)}\n")
    f.write("Structure of ObjectPolygon: norm (2B), mode (2B), color (2B), vertex_count N (2B), indices[N+1] (2B each, vi*16)\n\n")

    for fi, (p, norm, mode, col, cnt, v_words) in enumerate(valid_polys):
        rec_size = (4 + cnt + 1) * 2
        raw_rec = f16_bytes[p : p + rec_size]
        raw_hex = " ".join(f"{b:02x}" for b in raw_rec)
        v_indices = [w // 16 for w in v_words[:-1]]
        closed = (v_words[0] == v_words[-1])
        f.write(f"Face #{fi:02d} | Chunk Off: 0x{p:04X} | File Off: 0x{f16_off + p:06X} | Size: {rec_size:2d} bytes\n")
        f.write(f"  Header: norm=0x{norm:04X}, mode=0x{mode:04X}, color={col:3d} (0x{col:02X}), vertex_count={cnt}\n")
        f.write(f"  Raw Words (v*16): {' '.join(f'0x{w:04x}' for w in v_words)}\n")
        f.write(f"  Decoded Vertex Indices ({cnt} verts): {v_indices} (closed: {closed})\n")
        f.write(f"  Raw Bytes: {raw_hex}\n\n")

print(f"Dump complete! Generated:")
print(f"  - analysis/viewer/f16_raw_header_and_bsp.txt")
print(f"  - analysis/viewer/f16_raw_vertices.txt")
print(f"  - analysis/viewer/f16_raw_faces.txt")
