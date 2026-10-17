# Open Items
## Open Items (not blockers — tracked in findings log)

- ~15 cluster-B rows' exact fixup positions; 14 fixup *types* exist — +L only proven
  for the dominant far-pointer type (findings 20/21); exotic before-words (0xC08E…).
- 10 unresolvable overlay thunk entries (their target bytes aren't code where mapped).
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