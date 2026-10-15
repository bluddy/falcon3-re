# Current State
## Current State at a Glance (exact numbers)

| Metric | Value | Source |
|---|---|---|
| Functions in ground truth | **1,215** (888 resident + 192 overlay + 59 gap-sweep + **135 trace-verified**, finding 33) | `function_bytes.json` |
| Classification | ASM 855 / C 108 / DATA 152 / LEAF 90 / NEARTHUNK 10 | `classification.json` |
| Boundary verification | far-call targets EXACT 204→**340**; 3 iterations, 135 fns recovered; 87 UNKNOWN remain | `tools/verify_boundaries.py` → `analysis/traces/boundary_report.json` |
| Verified routines | **43 / 2,282 bytes** | `registry/routines.yaml` (`verified: MATCH`) |
| Rename ledger | 44 entries, all renamed + pushed to IDB | `registry/naming.yaml` |
| Struct definitions | 5 (4 confirmed, 1 hypothesis) | `registry/structs.yaml` |
| Globals inventoried | **1,968** (name=null until renamed) | `data_symbols.json` |
| Tests | **21 green** (`python -m unittest discover -s tests`) | `tests/test_naming.py` |
| Overlay IDB | 68 segments / 1,053,376 B (9 real + 59 synthetic, 2 skipped) | `overlay_placement.json` |
| Overlay fixups applied | 25,222 × +0x1000 (byte-guarded) | finding 21 |
| IDB regen cost | ~6 headless IDA runs (runbook below) | pipeline.md |
| Findings logged | 1–34 (append-only) | `docs/findings_log.md` |
| Segment classification | 116–119 segs/run, **multi-kind** (`kinds[]`+`kind`); DGROUP 27687 HYPOTHESIS, resident base 0x1F5 PROVEN; 0 heap blocks (hook postdates traces) | `tools/classify_segments.py` → `analysis/traces/segment_classification.json` |
| Thunk states | **66/66 record ids stable across 12 dumps** (303 thunks/dump); live targets resolved, load-base normalized | `tools/merge_thunk_states.py` → `analysis/traces/thunk_states.json` |
| Game knowledge | 379-line manual extraction | `registry/game_knowledge.yaml` |
| Dynamic dumps | **12 × 1 MB** conventional-RAM dumps committed: 9 from instrumented build (provenance PROVEN, menu→flight) + 3 legacy (UNKNOWN); first-pass inventory DONE | `./memdump` → `docs/memdump.md`, `analysis/memdump/inventory.json` |
| Traces | 2 × FALCON_TRACE runs **mined** (4.8 M far calls; fileio + fartrans → `analysis/traces/` incl. RTLink load map) | `memdump/trace_20261014_*`, `docs/memdump.md` |
| dosbox-staging build | **DONE**: `src/dosbox-staging/build/falcon/dosbox_with_debugger.exe` (0.84.0-alpha, `OPT_DEBUGGER=ON` + falcon trace hooks, smoke-tested) | `tools/build_dosbox_debugger.ps1`; trace via env `FALCON_TRACE=<prefix>` |