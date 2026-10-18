# Falcon3 Decompilation Status — handover document

**Last updated**: 2026-10-18 (session 18 — see Time Log; always bump + append row)
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

**The Resident -> Thunk -> Overlay bridge now exists (finding 56):** crossing edges **8 -> 213**, distinct overlay functions reachable from resident **5 -> 73**, refs INTO the thunk table **204 unresolved -> 0 of 230**, slots exporting their JMP FAR **27/303 -> 296/303**, functions **1,284 -> 1,678**, static edges **1,764 -> 2,493**, `static_unresolved` **1,257 -> 702**. Both causes were mechanical: the thunk table was read **53 entries late** (`0x1EBAF` vs the real `0x1E99D`, i.e. `Thunk #053` not `#000`) and the registration decode stopped one instruction short of the `jmp far` at `slot+3`. **Slot #302 (`0x2C969`) can never be a function** -- it straddles the loader boundary `seg021 0x2AA30..0x2C970 | seg022 0x2C970..0x2CF60` and `add_func` refuses cross-segment ranges (finding 37); it has **0 refs** in or out, so 302/303 is accepted. **The `+0x1540` mystery is solved**: the fixup `seg` field names a paragraph anchor, so `abs = (seg-w0)*16 + off` (`0x1F64 = w0+0x154` -> IDA `0x2F640`), giving 100% word-ok for every non-zero anchor; `R05_1E10` is a **24-sub-block split**, and the anchor begins with a name table (`global.amo`/`local.amo`/`harpoon.dat`), not a fixup base. The 12,118-fixup correction is **verified but deliberately not applied** (it would mass-CHANGE overlay bytes and needs a manifest). **(now applied — finding 57.)**

**Sub-block fixups applied (finding 57):** the correction finding 56 verified but staged is now executed — `abs = (seg-w0)*16 + off`, **11,475 NEW words written, 25,222 already correct, 0 mismatch, 306 function spans unchanged**. The first run was refused by its own span guard (`sub_4DA46` grew 1 byte while re-decoding data) and rerun with re-decode limited to pre-existing instruction heads. Because a bulk byte change would otherwise be indistinguishable from drift, `registry/subblock_fixups_expected.json` pins the **59 changed functions by (key, ea, size) and the sha256 of their bytes before *and* after**, and `verify_rebuild.py` learned a **PATCH** class that matches on both hashes — an unlisted or mis-hashed change still fails. Effect: static edges **2,493 -> 2,730**, overlay orphans **228 -> 224**, and **71 -> 990 retargeted call sites now land exactly on a registered function entry** (resident 38 -> 923); 719 functions had zero indegree at HEAD, **138 now have an incoming edge** (134 resident, 4 overlay). `static_unresolved` went **702 -> 957** — arithmetic, not regression: 449 retargeted destinations are now honest *data* (233 distinct addresses, hottest `0x28CAB` x36) that used to be interior hits, and 5 brand-new sites do the same (702 + 250 + 5 = 957). Inside `sub_2E2F0` there are now **1,053 interior refs across 13 4 KB buckets = exactly 6 sub-block anchors (finding 58), none at a function start** — the next structural win is splitting that span.

**Unresolved-destination audit (finding 58, read-only):** the `static_unresolved = 957` backlog is **515 distinct destinations**, each freshly decoded in IDA: **401 dsts / 750 refs (78%) are frameless 16-bit code** ending `retf`/`jmp`/`retn` — only **12/401** carry the strict `55 8B EC`/`C8` prologue that the step-3 guards required, 196 sit right after a terminator; **30 are indexed jump-table case targets** (`jmp/call cs:off_X[bx]`, mapped 12/12 onto table words + paragraph base `0x11BA0`) — **zero `FF 1E`/`FF 2E` pointer-variable refs exist**; **84 are anomalies** (49 undecodable-first-byte — including `0x6E1EA` x24 which is *inside* the ASCII string `WRONG VERSION!` and `0x6DFF0` x23 which is a word table — 28 long code without a terminator, 7 with no segment). **`sub_2E2F0` is now mapped, not guessed:** 24 anchors in `R05_1E10` = 1 segment base + **6 inside the blob** + 17 in the upper half (correcting finding 57's `13 sub-block anchors`, which was a 4 KB bucket heuristic); 1,053 refs into the blob = **971 internal, all dropped today by the `s != d` rule**, + 71 external calls over 22 addresses + 10 thunk; **371 entry seeds**; data is only **3 holes / 239 B**; 7 blocks whose largest is 46,416 B. The split waits on a new `verify_rebuild` class: a manifest whose `new_fns ∪ data_holes` tiles the old span exactly and whose holes keep their sha256, or it is `CHANGED`.

**`sub_2E2F0` carved (finding 59), gate first:** the 46 KB blob is now **258 functions + 3 data holes (239 B) pinned by sha256**, planned in `registry/subblock_split_expected.json` *before* any mutation. `verify_rebuild` learned a **CARVE** class (exact planned `(key, ea, size)` set, no function may overlap a hole, parent must shrink, and each hole's sha256 must match the **live** export that `verify_idb.py` now writes to `data_holes.json`, failing if a hole is covered by a function or not flagged as data). Boundaries came from the terminator-backwards rule over 372 seeds, cross-checked against the existing decode: 10 crossing instructions split into 8 zero-padding items (deleted) and **2 real instructions -- `9A` at `0x32552`, `3D` at `0x3A2D6` -- whose seeds were dropped as backward-decode artefacts**. The mutator refused to save three times (missing `idc.get_byte`, a `%d` on a string, and `create_insn` returning 0 when another item sits inside an entry's first instruction) and each time the backup was restored and re-verified **INTACT**. Result: functions **1,678 -> 1,935**, static edges **2,730 -> 4,013 (+1,283)**, refs into the blob forming edges **82 -> 812** with **572 at an exact function start**, code refs unchanged at 9,244 (nothing lost), 256/258 new functions already called.

**Upper-half P0+P1 done (finding 60):** inventory of `0x3ACAC..0x669F0` in `upper_map.json` — 18 anchor blocks, 179,524 B, only **38 fns / 2.4%**, evidence concentrated in two blocks (163 and 93 refs) with **three blocks carrying zero call evidence (18,992 B the largest)**, 68 candidate data holes / 6,278 B from UI strings, 8 RTLink `entry_ea`s. The dynamic CS→record gap is **root-caused and closed**: `mine_traces` only ever globbed `trace_*` (the 37 MB `debug_test` dump was never mined — now 5 runs / 46 records), and the address rule is record-relative (`runtime CS = link seg + 0x1F5`, `IDA = ida_ea + ((cs−0x1F5)−w0)*16 + ip`) with **mutually exclusive variant records sharing `w0=0x1E10`** (R05/R27/R28/R29) disambiguated by terminator content — re-mining shows R05 and R29 both loaded at `0x2005` in different runs. Result: `runtime_seg_map.json` resolves **432 → 28,264** overlay events, `dynamic_unresolved` **122,263 → 64,067**, union **4,016 → 4,034**. **Honest negative: 0 dynamic events touch the upper half**, so that range still rests on P2's static chain sweep (P3 registration under a manifest, P4 measurement follow).

**Upper half registered (finding 61):** P2's chain sweep (`sweep_upper.py`) walked **22,240 instructions / 59,641 B** across the four evidence-rich blocks under strict rules -- existing IDA decodes always win, `00` runs only skip before entry-like code, mid-item conflicts resync instead of stopping, stale `<=15 B` data items step over, mid-body islands bridge only when a chain re-closes on a terminator, and no piece is emitted without evidence (seed / existing code item / closed boundary / any referenced dst). P3 then registered it behind the new **REGISTER** gate: `registry/upper_register_expected.json` pins **116 new functions + 24 kept + 68 data holes (6,278 B)** with exact tiling and live sha256, and the mutator (`register_upper.py`) converted the holes, created 19,289 instructions only where none existed, and saved only with every guard green. Outcome: functions **1,935 -> 2,051**, static edges **4,013 -> 4,907**, **`static_unresolved` 957 -> 772** (957 - 291 in-scope destinations now registered + 106 newly revealed refs still outside), 107/116 new functions already have callers. Zero-evidence blocks (1,552 / 880 / 18,992 B) deliberately untouched; 44 in-scope dsts (83 refs) remain inside documented stops.

**Still outstanding:** `~17 multi-entry ranges from findings 43–47` (`sub_254C0` = 7 entries, `sub_10D8C` = 4 + data, `sub_23036` ≥4); `sub_22DFF` undecoded regions; 203 unnamed `dyn==0` Level-0 endpoints.

**Rebuild = one canonical runbook** [`docs/workflow/idb_regeneration.md`](docs/workflow/idb_regeneration.md) (finding 40 audit). ⚠️ Rules: every IDB-mutating script must `save_database()` explicitly (never rely on idat's exit-save); gate commits with **`tools/verify_rebuild.py`** (diffs fresh `function_bytes.json` vs git HEAD, exit 1 on divergence); diagnostics must **never `del_items` existing functions**; text tools must **prune `dosbox*` under `src/`**. The EXE itself is *not* in git — verify md5 `2BDD74F4…` against `registry/FALCONCD.EXE.yaml` first.
## Open Items

See [Open Items](docs/open_items.md)

## Reference Projects

See [Reference Projects](docs/reference_projects.md)

## Artifacts

See [Artifacts](docs/artifacts.md)
