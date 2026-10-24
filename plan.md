# Falcon3 Decompilation Plan

> **Knowledge capture** (see `docs/pipeline.md` "Knowledge Capture Protocol"):
> log every finding/disproval in `docs/findings_log.md` (append-only),
> keep per-routine state in `registry/routines.yaml`,
> byte-level formats in `docs/structures.md`, renames+comments in `src/` files.

---

# Track E Plan (ADOPTED 2026-10-24) — native 64-bit rebuild in OCaml

North star: **a proper 64-bit OCaml application that behaves like Falcon 3.0** —
flat memory (no segments/far pointers/overlays/EMS), behavioural fidelity, **no
byte-parity goal**. Knowledge extraction and the rebuild proceed together: every
slice of the program gets *understood → written into the text sinks → re-implemented
→ checked against the original*.

Rules (from `docs/pipeline.md` Track E):
1. **Text-first, IDB-second** — IDB is the human observation window; committed
   files are canonical.
2. **Per-unit convergence**: struct `confirmed` in `registry/structs.yaml` →
   system write-up → re-implementation → behaviour check vs the original.
3. Knowledge Capture Protocol on every step (findings / registries / time log).
4. Tracks B/C stay as an optional byte-fidelity side check; Track D (parked)
   supplies the oracle machinery (harvester traces/memdumps).

Current foundation (why this is tractable now): **2,030 semantic names** across
all call-graph levels (0–21 complete), 2,237-function ground truth, traces +
12 memdumps as reference behaviour, manual extracted into
`registry/game_knowledge.yaml`, `naming.py check`/gates green.

## E0 — Scaffold (first days)

- [ ] OCaml toolchain on Windows: opam (native Windows) + dune; verify
      `dune build && dune test` on a hello lib.
- [ ] Create **`rebuild/`** (top-level, this repo): `dune-project`, `lib/`,
      `test/`, short `README` stating conventions:
      - module/function names follow the semantic names from `registry/naming.yaml`
        (that ledger is the map ida ↔ rebuild);
      - integer types preserve 16/32-bit wraparound semantics (no silent
        widening) — fidelity means matching the original's arithmetic, not
        "improving" it;
      - where struct types live and how they cross-link to `structs.yaml`.
- [ ] Decide test-data policy: `game/` is **gitignored**, so tests reading real
      files must skip gracefully when absent (document the requirement); commit
      tiny synthetic fixtures for format edge cases.
- [ ] Wire gates: `naming.py check` stays green; note in pipeline.md that Track E
      adds `dune test` to the gate list.

## E1 — Milestone ME1: first file-format parser

Chosen (2026-10-24): **a file-format parser** — verifiable against bytes on disk,
no oracle needed.

- [ ] **Pick the format** (shortlist, best-first):
      1. **DAT+IDX pairs** — dozens exist (`ACMI`, `IA`, `PEOPLE`, `TACTS`,
         `MADFONT`, menus, patches…): the tiny IDX is an offset/count table, so
         the format is *self-checking* (IDX offsets must tile DAT exactly) even
         before the EXE parser is found.
      2. **Weapon `.BIN` tables** — 33 files at exactly **8,452 B** = one fixed
         record struct validated 33×.
      3. `ARMSDATA\` (308 files) or `REPORT.DAT` (539 KB) — bigger, later.
- [ ] **Find the parser in the EXE**: filename string xref (headless IDA export
      or the IDB browse window) → open/read loop through `op_dispatch` (DOS
      service shim, finding 48) → the read/parse routine.
- [ ] **Document**: format + fields → `registry/structs.yaml` (`confirmed`,
      offset/size/type per field + witness ea) and `docs/structures.md`
      (narrative: header, index, record, invariants).
- [ ] **Implement** in `rebuild/`: parser + `dune test` running against the real
      file (parse → assert invariants → round-trip or field spot-checks).
- [ ] Findings entry + time log.
- **Done =** `dune test` green on the real files + struct `confirmed` + write-up.

## E2 — Foundations (parallel with E1/E3)

- [ ] **Fixed-point math module** — collect every `fixed_*` routine from the
      ledger (sign/shift/mul/div/normalize family), write `docs/fixed_point.md`
      (Q-format per routine, overflow/shift conventions), implement OCaml
      `Fixed` with exact integer semantics. Everything numeric (dynamics,
      projection, HUD) depends on this.
- [ ] **Memory-semantics write-up** — farptr / handle / slot / EMS subsystems
      documented as *expected semantics* ("what the game assumes happens when
      …"), because Track E replaces the mechanism but must preserve behaviour.
- [ ] **Struct backlog** — promote `structs.yaml` hypothesis → `confirmed`
      (targets: farobj record, kb record, slot2/slot3 window records, entity/
      mission/save). 5 structs today.
- [ ] **Domain write-ups** (one `docs/` section each, cross-referenced to the
      named routines): file processing → flight dynamics → drawing → enemy AI →
      UI/menus → sound. Reuses the completed naming campaign as the index.

## E3 — Oracle harness (before large-scale implementation)

- [ ] Define comparison granularity: **numeric state vectors per frame/step**
      (positions, angles, HUD values) rather than pixels, initially.
- [ ] Capture golden traces from the original: the **harvester**
      (`src/dosbox-staging/build/falcon`, `FALCON_TRACE`) already boots the game
      — record input sequences → state dumps for chosen scenarios.
- [ ] OCaml test harness: replay the same inputs, diff against golden, report
      per-value mismatches with routine/ea attribution.
- [ ] Keep Track D parked: no libdosbox/masm2c work needed for this — the
      existing staging harvester + memdumps suffice; revisit only if granularity
      is insufficient.

## E4 — Subsystems, in dependency order

| # | Subsystem | Depends on | Oracle |
|---|-----------|-----------|--------|
| 1 | Fixed-point math | — | unit (spec) |
| 2 | Data records/entities (structs) | 1 | file bytes |
| 3 | File I/O + formats | 2 | file bytes |
| 4 | **Flight dynamics** (`aircraft_motion_step`, `pos_*`) | 1–3 | golden traces |
| 5 | Game loop / input / events (`main_frame_update_loop`, `key_*`) | 4 | traces |
| 6 | Enemy AI / behaviour (`farobj_behavior_dispatch_step`, scripts) | 4–5 | traces |
| 7 | Rendering (draw algorithms, HUD, 3D view) | 1–6 | frame/VRAM compare — **last, hardest** |
| 8 | Sound (AdLib/SB, `FALCON3.SMP`) | 5 | port-level later |
| 9 | Menus/UI (R17/R32 families) | 5 | interaction traces |

Each subsystem passes the convergence criteria before moving on (struct
`confirmed` + write-up + implemented + behaviour-checked).

## E5 — Assembly & running

- [ ] **Headless core first**: mission tick-loop with rendering stubbed —
      compare long traces (cheapest meaningful "it runs").
- [ ] SDL3 front end (rendering/audio/input) once E4-7 lands.
- [ ] Original assets used as-is (parsers from E1/E2-3 read `game/` directly).

## Milestones

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| ME1 | ~1 week | `rebuild/` scaffolded + first DAT/IDX (or weapon BIN) parser green in `dune test`, struct `confirmed` |
| ME2 | ~2–3 weeks | `Fixed` module + fixed-point spec; memory-semantics write-up; structs.yaml backlog promoted; oracle harness v1 (golden trace captured + replay diff) |
| ME3 | ~1–2 months | Flight-dynamics slice reproduces original numeric trajectories from golden traces |
| ME4 | — | Headless core loop running long traces clean (loop/input/AI/dynamics) |
| ME5 | — | Rendering + sound + UI: game visibly playable |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| OCaml/Windows tooling friction | opam native Windows is mature; keep `dune test` trivial so toolchain breakage is obvious early |
| Oracle coverage gaps (traces only cover seen scenarios/segments) | start unit-level (file bytes, math spec) where possible; widen scenarios as needed — harvester already proven |
| Formats not yet decoded (e.g. tail compression, finding 31) | E1 picks *self-verifying on-disk* formats; unknown formats don't block |
| Behaviour divergence drift | golden traces pinned per subsystem; every slice re-runs prior diffs |
| Rendering fidelity is subjective | deliberately last; VRAM/frame compare via memdumps instead of eyeballing |
| Knowledge loss to the IDB | canonical-text rule enforced; `naming.py check` in gates |

---

---

# Legacy plan (Phases 0–5: the Tracks A–D era — retained as history)

> **Mostly historical.** Phases 0–2 = Track A/B foundations (still valid, largely
> done). **Phase 3 (subsystem RE & registry) still feeds Track E** — it is now
> E2's backlog. **Phase 4 (C porting & splice) is superseded by Track E** as the
> rebuild goal; Track C remains an optional byte-fidelity side check, and its
> Ghidra items were never adopted (see `docs/pipeline.md`).

## Phase 0: Foundation (DONE ✅)
- [x] Fresh IDA Pro 9.1 headless snapshot of FALCONCD.EXE
- [x] RTLink 18-byte directory parsed, 9 overlay groups mapped with 16-bit segment bases
- [x] Toolchain evidence documented (not MSC 6.0, RTLink/Plus, PKWARE DCL, C+ASM)
- [x] Prior art cataloged (DOSBox dumps, limitations)
- [x] Status, structures, toolchain docs written

## Phase 1: Overlay Decoding & Coverage (1-2 weeks)

### 1.1 Record Format Decoding ✅
- [x] Decode record headers in tail (bytes before `A` data)
- [x] Map fixup tables (related to field `B`) - 1569 entries, 14 types
- [x] Determine if records are contiguous per segment or scattered
- [x] Verify 39-record C=0x1D group (0x569F, 64 KB span) layout

### 1.2 Full Overlay Mapping ✅ (partial)
- [x] Place all 70 records at correct runtime offsets (1569 fixups applied)
- [x] Run autoanalysis on each overlay segment - 22 overlay functions found
- [ ] Target: >2000 functions total, >200 KB code coverage
- [ ] Identify overlay subsystems (graphics, sound, sim, UI, etc.)

### 1.2b Overlay ground-truth rebuild (findings 16–21) ✅ 5/5 core done
- [x] Re-derive record schema — gunship_2000 discovery_log (finding 17),
      validated on Falcon rows idx7/idx1
- [x] Validate file base per row — w2×16 chain + fixup scanner (finding 18);
      **cluster-B (rows 50–69) found at B0=0xFFFA0 (finding 20)** — all 70 placed
- [x] Runtime placement model solved: block=[(0x1000+w0)<<4, +span×16), transient
      overlap, thunk word = row index (finding 18)
- [x] **Rebuild IDB overlay segments** — 68 segments / 1,053,376 B (findings 19/20)
- [x] **Function discovery + classification** — **192 overlay fns (was 22-wrong),
      1,007 total; C-class 97** (findings 19/20)
- [x] **Fixup application** — 25,222 × +0x1000 applied, byte-guarded (finding 21);
      caveat: dominant far-ptr type verified, ~14 types exist (recheck per-type)
- Open (follow-ups, not blocking): 10 unresolvable thunk entries; clip-shadow
  fixups (177) skipped by design; exotic fixup types; segment display names

### 1.3 Thunk → Record Resolution ✅
- [x] Link thunk table IDs to 18-byte dir `id` to record `off`
- [x] Build call graph: resident → overlay entry points (86 thunks mapped)
- [ ] Verify overlay unload/reload semantics

### 1.4 PKWARE Asset Extraction ✅
- [x] Assets already unpacked in `game/` directory (DISPLAY.DAT, ARMSDATA\*.DAT, etc.)
- [x] PKWARE strings in EXE are just library copyright + Huffman tables
- [ ] Decompress with PKWARE DCL if needed for runtime analysis
- [ ] Parse asset formats (palettes, sprites, map data, instrument art)

## Phase 2: Porting Setup & Library Matching (1 week)

### 2.1 MSC 5.1 Environment Setup ✅
- [x] Set up DOSBox + MSC 5.1 toolchain (from `f19re` reference)
- [x] Verify `CL.EXE` / `LINK.EXE` produce compatible objects
- [x] Test object-to-EXE roundtrip for a small test function

### 2.2 Library Matching
- [ ] Extend `libscan.py` with MSC 5.1 libraries (from `f19re` toolchain)
- [ ] Run against resident image and overlays
- [ ] Identify any linked CRT modules (likely custom/none)

### 2.3 Reproducible Build Environment
- [ ] Document DOSBox + MSC 5.1 + LINK versions
- [ ] Create `compile_falcon.bat` / `compile_falcon.py` (cf. `gunship_2000/scripts/compile_msc6.py`)
- [ ] Verify object-to-EXE roundtrip for a small test function

## Phase 3: Subsystem RE & Registry (2-3 weeks)

### 3.1 Core Subsystems (priority order)
1. **Overlay Manager** (resident 0x1AA3:0x0590) — RTLink interface
2. **Video/Renderer** — cockpit, HUD, 3D view, palette management
3. **Input/Joystick** — calibration strings at 0x67B00, INT 15h AH=84h
4. **Simulation Loop** — entity update, physics, AI
5. **Mission/Menu System** — state machines, save/load
6. **Sound/Music** — `FALCON3.SMP`, AdLib/SB drivers
7. **Asset Pipeline** — PKWARE decompression, DAT parsing

### 3.1b Embedded-data parser RE (see docs/pipeline.md "Parser RE")
- [ ] Read the RTLink loader/dispatch code (proves our static struct decodings)
- [ ] Find DAT-format parsers via string xrefs (`ARMSTABL.DAT`, `DISPLAY.DAT`, mission/save/ACMI)
- [ ] Document each format in `docs/structures.md` → each parser is a porting target

### 3.1c Routine classification (drives all porting)
- [ ] Classify all 839 functions: C-compiled (`ENTER`/consistent frames) vs hand-ASM vs data
- [ ] C-compiled set = Track B port targets; hand-ASM set = transcribe to `.asm`

### 3.2 Registry YAML (per `gunship_2000/registry/`)
- [x] `game_knowledge.yaml` — game systems from manual (modes, weapons, controls)
- [ ] **Per-routine schema** (convergence ledger): `{ea, ida_name, class, hypothesis, port_status, port_file}` — renames land in registry AND C files
- [ ] Per-file: `FALCONCD.EXE.yaml`, `HORNETCD.EXE.yaml`, `MIGCD.EXE.yaml`
- [ ] Per-overlay: `OVL_1E10.yaml`, `OVL_569F.yaml`, etc.
- [ ] Data structures: `entity_t`, `vehicle_t`, `mission_t`, `cockpit_t`, etc.

### 3.3 Cross-Reference & Call Graph
- [ ] Full call graph from `start` through overlay thunks
- [ ] Identify global variables (DS-relative, EMS/XMS handles)
- [ ] Document segment aliasing (CS/DS/EMS/XMS views)

## Phase 4: C Porting & Splice Rebuild (4-6 weeks)

Convergence model (see `docs/pipeline.md` "Convergence Model"):
**Track B** (per-routine C ports, registry renames accumulate knowledge) ↔
**Track 1** (splice verified bytes into original EXE + `mzdiff` proves no drift).
Note: no RTLink binary ⇒ classic relink impossible; splice-in-place replaces it.

### 4.0 Ground-truth infrastructure
- [ ] IDA full-listing export (`.lst`) → feeds `mzmap` + asm-skeleton generator
- [ ] Routine classification pass (3.1c) → port set vs transcribe set
- [ ] Batch portcheck driver (`scripts/build_track2.py`-style) + pass/fail metric
- [ ] Wire Ghidra 16-bit decompile (adapt gunship's `ghidra_dump_to_lst_final.py`) for draft C

### 4.1 Function porting loop
For each major function:
1. Draft C (Ghidra decompile + manual reading); ASM routines transcribed instead
2. Compile with MSC 5.1 (`/AL`, far) → portcheck byte-verify
3. Record in registry: hypothesis name + status; rename in C file
4. Splice into EXE copy (`tools/splice.py`), run `mzdiff` (WSL, shared with gunship)

### 4.2 Assembly Stubs
- Keep hand-written ASM for: interrupt handlers, BIOS/DPMI calls, tight loops
- Document calling convention for C↔ASM boundary

### 4.3 Splice verification (Track 1)
- [ ] `tools/splice.py`: patch verified routine bytes at `hdr + (ea - 0x10000)`
      (guard: refuse if existing bytes ≠ IDA ground truth)
- [ ] `mzmap FALCONCD.EXE` → map once; `mzdiff` original vs spliced after each batch
- [ ] Functional test in DOSBox: menus, instant action, joystick

### 4.4 Full coverage milestone
- Byte-identical splice covering 100% of resident code segments;
  RTLink header/tail remain verbatim from original (= ground truth by construction)

## Phase 5: Variants & Extras (1 week)

- [ ] HORNETCD.EXE / MIGCD.EXE diff analysis (likely same code, different assets)
- [ ] RESETALL.EXE — Borland C++ 1991, separate tool
- [ ] FALCON3.SMP — sound driver format
- [ ] Multiplayer/serial/null-modem code (if present)

## Milestones

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| M1: Overlay decode | Week 2 | All 70 records placed, functions found |
| M2: MSC 5.1 env + libs | Week 3 | Confirmed build env + libscan matches |
| M3: Registry v1 | Week 5 | `registry/*.yaml`, `game_knowledge.yaml` |
| M4: First C port | Week 7 | One subsystem ported, verified |
| M5: Splice convergence | Week 12 | 100% resident code splice-verified + `mzdiff` clean + runs in DOSBox |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Overlay format too complex | Focus on resident + largest overlays first; asset extraction separate |
| No 16-bit decompiler | Use Ghidra with 16-bit analyzer + manual porting; `f19re` did it |
| MSC 5.1 env setup | Reference `f19re` DOSBox + MSC 5.1 setup; `gunship_2000` has MSC 6.0 |
| EMS/XMS dynamic views | Model as separate segment bases in IDA; document DS aliasing |
| Asset formats undocumented | Extract from memory dumps (`MEMDUMP_*.BIN`) + PKWARE decompress |

## Resources

- `C:\Users\yotam\projects\f19re` — MSC 5.1 rebuild reference
- `C:\Users\yotam\projects\gunship_2000` — RTLink overlay tools, registry templates
- `C:\Program Files\IDA Professional 9.1\idat.exe` — headless analysis
- `C:\tools\ghidra\ghidra_12.0_DEV` — 16-bit decompilation aid
- DOSBox + MSC 5.1/6.0/Borland installs (from `gunship_2000/tools/msc6.0`)