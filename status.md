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

1. ~~Trace-driven boundary verification~~ **DONE (finding 33)**: 135 functions recovered (1,080 → 1,215), EXACT 204→340. Remaining: 87 UNKNOWN candidates in `boundary_report.json` (incl. `01F5:018F`, 132K calls, IDA refuses even with chunk conversion); MID cases are mostly dispatch-table labels — documented, not pursued. Re-check port-queue C candidates against new boundaries.
2. ~~Segment classification + thunk-state merge~~ **DONE (finding 34)**: `segment_classification.json` (multi-kind, DGROUP 27687 HYPOTHESIS, resident base PROVEN) + `thunk_states.json` (66/66 stable). Remaining: (a) **fresh traced run** to populate `SEG_HEAP_ALLOC` — the AH=48h/49h call-site hook postdates both committed traces; (b) confirm DGROUP via a dump-side pointer check (promote HYPOTHESIS → PROVEN); (c) **patch the static thunk table to the live targets** so agents see the true call graph; (d) memory-deref + indirect-target logging (advice.md §3.3 hooks 2–3) still unimplemented.
3. **Track C first splice test**: Export IDB assembly (`idat -A -Stools/ida_export.asm`), run `extract_routines.py` → `splice.py` with keyboard unit verified routines → reassemble → `mzdiff.py` verification against function_bytes.json ground truth.
4. **Fix mzdiff fixup handling**: Apply RTLink fixups when extracting bytes from EXE for accurate comparison.
5. **10 straggler thunk entries** (user explicitly deferred; findings 19/26).
6. `libscan.py` with compiler libs (MSC 5.1 *and* BC 2.0) for library-function ID.

## Open Items

See [Open Items](docs/open_items.md)

## Reference Projects

See [Reference Projects](docs/reference_projects.md)

## Artifacts

See [Artifacts](docs/artifacts.md)
