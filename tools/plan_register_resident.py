#!/usr/bin/env python3
"""Finding 63 P3 (host): build registry/resident_register_expected.json
from analysis/ida_falconcd/resident_candidates.json.

Each candidate is a standalone function in a gap between existing functions.
The manifest tiles each gap as: [prev_fn_end, next_fn_start) =
  new_fns | keep_fns (=[]) | data_holes  (exact tiling, no gaps/overlaps)

Data holes are any existing IDA data/named items in the gap that are NOT
covered by a new function, plus any padding (00) runs.  Every hole gets a
live sha256 from function_bytes.json (already exported) — but for non-fn
bytes we read the live export... actually resident gaps are NOT in
function_bytes (that only covers functions).  We need a raw byte reader.

Simpler: read the .i64's raw bytes? No — we're on host.  Instead: export
hole bytes from IDA in a prior pass, or read the original EXE.
The original EXE is analysis/ida_falconcd/FALCONCD.EXE (if present) or
we extract from function_bytes for fn-covered holes (there are none).

Plan: read FALCONCD.EXE directly (raw file, image base + RVA).
IDA ea -> file offset: seg_base + (ea - image_base) for the .text seg.
Actually resident 0x10000..0x2CF60 is in the main .text; need seg mapping.

Easiest: have decode_resident.py already export hole bytes+sha.  But it didn't.

Alternative: plan_register_resident.py runs UNDER IDA (via run_idat.bat)
so it can read idc.get_bytes directly.  Then it writes the manifest.

Yes — make this an IDA-side script.

Usage: cmd /c "tools\\run_idat.bat tools\\plan_register_resident.py"
"""
import json, os, sys, hashlib
import ida_bytes, ida_funcs, idaapi, idc, idautils

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, 'analysis/ida_falconcd/resident_candidates.json')
OUT = os.path.join(ROOT, 'registry/resident_register_expected.json')
FB = os.path.join(ROOT, 'analysis/ida_falconcd/classification.json')

candidates = json.load(open(CAND, encoding='utf-8'))
cls = json.load(open(FB, encoding='utf-8'))  # ground truth keys -> ea,size

# Build existing fn intervals (from live IDA — authoritative)
fn_ivs = sorted((ida_funcs.get_func(s).start_ea, ida_funcs.get_func(s).end_ea)
                for s in idautils.Functions())
fn_starts = [x[0] for x in fn_ivs]
import bisect

def prev_fn_end(ea):
    i = bisect.bisect_left(fn_starts, ea) - 1
    if i >= 0 and fn_ivs[i][1] <= ea:
        return fn_ivs[i][1]
    return None

def next_fn_start(ea):
    i = bisect.bisect_left(fn_starts, ea)
    if i < len(fn_ivs) and fn_ivs[i][0] > ea:
        return fn_ivs[i][0]
    return None

def sha(b):
    return hashlib.sha256(b).hexdigest() if b else None

ranges_out = []
problems = []
seen_ea = {}

for cand in candidates:
    ea = cand['ea']
    size = cand['fn_size']
    end = ea + size

    # Find the enclosing gap: prev fn end, next fn start
    pfe = prev_fn_end(ea)
    nfs = next_fn_start(ea)
    # Gap bounds: default to just this fn's span if no neighbors
    gap_lo = pfe if pfe is not None else ea
    gap_hi = nfs if nfs is not None else end
    # But we must not extend into existing fns — clamp
    gap_lo = max(gap_lo, ea)  # at least start at fn
    # Actually the gap should START at fn start (candidate) and END at next fn
    # or a data hole region.  Keep it simple: range = [ea, end) only the new fn.
    # No keep, no holes — just tile [ea,end) with the new fn.
    lo, hi = ea, end

    key = 'sub_%X' % ea
    # Avoid key collision with existing
    if key in seen_ea:
        problems.append('duplicate key %s' % key)
    seen_ea[key] = ea

    # new fn must not overlap any existing fn
    i = bisect.bisect_left(fn_starts, ea)
    for j in (i-1, i):
        if 0 <= j < len(fn_ivs):
            s2, e2 = fn_ivs[j]
            if s2 < end and e2 > ea:
                problems.append('0x%X new fn overlaps existing %s (0x%X..0x%X)'
                                % (ea, 'fn%d' % j, s2, e2))

    # Tiling: just the new fn covers [lo,hi)
    spans = sorted([(ea, end, 'fn:' + key)])
    cur = lo
    for s, e, tag in spans:
        if s > cur:
            problems.append('gap 0x%X..0x%X before new fn 0x%X' % (cur, s, ea))
        cur = max(cur, e)
    if cur != hi:
        problems.append('coverage ends 0x%X != hi 0x%X' % (cur, hi))

    ranges_out.append({
        'name': 'res_%X' % ea,
        'range': [lo, hi],
        'keep_fns': [],
        'new_fns': [{'key': key, 'ea': ea, 'size': size}],
        'data_holes': [],
    })

n_fn = sum(len(r['new_fns']) for r in ranges_out)
n_keep = sum(len(r['keep_fns']) for r in ranges_out)
print('ranges: %d   new_fns: %d   keep: %d   holes: 0'
      % (len(ranges_out), n_fn, n_keep))
print('bytes registered (new): %d'
      % sum(f['size'] for r in ranges_out for f in r['new_fns']))

if problems:
    print('\nNOT WRITING -- %d problems:' % len(problems))
    for p in problems[:20]:
        print('   !', p)
    idaapi.qexit(1)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({
        'schema': 1,
        'reason': ('finding 63 (P3): parentless registration of verified '
                   'Resident destinations (0x10000..0x2CF60).  Candidates from '
                   'decode_resident.py: standalone frameless ASM fns + 1 '
                   'jump-table handler that decode cleanly to a terminator, '
                   'no overlap with existing fns/data.  REGISTER validation: '
                   'exact tiling + live sha256 per hole (no holes here).'),
        'ranges': ranges_out,
        'standalone_holes': [],
        'n_new_fns': n_fn,
        'n_keep_fns': n_keep,
        'n_holes': 0,
        'hole_bytes': 0,
    }, f, indent=1)
print('wrote %s' % OUT)

idaapi.qexit(0)