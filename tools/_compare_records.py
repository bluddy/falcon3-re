import json

rt = json.load(open('analysis/ida_falconcd/rtlink_records.json'))
dump = json.load(open('analysis/ida_falconcd/ida_record_bytes.json'))

report = []
for key in sorted(rt, key=int):
    r = rt[key]
    raw = r['record_data'][:r['A'] * 2]  # first A bytes as hex
    ida = dump[key]['ida_bytes']
    if ida is None:
        report.append((key, 'NO BYTES', None))
        continue
    raw_b = bytes.fromhex(raw)
    ida_b = bytes.fromhex(ida)
    if len(raw_b) != len(ida_b):
        report.append((key, 'LEN %d vs %d' % (len(raw_b), len(ida_b)), None))
        continue
    diffs = [(i, raw_b[i], ida_b[i]) for i in range(len(raw_b)) if raw_b[i] != ida_b[i]]
    report.append((key, 'identical' if not diffs else '%d bytes differ' % len(diffs), diffs))

for key, status, diffs in report:
    print('id=%-4s %s' % (key, status))
    if diffs:
        # show first diffs + check if +0x1000-word pattern
        raw_b = bytes.fromhex(rt[key]['record_data'][:rt[key]['A'] * 2])
        ida_b = bytes.fromhex(dump[key]['ida_bytes'])
        pat = []
        for i, rv, iv in diffs[:6]:
            w = (i // 2) * 2
            rw = int.from_bytes(raw_b[w:w + 2], 'little')
            iwd = int.from_bytes(ida_b[w:w + 2], 'little')
            pat.append('off0x%X: word 0x%04X->0x%04X (delta %+d)' % (i, rw, iwd, (iwd - rw) & 0xFFFF))
        print('   ', '; '.join(pat))
