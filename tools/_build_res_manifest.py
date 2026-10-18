import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, ida_name, json, os, sys, hashlib, bisect
ROOT = r"C:\Users\yotam\projects\falcon3"
READY = os.path.join(ROOT, 'analysis/ida_falconcd/resident_manifest_ready.json')
OUT = os.path.join(ROOT, 'registry/resident_register_expected.json')
ready = json.load(open(READY, encoding='utf-8'))
fn_ivs = sorted((ida_funcs.get_func(s).start_ea, ida_funcs.get_func(s).end_ea)
                for s in idautils.Functions())
fn_starts = [x[0] for x in fn_ivs]
problems = []
ranges_out = []
seen = set()
for r in ready:
    entry = r['entry']; size = r['size']; end = entry + size; key = r['key']
    if key in seen:
        problems.append('dup key %s' % key)
    seen.add(key)
    # overlap with existing fn
    i = bisect.bisect_left(fn_starts, entry)
    for j in (i-1, i):
        if 0 <= j < len(fn_ivs):
            s2,e2 = fn_ivs[j]
            if s2 < end and e2 > entry:
                problems.append('0x%X overlaps existing fn 0x%X..0x%X' % (entry, s2, e2))
    # tiling [entry,end) with just the new fn
    lo, hi = entry, end
    spans = [(entry, end)]
    cur = lo
    for s,e in spans:
        if s > cur: problems.append('gap before 0x%X' % entry)
        cur = max(cur, e)
    if cur != hi: problems.append('coverage 0x%X != hi 0x%X' % (cur, hi))
    ranges_out.append({
        'name': 'res_%X' % entry,
        'range': [lo, hi],
        'keep_fns': [],
        'new_fns': [{'key': key, 'ea': entry, 'size': size}],
        'data_holes': [],
    })
n_fn = sum(len(x['new_fns']) for x in ranges_out)
print('ranges: %d  new_fns: %d  keep: 0  holes: 0' % (len(ranges_out), n_fn))
print('bytes: %d' % sum(f['size'] for x in ranges_out for f in x['new_fns']))
if problems:
    print('NOT WRITING %d problems:' % len(problems))
    for p in problems[:20]: print('  !', p)
    idaapi.qexit(1)
json.dump({
    'schema': 1,
    'reason': ('finding 63: parentless registration of verified Resident dsts. '
               'Aligned to real instruction heads (3 mid-instruction entries '
               'corrected: 0x28CAB->0x28CA8, 0x10423->0x10422, 0x108E7->0x108E6). '
               'Only the 23 candidates confirmed add_func-able. REGISTER: exact '
               'tiling + live sha256 (no holes).'),
    'ranges': ranges_out,
    'standalone_holes': [],
    'n_new_fns': n_fn, 'n_keep_fns': 0, 'n_holes': 0, 'hole_bytes': 0,
}, open(OUT, 'w'), indent=1)
print('wrote %s' % OUT)
idaapi.qexit(0)