import json
import struct
from pathlib import Path

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
d = Path('game/FALCONCD.EXE').read_bytes()
hdr = struct.unpack_from('<H', d, 0x08)[0] * 16

same = diff = 0
diffs = []
for name, info in sorted(fb.items()):
    if not info.get('bytes'):
        continue
    ea = info['ea']
    size = info['size']
    raw_off = hdr + (ea - 0x10000)
    if raw_off < 0 or raw_off + size > len(d):
        continue
    raw = d[raw_off:raw_off + size]
    ida = bytes.fromhex(info['bytes'])
    if raw == ida:
        same += 1
    else:
        diff += 1
        # characterize: which byte positions differ, by how much
        deltas = [(i, raw[i], ida[i], ida[i] - raw[i]) for i in range(size) if raw[i] != ida[i]]
        diffs.append((name, hex(ea), raw.hex(), ida.hex(), deltas[:6]))

print('identical: %d  differing: %d' % (same, diff))
print()
for name, ea, raw, ida, deltas in diffs[:25]:
    print('%-12s ea=%s' % (name, ea))
    print('   raw %s' % raw)
    print('   ida %s' % ida)
    print('   pos/delta: %s' % deltas)
if len(diffs) > 25:
    print('... %d more' % (len(diffs) - 25))

# Save full list for the log
with open('analysis/ida_falconcd/raw_vs_ida_diffs.json', 'w') as f:
    json.dump([{'name': n, 'ea': e, 'raw': r, 'ida': i} for n, e, r, i, _ in diffs], f, indent=1)
print('\nwrote analysis/ida_falconcd/raw_vs_ida_diffs.json')
