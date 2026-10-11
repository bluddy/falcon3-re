import struct
import json
from pathlib import Path

d = Path('game/FALCONCD.EXE').read_bytes()
HDR = 0x2C00
DIR_FILE = 0x1E24F
N = 70

def u16(o):
    return struct.unpack_from('<H', d, o)[0]

print('%-3s %-5s %-6s %-9s %-6s %-5s %-5s %-6s %-5s %-5s' % (
    '#', 'id', 'seg', 'tail_off', 'A', 'B', 'C', 'A2', 'c12', 'c400'))
rows = []
for i in range(N):
    o = DIR_FILE + i * 18
    seg, c12ed, tail_off, c400, a, b, c, rid, a2 = struct.unpack_from('<HHIHHHHHH', d, o)
    rows.append(dict(idx=i, id=rid, seg=seg, tail=tail_off, A=a, B=b, C=c, A2=a2, c12=c12ed, c400=c400))
    print('%-3d 0x%-4X 0x%-4X 0x%-7X %-5d %-5d 0x%-3X 0x%-4X 0x%-4X 0x%-4X' % (
        i, rid, seg, tail_off, a, b, c, a2, c12ed, c400))

json.dump(rows, open('analysis/ida_falconcd/dir_fresh.json', 'w'), indent=1)

# sanity: c12ed/c400 constants?
print()
print('c12ed distinct:', sorted(set(r['c12'] for r in rows)))
print('c400 distinct:', sorted(set(r['c400'] for r in rows)))
print('A==A2 always:', all(r['A'] == r['A2'] for r in rows))
print('ids unique:', len(set(r['id'] for r in rows)) == N)
