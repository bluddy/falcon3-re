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

- **Graph cleanup (side task):** `classification.json` carries **13 DATA-class +
  10 NEARTHUNK "functions"** that are dispatch-table labels / 4-byte far stubs,
  not callable routines. They pollute `callgraph_partial.json` endpoints
  (e.g. they appear in Level 3/4 lists) and inflate the function count.
  Reclassify or drop them, then re-run `export_callrefs.py` +
  `callgraph_bottomup.py`. Needs a rule for `function_bytes` (they ARE
  registered in the IDB) vs `classification` (should say label).
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
- **`op_dispatch` (`sub_2257B`) is the graph's highest-fan-in node (39
  callers, 17 table targets)** — resolving its 17 targets is the single best
  next move for Level-2 work.
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
- **`op_dispatch` targets are only starting to resolve**: `sub_22699`
  (`file_create`, AH=3Ch) and `sub_227D3` both list `op_dispatch` among their
  static callers — i.e. they *are* dispatch targets. ~15 more unidentified.
- **Level-1 dynamic evidence is now EXHAUSTED** (finding 47): batch 5's tail
  reached `dyn=0`, so all 143 dyn>0 Level-1 nodes are named and the remaining
  **207 have zero dynamic-call weight**. Batching by dyn no longer ranks
  anything — switch to static fan-in ordering, or move to Level 2 / the bulk
  cleanup pass.