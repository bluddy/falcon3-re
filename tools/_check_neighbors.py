import json

fb = json.load(open('analysis/ida_falconcd/function_bytes.json'))
survey = json.load(open('analysis/ida_falconcd/survey.json'))

# e80100cb family: what IDA says starts/ends around them
names = ['sub_205BF', 'sub_23793', 'sub_237C9', 'sub_239EE', 'sub_24984', 'sub_24A90', 'sub_25773']
eas = sorted(fb[n]['ea'] for n in names)

# Build (ea, name, end) list and show neighbors
funcs = sorted((f['ea'], f['name'], f['ea'] + f['size']) for f in survey['functions'])

for ea in eas:
    print('=== target ea=%s' % hex(ea))
    for fea, fname, fend in funcs:
        if abs(fea - ea) <= 0x40 or (fea < ea < fend):
            b = fb.get(fname, {}).get('bytes', '?')
            print('   %-12s ea=%-8s end=%-8s %s' % (fname, hex(fea), hex(fend), b))

# Also: what raw IDA bytes follow each target (next 16 bytes of *any* containing function)
print()
print('Context: bytes of the *containing/below* function')
for ea in eas:
    for fea, fname, fend in funcs:
        if fea <= ea < fend:
            b = bytes.fromhex(fb[fname]['bytes'])
            off = ea - fea
            print('%s +0x%x: %s ... [%s @+0x%x]' % (
                fname, off, b[off:off+8].hex(), fb[fname]['bytes'][:16], off))
            break
