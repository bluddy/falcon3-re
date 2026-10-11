# Falcon3 Decompilation Status

**Date**: 2026-10-10
**Branch**: main (initial)
**Snapshot**: `analysis/ida_falconcd/FALCONCD.EXE.i64` (IDA Pro 9.1 headless)

## Executive Summary

Falcon3 (FALCONCD.EXE + variants) is a **DOS 16-bit far/large model** game using **RTLink/Plus** overlay linker and **PKWARE DCL** compression. The codebase is **Microsoft C 5.1 (C modules) + hand-written ASM** with **no standard CRT** (not MSC 6.0, not Borland). The EXE is 1.37 MB with a 118 KB resident image and 1.2 MB overlay/asset tail.

**Fresh IDA Pro 9.1 snapshot created** — 817 functions, 82 KB code, 9 overlay groups mapped at correct runtime addresses using 16-bit segment bases (allowing CS/DS overlap). This replaces prior DOSBox-dump IDBs which had limited code coverage.

## Verified Facts

| Item | Status | Evidence |
|------|--------|----------|
| Linker | ✅ RTLink/Plus | Strings, 18-byte directory, thunk table |
| Compression | ✅ PKWARE DCL | Strings, `PK\x03\x04` in tail |
| CRT | ❌ MSC 6.0 | No `B430CD21`, no error strings |
| CRT | ❌ Borland | No "Borland" strings in main EXEs |
| Compiler | ✅ **MSC 5.1 (C) + hand-ASM** | **30 `ENTER`, 84 `558BEC`, 0 `83EC`** |
| Code model | ✅ Far/large | 468/839 far, retf, stack args `[BP+6]` |
| Overlays | ✅ RTLink | 70 records, 9 segment groups, thunk dispatch |
| RESETALL.EXE | ✅ Borland C++ 1991 | Copyright string (garbled) |

## Code Coverage

| Region | Functions | Code Bytes | Notes |
|--------|-----------|------------|-------|
| Resident image (seg000-022) | 817 | ~82 KB | Entry, overlay mgr, video, input, core sim |
| Overlay 0x1E10 | 14 | ~1 KB | Large (34 KB), functions found |
| Overlay 0x569F | 14 | ~1 KB | 64 KB span, functions found |
| Overlay 0x5CD9 | 2 | ~1 KB | Small (617 B) |
| Overlay 0x5DFF | 4 | ~1 KB | |
| Overlay 0x5E0B | 1 | ~1 KB | |
| Overlay 0x5E8F | 1 | ~1 KB | |
| Overlay 0x5F6C | 1 | ~1 KB | |
| Overlay 0x606E | 1 | ~1 KB | |
| Other overlay groups | 0 | 0 | Need deeper analysis |

**Total**: 839 functions, 83 KB. Gap: ~1.2 MB tail mostly asset data + unprocessed overlays.

## Portcheck Pipeline ✅
- C source → DOSBox-X + MSC 5.1 (`/AL` large model) → .OBJ + .COD
- .COD parsing → byte extraction
- Compare against `function_bytes.json` (IDA ground truth, fixups applied)

**Tested and working:**
- `hello.c` → `main(){return 0;}` → `b8 2a 00 c3` (mov ax, 42; ret) ✅
- `getans.c` → `get_answer(){return 42;}` → `b8 2a 00 c3` ✅
- **`sub_16FDD` → `b8 01 00 cb` MATCH** (`int far` + `/AL` was the fix) ✅
- **`sub_2CB6E` → `b8 ff ff cb` MATCH** ✅

**Pipeline doc**: `docs/pipeline.md` (modeled on gunship_2000's PIPELINE.md; adds
Track C plan using `mzdiff` from `f19re/mzretools`, plus all naming/near-far gotchas).

## Game Knowledge Base ✅
- Extracted full text from `manual.pdf` (254 pages, 484 KB)
- Added comprehensive sections: game modes, weapons, avionics, aircraft, file formats, controls, campaign structure
- Registry expanded: 158 → 379 lines

## Immediate Next Steps

1. **Identify target functions** from survey.json small functions for verification
   - ✅ `sub_16FDD` (return 1) and `sub_2CB6E` (return -1) verified byte-for-byte
   - ❌ `sub_10340` is hand-written ASM (not C) — port as asm or skip
2. **Write C equivalents** for target functions (filter size ≤ 10, far, nretf=1, C prologues)
3. **Run portcheck** to verify byte-for-byte match; log verified set in registry
4. **Build registry** of verified functions
5. **Port MSC 5.1 libraries** — extend `libscan.py` with MSC 5.1 libs (from `f19re` toolchain)
6. **Track C setup** — copy gunship's `extract_routines.py`/`replace_routines.py`, build `mzretools` for `mzdiff`

## Blockers

- Overlay record format (headers/fixups) not fully decoded → can't map all 70 records cleanly.
- 1.2 MB tail structure unknown beyond 68 KB of records → asset extraction needed.
- No FLIRT signatures for 16-bit far model → manual compiler ID required.
- EMS/XMS memory views not represented in static IDB.

## Reference Projects

| Project | Status | Relevance |
|---------|--------|-----------|
| `f19re` | Full rebuild (MSC 5.1) | Compiler/linker toolchain, portcheck workflow |
| `gunship_2000` | In progress (MSC 6.0) | RTLink overlay extraction, registry YAML, Ghidra placement |

## Artifacts

- `analysis/ida_falconcd/FALCONCD.EXE.i64` — fresh IDA Pro 9.1 DB
- `analysis/ida_falconcd/survey.json` — segments, functions, strings, overlays
- `analysis/ida_falconcd/functions.tsv` — function list for registry
- `analysis/ida_falconcd/function_bytes.json` — **ground truth bytes** (IDA, relocated)
- `analysis/ida_falconcd/overlays.json` — RTLink directory parsed
- `docs/pipeline.md` — full pipeline + convergence model + knowledge capture protocol
- `docs/findings_log.md` — append-only findings history
- `registry/routines.yaml` — per-routine convergence ledger
- `docs/toolchain.md`, `docs/structures.md`, `docs/prior_art.md`, `docs/overlay_fixups.md`