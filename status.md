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

## Partial Call Graph (bottom-up method, session 17d)

Artifact: `analysis/traces/callgraph_partial.json` — **327 endpoints, 911/1,232 nodes, 6 levels** (edges = 1,494 static IDA refs ∪ runtime `indirect_far`). Method: leaves → callers → repeat (partial by design; trace coverage is incomplete). Rebuild: run `tools\export_callrefs.py` (IDA) then `tools\callgraph_bottomup.py` after any IDA change. Work **Level-0 hot leaves first** so types propagate upward. See finding 38 for verified vs. refuted external advice (`docs/advice3.md`).

**Level-0 COMPLETE (findings 39, 41, 42):** **56 of 328 endpoints named** — batching stopped by evidence: of the 272 unnamed, only **69 have dynamic evidence** (6,532 calls total, ~95 avg vs batch-1's 318K/210K); 13 are DATA-class junk; false-leaf rate just **2/328** (register-indirect scan). 7 groups (`far_cb_0..9` trampolines + gated variants, cb-arg block save/restore/table-set, input/hw, CS state get/set, tables, geometry/clip, init/irq/list), each with a `sig:` contract. Also split the **51,676 B `sub_2E2D0`** blob into 3 (recovered 8,312 + 8,696-call entries; EXACT 466→468).

**Level-1 in progress (findings 43–46):** **113 Level-1 nodes named** (batches 1–4, dyn top now down to **9**/node) — ledger **204**, `routines.yaml` **205**, all pushed to IDB, `check` green, `verify_rebuild` faithful with round-trip assertions, and **verified by positive IDA read-back: match=204 / mismatch=0**. Highlights: **`op_dispatch` (39 callers = graph's highest fan-in)**, `fn_table_dispatch`, `entity_setup_step` (19 callees), `group_register_main` (1,511 B = largest unnamed C), `state_mode_check` (10 callers) plus the `mode_slot_*` family, `table_dword_set`↔`table_dword_get` pair closed, `critical_section_wrap`, `int8_vector_hook`/`unhook` (timer IRQ), `sound_device_init` (**passes the `0x388` AdLib port**), `key_code_resolve`+`key_action_execute`, `kb_records_rebuild`, plus **11 C-class functions now named = new port candidates**. **Rules: (a) callee context suggests, disassembly confirms; (b) never rely on optional imports inside IDAPython — an except-path must be loud; (c) batch slices always start at `L0_START=0` (the unnamed list shrinks every batch); (d) never emit IDAPython scripts via PS 5.1 `Set-Content -Encoding UTF8` (BOM ⇒ IDA compile failure).** Next: Level-1 batch 5 (267 unnamed Level-1 remain), then Level 2 — resolving `op_dispatch`'s 17 targets.

**Graph cleanup (deferred, tracked in [Open Items](docs/open_items.md)):** 13 DATA + 10 NEARTHUNK as functions; **~17 multi-entry/merged IDA boundary errors** accumulated across findings 43–46 (worst: `sub_254C0` = 7 entries, `sub_10D8C` = 4 entries + embedded data, `sub_23036` ≥4); DATA-but-code misclassifications (`sub_228BF`, `sub_10E03`, `sub_224C2`); `sub_22DFF` undecoded regions; 203 unnamed `dyn==0` Level-0 endpoints. A single bulk cleanup pass would be worthwhile once naming winds down.

**Rebuild = one canonical runbook** [`docs/workflow/idb_regeneration.md`](docs/workflow/idb_regeneration.md) (finding 40 audit). ⚠️ Rules: every IDB-mutating script must `save_database()` explicitly (never rely on idat's exit-save); gate commits with **`tools/verify_rebuild.py`** (diffs fresh `function_bytes.json` vs git HEAD, exit 1 on divergence); diagnostics must **never `del_items` existing functions**; text tools must **prune `dosbox*` under `src/`**. The EXE itself is *not* in git — verify md5 `2BDD74F4…` against `registry/FALCONCD.EXE.yaml` first.
## Open Items

See [Open Items](docs/open_items.md)

## Reference Projects

See [Reference Projects](docs/reference_projects.md)

## Artifacts

See [Artifacts](docs/artifacts.md)
