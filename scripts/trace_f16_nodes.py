import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)

p = to
to_entries = []
while p + 2 <= len(obj):
    w = struct.unpack_from('<H', obj, p)[0]
    p += 2
    if w == 0xFFFF:
        break
    to_entries.append((p-2, w))

print(f"Tracing {len(to_entries)} entries in F-16:")

faces = []
for off, ptr in to_entries:
    if ptr >= len(obj):
        print(f"  Entry at 0x{off:04x}: ptr=0x{ptr:04x} OUT OF BOUNDS")
        continue
    # Let's see what is at ptr:
    # Check if polygon node
    w4 = struct.unpack_from('<4H', obj, ptr)
    norm, mode, col, cnt = w4
    if 3 <= cnt <= 16 and ptr + 8 + (cnt+1)*2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, ptr + 8)
        if all(w % 16 == 0 and (w//16) < vc for w in v_words) and v_words[0] == v_words[-1]:
            ring = [w//16 for w in v_words[:-1]]
            print(f"  Entry at 0x{off:04x} -> Node at 0x{ptr:04x}: col={col&0xff:3d}, cnt={cnt}, ring={ring}")
            faces.append({'col': col & 0xff, 'ring': ring})
            continue
    print(f"  Entry at 0x{off:04x} -> Other at 0x{ptr:04x}: {[hex(x) for x in struct.unpack('<4H', obj[ptr:ptr+8])]}")

print(f"\nDirect polygon nodes found from 'to' stream: {len(faces)}")
