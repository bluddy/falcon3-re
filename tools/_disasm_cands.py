from capstone import *
import json

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
md = Cs(CS_ARCH_X86, CS_MODE_16)
md.detail = False

for name in ['sub_32D07', 'sub_385A6', 'sub_33FA4', 'sub_37020', 'sub_3141F', 'sub_67F1A', 'sub_671C6']:
    info = fb[name]
    b = bytes.fromhex(info['bytes'])
    print('--- %s ea=%s (%dB) %s' % (name, hex(info['ea']), info['size'], info['bytes']))
    pos = 0
    for i in md.disasm(b, info['ea']):
        print('  %06x: %-12s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        pos = i.address + i.size - info['ea']
    if pos < len(b):
        print('  [undecoded tail: %s]' % b[pos:].hex())
