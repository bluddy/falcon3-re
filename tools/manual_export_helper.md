# Quick Manual Export

Since IDA batch mode isn't cooperating, here's the fastest way to get the export done:

## Option 1: Copy-Paste into IDA (FASTEST - 30 seconds)

1. Open IDA with FALCONCD.EXE.i64
2. Press `Alt+F7` or go to `File` → `Python command`
3. Copy-paste this entire block and press Enter:

```python
import idaapi, idautils, idc, json, os
idaapi.auto_wait()
segs = [{'name': idaapi.get_segm_name(s), 'start_ea': s.start_ea, 'end_ea': s.end_ea, 'selector': s.sel} for s in [idaapi.getseg(ea) for ea in idautils.Segments()] if s]
funcs = []
for func_ea in idautils.Functions():
    f = idaapi.get_func(func_ea)
    if f:
        s = idaapi.getseg(func_ea)
        funcs.append({'name': idc.get_func_name(func_ea), 'start_ea': f.start_ea, 'end_ea': f.end_ea, 'segoff': f"{idaapi.get_segm_name(s)}:{func_ea-s.start_ea:04X}" if s else "?"})
multi = {}
for func_ea in idautils.Functions():
    f = idaapi.get_func(func_ea)
    if not f: continue
    fname = idc.get_func_name(func_ea)
    ents = []
    ea = f.start_ea
    while ea < f.end_ea:
        if ea != f.start_ea:
            xrefs = [x for x in idautils.CodeRefsTo(ea, 0) if x + idc.get_item_size(x) != ea]
            if xrefs:
                s = idaapi.getseg(ea)
                ents.append({'address': ea, 'segoff': f"{idaapi.get_segm_name(s)}:{ea-s.start_ea:04X}" if s else "?", 'offset_from_start': ea - f.start_ea, 'xref_count': len(xrefs)})
        ea = idc.next_head(ea, f.end_ea)
    if ents: multi[fname] = ents
outpath = os.path.join(os.path.dirname(idc.get_idb_path()), 'segment_map.json')
with open(outpath, 'w') as f: json.dump({'segments': segs, 'functions': funcs, 'multi_entry_functions': multi, 'summary': {'total_segments': len(segs), 'total_functions': len(funcs), 'multi_entry_count': len(multi)}}, f, indent=2)
print(f"✓ Export complete: {outpath}")
print(f"  Segments: {len(segs)}, Functions: {len(funcs)}, Multi-entry: {len(multi)}")
```

4. Wait ~30 seconds for it to complete
5. You'll see output like: `✓ Export complete: C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\segment_map.json`

## Option 2: Run Script File

1. Open IDA with FALCONCD.EXE.i64
2. `File` → `Script file...`
3. Select: `C:\Users\ybarnoy\projects\falcon3\tools\export_segments_simple.py`
4. Wait for completion message in Output window

## After Export

Move the file to the analysis directory:
```powershell
Move-Item C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\segment_map.json C:\Users\ybarnoy\projects\falcon3\analysis\s4\segment_map.json -Force
```

Then verify the seg020:051B hypothesis:
```powershell
cd C:\Users\ybarnoy\projects\falcon3\analysis\s4
python verify_10bdb_mapping.py
```

## What This Does

The script:
- Exports all segment definitions (names, start/end addresses)
- Lists all 4,127 functions with their segment:offset notation
- Finds multi-entry functions (functions with secondary entry points called from elsewhere)
- Saves everything to `segment_map.json`

The most important output is the multi-entry functions list, which should show us that `seg020:051B` is a secondary entry point with ~10,222 xrefs - confirming our hypothesis about "sub_10BDB".
