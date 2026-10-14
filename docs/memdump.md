# Memdump Tracker — `./memdump/*.BIN`

**Purpose**: raw 1 MB conventional-RAM snapshots of Falcon 3.0 running under
DOSBox, used as dynamic ground truth (advice.md §Snapshot Splicing; findings
30/31). The instrumented dosbox-staging build (finding 30) will re-dump these
with known provenance; the current files predate this repo.

**Protocol**: update this file whenever a step completes or a claim is
disproved. Every derived claim carries a certainty level
(PROVEN/STRONG/HYPOTHESIS/UNKNOWN — see status.md "Verified Facts").

---

## Inventory

| File | Size | MD5 | Timestamp | Provenance |
|---|---|---|---|---|
| `memdump/MEMDUMP_menu.BIN` | 1,048,576 | `394275fcb9556c02e852a0a8499cde32` | 2026-02-13 | **UNKNOWN** (dump tool/build unknown; likely old DOSBox 0.74 — finding 30) |
| `memdump/MEMDUMP_mission.BIN` | 1,048,576 | `bdcd9664bb0eaebb8a9a65171ff50c65` | 2026-02-13 | UNKNOWN (as above) |
| `memdump/MEMDUMP_sim.BIN` | 1,048,576 | `74765360fd38940073d5d9149d65e5e1` | 2026-02-13 | UNKNOWN (as above) |

Regenerate the machine-readable inventory (paragraph diffs, IVT, MCB walk):

```bash
C:\Python314\python.exe tools\memdump_inventory.py   # -> analysis/memdump/inventory.json
```

## First-pass results (2026-10-14, session 16 — `tools/memdump_inventory.py`)

All claims below are **HYPOTHESIS** until re-verified against a dump from the
instrumented build.

1. **Layout sanity**: linear 1 MB image; real-mode IVT at `0000:0000` with
   BIOS vectors at `F000:xxxx` → the dumps really are conventional-RAM flats.
2. **DOS arena** (MCB walk, DOSBox `sMCB` layout): real chain starts at
   paragraph `0x117`; **game PSP = paragraph `0x118`** (small 1.4 KB block,
   probably a launcher/stub) and **main program PSP = paragraph `0x192`**
   which owns a 30,141-paragraph (482 KB) block + two more large blocks
   (12 KB, 65 KB) → likely image + far-heap allocations of the game.
   Tentative runtime load segment of the main image: **`0x1A2`**
   (= PSP `0x192` + 0x10).
3. **Runtime-vs-static mapping (to verify)**: with IDA image base para
   `0x1000`, the working hypothesis is
   `runtime_para = ida_para - 0x1000 + 0x1A2` (= `ida_para - 0xE5E`).
   Check against known overlay load list segments (e.g. `0x1CF6` → `0x1E98`).
4. **Paragraph diffs** (16-byte granularity):
   - menu vs mission: **17.3 % differ** (same session family — mission screen
     inside the menu system)
   - menu vs sim: **47.1 % differ**, sim vs mission: **45.1 % differ**
     → large overlay-pool swap between menu system and 3D sim, exactly as
     advice.md predicts (identical paragraphs ≈ resident code).
   - MCB block counts: menu/mission ~10 blocks vs sim ~48 → sim allocates
     far more heap (terrain/object pools).
5. IVT: 105 vectors point above the DOS kernel (`CS >= 0x100`) in every dump.

## Progress checklist (advice.md mapping)

- [x] Inventory: hashes, sizes, timestamps (this file)
- [x] First-pass paragraph diff menu/mission/sim (`tools/memdump_inventory.py`)
- [x] MCB-chain walk + PSP discovery (same script)
- [ ] **Re-dump** menu/mission/sim from the instrumented dosbox-staging build
      (provenance UNKNOWN → PROVEN) — depends on finding 30 build
- [ ] Verify `runtime = ida - 0xE5E` against known runtime segments
      (thunk/overlay load list, finding 18)
- [ ] Merge menu+sim+briefing dumps to resolve **live thunk states**
      (advice.md "Fixing the Live Thunk Trap") → patch thunks to live targets
- [ ] Identify resident vs overlay-pool segment ranges per dump (identical
      paragraphs = resident; differing low ranges = overlay pool)
- [ ] Carve heap blocks (MCB-owned, owner=0x192) → scan DGROUP for far
      pointers into them (advice.md §4) → **find decompressed asset buffers**
      (compression format UNKNOWN, finding 31 — do this instead of guessing
      the algorithm)
- [ ] Emit segment classification JSON (SEG_DGROUP / SEG_STATIC /
      SEG_OVERLAY_ID(n) / SEG_HEAP_ALLOC(callsite)) from the trace build's
      `*_fartrans.jsonl` + these dumps
- [ ] Cross-check carved overlay bytes against `function_bytes.json` ground
      truth (validates fixup application, finding 21)

## Usage notes

- Dumps are **local-only** (not committed); this tracker + `inventory.json`
  are the committed record.
- Tools operate on the raw 1 MB flat: paragraph `p` is at byte offset `p*16`.
