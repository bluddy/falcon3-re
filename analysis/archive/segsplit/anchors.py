"""Host-side: per overlay record, the distinct fixup `seg` paragraphs (anchors)
and the offsets they cover.  Table location logic copied from
tools/validate_fixup_semantics.py.  Writes anchors.json."""
import json
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\ybarnoy\projects\falcon3")
EXE = (ROOT / "game/FALCONCD.EXE").read_bytes()
DIR = 0x1E24F
CLUSTER_B0 = 0x100000
SPECIAL = {0x1D0D, 0x1D31}

rows = {}
for i in range(70):
    o = DIR + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows[i] = dict(idx=i, w0=w0, w2=w2, span=w4, fixups=w5)
placements = {p['idx']: p for p in json.load(open(ROOT / 'analysis/ida_falconcd/overlay_placement.json'))}
located = {e['idx']: e for e in json.load(open(ROOT / 'analysis/ida_falconcd/record_fixup_located.json'))}


def table_pos(r):
    if 50 <= r['idx'] <= 69:
        return CLUSTER_B0 + (r['w2'] << 4)
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


out = {}
for idx, r in rows.items():
    p = placements.get(idx)
    if not p or p['addr'] == 'skip' or not p['ida_len']:
        continue
    pos = table_pos(r)
    if pos is None:
        continue
    arena = set(range(r['w0'], r['w0'] + max(1, r['span']))) | SPECIAL
    anc = defaultdict(list)
    for k in range(r['fixups']):
        if pos + k * 4 + 4 > len(EXE):
            break
        off, seg = struct.unpack_from('<HH', EXE, pos + k * 4)
        if seg not in arena or seg in SPECIAL:
            continue
        anc[seg].append(off)
    lst = []
    for seg in sorted(anc):
        offs = anc[seg]
        rel = (seg - r['w0']) * 16
        if rel >= p['ida_len']:
            continue
        lst.append({"seg": seg, "rel": rel, "ea": p['ida_ea'] + rel, "n": len(offs),
                    "min_off": min(offs), "max_off": max(offs),
                    "min_ea": p['ida_ea'] + rel + min(offs), "max_ea": p['ida_ea'] + rel + max(offs)})
    out[idx] = {"name": p['seg_name'], "ida_ea": p['ida_ea'], "len": p['ida_len'], "w0": r['w0'],
                "anchors": lst}

json.dump(out, open(ROOT / "analysis/segsplit/anchors.json", "w"), indent=1)
for idx, o in out.items():
    if len(o['anchors']) > 1 or o['len'] > 0x10000:
        print("%2d %-10s len=%06X anchors=%d" % (idx, o['name'], o['len'], len(o['anchors'])))
        for a in o['anchors']:
            print("     seg=%04X rel=%05X ea=%06X n=%4d off=%04X..%04X" % (
                a['seg'], a['rel'], a['ea'], a['n'], a['min_off'], a['max_off']))
