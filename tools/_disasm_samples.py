from capstone import *
import json

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
md = Cs(CS_ARCH_X86, CS_MODE_16)

samples = ['sub_205BF', 'sub_105D7', 'sub_2295E', 'sub_10348', 'sub_254A2',
           'sub_10CBE', 'sub_25DE5', 'sub_22455', 'sub_260AF', 'sub_2793A']
for name in samples:
    info = fb[name]
    b = bytes.fromhex(info['bytes'])
    ea = info['ea']
    print('--- %s ea=%s (%dB) %s' % (name, hex(ea), info['size'], info['bytes']))
    for i in md.disasm(b, ea):
        print('  %06x: %-12s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
