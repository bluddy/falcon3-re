import struct

with open('game/REPORT.DAT', 'rb') as f:
    rep = f.read()

# Item 0 in Western aircraft
sec0_off = struct.unpack_from('<I', rep, 4)[0]
rel_off = struct.unpack_from('<I', rep, sec0_off + 2)[0]
abs_off = sec0_off + rel_off
item_size = struct.unpack_from('<H', rep, abs_off)[0]
item_data = rep[abs_off+2 : abs_off+2+item_size]

rec_off = struct.unpack_from('<H', item_data, 4)[0]
lod_off = rec_off + 50
vc, vo, to = struct.unpack_from('<3H', item_data, lod_off)

print(f"REPORT.DAT F-16: vc={vc}, vo={vo} (0x{vo:04x}), to={to} (0x{to:04x})")
print(f"vo + vc*6 = {vo + vc*6} (0x{vo + vc*6:04x})")
print(f"Words at to (0x{to:04x}):")
for i in range(16):
    w = struct.unpack_from("<H", item_data, to + i*2)[0]
    print(f"  to[{i:2d}] offset 0x{to + i*2:04x}: {w} (0x{w:04x})")
