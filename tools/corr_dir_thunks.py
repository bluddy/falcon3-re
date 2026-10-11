import struct
from pathlib import Path
from collections import defaultdict

d = Path('game/FALCONCD.EXE').read_bytes()
HDR = 0x2C00

# fresh dir: 70 x 18B at 0x1E24F: seg,12ED,tail,0400,A,B,C,id,A2
dir_by_id = {}
for i in range(70):
    o = 0x1E24F + i * 18
    seg, c12, tail, c4, a, b, c, rid, a2 = struct.unpack_from('<9H', d, o)
    dir_by_id[rid] = dict(idx=i, seg=seg, tail=tail, A=a, B=b, C=c, A2=a2)

# thunks: rec_id -> [(ljmp_seg, ljmp_off)]
thunks = defaultdict(list)
for i in range(200):
    o = 0x1EBAF + i * 10
    if o + 10 > len(d) or d[o] != 0xE8 or d[o + 3] != 0xEA:
        break
    loff, lseg, rid = struct.unpack_from('<HHH', d, o + 4)
    thunks[rid].append((lseg, loff))

print('%-4s %-5s %-6s %-7s %-5s | thunks ljmp (link seg:off) + runtime' % (
    'id', 'dirseg', 'tail', 'A', 'B'))
for rid in sorted(set(list(dir_by_id) + list(thunks))):
    dr = dir_by_id.get(rid)
    th = thunks.get(rid, [])
    ds = 'seg=%04X tail=%04X A=%-5d B=%d C=%02X' % (dr['seg'], dr['tail'], dr['A'], dr['B'], dr['C']) if dr else '(NO DIR)'
    ts = ' '.join('%04X:%04X->rt%05X' % (s, o, ((0x1000 + s) << 4) + o) for s, o in sorted(set(th)))
    print('%-4s %s | %s' % (rid, ds, ts))
