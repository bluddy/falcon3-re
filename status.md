# Falcon3 Decompilation Status — handover document

**Last updated**: 2026-10-17 (session 17 — see Time Log; always bump + append row)
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

**Level-1 COMPLETE (findings 43–47):** **143 Level-1 nodes named (batches 1–5)** — **batch 5's tail hit `dyn=0`, so every Level-1 node with dynamic evidence is named; the remaining 207 have zero dynamic-call weight**, which ended batch-by-dyn. Ledger **234 → 266**, `routines.yaml` **235 → 265**, `check` green, `verify_rebuild` faithful, **IDA read-back: functions 264/264 + globals 2/2, zero mismatches**. **Batch 5's tail reached `dyn=0`, so every Level-1 node with dynamic evidence is now named; the remaining 207 have zero dynamic-call weight** — batch-by-dyn is finished (switch to static fan-in, Level 2, or the bulk cleanup pass). Highlights: **`op_dispatch` (39 callers = graph's highest fan-in)**, `fn_table_dispatch`, `entity_setup_step` (19 callees), `group_register_main` (1,511 B = largest unnamed C), `state_mode_check` (10 callers) plus the `mode_slot_*` family, `table_dword_set`↔`table_dword_get` pair closed, `critical_section_wrap`, `int8_vector_hook`/`unhook` (timer IRQ), `sound_device_init` (**passes the `0x388` AdLib port**), `key_code_resolve`+`key_action_execute`, `kb_records_rebuild`, `ems_init` (full INT 67h bring-up), `program_terminate` (AH=4Ch), `vec3_dot`, **`file_create` = first confirmed `op_dispatch` target**; **42 C-class functions now named (12 from batches 1–5) = port candidates**. **Rules: (a) callee context suggests, disassembly confirms; (b) never rely on optional imports inside IDAPython — an except-path must be loud; (c) batch slices always start at `L0_START=0` (the unnamed list shrinks every batch); (d) never emit IDAPython scripts via PS 5.1 `Set-Content -Encoding UTF8` (BOM ⇒ IDA compile failure).** Next: static-fan-in ordering over the 207 evidence-free Level-1 nodes, or the bulk cleanup pass.

**Level 2 COMPLETE (finding 48):** **both indirect-dispatch hubs 100% resolved — `op_dispatch` 16/16, `fn_table_dispatch` 15/15 (31 targets)**. `op_dispatch` is a **DOS service shim**: a 32-byte table where each slot sets `AH` and issues `int 21h` (alloc/free/open/close/read/write/lseek + create, find-first/next, get-DTA, memcpy, memset, print, delete, file-size). **`opcode = BX/2` proven three ways** — 8086 16-bit addressing has no scale field; `sub_165AE` passes `BX=14,CH=2` ⇒ lseek-from-end = file size and `sub_13F00` passes `BX=10,CX=4,DX=0x212` ⇒ read; and all 87 static sites load even BX immediates giving exactly {alloc,free,open,close,read,write,lseek}. This **retro-validates batch 5** (`slot2_alloc` = file-size + chunk math, `slot2_copy_chunks` = looped reads). `fn_table_dispatch` is the **view/projection dispatcher** (15 modes writing the 3-vector `es:3884/3886/3888`). New tool **`tools/dump_dispatch_tables.py`** (`DT_FNS=<dispatcher>`), and the ledger's **`kind: global`** path was exercised for the first time (2 dispatch-table globals).

**Graph cleanup pass 1 DONE (finding 49)** — and it corrected a wrong premise: `class` was **our** byte-string heuristic (only tested a trailing `c3`/`cb`), never IDA's, so it had mislabeled **128 real routines** as DATA. Fixed host-side via `tools/export_epilogues.py` → committed `last_insns.json` (IDA's decoded last instruction) with a byte-only fallback: **DATA 153 → 24, bad-class 163 → 34**, ASM 871 → 992, LEAF 96 → 104. **Zero IDB mutation**; gates green (`check` 266, `verify_rebuild` faithful 1,238/1,238). Also corrected: the **10 NEARTHUNK are callable far entry points** (`E8 01 00 CB`, one already `stub_to_1119c`), not junk. **Pass 2 DONE (finding 50) — it delivered 1 split, not 10:** finding 49's interior-ref list needed two more conditions (terminator *immediately* before + callable entry), which are now hard preconditions inside the new **`tools/split_function.py`**; 9 candidates were false positives, including `sub_213E6` which turned out to have *no error at all*. Split `table_iterate_loop` (`E8 01 00 CB` = NEARTHUNK stub merged with its 136 B body) → 4 B `stub_to_23966` + 136 B `table_iterate_loop`, exact 140 B coverage, **NEARTHUNK 10 → 11**. Gates: **integrity `INTACT`**, `verify_rebuild` **SPLIT 1 + ADDED 1, LOST 0 → faithful**, `check` OK (267), read-back 265/265; fns 1,238 → 1,239, endpoints 328 → 329. **Two tooling facts:** `push-ida` cannot handle a split (resolves by the old `sub_*` key, so it silently skips the rename — used an EA-keyed rename instead), and **MD5 is unusable for IDB integrity** (idat rewrites the file on every run; matching a fresh copy proves nothing) → new **`tools/verify_idb.py`** semantic gate. **Blocked, not deferred:** the 24 truncated ranges need a true end address that isn't derivable from bytes, and junk-object removal would report `LOST` (needs an intentional-removal allowlist).

**Overlay provenance (finding 51)** — measured, not assumed: 1,239 fns = 1,029 resident + **210 overlay**, all mapping to an RTLink record. **Overlay *nodes* are dynamic-derived** (finding 33's trace-driven repair) but **overlay *edges* are mostly static** — static reaches **28/210** overlay functions as a call target vs dynamic's **2/210** (dynamic `to_ida()` only covers 16 segments, so 145,212 of 379,498 events fall out). **Cross-record overlay edges = 0 from both sources** — all 28 static overlay→overlay edges are within one record. Two gaps logged: register the 19 unresolved resident→overlay thunk targets, and widen the CS→record map past 16 segments.

> ### ✅ RESOLVED (findings 52 → 53): overlay segments were decoded as 32-bit
>
> All `R*` segments have `bitness = 1` (32-bit) while the program is real-mode
> 16-bit. Root cause: **`tools/rebuild_overlay_segments.py:61` calls
> `ida_segment.add_segm(...)` and never sets `bitness`** (loader segments get
> 16-bit from the MZ header; runtime-created ones default to 32-bit).
> Verified empirically — resident `0x10BE2` renders `mov sp, cs:byte_10842+4 /
> pushf`, while overlay `0x103087` renders `mov ebx 579A000Ch` from bytes that
> are actually `1E 06 BB 0C 00 9A` = `push ds / push es / mov bx,000Ch`.
>
> **Fixed (finding 53).** `tools/rebuild_overlay_segments.py` now pins
> `bitness = 0` after `add_segm`; `tools/fix_overlay_bitness.py` set **68 `R*`
> segments → 16-bit**, cleared **1,053,376 B** of 32-bit items, re-probed 210
> overlay ranges (115 ends kept, 53 re-probed, 42 flagged); `fix_overlay_bodies.py`
> re-decoded **77,315/77,654 B**. Audit: **82 spans changed — overlay only,
> 0 resident, 0 moved, 0 probe-cap hits.**
>
> **Gate handling:** `verify_rebuild` correctly failed with `CHANGED 82`. Fixed
> with an **exact-match allowlist** (`registry/bitness_fix_expected.json`,
> keyed `key+ea+old_size+new_size` → counted as `RECODE`), so this bulk recode
> cannot become precedent — anything unlisted still fails. Now `RECODE 82,
> CHANGED 0, LOST 0 → faithful`.
>
> **Effect:** static edges 1,503 → **1,762**, nodes 913 → **1,007**, overlay
> coverage `R05` 13% → **100%** (17,655 heads), `R01` 36% → 92%. **But overlay
> orphans only fell 204/210 (97%) → 189/210 (90%)** — bitness blocked correct
> *analysis*; the missing *edges* need entry registration and the bridge→`entry_ea`
> remap instead. `DATA 24 → 45` = the 42 no-terminator functions landing where
> they belong.
> Also: `overlay_entries.target_linear` is **not** a copy of `entry_ea` (only
> 7/232 byte-identical; low addresses hold RTLink directory text) — use
> `entry_ea`.

**Overlay edge connectivity (finding 54) — node side solved, edge side not:** registered **45 overlay entry points** (fns **1,239 → 1,284**, **C 108 → 126** from the `enter` prologues), all 45 verified, gates green (`verify_rebuild` **ADDED 45 / CHANGED 0 / LOST 0 → faithful**). But overlay orphans went 189/210 → **232/255** — +45 nodes, only **+2 edges**. The `target_linear → entry_ea` remap measured **net-negative** (11 → 8 of the only 15 affected refs) and was reverted. **The real backlog is `edge_counts.static_unresolved = 1,257`** — refs whose source resolves but whose destination is in no registered function (off the entry grid / mid-region / no entry record). Read "91% orphaned" as *"1,257 destination registrations missing"*, not as unregistered overlay entries — those now largely are registered.

**What those 1,257 actually are (finding 55) - 84% are ordinary missing registrations, and the bridge has two mechanical defects:** bucketed by `tools/unresolved_dsts55.py`: **611 (49%) land inside an R\* segment with no function, 442 (35%) inside resident bytes with no function, 204 (16%) inside the .RTLink thunk table, 0 elsewhere** (src split 1,130 R\* / 127 Res). The shift hypothesis is now *control-tested*: across 445 distinct dsts x 12 candidate paragraph deltas, **+0x10000 lands exactly on a function start for 45 dsts vs 0 in a seeded random control; every other delta scores 6 vs 2 (noise)**. IDA side (`farops_export55.py`, 3,478 far operands): of 1,151 dead far-destinations **446 are fixed by +0x10000 and 408 of those rels are simply absent from the fixup tables we apply** (36 dropped by the `seg != w0` filter, 2 kept-but-unapplied); 433 of the 446 live in `R05_1E10`. **Two independent breaks in Resident -> Thunk -> Overlay:** (1) `prep_overlay_entries.py`, `parse_thunks.py`, `solve_thunk_assignment.py`, `validate_record_bases.py` hard-code `THUNK = 0x1EBAF` = **53 entries into** the 303-entry table at `0x1E99D` (= IDA `0x2BD9D`) - so `overlay_entries.json` is missing slots `0..52` (+ `95`, `99`) and **46 of the 53 offset slots' JMP targets have no function**; (2) `export_callrefs` only walks heads *inside functions*, so **49/303 slots are registered, only 27 emit a JMP FAR ref, 276 slots are never traversed**, and 19 of those 27 jump to unregistered targets. Concrete: thunk `0x2BD9D` = `e8 1d f2 ea 12 00 37 2d 01 00`; `0x2BDA0` is `jmp far 2D37:0012` -> linear `0x2D382`, `CodeRefsFrom` -> **no function** (row-1 `entry_ea 0x2D31A = r01_e01` belongs to slot #053, not #000). Unexplained flag: `R05_1E10`'s fixup offsets align with its far operands only after a **+5440-byte** shift (398/412) although its declared table run and payload base both check out - do not act on it yet.

**Still outstanding:** `~17 multi-entry ranges from findings 43–47` (`sub_254C0` = 7 entries, `sub_10D8C` = 4 + data, `sub_23036` ≥4); `sub_22DFF` undecoded regions; 203 unnamed `dyn==0` Level-0 endpoints.

**Rebuild = one canonical runbook** [`docs/workflow/idb_regeneration.md`](docs/workflow/idb_regeneration.md) (finding 40 audit). ⚠️ Rules: every IDB-mutating script must `save_database()` explicitly (never rely on idat's exit-save); gate commits with **`tools/verify_rebuild.py`** (diffs fresh `function_bytes.json` vs git HEAD, exit 1 on divergence); diagnostics must **never `del_items` existing functions**; text tools must **prune `dosbox*` under `src/`**. The EXE itself is *not* in git — verify md5 `2BDD74F4…` against `registry/FALCONCD.EXE.yaml` first.
## Open Items

See [Open Items](docs/open_items.md)

## Reference Projects

See [Reference Projects](docs/reference_projects.md)

## Artifacts

See [Artifacts](docs/artifacts.md)
