import struct, sys, collections

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def i32(b, o): return struct.unpack_from('<i', b, o)[0]

def load(p):
    b = open(p, 'rb').read()
    return b[:9], b[9:]

def analyze(p):
    hdr, body = load(p)
    blen, t1base, t2base = u16(hdr, 0), u16(hdr, 4), u16(hdr, 6)
    swap = hdr[8]
    print('=== %s  size=%d body=%d hdr_len=%d t1=0x%X t2=0x%X swap=%d' %
          (p.split('\\')[-1], blen + 9, len(body), blen, t1base, t2base, swap))
    # find table extents: entries until first FFFF or until offset that is out of range
    def table_extent(base, limit):
        n = 0
        while base + 2 * n + 2 <= len(body):
            v = u16(body, base + 2 * n)
            if v == 0xFFFF or v >= len(body):
                break
            n += 1
        return n
    n1 = table_extent(t1base, None)
    n2 = table_extent(t2base, None)
    print('  t1 entries=%d (0x%X..0x%X)  t2 entries=%d (0x%X..0x%X)' %
          (n1, t1base, t1base + 2 * n1, n2, t2base, t2base + 2 * n2))
    # region census: 0x00..t1base, split into 64-byte chunks
    print('  -- region byte stats (chunk: nonzero/max/small<0x40 pct) --')
    for lo in range(0, t1base, 64):
        chunk = body[lo:lo + 64]
        nz = sum(1 for c in chunk if c)
        mx = max(chunk) if chunk else 0
        sm = sum(1 for c in chunk if c < 0x40)
        if nz:
            print('    0x%04X-0x%04X nz=%2d max=%3d<40=%2d  %s' %
                  (lo, lo + len(chunk) - 1, nz, mx, sm,
                   ''.join('%02X' % c for c in chunk[:24])))
    return hdr, body, t1base, t2base, swap, n1, n2

for p in sys.argv[1:]:
    analyze(p)
