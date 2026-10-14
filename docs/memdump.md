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

All dumps below are committed (1 MB each, linear conventional RAM).

### Session A — instrumented build (2026-10-14, `dosbox_with_debugger.exe` + `FALCON_TRACE`)

Provenance: **PROVEN** — captured via `tools\run_falcon_traced.ps1`, dumps via
debugger `MEMDUMPBIN 0 0 100000` (see recipe below).

| File | MD5 | State |
|---|---|---|
| `MEMDUMP1_opening.BIN` | `6579bdbe22458394db8f48523c92342a` | opening / title |
| `MEMDUMP2_main_menu.BIN` | `3debffd982dc201d83baae1e8441dd54` | main menu (baseline for diffs) |
| `MEMDUMP3_briefing.BIN` | `c3fc08ed87a618a7ed1915457fae62e4` | briefing |
| `MEMDUMP4_edit_flights_zoom.BIN` | `e8a214bac0178dcfbd8fdd68f180d0b9` | edit flights (zoomed) |
| `MEMDUMP5_waypoints.BIN` | `875268acd6102fc22c2d98a1099bcdd3` | waypoints |
| `MEMDUMP6_pilots.BIN` | `33d882685b17bbb878e81763c8f113d8` | pilots |
| `MEMDUMP6_flight_takeoff.BIN` | `7d0c481cd894e10aebf8cd4e4cd3da67` | flight — takeoff |
| `MEMDUMP7_armament.BIN` | `223708388164dbcd6276c1d4efddd3c2` | armament |
| `MEMDUMP7_flight_outside_view.BIN` | `5128252a03bbda5946032d90a42c6148` | flight — outside view |

Paired traces from the same runs (committed):
`trace_20261014_231428_{fileio.jsonl,fartrans.jsonl,meta.json}` (menu states) and
`trace_20261014_232757_*` (full run incl. flight; 23:27–23:34).
Note: these two runs predate the throttle — their `calls`/`jumps` counts are
unsampled full counts. Newer runs wall-clock sample per target
(`FALCON_TRACE_THROTTLE_MS`, default 1 ms; `elapsed_ms` recorded).

### Session B — legacy dumps (2026-02-13, provenance **UNKNOWN**)

| File | MD5 |
|---|---|
| `MEMDUMP_menu.BIN` | `394275fcb9556c02e852a0a8499cde32` |
| `MEMDUMP_mission.BIN` | `bdcd9664bb0eaebb8a9a65171ff50c65` |
| `MEMDUMP_sim.BIN` | `74765360fd38940073d5d9149d65e5e1` |

Predate this repo (likely old DOSBox 0.74 — finding 30). Kept for comparison
only; treat session A as the ground truth.

Regenerate the machine-readable inventory (paragraph diffs vs baseline, IVT,
MCB walk over all `memdump/*.BIN`):

```bash
C:\Python314\python.exe tools\memdump_inventory.py   # -> analysis/memdump/inventory.json
```

## First-pass results (2026-10-14, session 16 — `tools/memdump_inventory.py`)

All claims below are **HYPOTHESIS** until cross-checked against the trace logs
(`trace_20261014_*_fartrans.jsonl` / `*_fileio.jsonl`).

### Session A (instrumented build — use these)

1. **Within-set paragraph diffs** (baseline `MEMDUMP2_main_menu`):
   - menu-family screens (briefing 15.6 %, edit-flights 17.7 %, waypoints
     17.8 %, pilots 17.8 %, armament 18.4 %) → same overlay family, small
     deltas;
   - flight dumps (takeoff 42.3 %, outside view 42.3 %) → the expected big
     menu↔sim overlay swap;
   - opening screen 36.8 % (splash/intro overlays differ from menu).
2. MCB arena behaves as advice.md predicts: menu-family dumps ~63–110 heads,
   flight/pilots dumps up to 220 heads (far more heap allocation in sim).
3. Legacy-vs-session-A diffs are 57–70 % — **do not compare across sessions**
   (different DOSBox build, different load addresses); each session is only
   meaningful against itself.
4. IVT stable: 106 vectors above the DOS kernel in every session-A dump.

### Session B (legacy, Feb 2026)

1. Linear 1 MB image; real-mode IVT at `0000:0000` → genuine conventional-RAM flats.
2. Game PSP para `0x118`, main program PSP para `0x192` (load seg `0x1A2`?),
   arena ~650 KB. Tentative mapping `runtime_para = ida_para - 0xE5E` —
   re-verify on session A before trusting.
3. menu vs sim 47.1 % differ, menu vs mission 17.3 %.

## Trace mining results (2026-10-14, finding 32 — `tools/mine_traces.py`)

Artifacts in `analysis/traces/` (`summary.json`, per-run `file_summary` /
`overlay_reads` / `segment_classes`, `overlay_load_map.json`,
`rtlink_loads.json`). Key results (PROVEN unless noted):

- **Session-A load base**: image para **`0x1F5`**, PSP **`0x1E5`** (MCB owner
  + `CD 20` verified in `MEMDUMP2`); both trace runs identical.
  - `runtime_seg = ida_seg - 0xE0B` · `runtime_lin = ida_lin - 0xE0B0`
  - `file_off = ida_lin - 0xD400` · RTLink records: `runtime = w0 + 0x1F5`
  - Supersedes the legacy `ida - 0xE5E` guess (session-dependent — re-derive).
- **`0x1161` = resident `seg020`** — main code hub: 1.44 M far calls, ≥7 hot
  IPs verified byte-for-byte against the EXE.
- **Overlay loads**: 41 tail file-offsets → segments, stable across both
  runs; 33 RTLink records joined (30 stable, 3 transient: idx 5, 29, 69);
  0 unmatched reads.
- **VGA**: ES `0xA000`/`0xA400`/`0xA800` at call entries.
- **DS is per-phase** (`0x6C27` menu-heavy vs `0x46A4` in run 2) — DGROUP
  classification must be per-function (open).

## Progress checklist (advice.md mapping)

- [x] Inventory: hashes, sizes, timestamps (this file)
- [x] First-pass paragraph diff menu/mission/sim (`tools/memdump_inventory.py`)
- [x] MCB-chain walk + PSP discovery (same script)
- [x] **Re-dump** menu/mission/sim from the instrumented dosbox-staging build
      (provenance UNKNOWN → PROVEN) — DONE 2026-10-14: 9 dumps + 2 FALCON_TRACE
      runs (session A above)
- [x] Verify runtime↔static mapping — session A: `runtime = ida - 0xE0B`,
      records `= w0 + 0x1F5` (finding 32; re-derive per session)
- [ ] Merge menu+sim+briefing dumps to resolve **live thunk states**
      (advice.md "Fixing the Live Thunk Trap") → patch thunks to live targets
- [x] Identify resident vs overlay-pool segment ranges per dump — image
      `[0x1F5..~0x1E96]` + seg020 `0x1161` / seg021 entry `0x1C98` runtime
      segs identified; pool segs from tail reads (5-6 host code, finding 32)
- [ ] Carve heap blocks (MCB-owned, owner=0x192) → scan DGROUP for far
      pointers into them (advice.md §4) → **find decompressed asset buffers**
      (compression format UNKNOWN, finding 31 — do this instead of guessing
      the algorithm)
- [ ] Emit segment classification JSON (SEG_DGROUP / SEG_STATIC /
      SEG_OVERLAY_ID(n) / SEG_HEAP_ALLOC(callsite)) from the trace build's
      `*_fartrans.jsonl` + these dumps — **partial**: VGA + overlay pool +
      target segs emitted (`analysis/traces/segment_classes.json`); DGROUP
      per-function + heap call-site tagging open
- [ ] Cross-check carved overlay bytes against `function_bytes.json` ground
      truth (validates fixup application, finding 21)

## How to re-dump 1 MB images from the instrumented build

The debugger **is compiled in** (`dosbox_with_debugger.exe`, `OPT_DEBUGGER=ON`)
— it is entered via hotkey, not a separate mode:

1. Run the game via `tools\run_falcon_traced.ps1` (trace runs in parallel).
2. Navigate to the state you want (menu / mission / sim).
3. Press **Alt+Pause** (Alt+Break) — the debugger window opens. (Default
   binding from `debugger.cpp: MAPPER_AddHandler(DEBUG_Enable, SDL_SCANCODE_PAUSE, MMOD2, ...)`.
   If your keyboard swallows Pause, remap: **Ctrl+F1** → Hotkeys → "Debugger".)
4. In the debugger command line type:
   ```
   MEMDUMPBIN 0 0 100000
   ```
   (hex seg=0, ofs=0, count=0x100000 → full 1 MB linear dump). It writes
   **`MEMDUMP.BIN` in the process working directory** (the debug message shows
   the absolute path) — rename it to `MEMDUMP_<state>.BIN` immediately.
5. Press **F5** (Run Program) to resume.
6. Repeat 3–5 for each state, then update the inventory table above and run
   `tools\memdump_inventory.py`.

## Usage notes

- Dumps are **local-only** (not committed); this tracker + `inventory.json`
  are the committed record.
- Tools operate on the raw 1 MB flat: paragraph `p` is at byte offset `p*16`.
