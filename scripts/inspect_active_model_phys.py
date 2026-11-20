with open('memdump/MEMDUMP7_flight_outside_view.BIN', 'rb') as f:
    dump = f.read()

import struct

seg = 0x26C0
off = 0x1110
phys = seg * 16 + off

print(f'Active model in flight outside view: 0x{seg:04X}:0x{off:04X} -> Physical 0x{phys:06X}')
chunk = dump[phys : phys + 128]
print('Bytes at active model pointer:')
for i in range(0, 128, 16):
    c = chunk[i:i+16]
    h = ' '.join(f'{b:02x}' for b in c)
    a = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in c)
    print(f'  0x{phys+i:06X}: {h:48s} {a}')

# Let's inspect LOD Header at this pointer:
vc, vo, to, w3, w4 = struct.unpack_from('<5H', dump, phys)
print(f'\nLOD Header: vc={vc}, vo=0x{vo:04X}, to=0x{to:04X}, w3=0x{w3:04X}, w4=0x{w4:04X}')
