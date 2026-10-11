import json
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
d = Path('game/FALCONCD.EXE').read_bytes()


def get(ea, n):
    for name, info in fb.items():
        if info['ea'] <= ea and ea + n <= info['ea'] + info['size']:
            b = bytes.fromhex(info['bytes'])
            return b[ea - info['ea']:ea - info['ea'] + n], True, name
    fo = 0x2C00 + (ea - 0x10000)
    return d[fo:fo + n], False, None


md = Cs(CS_ARCH_X86, CS_MODE_16)
for ea, n in ((0x2B040, 0x80), (0x2B1E5, 0x160)):
    b, trusted, name = get(ea, n)
    print('=== %#x trusted=%s fn=%s (%dB)' % (ea, trusted, name, len(b)))
    for i in md.disasm(b, ea):
        print('%06x: %-14s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    print()
