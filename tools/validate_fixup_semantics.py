"""Validate RTLink fixup semantics host-side and emit the patch list (finding 57).

Pass 1 (findings 17/18, committed as fixups_to_apply.json) kept only the pairs
whose `seg` field equalled the record's own `w0`, and addressed them as
`ida_ea + off`.  Finding 56 proved the real addressing is

    absolute offset = (seg - w0) * 16 + off        (paragraph anchor)

so that filter silently dropped every fixup that used a different sub-block
paragraph -- 12,118 of 37,661 pairs, including 408 of the dead far calls.
`R05_1E10` alone carries 24 distinct anchors, the dominant one being
`seg = 0x1F64 = w0 + 0x154` (i.e. +0x1540 bytes -> IDA 0x2F640).

Emits, for each pair whose anchor-corrected absolute offset lands inside the
record's written window:

  * ALWAYS, if pass 1 already emitted it (it is applied in the IDB and a fresh
    rebuild must reproduce those bytes -- dropping them would break fidelity);
  * otherwise only when the word looks like a link-time paragraph, i.e.
    `((word + 0x1000) << 4)` falls inside a segment the IDB actually holds.
    A non-paragraph word would be corrupted by `+= 0x1000`, so it is skipped.

Output: analysis/ida_falconcd/fixups_to_apply.json  {row: [[abs_off, word_before]]}
Usage: venv\\Scripts\\python tools\\validate_fixup_semantics.py
"""
import json
import struct
from collections import Counter
from pathlib import Path

EXE = Path('game/FALCONCD.EXE').read_bytes()
DIR = 0x1E24F

rows = {}
for i in range(70):
    o = DIR + i * 18
    if o + 18 > len(EXE):
        break
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows[i] = dict(idx=i, w0=w0, w2=w2, span=w4, fixups=w5)

placements = {p['idx']: p for p in json.load(open('analysis/ida_falconcd/overlay_placement.json'))}
located = {e['idx']: e for e in json.load(open('analysis/ida_falconcd/record_fixup_located.json'))}

CLUSTER_B0 = 0xFFFA0
SPECIAL = {0x1D0D, 0x1D31}


def table_pos(r):
    if 50 <= r['idx'] <= 68:
        return CLUSTER_B0 + (r['w2'] << 4)
    if r['idx'] == 69:
        return CLUSTER_B0 + (r['w2'] << 4) + 0x60
    e = located.get(r['idx'])
    if r['fixups'] and r['w2'] >= 0x1000:
        ov = set(range(r['w0'], r['w0'] + max(1, r['span']))) | SPECIAL
        bp = r['w2'] << 4
        ok = sum(1 for k in range(r['fixups'])
                 if struct.unpack_from('<H', EXE, bp + k * 4 + 2)[0] in ov) / r['fixups']
        if ok >= 0.8:
            return bp
    if e and e['fixup_frac'] >= 0.8:
        return e['fixup_pos']
    if r['w2'] >= 0x1000:
        return r['w2'] << 4
    return None


# every linear range the IDB holds bytes in (resident image + written records)
WINDOWS = [(0x10000, 0x2CF60)]
for p in placements.values():
    if p.get('ida_ea') is not None and p['ida_len']:
        WINDOWS.append((p['ida_ea'], p['ida_ea'] + p['ida_len']))


def para_ok(word):
    """Is `word` a link-time paragraph whose +0x1000 form lands in a real window?"""
    if word > 0xFFFF:
        return False
    lin = ((word + 0x1000) & 0xFFFF) << 4
    return any(lo <= lin < hi for lo, hi in WINDOWS)


# pass 1's FROZEN list. Read it from here and NOT from fixups_to_apply.json --
# that file is this script's own OUTPUT, so reading it back would turn a second
# run into a no-op (every entry would look "already applied") and quietly lose
# the new sub-block fixups.
pass1 = {int(k): set(v) for k, v in
         json.load(open('registry/fixups_pass1_applied.json'))['rows'].items()}

pairs_out = {}
stats = Counter()

for idx, r in rows.items():
    p = placements.get(idx)
    if not p or p['addr'] == 'skip' or not p['data_file'] or not p['ida_len']:
        continue
    pos = table_pos(r)
    if pos is None or pos + r['fixups'] * 4 > len(EXE):
        stats['no_table'] += 1
        continue
    arena = set(range(r['w0'], r['w0'] + max(1, r['span']))) | SPECIAL
    kept = pass1.get(idx, set())
    plist = []
    for k in range(r['fixups']):
        off, seg = struct.unpack_from('<HH', EXE, pos + k * 4)
        stats['pairs'] += 1
        if seg not in arena:
            stats['dropped_seg_out_of_arena'] += 1
            continue
        abs_off = (seg - r['w0']) * 16 + off          # <-- finding 56's anchor
        # the anchor must address bytes this record actually wrote, for pass-1
        # entries too -- anything outside was never applied (the applier's
        # getseg check skipped it) so dropping it costs no fidelity.
        if not (0 <= abs_off + 2 <= p['ida_len']):
            stats['dropped_outside_written_window'] += 1
            continue
        fpos = p['data_file'] + abs_off
        if fpos + 2 > len(EXE):
            stats['dropped_file_oob'] += 1
            continue
        w = struct.unpack_from('<H', EXE, fpos)[0]
        # pass-1 entries are reproduced WITHOUT the paragraph test: those bytes
        # are already patched in the IDB and a fresh rebuild must reach them.
        if abs_off in kept:
            stats['kept_pass1'] += 1
            plist.append((abs_off, w))
            continue
        # a new fixup only makes sense on a link-time paragraph -- += 0x1000 on
        # anything else (a count, an offset) would corrupt it.
        if not para_ok(w):
            stats['dropped_word_not_a_link_paragraph'] += 1
            continue
        stats['kept_new'] += 1
        plist.append((abs_off, w))
    if plist:
        pairs_out[idx] = plist

json.dump({str(k): v for k, v in pairs_out.items()},
          open('analysis/ida_falconcd/fixups_to_apply.json', 'w'))
print('fixup pairs read           : %d' % stats['pairs'])
print('  dropped: seg not in arena: %d' % stats['dropped_seg_out_of_arena'])
print('  dropped: abs_off outside written window: %d' % stats['dropped_outside_written_window'])
print('  dropped: not a link paragraph (and not already applied): %d'
      % stats['dropped_word_not_a_link_paragraph'])
print('  dropped: file oob         : %d' % stats['dropped_file_oob'])
print('kept: already applied by pass 1 : %d' % stats['kept_pass1'])
print('kept: NEW                        : %d' % stats['kept_new'])
print('TOTAL written                    : %d across %d records'
      % (sum(len(v) for v in pairs_out.values()), len(pairs_out)))
print('wrote analysis/ida_falconcd/fixups_to_apply.json')
