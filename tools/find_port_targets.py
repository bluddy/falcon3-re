"""Find clean port targets: C-class, small, ZERO relocatable words in range.

Relocatable word positions:
  resident: MZ relocation table (file positions -> ida linear)
  overlay : fixups_to_apply.json rows (ida_ea + rel)
Routines containing none can be byte-compared without normalization (finding 15 TODO).
"""
import json
import struct
from pathlib import Path

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
cls = json.load(open('analysis/ida_falconcd/classification.json'))
pl = {p['idx']: p for p in json.load(open('analysis/ida_falconcd/overlay_placement.json'))}
fx = {int(k): v for k, v in json.load(open('analysis/ida_falconcd/fixups_to_apply.json')).items()}

EXE = Path('game/FALCONCD.EXE').read_bytes()
hdr = struct.unpack_from('<H', EXE, 0x08)[0] * 16
nreloc = struct.unpack_from('<H', EXE, 0x06)[0]
roff = struct.unpack_from('<H', EXE, 0x18)[0]
mz_words = set()
for i in range(nreloc):
    off, seg = struct.unpack_from('<HH', EXE, roff + i * 4)
    file_pos = hdr + seg * 16 + off
    mz_words.add(file_pos - hdr + 0x10000)   # ida linear of the word

# overlay fixup ida positions
ov_words = set()
for idx, plist in fx.items():
    p = pl[idx]
    if p['addr'] == 'skip' or not p['ida_ea']:
        continue
    for rel, w in plist:
        ov_words.add(p['ida_ea'] + rel)

targets = []
for name, info in cls.items():
    if info['class'] != 'C':
        continue
    size = info['size']
    if size > 80:
        continue
    ea = info['ea']
    if any(ea <= w <= ea + size - 2 for w in mz_words if ea <= w <= ea + size - 2):
        continue
    if any(ea <= w <= ea + size - 2 for w in ov_words if ea <= w <= ea + size - 2):
        continue
    targets.append((size, ea, name))

targets.sort()
print('clean C targets (no reloc words): %d' % len(targets))
for size, ea, name in targets[:20]:
    b = fb[name]['bytes']
    print('  %-12s %3dB ea=0x%X overlay=%s %s' % (
        name, size, ea, fb[name].get('overlay'), b))
