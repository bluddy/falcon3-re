#!/usr/bin/env python3
"""Finding 63: audit the 93 Resident unresolved destinations (0x10000..0x2CF60)
for registerability.  Read-only analysis; produces analysis/ida_falconcd/resident_audit.json.
Run under plain python (host), not idat."""
import json, sys, os
from collections import Counter, defaultdict
from bisect import bisect_right

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

# Load classification + refs + dst_classified (finding 58)
cls = json.load(open(os.path.join(ROOT, 'analysis/ida_falconcd/classification.json'), encoding='utf-8'))
refs = json.load(open(os.path.join(ROOT, 'analysis/ida_falconcd/callgraph_refs.json'), encoding='utf-8'))
dst_list = json.load(open(os.path.join(ROOT, 'analysis/ida_falconcd/dst_list.json'), encoding='utf-8'))
dst_cls = json.load(open(os.path.join(ROOT, 'analysis/ida_falconcd/dst_classified.json'), encoding='utf-8'))

# Resident range
RES_LO, RES_HI = 0x10000, 0x2CF60

# Build class map from finding-58's dst_classified (cls field, not 'class')
cls_map = {rec['ea']: rec.get('cls', 'unknown') for rec in dst_cls if isinstance(rec, dict)}
# Jump-table = class b
jump_table_dsts = {ea for ea, c in cls_map.items() if c == 'b_ptr_or_indirect'}

# Index by range
ivs = sorted((v['ea'], v['ea']+max(v['size'],1), k) for k,v in cls.items())
st = [x[0] for x in ivs]

def enclosing_fn(ea):
    i = bisect_right(st, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2]
    return None

# Filter resident dsts
resident_dsts = [d for d in dst_list if RES_LO <= d['ea'] < RES_HI]

# Build audit records
records = []
for d in resident_dsts:
    ea = d['ea']
    n = d['n']
    cls_name = cls_map.get(ea, 'unknown')
    is_jt = ea in jump_table_dsts
    enclosing = enclosing_fn(ea)
    records.append({
        'ea': ea, 'n_refs': n, 'cls': cls_name,
        'jump_table': is_jt,
        'enclosing_fn': enclosing,
        'action': 'standalone' if not enclosing and not is_jt else
                  ('append_tail' if enclosing else 'jump_table_target'),
    })

# Stats
actions = Counter(r['action'] for r in records)
classes = Counter(r['cls'] for r in records)
total_refs = sum(r['n_refs'] for r in records)

out = {
    'range': [hex(RES_LO), hex(RES_HI)],
    'total_dsts': len(records),
    'total_refs': total_refs,
    'actions': dict(actions),
    'classes': dict(classes),
    'jump_table_dsts': sorted(hex(e) for e in jump_table_dsts),
    'records': records,
    'top': sorted(records, key=lambda x: -x['n_refs'])[:15],
}

with open(os.path.join(ROOT, 'analysis/ida_falconcd/resident_audit.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1)

print(f"Resident range {hex(RES_LO)}..{hex(RES_HI)}")
print(f"  dsts: {len(records)}   refs: {total_refs}")
print(f"  actions: {dict(actions)}")
print(f"  classes: {dict(classes)}")
print(f"  jump-table dsts: {len(jump_table_dsts)}")
print(f"  top 5 by refs: {[(hex(r['ea']), r['n_refs'], r['action']) for r in out['top'][:5]]}")
print(f"wrote resident_audit.json")