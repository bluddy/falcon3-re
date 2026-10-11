import json
import struct
from pathlib import Path

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
d = Path('game/FALCONCD.EXE').read_bytes()
hdr = struct.unpack_from('<H', d, 0x08)[0] * 16

# Load MZ relocations: file positions of relocated words
nreloc = struct.unpack_from('<H', d, 0x06)[0]
reloc_off = struct.unpack_from('<H', d, 0x18)[0]
reloc_file_pos = set()
for i in range(nreloc):
    off, seg = struct.unpack_from('<HH', d, reloc_off + i * 4)
    reloc_file_pos.add(hdr + seg * 16 + off)

IMAGE_END = hdr + 0x1CF51  # resident image only; overlay funcs live in tail

resident_ok = resident_bad = 0
overlay = 0
bad = []
for name, info in sorted(fb.items()):
    if not info.get('bytes'):
        continue
    ea, size = info['ea'], info['size']
    if ea >= 0x10000 + 0x1CF51:
        overlay += 1
        continue
    raw_off = hdr + (ea - 0x10000)
    raw = d[raw_off:raw_off + size]
    ida = bytes.fromhex(info['bytes'])
    if raw == ida:
        resident_ok += 1
        continue
    # every differing byte position must be a reloc position AND +0x1000 word addition
    ok = True
    for i in range(size):
        if raw[i] != ida[i]:
            fp = raw_off + i
            if fp not in reloc_file_pos and (fp - 1) not in reloc_file_pos:
                ok = False
                break
    if ok:
        resident_ok += 1
    else:
        resident_bad += 1
        bad.append((name, hex(ea), raw.hex(), ida.hex()))

print('resident functions: consistent-with-relocs: %d, unexplained: %d' % (resident_ok, resident_bad))
print('overlay-range functions (skipped): %d' % overlay)
for b in bad[:15]:
    print('  UNEXPLAINED', b)
