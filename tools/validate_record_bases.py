"""Validate per-row RTLink record file bases (finding 17 open question).

For each of the 70 dir rows try:
  A: fixup_file = w2 * 16                       (gunship GS formula, file-absolute para)
  B: fixup_file = TAIL_START + w2               (old tail-relative read)

Score each candidate:
  fixup_pairs  = fraction of (off,seg) pairs whose seg is a known overlay segment
  disasm_cov   = capstone decode coverage of the data region head (code records)
  ascii_ratio  = printable ratio of the data region head (data records)

Then test runtime packing hypotheses for thunk containment:
  arena base = 0x1000 + w0 (runtime para), records packed in dir order,
  span units = bytes | paras.
  Check: every thunk target (runtime linear) falls inside SOME record's span
  (matches count / total thunks, per thunk-word interpretation {index, id_field}).

Outputs: prints table + writes analysis/ida_falconcd/record_validation.json
"""
import json
import struct
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    MD = Cs(CS_ARCH_X86, CS_MODE_16)
    HAVE_CS = True
except ImportError:
    HAVE_CS = False

ROOT = Path('.')
EXE = (ROOT / 'game/FALCONCD.EXE').read_bytes()
TAIL_START = 0x1FB51
DIR_FILE = 0x1E24F
# finding 55/56: table starts at 0x1E99D (303 entries); 0x1EBAF was entry #053
THUNK_FILE = 0x1E99D

rows = []
for i in range(70):
    o = DIR_FILE + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows.append(dict(idx=i, w0=w0, w2=w2, flags=w3 >> 8, span=w4,
                     fixups=w5, id=w7, dsize=w8))

OVERLAY_SEGS = sorted({r['w0'] for r in rows} | {0x1D0D, 0x1D31, 0x1EFE})
OVSET = set(OVERLAY_SEGS)


def fixup_score(fixup_file, count):
    if count == 0 or fixup_file < 0 or (fixup_file + count * 4) > len(EXE):
        return 0.0, []
    pairs = struct.unpack_from('<%dI' % count, EXE, fixup_file)
    ok = 0
    out = []
    for v in pairs:
        off, seg = v & 0xFFFF, v >> 16
        if seg in OVSET:
            ok += 1
        out.append((seg, off))
    return ok / count, out


def data_score(data_file, n=160):
    if data_file < 0 or data_file >= len(EXE):
        return 0.0, 0.0
    blob = EXE[data_file:data_file + n]
    ascii_r = sum(1 for b in blob if 32 <= b < 127 or b in (9, 10, 13)) / len(blob)
    cov = 0.0
    if HAVE_CS:
        total = 0
        good = 0
        for i in MD.disasm(blob, data_file):
            good += i.size
            total = i.size
        # decode contiguous head
        pos = 0
        for i in MD.disasm(blob, 0):
            if i.address != pos:
                break
            pos = i.address + i.size
        cov = pos / len(blob)
    return cov, ascii_r


report = []
for r in rows:
    entry = dict(r)
    for tag, base in (('A', r['w2'] * 16), ('B', TAIL_START + r['w2'])):
        fs, pairs = fixup_score(base, r['fixups'])
        data_f = base + ((r['fixups'] * 4 + 15) // 16) * 16
        cov, ar = data_score(data_f)
        entry[tag] = dict(base=base, fixup_pairs=round(fs, 3),
                          disasm_cov=round(cov, 2), ascii=round(ar, 2),
                          data_file=data_f)
    # verdict: prefer candidate with high fixup score AND (cov or ascii high)
    sa = entry['A']['fixup_pairs'] * 2 + max(entry['A']['disasm_cov'], entry['A']['ascii'])
    sb = entry['B']['fixup_pairs'] * 2 + max(entry['B']['disasm_cov'], entry['B']['ascii'])
    entry['verdict'] = 'A' if sa >= sb else 'B'
    report.append(entry)

# ---- print per-row table
print('%-3s %-5s %-8s | %-34s | %-34s | v' % ('idx', 'w0', 'w2', 'A: pairs/cov/ascii @base', 'B: pairs/cov/ascii @base'))
for e in report:
    a, b = e['A'], e['B']
    print('%-3d %-5X %-8X | %.2f %.2f %.2f @%-9X | %.2f %.2f %.2f @%-9X | %s' % (
        e['idx'], e['w0'], e['w2'],
        a['fixup_pairs'], a['disasm_cov'], a['ascii'], a['base'],
        b['fixup_pairs'], b['disasm_cov'], b['ascii'], b['base'],
        e['verdict']))
va = sum(1 for e in report if e['verdict'] == 'A')
print('verdict: A=%d B=%d' % (va, len(report) - va))

# ---- thunk containment under packing hypotheses
thunks = []
for i in range(300):
    o = THUNK_FILE + i * 10
    if o + 10 > len(EXE) or EXE[o] != 0xE8 or EXE[o + 3] != 0xEA:
        break
    loff, lseg, wid = struct.unpack_from('<HHH', EXE, o + 4)
    thunks.append((wid, ((0x1000 + lseg) << 4) + loff))


def containment(unit_shift):  # 0 = bytes, 4 = paras(*16)
    spans = []  # (start_linear, end_linear, row_idx)
    base_para = None
    cur = None
    for r in rows:
        size = r['span'] << unit_shift
        if cur is None or r['w0'] != cur[0]:
            # new arena — but records of same w0 may be non-contiguous in dir;
            # pack strictly in dir order, resetting when w0 changes
            cur = (r['w0'], (0x1000 + r['w0']) << 4)
        start = cur[1]
        spans.append((start, start + size, r['idx'], r['w0']))
        cur = (r['w0'], start + size)
    hits = miss = 0
    per_word = {}
    for wid, lin in thunks:
        # interpretation index: row = wid ; id_field: row = wid - 2
        for rowidx in (wid, wid - 2):
            pass
        ok = any(s <= lin < e for s, e, _, _ in spans)
        hits += ok
        miss += (not ok)
        per_word.setdefault(wid, []).append(ok)
    return hits, miss, spans, per_word


for us, label in ((0, 'bytes'), (4, 'paras')):
    hits, miss, spans, per_word = containment(us)
    print('packing %-6s (dir order, reset on w0 change): thunks inside=%d outside=%d' % (label, hits, miss))

json.dump(report, open(ROOT / 'analysis/ida_falconcd/record_validation.json', 'w'), indent=1)
print('wrote analysis/ida_falconcd/record_validation.json')
