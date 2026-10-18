#!/usr/bin/env python3
"""Finding 64 (IDA-side, read-only): build overlay_scope.json for the top 6
R* overlay segments.  For each named segment, find its exact IDA [start,end)
range and emit a scope block.  Also emit the segment boundaries so the sweep
covers the full segment (not just the unresolved-dst span).

Usage: cmd /c "tools\\run_idat.bat tools\\build_overlay_scope.py"
"""
import json, os, sys
import idaapi, ida_segment, idautils, idc

ROOT = r"C:\Users\yotam\projects\falcon3"
OUT = os.path.join(ROOT, 'analysis/ida_falconcd/overlay_scope.json')

TARGETS = ['R30_569F', 'R06_5CD9', 'R53_569Fs', 'R14_5E0B', 'R17_5E8F', 'R35_569Fs']

# Enumerate all IDA segments, match by name
segments = {}
for n in idautils.Segments():
    seg = idaapi.getseg(n)
    if not seg:
        continue
    name = idc.get_segm_name(n)   # get_segm_name takes an ea, not a seg object
    segments[name] = (seg.start_ea, seg.end_ea)

scope = []
found = []
for t in TARGETS:
    # exact name match, or prefix match (segment may have suffix)
    match = None
    for name, (s, e) in segments.items():
        if name == t or name.startswith(t) or t in name:
            # prefer exact, then shortest
            if match is None or len(name) < len(match[0]):
                match = (name, s, e)
    if match:
        name, s, e = match
        scope.append({"name": "ovl_" + t, "lo": s, "hi": e})
        found.append((t, name, s, e, e - s))
    else:
        found.append((t, None, 0, 0, 0))

# Fallback: for segments not found by name, use the dst-list span padded to
# segment boundaries via placement (we emit dst span as last resort).
lst = json.load(open(os.path.join(ROOT, 'analysis/ida_falconcd/dst_list.json'),
                     encoding='utf-8'))
for t, name, s, e, sz in list(found):
    if name is None:
        zone = 'overlay:' + t
        ds = [d['ea'] for d in lst if d['zone'] == zone]
        if ds:
            lo, hi = min(ds), max(ds) + 1
            # pad to 16-byte boundaries
            lo &= ~0xF
            hi = (hi + 0xF) & ~0xF
            scope.append({"name": "ovl_" + t, "lo": lo, "hi": hi})
            found = [(t, 'dst-span', lo, hi, hi - lo) if x[0] == t else x
                     for x in found]

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({
        "scope": scope,
        "note": ("finding 64: top 6 R* overlay segments.  Ranges from IDA "
                 "segment table where named, else padded dst-list span."),
        "found": [{"target": t, "seg": n, "lo": hex(s), "hi": hex(e), "size": sz}
                  for t, n, s, e, sz in found],
    }, f, indent=1)

print("wrote %s" % OUT)
for t, n, s, e, sz in found:
    print("  %-12s seg=%-14s 0x%X..0x%X (%d B)" % (t, n, s, e, sz))
print("scope blocks: %d  total bytes: %d" % (len(scope), sum(x['hi']-x['lo'] for x in scope)))

idaapi.qexit(0)