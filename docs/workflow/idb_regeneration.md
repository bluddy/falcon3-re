# IDB Regeneration Runbook
### 4. IDB regeneration runbook (if lost/corrupt — details in pipeline.md)

```
idat -A -S tools\ida_snapshot.py               <IDB>   # fresh analysis (legacy overlays!)
idat -A -S tools\rebuild_overlay_segments.py   <IDB>   # correct layout from committed placement
idat -A -S tools\_add_missed_fn.py             <IDB>   # sub_19D65 (manual fn)
idat -A -S tools\add_missed_functions.py       <IDB>   # 11 kb-unit gap fns (finding 28)
idat -A -S tools\add_gap_functions.py          <IDB>   # 59 gap-sweep fns (finding 28 follow-up)
idat -A -S tools\mark_overlay_entries.py       <IDB>   # 184 thunk entries -> ~192 fns
idat -A -S tools\apply_overlay_fixups.py       <IDB>   # 25,222 fixups
idat -A -S tools\extract_ida_bytes.py          <IDB>   # regenerate ground truth (keys stable)
venv\Scripts\python tools\classify_routines.py
venv\Scripts\python tools\naming.py push-ida           # re-sync semantic names
# host-side JSON regen only if the EXE changed: prep_overlay_placement.py ->
# prep_overlay_entries.py -> validate_fixup_semantics.py (then IDA steps above)
```