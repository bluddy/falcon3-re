# Falcon3 Decompilation Plan

> **Knowledge capture** (see `docs/pipeline.md` "Knowledge Capture Protocol"):
> log every finding/disproval in `docs/findings_log.md` (append-only),
> keep per-routine state in `registry/routines.yaml`,
> byte-level formats in `docs/structures.md`, renames+comments in `src/` files.

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