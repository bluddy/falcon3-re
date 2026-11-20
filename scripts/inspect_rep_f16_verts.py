import struct
from pathlib import Path

with open('game/REPORT.DAT', 'rb') as f:
    rep = f.read()

# Find F-16 in Western aircraft (section 0)
sec_off = struct.unpack_from('<I', rep, 4)[0]
item_count = struct.unpack_from('<H', rep, sec_off)[0]

for item_idx in range(item_count):
    rel_off = struct.unpack_from('<I', rep, sec_off + 2 + item_idx * 4)[0]
    abs_off = sec_off + rel_off
    item_size = struct.unpack_from('<H', rep, abs_off)[0]
    item_data = rep[abs_off + 2 : abs_off + 2 + item_size]
    
    text_off = struct.unpack_from('<H', item_data, 0)[0]
    raw_text = item_data[text_off:text_off+100]
    if b'F-16' in raw_text:
        rec_off = struct.unpack_from('<H', item_data, 4)[0]
        sig_pos = item_data.find(b'\xff\xff', rec_off)
        lod_off = rec_off + 50
        vc, vo, to = struct.unpack_from('<3H', item_data, lod_off)
        raw_verts = [struct.unpack_from('<hhh', item_data, vo + i*6) for i in range(vc)]
        print(f"REPORT.DAT F-16: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")
        print("First 15 raw vertices of F-16 in REPORT.DAT (X, Y, Z):")
        for i, (x, y, z) in enumerate(raw_verts[:15]):
            print(f"  v{i:2d}: X={x:5d}, Y={y:5d}, Z={z:5d}")
        
        xs = [v[0] for v in raw_verts]
        ys = [v[1] for v in raw_verts]
        zs = [v[2] for v in raw_verts]
        print(f"\nRanges in REPORT.DAT:")
        print(f"  X: min={min(xs)}, max={max(xs)}, span={max(xs)-min(xs)}")
        print(f"  Y: min={min(ys)}, max={max(ys)}, span={max(ys)-min(ys)}")
        print(f"  Z: min={min(zs)}, max={max(zs)}, span={max(zs)-min(zs)}")
        break
