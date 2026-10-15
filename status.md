# Falcon3 Decompilation Status — handover document

**Last updated**: 2026-10-14 (session 16 — see Time Log; always bump + append row)
**Branch**: master (HEAD `6fb6902` at time of writing)
**Snapshot**: `analysis/ida_falconcd/FALCONCD.EXE.i64` (IDA Pro 9.1, headless only)
**IDA install**: `C:\Program Files\IDA Professional 9.1\` (idat.exe at
  `C:\Program Files\IDA Professional 9.1\idat.exe`; interactive IDA must NEVER open
  Falcon — it holds the Gunship DB)

> This file is the **entry point for a future agent**. It states the exact current
> state and the exact method. Deep rationale lives in `docs/findings_log.md`
> (append-only history, findings 1–34), detailed procedures in `docs/pipeline.md`.
> Protocol: **Knowledge Capture** — 7 sinks, findings log append-only, status
> Time Log bumped on every change.

---

# Time Log

See [Time Log](docs/time_log.yaml)

## Executive Summary

See [Executive Summary](docs/executive_summary.md)

## Current State at a Glance

See [Current State](docs/current_state.md)

## Verified Facts

See [Verified Facts](docs/verified_facts.md)

## The Method

See [The Method](docs/workflow/main.md)

## Verified Routines

See [Verified Routines](docs/verified_routines.md)

## Code Coverage

See [Code Coverage](docs/code_coverage.md)

## Game Knowledge Base

See [Game Knowledge Base](docs/game_knowledge_base.md)

## Immediate Next Steps (in order)

1. ~~**Patch static thunk table in IDA**~~ ✅ DONE (session 17): `tools/patch_thunks_ida.py` ran headless. Thunk table at IDA EA **0x2BD9D** (not 0x1EBAF). 299/303 thunks patched — E8 trap at +0..+2 replaced with NOPs so IDA flows into JMP FAR at +3. Segments converted (JSON seg + 0x0E5E = IDA seg). 4 ambiguous (dup offset 0x000A in recs 1/53) skipped — segments already correct. Log: `analysis/ida_falconcd/patch_thunks.log`.

2. ~~**Fresh traced run** (populate SEG_HEAP_ALLOC)~~ ✅ DONE (session 17): `trace_20261015_211031` — 3.97M far calls, 82 target CS, 1,093 overlay reads, **674 heap blocks → 655 SEG_HEAP_ALLOC segments** with call-site attribution. Traces mined (`mine_traces.py`), segments classified (`classify_segments.py` → `segment_classification.json`).

3. ~~**Memory-deref + indirect-target hooks**~~ ✅ DONE (session 17): Hooks 2+3 implemented in `falcon_trace` + interpreter core. **Hook 2** (memderef): `DO_PREFIX_SEG` logs every DS:/ES: segment-override instruction → `<prefix>_memderef.jsonl` (8,352 unique CS:IP sites in test run). **Hook 3** (indirect far): `CALL Ep`/`JMP Ep` in GRP5 log resolved targets → `<prefix>_fileio.jsonl` events (379,498 in test run). Requires `core=normal` (forced at startup when `FALCON_TRACE` set — dynamic core bypasses `prefix_none.h`). Debug fix: `falcon_trace_enabled` was defined twice (anonymous namespace + file scope), `FalconTrace_Active()` read the wrong one.

4. ~~**Re-check port-queue C candidates** against new boundaries~~ ✅ DONE (session 17c): **108 C candidates, zero defects** (no overlap/missing/size-mismatch, all `ENTER` prologue); C boundary EXACT **8→33** vs comprehensive trace; 4 clean reloc-free port targets. The 87 UNKNOWN decomposed = **67 thunk entries + 13 data labels + 4 real code** (confirms "not functions"). Bonus: **19 missed functions registered** (fn count 1,215→1,234) including `0x22AFF` (174,766 calls, IRET handler) and `0x1018F` (132,401 calls). Boundary EXACT 340→466. Tools: `add_trace_functions.py`, `fix_trace_functions.py`.

## All four immediate next steps are complete. Next session should re-plan from [Open Items](docs/open_items.md) and `docs/advice.md`.
## Open Items

See [Open Items](docs/open_items.md)

## Reference Projects

See [Reference Projects](docs/reference_projects.md)

## Artifacts

See [Artifacts](docs/artifacts.md)
