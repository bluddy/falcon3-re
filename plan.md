# Falcon3 Decompilation Plan

## Phase 0: Foundation (DONE ✅)
- [x] Fresh IDA Pro 9.1 headless snapshot of FALCONCD.EXE
- [x] RTLink 18-byte directory parsed, 9 overlay groups mapped with 16-bit segment bases
- [x] Toolchain evidence documented (not MSC 6.0, RTLink/Plus, PKWARE DCL, C+ASM)
- [x] Prior art cataloged (DOSBox dumps, limitations)
- [x] Status, structures, toolchain docs written

## Phase 1: Overlay Decoding & Coverage (1-2 weeks)

### 1.1 Record Format Decoding
- [ ] Decode record headers in tail (bytes before `A` data)
- [ ] Map fixup tables (related to field `B`)
- [ ] Determine if records are contiguous per segment or scattered
- [ ] Verify 39-record C=0x1D group (0x569F, 64 KB span) layout

### 1.2 Full Overlay Mapping
- [ ] Place all 70 records at correct runtime offsets
- [ ] Run autoanalysis on each overlay segment
- [ ] Target: >2000 functions total, >200 KB code coverage
- [ ] Identify overlay subsystems (graphics, sound, sim, UI, etc.)

### 1.3 Thunk → Record Resolution
- [ ] Link thunk table IDs to 18-byte dir `id` to record `off`
- [ ] Build call graph: resident → overlay entry points
- [ ] Verify overlay unload/reload semantics

### 1.4 PKWARE Asset Extraction
- [ ] Locate `PK\x03\x04` boundaries in tail
- [ ] Extract `DISPLAY.DAT`, `ARMSDATA\ARMSTABL.DAT`, `ARMSmmaa.DAT`
- [ ] Decompress with PKWARE DCL (sibling `gunship_2000` has tools)
- [ ] Parse asset formats (palettes, sprites, map data, instrument art)

## Phase 2: Compiler Identification & Porting Setup (1 week)

### 2.1 Compiler Fingerprinting
- [ ] Build MSC 5.1 / 6.0 / Borland C++ 2.0/3.0 / Watcom test objects
- [ ] Compare prologue/epilogue patterns, register usage, stack frames
- [ ] Test against Falcon3 function samples (large C functions at 0x1AB34, 0x1EA58, etc.)
- [ ] Check library function signatures (memcpy, strcpy, printf-like)

### 2.2 Library Matching
- [ ] Extend `libscan.py` with MSC 5.1 libraries (from `f19re`)
- [ ] Run against resident image and overlays
- [ ] Identify any linked CRT modules

### 2.3 Reproducible Build Environment
- [ ] Document DOSBox + compiler + linker versions
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

### 3.2 Registry YAML (per `gunship_2000/registry/`)
- [ ] `game_knowledge.yaml` — memory map, segment purposes, key variables
- [ ] Per-file: `FALCONCD.EXE.yaml`, `HORNETCD.EXE.yaml`, `MIGCD.EXE.yaml`
- [ ] Per-overlay: `OVL_1E10.yaml`, `OVL_569F.yaml`, etc.
- [ ] Data structures: `entity_t`, `vehicle_t`, `mission_t`, `cockpit_t`, etc.

### 3.3 Cross-Reference & Call Graph
- [ ] Full call graph from `start` through overlay thunks
- [ ] Identify global variables (DS-relative, EMS/XMS handles)
- [ ] Document segment aliasing (CS/DS/EMS/XMS views)

## Phase 4: C Porting & Rebuild (4-6 weeks)

### 4.1 Function Porting Loop
For each major function:
1. Decompile (Hex-Rays not available for 16-bit → manual / Ghidra)
2. Write C equivalent matching stack frame / calling convention
3. Compile with target compiler, diff object (`mzdiff`)
4. Verify in DOSBox

### 4.2 Assembly Stubs
- Keep hand-written ASM for: interrupt handlers, BIOS/DPMI calls, tight loops
- Document calling convention for C↔ASM boundary

### 4.3 Linker Script
- Reproduce RTLink `.LNK` / response file
- Segment ordering, overlay groups, STACK/HEAP sizes
- PKWARE compression step for assets

### 4.4 Full Rebuild Verification
- `mzdiff` original vs rebuilt EXE
- Binary equivalence for code sections (allow timestamps/debug info diff)
- Functional test in DOSBox: missions, menus, sim, joystick

## Phase 5: Variants & Extras (1 week)

- [ ] HORNETCD.EXE / MIGCD.EXE diff analysis (likely same code, different assets)
- [ ] RESETALL.EXE — Borland C++ 1991, separate tool
- [ ] FALCON3.SMP — sound driver format
- [ ] Multiplayer/serial/null-modem code (if present)

## Milestones

| Milestone | Target | Deliverable |
|-----------|--------|-------------|
| M1: Overlay decode | Week 2 | All 70 records placed, functions found |
| M2: Compiler ID | Week 3 | Confirmed compiler + build env |
| M3: Registry v1 | Week 5 | `registry/*.yaml`, `game_knowledge.yaml` |
| M4: First C port | Week 7 | One subsystem ported, verified |
| M5: Full rebuild | Week 12 | Byte-equivalent EXE (modulo timestamps) |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Overlay format too complex | Focus on resident + largest overlays first; asset extraction separate |
| No 16-bit decompiler | Use Ghidra with 16-bit analyzer + manual porting; `f19re` did it |
| Compiler mismatch | Test all period candidates; MSC 5.1 most likely (era 1991-92) |
| EMS/XMS dynamic views | Model as separate segment bases in IDA; document DS aliasing |
| Asset formats undocumented | Extract from memory dumps (`MEMDUMP_*.BIN`) + PKWARE decompress |

## Resources

- `C:\Users\yotam\projects\f19re` — MSC 5.1 rebuild reference
- `C:\Users\yotam\projects\gunship_2000` — RTLink overlay tools, registry templates
- `C:\Program Files\IDA Professional 9.1\idat.exe` — headless analysis
- `C:\tools\ghidra\ghidra_12.0_DEV` — 16-bit decompilation aid
- DOSBox + MSC 5.1/6.0/Borland installs (from `gunship_2000/tools/msc6.0`)