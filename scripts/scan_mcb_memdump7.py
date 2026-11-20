with open('memdump/MEMDUMP7_flight_outside_view.BIN', 'rb') as f:
    dump = f.read()

p = 0
while p < 0x9FFF:
    off = p * 16
    t = dump[off]
    if t in (0x4D, 0x5A):
        owner = int.from_bytes(dump[off+1:off+3], 'little')
        size = int.from_bytes(dump[off+3:off+5], 'little')
        name = dump[off+8:off+16].decode('ascii', errors='replace').strip('\x00 ')
        if 0 < size <= 0xA000 and (owner == 0 or 0x40 <= owner <= 0x9FFF):
            print(f'MCB at para 0x{p:04X} (phys 0x{off:06X}): type={chr(t)}, owner=0x{owner:04X}, size=0x{size:04X} ({size*16} B), name="{name}"')
            p += size + 1
            if t == 0x5A:
                break
            continue
    p += 1
