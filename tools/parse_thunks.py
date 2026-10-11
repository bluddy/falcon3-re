import struct
from pathlib import Path
from collections import Counter

d = Path('game/FALCONCD.EXE').read_bytes()
HDR = 0x2C00
THUNK_FILE = 0x1EBAF

# parse up to 120 entries, stop when pattern breaks
entries = []
for i in range(120):
    off = THUNK_FILE + i * 10
    if off + 10 > len(d):
        break
    e8, disp, ea_op = d[off], struct.unpack_from('<h', d, off + 1)[0], d[off + 3]
    if e8 != 0xE8 or ea_op != 0xEA:
        break
    ljmp_off, ljmp_seg, rec_id = struct.unpack_from('<HHH', d, off + 4)
    thunk_link = off - HDR  # link-time linear
    call_target = thunk_link + 3 + disp  # link-time linear of loader
    entries.append((i, rec_id, ljmp_seg, ljmp_off, call_target))

print('parsed', len(entries), 'thunks')
# loader call targets
print('loader targets (link linear):', sorted(set('%X' % e[4] for e in entries)))
# record ids present
ids = [e[1] for e in entries]
print('record ids:', sorted(set(ids)))
print('ids with >1 thunk (dups):', [k for k, v in Counter(ids).items() if v > 1])

# runtime ljmp targets: stored seg is link para; runtime = +0x1000 (IDA: +0x10000 lin)
print()
print('%-4s %-5s %-10s %-10s %-14s' % ('idx', 'rec', 'ljmp_seg', 'ljmp_off', 'runtime_ea'))
for i, rec, seg, loff, ct in entries[:20]:
    rt = ((0x1000 + seg) << 4) + loff
    print('%-4d 0x%-4X 0x%-8X 0x%-8X 0x%X' % (i, rec, seg, loff, rt))
