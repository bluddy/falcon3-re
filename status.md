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

## Immediate Next Steps

1. **Process overlay fixups** — decode record headers/fixups to place all 70 records correctly (currently only record data `A` bytes mapped).
2. **Extract PKWARE assets** — `DISPLAY.DAT`, `ARMSDATA\*.DAT` from tail for mission/cockpit data.
3. **Full overlay mapping** — apply fixups to all 70 records → re-run IDA snapshot → target >2000 functions, >200 KB code.
4. **Map thunk→record→function** — link thunk table IDs to overlay records to entry points.
5. **Port MSC 5.1 libraries** — extend `libscan.py` with MSC 5.1 libs (from `f19re` toolchain).

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
- `analysis/ida_falconcd/overlays.json` — RTLink directory parsed
- `docs/toolchain.md`, `docs/structures.md`, `docs/prior_art.md`