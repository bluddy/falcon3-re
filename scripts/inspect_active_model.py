with open('memdump/MEMDUMP7_flight_outside_view.BIN', 'rb') as f:
    dump = f.read()

import struct

seg = 0x67B8
off = 0x26C0
phys = seg * 16 + off

print(f'Model pointer 0x{seg:04X}:0x{off:04X} -> Physical 0x{phys:06X}')
chunk = dump[phys : phys + 64]
print('Bytes at 0x%06X:' % phys)
print(' '.join(f'{b:02x}' for b in chunk))

# What is at [si]?
# In object_3d_project_and_draw / object_quad_proj_draw:
# cx = [si], vo = [si+2], to = [si+4]
vc, vo, to, w3, w4 = struct.unpack_from('<5H', dump, phys)
print(f'LOD Header at 0x{phys:06X}: vc={vc}, vo=0x{vo:04X}, to=0x{to:04X}, w3=0x{w3:04X}, w4=0x{w4:04X}')
