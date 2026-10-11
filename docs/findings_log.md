# Findings Log (append-only)

The chronological record of everything we learn about Falcon 3.0's code, data and
toolchain. **Append-only**: when a hypothesis is disproved, do not delete the entry —
mark it `DISPROVEN` and add the correction. The registry YAMLs hold the *current*
state; this log holds the *history* so reasoning and dead ends are never lost.

Format: `## <date> <seq> - <title>` with a `Status:` line
(`CONFIRMED` / `HYPOTHESIS` / `DISPROVEN` / `SUPERSEDED`).

Entries cross-reference artifacts (`registry/`, `docs/structures.md`, `analysis/`, commits).

---

## 2026-10-10 01 - Toolchain: Microsoft C 5.1 + hand-written ASM (NOT MSC 6.0/Borland)
Status: CONFIRMED (for C modules; ASM is hand-written)

Evidence: 30 `ENTER` (opcode C8) prologues with MSC 5.1-style stack sizes; 84 manual
`55 8B EC` prologues with inconsistent register-save order (hand-tuned); **0** `83 EC`
(`sub sp`) standard-C frames; no `B4 30 CD 21` (MSC 6.0 signature); no CRT error
strings; no Borland strings in main EXEs. RESETALL.EXE separately = Borland C++ 1991.
Details: `docs/toolchain.md`.

## 2026-10-10 02 - Linker: RTLink/Plus, 70 overlay records, 9 segment groups
Status: CONFIRMED

Strings ("Internal error in .RTLink(R)/Plus run-time code.", eov000x, reload stack).
18-byte directory at file 0x1E24F; thunk table 10-byte stubs at file 0x1EBAF (86
thunks); 4-byte tail directory (51 entries) at file 0x1FB61. Structs in
`docs/structures.md`; group summary in registry `FALCONCD.EXE.yaml`.

## 2026-10-10 03 - Fixup tables: 1569 entries, 14 types, applied into IDA
Status: CONFIRMED (static decode); loader-code confirmation pending (Parser RE)

Parsed from record tails (`tools/extract_fixups.py` → `analysis/.../fixup_tables_*.json`),
applied via `tools/apply_fixups_ida.py` so overlay code sits at runtime paragraphs.
Types seen: 0x33ae, 0x400c, 0x39ab, 0x3e52, 0x393c, 0x3de4, 0x3f25, 0x3bdd, 0x3d81,
0x38db, 0x3dad, 0x3fd8, 0x3fd2, 0x06c7. Semantics per type: HYPOTHESIS (see
`docs/overlay_fixups.md`), proof = disassembling the applier.

## 2026-10-10 04 - Compression: PKWARE DCL; assets already unpacked
Status: CONFIRMED

PKWARE copyright + patent strings, `PK\x03\x04` in tail. Asset files already extracted
in `game/` (DISPLAY.DAT, ARMSDATA\*.DAT). Per-asset stream framing: NOT YET MAPPED.

## 2026-10-10 05 - Fresh IDA Pro 9.1 snapshot replaces DOSBox-dump IDBs
Status: CONFIRMED

Headless `idat.exe` on a copy of FALCONCD.EXE (never opened in interactive IDA — it
holds GS2.exe.i64). 839 functions (817 resident + 22 overlay), 83 KB code.
Artifacts: `analysis/ida_falconcd/`.

## 2026-10-11 06 - IDA bytes ≠ raw-EXE bytes (relocation trap)
Status: CONFIRMED — SUPERSEDES naive file-offset comparison

Raw reads at `hdr + (ea - 0x10000)` show **pre-relocation** bytes: DOS applies 2717 MZ
relocations at load (segments 0x1AA3, 0xE56, 0x80F, …) and IDA applies them too.
Ground truth = `analysis/ida_falconcd/function_bytes.json` (extracted from the IDB via
`tools/extract_ida_bytes.py`). `portcheck_falcon.py` now prefers it over raw reads.
Symptom if forgotten: portcheck "expected" bytes look like garbage at correct offsets.

## 2026-10-11 07 - Portcheck pipeline working (C → DOSBox-X MSC 5.1 → .cod → compare)
Status: CONFIRMED

Compile line: `rbin\cl /c /AL /Gs /Fc<NAME8> /Ic:\include <file.c>` in
`dos_compilers\msc5.1`. `.COD` lands in MSC root, **not** source dir. C function name
must equal IDA routine name (parser searches `_name PROC`); filename itself is 8.3
truncated (`sub_16FDD` → `sub_16FD.c` / `SUB_16FD.COD`) but the function name inside
can be 9 chars.

## 2026-10-11 08 - First verified game routines: sub_16FDD, sub_2CB6E
Status: CONFIRMED (byte-identical)

- `sub_16FDD` (seg 0x16FD, ofs 0xD, 4 B): `b8 01 00 cb` = `return 1;` ✅
- `sub_2CB6E` (seg 0x2CB6, ofs 0xE, 4 B): `b8 ff ff cb` = `return -1;` ✅
Key: `/AL` large model + `int far func(void)` (qualifier after return type; MSC 5.1 has
no `__far` — C2054; `far int` order — C2062). Without far, compiler emits `RET` (C3)
but originals use `RETF` (CB).
Registry: `registry/routines.yaml`. Sources: `src/sub_16FDD.c`, `src/sub_2CB6E.c`.

## 2026-10-11 09 - sub_10340 is hand-written ASM, not C
Status: CONFIRMED (disproves "small = C-compiled" assumption)

IDA bytes `d1 e3 2e 89 87 25 00 cb` = `sal bx,1; mov cs:[bx+25h],ax; retf` — ad-hoc
logic, no C prologue. (An earlier raw-read suggestion `a1 0c 00 ab…` was the
relocation trap from Finding 06.) Lesson: classify before porting; size alone proves
nothing.

## 2026-10-11 10 - mzdiff/mzmap reusable (not game-specific)
Status: CONFIRMED

WSL binaries v1.0.20 at `gunship_2000/tools/f19re/mzretools/debug/{mzdiff,mzmap}` (the
GS2000 doc's `build/` path is stale). Generic MZ tools; only `.map` files are per-EXE
(`mzmap` generates them, can ingest an IDA `.lst`). Both verified running.

## 2026-10-11 11 - Track 1 will be splice-in-place, not relink
Status: CONFIRMED (design decision)

No RTLink/Plus binary ⇒ classic relink impossible. Instead: original EXE = immutable
scaffold (header/relocs/RTLink tail verbatim), verified routine bytes patched at
`hdr + (ea - 0x10000)` under a byte-identity guard ⇒ relocations stay valid by
construction. Whole-image check via `mzdiff`. Design + gap analysis:
`docs/pipeline.md` "Convergence Model".

## 2026-10-11 12 - Manual extracted; game knowledge in registry
Status: CONFIRMED

`game/manual.pdf` (254 pp) → `manual_full.txt` → `registry/game_knowledge.yaml`
(379 lines): modes, campaign structure, pilot abilities, weapons, HUD/REO/DED, ACMI,
file mentions (TOPTEN, *.mis, replay tapes).

---
(append new findings below)
