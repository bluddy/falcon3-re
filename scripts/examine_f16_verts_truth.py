import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
f16 = data[offs[3]:offs[4]]

print(f"F-16 total length: {len(f16)}")
byte2 = struct.unpack_from('<H', f16, 2)[0]
print(f"byte2: 0x{byte2:04x}")

# Where is F-16 LOD table?
# In extract_all_3d_assets.py:
# find_lod_table found it around 0x0010 or 0x0036
# Let's inspect words from 0x000c to 0x0060
print("\nHeader words from 0x000c to 0x0060:")
for p in range(0x000c, 0x0060, 2):
    w = struct.unpack_from('<H', f16, p)[0]
    print(f"0x{p:04x}: 0x{w:04x} ({w})")
