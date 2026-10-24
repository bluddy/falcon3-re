import struct, sys

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def i16(b, o): return struct.unpack_from('<h', b, o)[0]
def i32(b, o): return struct.unpack_from('<i', b, o)[0]

def hexdump(b, lo, hi, base=None):
    if base is None: base = lo
    for o in range(lo, hi, 16):
        row = b[o:o + 16]
        print('  %04X: %s  |%s|' % (base + o, ' '.join('%02X' % c for c in row),
              ''.join(chr(c) if 32 <= c < 127 else '.' for c in row)))

p = sys.argv[1]
b = open(p, 'rb').read()
body = b[9:]
t1base, t2base = u16(b, 4), u16(b, 6)
print('%s size=%d t1=0x%X t2=0x%X swap=%d' % (p, len(b), t1base, t2base, b[8]))
if len(b) < 2000:
    hexdump(body, 0, min(len(body), t1base + 0x40))
    print('--- tail ---')
    hexdump(body, max(0, len(body) - 0x80), len(body))
else:
    hexdump(body, 0x40, 0x110)
    print('--- quadrant walk1 blocks (0x400..0x4FF) ---')
    hexdump(body, 0x400, 0x500)
    print('--- quadrant walk2 block q0 (0x000..0x0FF) ---')
    hexdump(body, 0x000, 0x100)
    # tables + first lists
    print('--- t1 words ---')
    print(' ', ' '.join('%04X' % u16(body, t1base + 2 * i) for i in range(8)))
    print('--- t2 words ---')
    print(' ', ' '.join('%04X' % u16(body, t2base + 2 * i) for i in range(8)))
