# Open Items
## Open Items (not blockers — tracked in findings log)

- ~15 cluster-B rows' exact fixup positions; 14 fixup *types* exist — +L only proven
  for the dominant far-pointer type (findings 20/21); exotic before-words (0xC08E…).
- 10 unresolvable overlay thunk entries (their target bytes aren't code where mapped).
- **✅ RESOLVED (findings 52 → 53): every `R*` overlay segment had `bitness = 1`
  (32-bit) in a real-mode 16-bit program.** Cause: `rebuild_overlay_segments.py:61`
  called `add_segm` and never set bitness. Fixed across 68 segments
  (1,053,376 B cleared, 210 ranges re-probed: 115 kept / 53 re-probed / 42
  flagged), source patched, bodies re-decoded (77,315/77,654 B). Ground truth
  shifted by **82 overlay spans, ea unchanged, 0 resident** — allowlisted by
  exact match in `registry/bitness_fix_expected.json` (so `verify_rebuild`
  still fails anything unlisted). Overlay coverage `R05` 13% → 100%.
  **Remaining overlay work is the EDGE side, not bitness — and finding 54
  measured it:** after registering 45 viable `overlay_entries` (fns 1,239 →
  1,284, C 108 → 126), orphans only went 189/210 → 232/255 (+45 nodes, +2
  edges), and the `target_linear → entry_ea` remap proved **net-negative**
   **(i) and (ii) below are now FIXED -- finding 56 built the bridge:**
   crossing Resident->Overlay edges **8 -> 213**, overlay fns reachable from
   resident **5 -> 73**, refs into the thunk table **0 unresolved of 230**
   (254 slots registered, `sub_2BFCD` 210B split 21x10B, `sub_2BE83` 20B
   split 2x10B, slot #053 detached from `start` with its xref kept).
   **Remaining:** (a) **346 distinct destinations stay unregistered and NONE
   passes the prologue/terminator guards** (274 have no 16-bit prologue, 106
   no reachable terminator) -- the residual `static_unresolved` (702 after f56, **957 after f57**) is now a
   *diagnosis* problem, not a registration one; (b) overlay orphans only
   232 -> 228, because the pre-existing orphans are functions nothing CALLS;
   (c) slot #302 (`0x2C969`) is permanently un-registerable -- it straddles
   the loader segment boundary `seg021 0x2AA30..0x2C970 | seg022 0x2C970`
   (d) **DONE — finding 57 applied the correction** with the exact-match
   manifest it needed: 11,475 NEW words (25,222 already correct), 0
   mismatch, 306 spans unchanged, **59 changed functions pinned by
   (key, ea, size) + before/after sha256** in
   `registry/subblock_fixups_expected.json` (a fixup at `0x3FD81`
   straddles into `sub_3FD82`, so attribution is by word overlap).
   **(e) RESOLVED BY CLASSIFICATION (finding 58):** the 957 unresolved
   refs = **515 distinct dsts = 401 frameless-code (registerable; only
   12/401 pass a strict prologue test, 196 are preceded by a terminator)
   + 30 jump-table case targets + 84 anomalies** (49 undecodable incl. the
   `WRONG VERSION!` string at `0x6E1EA` x24 and a word table at `0x6DFF0`
   x23, 28 long-code-no-terminator, 7 no-segment); 251 of the 515 sit in
   `0x3ACAC..0x669F0`; (f) **DONE (finding 59): `sub_2E2F0` is carved**
   -- the map (6 anchors inside, not f57's 4 KB-bucket "13"; data = 3
   holes / 239 B) drove a manifest-planned split into **258 functions +
   3 sha256-pinned holes**, boundaries from the terminator-backwards rule
   with 2 seeds dropped where a real `9A`/`3D` instruction crossed;
   static edges **2,730 -> 4,013**, refs into the blob 82 -> **812
   edges** (**572** at an exact function start), 256/258 new fns called;
   the gate is `verify_rebuild`'s CARVE class + `verify_idb`'s live hole
   export (`data_holes.json`) -- **still open here**: 112 rejected seeds
   stay interior by design, 2 new pieces have zero indegree, and
   `0x3ACAC..0x669F0` (251 unregistered dsts) is registration work;
   (g) 138 functions had zero indegree at HEAD and now have an edge
   (134 resident, 4 overlay), while the 226 remaining overlay orphans are
   still never called by anything static.
  ⚠ `0x2CF6A` is a **junk function registered on RTLink directory text**
  (`"MP\0DISPLAY.DAT"`) — a candidate for the removal policy.
- **Cross-record overlay edges do not exist yet (finding 51) — measured 0 from
  BOTH sources**, not "dynamic-only": all 28 static overlay→overlay edges are
  within one RTLink record, and dynamic reaches only 2/210 overlay functions
  (vs static 28/210). Two gaps to close if cross-overlay structure is wanted:
  (a) register the **19 unresolved resident→overlay** refs (thunk targets inside
  overlay territory but inside no registered function);
  (b) widen the runtime **CS → record map past the 16 segments** currently in
  `rtlink_loads.json`/`overlay_placement.json` — everything else vanishes in
  `callgraph_bottomup.to_ida()`, accounting for part of the 145,212 unresolved
  `indirect_far` events (38% of 379,498).
- Overlay byte content for 2 skipped rows (zero-span placeholders, finding 19).
- EMS/XMS runtime memory views not representable in the static IDB.
- Batch portcheck driver + per-routine asm transcripts (Track C) not built yet.
- **Compression of the 1.2 MB tail UNKNOWN** — no `PK\x03\x04` anywhere; only DCL
  copyright strings; per-asset framing never mapped; never decompressed anything
  (findings 04 vs 31). Decide format empirically via `blast` carving + runtime dumps.
- Provenance of `./memdump/*.BIN` (Feb 2026, tool unknown) — must be re-established
  or replaced by dumps from the instrumented dosbox-staging build.

### Deferred from the bottom-up naming pass (findings 39–42)

- **Graph cleanup pass 1 DONE (finding 49):** `class` was *our* byte-string
  heuristic, not IDA's — it only tested for a trailing `c3`/`cb`, so it had
  mislabeled **128 real routines** (tail `jmp`, `ret imm16`, `iret`, tail
  call) as DATA. Now classified from IDA's decoded last instruction
  (`tools/export_epilogues.py` → committed `last_insns.json`):
  **DATA 153 → 24, bad-class 163 → 34**, ASM 871 → 992, LEAF 96 → 104.
  **Correction:** the 10 NEARTHUNK (`E8 01 00 CB`) are *callable* far entry
  points, not junk — one is already named `stub_to_1119c`; exonerated.
  **Pass 2 DONE, finding 50 — it delivered 1 split, not 10.** The interior-ref
  signal found 11 sites but is a *signal*, not a diagnosis; two more
  conditions are required and both are now built into
  `tools/split_function.py`: (i) the instruction **immediately** before the
  interior must terminate flow (a terminator *anywhere earlier* is worthless in
  a large body) → 4 pass / 7 reject, and (ii) it must be a callable entry →
  byte inspection rejected `sub_213E6` (**no error at all** — a shared epilogue
  correctly owned by `sub_213E6`), `sub_2A340` (shared `sub cx,cx; retn` stub
  reached by branches), `r30_e77` (garbled data).
  **Done:** `table_iterate_loop` split at `0x23966` — head bytes `E8 01 00 CB`
  = the NEARTHUNK stub pattern merged with its 136 B body; exact 140 B
  coverage; NEARTHUNK 10 → 11.
  **Still open:**
  (a) 24 mid-stream/truncated ranges — `sub_233C0` (4 callers, ends `pop`),
      `sub_1406A`, `sub_228BF` (= `int32_to_ascii`), `r08_e46` (`ud0` = data).
      **Blocked:** a true end address is not derivable from the bytes, and
      guessing breaks byte-identity. Needs an independent witness (a trace, a
      `next_head` gap, or a known epilogue);
  (c) dropping genuinely-junk function objects → would report `LOST`, which
      `verify_rebuild` rightly fails on. Needs an explicit intentional-removal
      allowlist first. **Also note reclassifying alone does NOT change the
      graph** (Step 8 consumes ea/size intervals, not `class`).
- **Level-0 remainder (deliberately deferred):** **203 unnamed endpoints with
  `dyn == 0`** (never observed as far-call targets) + **69 with dyn>0 but
  ~95 calls avg** — harvested only if wanted "because we can"; low value vs
  Level 1. Listed in `callgraph_partial.json` `levels[0]`, rank by
  `dyn_target_calls`. Note some will be the DATA-class items above.
- **Deeper split of `sub_2E2F0` residual** (finding 42): the 51,644B remainder
  still contains MID targets `0x2E37B` (1 call), `0x2E380` (0), `0x2E6C6`
  (0) — off the 16-byte slot grid; low value, split only if a trace ever shows
  them hot. Probe tool: `tools/probe_blob_split.py`.
- **Multi-entry / merged ranges found while naming Level 1** (finding 44) —
  all are IDA boundary errors, same class as `sub_2E2D0`:
  `sub_23036` (>=4 entries, 413B), `sub_128A1` (4), `sub_22996` (2),
  `sub_127D4` (3 tail entries), `sub_25A06` (trampoline+wrapper merged, same
  shape as `sub_25F64`), `sub_26FF4` (4 conditional entries),
  `sub_1509E` (shares its prologue with `sub_128A1`+0x2C — possible
  duplicated/mis-bound code), `sub_23D85` (4B stub whose 72B range includes
  ~64B trailing data), `sub_26FE4` (possible 1B overrun).
- **`sub_22DFF` contains undecoded/data regions** (0x22E18–0x22E93) inside a
  code function — possibly self-modifying code; needs a careful look before
  trusting its `angle_adjusted_copy` name (conf: low).
- **RESOLVED (finding 48):** `op_dispatch` (`sub_2257B`, 39 callers) — all
  **16/16** table targets named; it is a **DOS service shim** (opcode = BX/2:
  alloc/free/open/close/read/write/lseek + create, find-first/next, get-DTA,
  memcpy, memset, print, delete, file-size). `fn_table_dispatch` likewise
  **15/15** (view/projection modes). New tool `tools/dump_dispatch_tables.py`
  resolves any dispatcher via `DT_FNS=<name>`.
- **More boundary/classification errors from Level-1 batches 3–4** (findings
  45–46): multi-entry ranges `sub_254C0` (7 entries!), `sub_10D8C` (4 entries
  + 9B of data), `sub_27697` (2), `sub_257B1` (2), `sub_10E03` (2),
  `sub_23036` (≥4), `sub_128A1`, `sub_22996`, `sub_127D4`, `sub_25A06`,
  `sub_26FF4`, `sub_1509E`, `sub_23D85`, `sub_26FE4`; `sub_2BFCD` is 8B of
   code in a 210B range (rest = resident-tail data); **`sub_10E03` classified
   DATA but is code**, and its callee `sub_224C2` likewise; batch 5 adds
   **`sub_13755`** (DATA-class but called by `entity_seg_reset`) and
   **`sub_10BE2`** (DATA-class but is `stack_reset_dispatch` — resets SP,
   `pushf/call far/popf`, dispatches to 8+ subsystems). 5 DATA-but-code now.
- **9 of 16 `op_dispatch` opcodes have no static call site** (finding 48):
  {2,8,9,10,11,12,13,14,15} = create, find first/next, get-DTA, memcpy,
  memset, print, delete, file-size. All 87 static sites load an immediate BX
  mapping to the other 7. Find the computed-index caller(s), or confirm they
  are runtime-only / dead.
- **Who writes `cs:word_22D28`?** — the `fn_table_dispatch` opcode source.
  Resolving it tells which view/projection mode each caller selects.
- **Level-1 dynamic evidence is now EXHAUSTED** (finding 47): batch 5's tail
  reached `dyn=0`, so all 143 dyn>0 Level-1 nodes are named and the remaining
  **207 have zero dynamic-call weight**. Batching by dyn no longer ranks
  anything — switch to static fan-in ordering, or move to Level 2 / the bulk
  cleanup pass.

- **Upper half `0x3ACAC..0x669F0` plan (after finding 59):** 179,524 B with
  only **38 functions / 4,304 B (2.4%)** registered, so this is *registration*,
  not a split: 251 unresolved destinations (445 `CALL` + 1 `JMP`; 211 frameless
  code, 40 anomalies, 126 terminator-preceded, 0 already functions, 0 thunk
  targets), 17 of the 24 anchors -> **18 blocks**, evidence heavily skewed
  (`0x3B830..0x43AE0` 33,456 B with 89 dsts/163 refs and `0x43AE0..0x48DB0`
  21,200 B with 50/93 carry the bulk; `0x500C0..0x54AF0` 18,992 B has **zero**
  call evidence; `0x54AF0..0x669F0` 73,472 B holds `*** PAUSED ***` /
  `SPEED = KNOTS` and only 1 strong entry). 8 RTLink `entry_ea`s land here, and
  unlike `0x2F640` these anchors are **code-led**, so holes are few (string
  runs in the UI block + `0x4FD80`). Ordered plan: **P0** per-anchor-block
  inventory (bytes/strings/entries/coverage -> `upper_map.json`); **P1** widen
  the dynamic CS->record map past the 16 covered segments (finding 51's gap)
  so `indirect_far` events into R05 resolve -- the only plausible evidence for
  the zero-dst blocks; **P2** chain-sweep entries (terminator before + a
  forward chain from a verified entry must reach it, and never contradict the
  existing decode; confidence A chain-verified / B ref-dst + terminator /
  C ref-dst only) instead of seed-carving, because ref density here is ~8x
  lower than the blob's; **P3** register block by block, highest-evidence
  first, under a manifest with **parentless entries** -> a new `verify_rebuild`
  `REGISTER` class (exact tiling of the stated range by `new_fns` + sha256
  holes) so a wave of ADDED never becomes a free pass the way loose
  registration did in finding 54; **P4** measure (`static_unresolved`
  957 -> ~511, +251 functions that are by construction called) recorded incrementally
  (P0+P1 = finding 60, P2-P4 next). Explicitly not doing: reusing the finding-59 mutator as-is (no
  parent function exists to delete here), or registering the 40 class-(c)
  anomalies without a chain.

- **Upper-half P0+P1 DONE (finding 60):** `map_upper.py` ->
  `upper_map.json` (18 blocks, 68 candidate holes / 6,278 B, 3 zero-evidence
  blocks incl. 18,992 B, 8 RTLink entry_eas, anchors code-led). The dynamic
  gap had two causes, both fixed: `mine_traces` globbed `trace_*` only (the
  `debug_test` dump was never mined -> now 5 runs / **46 records** / unstable
  offsets 0), and the mapping is **record-relative + content-decidable**
  (`runtime CS = link seg + 0x1F5`; `IDA = ida_ea + ((cs-0x1F5)-w0)*16 + ip`;
  the global `+0xE0B0` identity holds for only 9/68 placements). Found a
  **variant swap**: R05/R27/R28/R29 all declare `w0=0x1E10`, so candidates
  are decided by terminator content (0x3BEC 26,622 ev -> R29 2/2; 0x2159 ->
  R05 17/19; loader read-evidence as tie-break) and re-mining independently
  shows both R05 and R29 loaded at `0x2005` in different runs. Effects:
  overlay events **432 -> 28,264**, unmapped **32,392 -> 4,560** (residue =
  4,469 below-image `0188:0000` jumps + 91 heap-block calls),
  `dynamic_unresolved` **122,263 -> 64,067**, union **4,016 -> 4,034**.
  **Still open:** **0 dynamic events src-or-dst land in the upper half** --
  no call evidence exists for it yet, so **P2 (chain sweep) is the
  load-bearing step**, then P3 (manifest registration) and P4 (measure).

- **Upper-half P2+P3 DONE (finding 61):** 116 functions registered over
  77 manifest ranges (i 49 fns/24,675 B, ii 36/19,028, iii 24/5,908, iv
  7/1,262 + 5,263 B pinned strings), **68 holes / 6,278 B sha256-pinned**
  (58 in-range + 10 standalone) via the new **REGISTER** gate (exact
  tiling + live hole export; `pending` before, `applied` after). Sweep
  walked 22,240 insns / 59,641 B; static **4,013 -> 4,907** and
  **`static_unresolved` 957 -> 772** (exactly -291 in-scope dsts now
  registered +106 newly revealed refs still outside); 107/116 new fns
  called; zero-evidence blocks (1,552 / 880 / 18,992 B) untouched by
  design. **Still open:** (a) 44 in-scope dsts / 83 refs sit in
  documented stops (data, undecodable, chains that never close); (b) the
  UI block `0x54AF0..0x669F0` is data-dominated: only 6,525 B of 73,472
  covered, 7 fns -- its 67 string gaps are pinned but its code islands
  mostly fail the entry-after-padding test; (c) 74,631 B of scope stays
  uncovered with stop reasons in `upper_sweep.json`; (d) out-of-scope
  residue: 318 dsts / 583 refs plus blocks `0x493C0..0x4E520`,
  `0x4FD20..0x500C0`.

- **R05_1E10 sweep DONE (finding 62):** 12 remaining evidence blocks
  registered (82 fns, 96 ranges), `static_unresolved` **772 -> 660**;
  block iv (73 KB / 7 fns) diagnosed: its 28 residual dsts sit behind
  binary UI tables and **26/27 fail Stage-2 for no terminator behind**
  (class-c anomalies, not clean functions). **Still open:** (a) **93
  resident dsts / 236 refs** in `0x10000..0x2CF60` -- needs a
  finding-54-style registration pass over resident gaps; (b) **254
  other-overlay dsts / 424 refs** -- `R30_569F` 71, `R06_5CD9` 25,
  `R53_569Fs` 16, `R14_5E0B` 14, `R17_5E8F` 12, `R35_569Fs` 12,
  `R12/R32/R40_569Fs` 4 each -- separate RTLink records already mapped
  by finding 60's runtime map, each needs its own sweep/REGISTER cycle;
  (c) in-scope residue 63 dsts / 109 refs inside documented stops;
  (d) untouched zero block `0x500C0..0x54AF0` (0 dsts) stays out.

- **Resident destinations registered (finding 63):** 24 new fns,
  `static_unresolved` **660 -> 564**, Resident refs **236 -> 140**.
  `0x43E0C` variant check answered (not checkable -- mutually exclusive
  variants, sparse s-snippets). **Still open:** (a) **73 Resident dsts /
  140 refs** are honest residue (27 already-fn, 18 gap-into-existing, 3
  undecodable, 13 rejected standalone, 1 jt-tail) -- no further
  registration there; (b) **the other R\* overlays** remain the big
  bucket: R05 79, **R30_569F 71**, **R06_5CD9 25**, R53 16, R14 14,
  R17 12, R35 12, R12/R32/R40 4 each -- these are separate RTLink
  records already mapped by finding 60's runtime map, each needs its own
  sweep/REGISTER cycle (Finding 64); (c) in-scope R05 residue 63 dsts /
  109 refs inside documented stops; (d) untouched zero block
  `0x500C0..0x54AF0` (0 dsts) stays out.

- **Top 6 R\* overlays registered (finding 64):** 80 new fns,
  `static_unresolved` **564 -> 455**, **R30_569F fully resolved**
  (0 dsts), R06/R17/R35 down to 1-2. **Still open:** (a) **R53_569Fs 12
  dsts / 14 refs + R14_5E0B 10 dsts / 36 refs** remain (undecodable-byte
  fns converted to holes + class-c anomalies); (b) small R\* overlays
  (R12/R32/R40 4 dsts each, R33 3, R09/R34/R64/R69/R02/R10/R36/R54 1-2)
  -- ~30 dsts total, low priority; (c) **R05_1E10 in-scope residue 72
  dsts / 157 refs** inside documented stops (f62 block-iv tables); (d)
  Resident residue 73 dsts / 140 refs (already-fn, gap-into-existing,
  undecodable, rejected -- honest, no further registration); (e)
  untouched zero block `0x500C0..0x54AF0` (0 dsts) stays out.
- **Next (per plan):** recompute the **global bottom-up call graph** with
  SCC-condensed topological depth, RTLink thunk pass-through, and
  dual-tier (dyn_calls, static_in_degree) ranking, then resume naming
  from Level 0.

- **Call-graph audit done (finding 65):** named detection fixed (fb ea-join
  = 265), thunk slots excluded (302), SCC/levels verified sound (giant
  216-node SCC at L19, no inverted edges, 0 invariant violations).
  **Corrected queue: 1,676 to-name, 718 at Level 0.** Top-30 clean (the
  5 Finding-39 names + 148 thunks removed).
- **Ready for Global Level-0 Batch 1:** name from the 718-entry Level-0
  queue (dyn/in_degree ranked). Watch-outs from the audit: (a) 3
  `in_deg==0` dyn leaves (`sub_1018F`, `sub_22AFF`, `sub_24D46`) are
  indirect far-call targets -- name by body, no caller evidence; (b) 3
  DATA-class leaves in the top-30 (`sub_22C91` [truncated by `nullsub_19`
  -- real span to `retf`@0x22CD4], `sub_22C62`, `sub_25CCB`) need
  epilogue-window reclassification before trusting their class; (c) 92
  DATA-class fns total (91 queued), mostly large RTLink dispatch fns in
  the giant SCC.
- **Follow-ups:** reclassify the 92 low-confidence DATA fns (epilogue
  window + the `nullsub_19` truncation of `sub_22C91`); consider whether
  the 24 trap-only thunk far-targets deserve resolution (they point at
  `word_*`/`unk_*` data -- possibly real targets behind data tables).

- **Global Level-0 Batch 1 done (finding 66):** 30 named, `named`
  **265 -> 295**, Level-0 queue **718 -> 688**. All 4 gates green
  (check 297, verify_rebuild faithful, verify_idb INTACT, read-back
  295/295+2/2). Hygiene: epilogues 2,237/2,237; `sub_22C91` confirmed
  truncated by spurious `nullsub_19@0x22C9E` (real retf@0x22CD4),
  `sub_22C62` span over-extends into its own data table.
- **Next (Batch 2):** Level-0 ranks 31-60 (tail of the dyn>0 band: last
  dyn>0 at rank **130**, first dyn==0 at rank **131 = r30_e66** overlay
  in=39). Ranks 31-50: sub_103C6(162), sub_25247(136), sub_27673(131),
  ... sub_254BB(70). After rank 130 the queue becomes static-fan-in
  R05/overlay leaves (no trace coverage).
- **Follow-ups:** reclassify the 92 low-confidence DATA fns (epilogue
  window + `nullsub_19` truncation of `sub_22C91`); resolve the 24
  trap-only thunk far-targets (point at `word_*`/`unk_*` data).

- **Level-0 value cliff mapped + Batch 2 done (finding 67):** 30 named,
  `named` **295 -> 325**, Level-0 queue **688 -> 658**. Buckets: dyn>=10
  = 99 fns/19,944 calls (cliff after), dyn0,in>=5 = 45, **orphans = 168
  excluded** (effective nameable L0 = 520). All 4 gates green (check 327,
  verify_rebuild faithful, verify_idb INTACT, read-back 325/325+2/2).
- **Next (Batch 3):** the remaining **84 `dyn>=10` Level-0 leaves**
  (8,227 calls) are the last high-value dynamic band; then the static
  fan-in hubs (`dyn0,in>=5` now 30 left). The 168 orphans stay excluded
  (0 callers/0 callees -- not reachable bottom-up).
- **Follow-ups:** 4 low-conf R-overlay farptr thunks (r12/r08/r39/r69)
  have undecodable mid-instruction spans (class-c) -- reclassify when the
  epilogue window / span repair lands; 92 low-conf DATA fns still queued;
  24 trap-only thunk far-targets point at word_*/unk_* data.