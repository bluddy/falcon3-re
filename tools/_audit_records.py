from capstone import *
import json

rt = json.load(open('analysis/ida_falconcd/rtlink_records.json'))
md = Cs(CS_ARCH_X86, CS_MODE_16)

# Sanity-check raw (unpatched) record code for a few records
for key in ['52', '53', '55', '56', '57']:
    r = rt.get(key)
    if not r:
        continue
    data = bytes.fromhex(r['record_data'])
    code = data[:r['A']]  # A = record size
    print('=== id=%s seg=0x%X tail_off=0x%X A=%d fixup_size=%d' % (
        key, r['seg'], r['off'], r['A'], r['fixup_size']))
    # decode first 48 bytes
    decoded = list(md.disasm(code[:48], 0))
    if not decoded:
        print('  [NO DECODE]')
    for i in decoded[:14]:
        print('  %04x: %-12s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    print()
