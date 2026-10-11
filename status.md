# Falcon3 Decompilation Status

**Last updated**: 2026-10-11 (session 5, same night — see Time Log; always bump + append row)
**Branch**: master
**Snapshot**: `analysis/ida_falconcd/FALCONCD.EXE.i64` (IDA Pro 9.1 headless)

## Time Log

| Date/time | Elapsed since prev | What changed |
|-----------|--------------------|--------------|
| 2026-10-10 (evening) | — | Initial status: fresh IDA snapshot, toolchain ID, RTLink decode |
| 2026-10-11 (day) | ~1 day | Portcheck pipeline; manual → game_knowledge.yaml; function_bytes ground truth |
| 2026-10-11 (late) | same day | pipeline.md (convergence/mzdiff); knowledge protocol + findings log 1-12; first 2 verified routines |
| 2026-10-11 (night) | same day | Findings 13-16: classification 839, LEAF families, resident 815/815 validated, **overlay IDB layout proven wrong** + remediation plan 1.2b |
| 2026-10-11 (late night) | same day | **Finding 17: RTLink record schema cracked via gunship_2000** (w2×16 fixup base, flags 0x04/0x01, thunk=index, 4-byte-dir=misread fixup table); loader disassembled (`sub_2AFBD`/`sub_2AC4C`); structures.md + plan 1.2b updated. Open: per-row file base validation → IDB rebuild |
| 2026-10-11 (deep night) | same day | **Finding 18: runtime placement model SOLVED** — block=[(0x1000+w0)<<4, +span×16), same-w0 overlap (transient), thunk word=row index (63/63 self-consistent), paras containment 250/250; w2×16 base 61/70 + scanner 46/70; small-w2 rows=data-first. plan 1.2b: 2/5 items done. Next: `rebuild_overlay_segments.py` |
| 2026-10-11 (session 3) | same day | **Finding 19: overlay IDB REBUILT** — 48 segments / 778,640 B (8 real + 40 synthetic; cluster-B 50–69 unplaced), 184 thunk entries marked → **141 overlay functions, 956 total**, C-class 65→98; `function_bytes.json` re-extracted (live); plan 1.2b 4/5 (fixup application + cluster-B remain) |
| 2026-10-11 (session 4) | same day | **Findings 20+21: cluster-B FOUND (B0=0xFFFA0)** — all 70 rows placed → 68 segments / 1,053,376 B; **fixups applied: 25,222 × +0x1000** byte-guarded; entries 250 → **192 overlay fns, 1,007 total**; C=97 with relocated DGROUP. **plan 1.2b 5/5 core done** |
| 2026-10-11 (session 5) | same day | **Finding 22: COMPILER REVISED — Borland C++ 2.0 `bcc -c -ml -1 -O`** (user installed; enter/leave = BC; MSC 5.1/6.0 re-tested → no enter, DISPROVEN for C); **sub_1A6D4 44B MATCH** end-to-end via new portcheck `--cc bcc` + `obj_extract.py`; toolchain.md rewritten. C-port queue resumed |

## Executive Summary

Falcon3 (FALCONCD.EXE + variants) is a **DOS 16-bit far/large model** game using **RTLink/Plus** overlay linker and **PKWARE DCL** compression. The codebase is **Microsoft C 5.1 (C modules) + hand-written ASM** with **no standard CRT** (not MSC 6.0, not Borland). The EXE is 1.37 MB with a 118 KB resident image and 1.2 MB overlay/asset tail.

**Resident ground truth is PROVEN**: all 815 resident functions = raw EXE + MZ relocations (findings 15). **Overlay ground truth COMPLETE (plan 1.2b 5/5)**: RTLink schema + placement model (17/18), IDB rebuilt — all 70 rows placed incl. cluster-B at B0=0xFFFA0 (19/20) — 68 segments / 1.05 MB, **25,222 fixups applied** byte-guarded (21), **192 overlay functions → 1,007 total**, C-class 97 with relocated far pointers. Follow-ups: 10 straggler entries, exotic fixup types, then resume C-port queue.

## Verified Facts

| Item | Status | Evidence |
|------|--------|----------|
| Linker | ✅ RTLink/Plus | Strings, 18-byte directory, thunk table |
| Compression | ✅ PKWARE DCL | Strings, `PK\x03\x04` in tail |
| CRT | ❌ MSC 6.0 | No `B430CD21` — but inconclusive: no CRT embedded at all (finding 22) |
| CRT | ❌ Borland CRT | No "Borland" strings — same fallacy (strings come from absent CRT) |
| Compiler (C) | ✅ **Borland C++ 2.0** (`bcc -c -ml -1 -O`) | **sub_1A6D4 44B byte-exact match**; enter/leave/imm0/or-si codegen (finding 22) |
| ~~Compiler (C)~~ | ~~MSC 5.1~~ | **DISPROVEN for C** — version-verified 5.10 + 6.00ax emit no enter under any flag (finding 22) |
| Compiler (ASM) | ✅ Hand-written | 84 × `558BEC` with variable register saves (unaffected) |
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