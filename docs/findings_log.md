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

## 2026-10-11 13 - Classification pass over all 839 functions
Status: CONFIRMED (heuristic, confidence-tagged)

`tools/classify_routines.py` → `analysis/ida_falconcd/classification.json`.
Counts: **ASM 622 (74%), C 83 (9%), DATA 65 (7%), LEAF 62 (7%), NEARTHUNK 7**.
- `C` = ENTER prologue with proper encoding (`c8 NNNN 00`, level 0) or frame+LEAVE.
  65 resident C functions decode as genuine MSC 5.1 code (arg pushes `[bp+6]/[bp+8]`,
  `59 59` caller cleanup, `[bp-2]/[bp-4]` return-pair stores).
- Resident C smallest → first real port queue: `sub_1A6D4` (44 B, ea 0x1A6D4),
  then sub_19CB0 (55 B), sub_17AD4 (61 B)… full list in classification.json.

## 2026-10-11 14 - Frameless LEAF families dissected (capstone, 16-bit)
Status: CONFIRMED

Disassembled the frameless small functions; four distinct families:
1. `b8 xx xx cb` — **ret const → C-portable** (sub_16FDD, sub_2CB6E verified).
2. `2e a0/a1/a2/a3 xx xx cb` — `mov ax, cs:[X]` / `mov cs:[X], al` — **CS-relative
   near-data accessors** (hand-ASM: small data tables embedded in the code segment;
   MSC 5.1 large model emits DS-relative, so NOT C-portable as written). ~13 routines.
3. `2e ff 1e xx xx cb` — `lcall cs:[table]; retf` — **indirect far dispatch stubs**
   (call through CS function-pointer table, then far-return). ~15 routines.
4. `e8 01 00 cb` (7×) — `call next_func; retf` — **far→near trampoline**: a far entry
   stub that near-calls the *following* near function (which ends `c3`), then retf.
   Layout `[far stub][near function]`. Structural, NOT C. Classified `NEARTHUNK`.
Also seen: `sub_25741`-family `mov al, cs:[A]; mov cs:[B], al; retf` byte-copy pairs.
Note: IDA names/boundaries for these are placeholder — rename via registry.

## 2026-10-11 15 - Ground truth validated: IDA bytes = raw EXE + MZ relocations (+0x1000)
Status: CONFIRMED — hard proof of `function_bytes.json` correctness

Compared all 839 functions' IDA bytes vs raw file at `hdr + (ea - 0x10000)`:
- **434 identical, 405 differ — and every single difference is a relocated word
  (+0x1000 = load base paragraph) at a position covered by the 2717-entry MZ
  relocation table. 815/815 resident functions fully explained, 0 anomalies**
  (`tools/_validate_relocs.py`; diff dump in `raw_vs_ida_diffs.json`).
- Consequence: `function_bytes.json` = **runtime image at load base 0x10000**; raw EXE
  = link-time base 0. For a routine containing far-pointer words, the two differ by
  exactly +0x1000 at reloc positions.
- **Portcheck TODO**: when comparing compiled `.cod` bytes for routines containing far
  calls (e.g. `9a .. .. 64 1f`), normalize: allow word = raw±0x1000 at reloc positions,
  or compare against raw-EXE + applying relocs. Our two verified routines had no far
  pointers, so this hasn't bitten yet.
- **Splice rule**: patch *unrelocated* (file/link-time) bytes into the EXE copy —
  DOS applies relocations at load. Never splice IDA-relocated bytes.

## 2026-10-11 16 - Overlay layout in the IDB is WRONG; resident validated good
Status: CONFIRMED (superseded the "maybe garbage decode" phrasing) — remediation required

**Resident: 815/815 functions = raw EXE + MZ relocations (+0x1000/word at exactly the
2717 reloc positions). Zero unexplained. Resident bytes are trusted ground truth.**

Overlay investigation (artifacts: `ida_record_bytes.json`, `ida_overlay_dump.json`,
`tools/dump_record_bytes.py`, `tools/dump_overlay_ranges.py`, `tools/_compare_records.py`):

1. Raw record payloads (from `rtlink_records.json`) DO exist in the IDB — but at
   **cluster bases 0x2D7B4 / 0x660A4 / 0x2F492** (content = base + tail_off, records in
   tail-file order), **not** at runtime positions. E.g. record id=56 (seg 0x569F,
   tail 0x1174) found at 0x67218 = 0x660A4+0x1174, while the runtime formula gives
   0x67B64 — whose content is unrelated tail bytes.
2. Content AT runtime-correct positions comes from **wrong tail offsets**: the bytes at
   id=8's runtime spot (0x73271 = (0x1000+0x5CD9)<<4 + 0x64E1) are actually tail bytes
   at tail_off 0xD1CD (file 0x2CD1E), not record 8 (tail 0x64E1).
3. **~30 of 70 record payloads not found anywhere** in the dumped overlay ranges.
4. The placement formula itself is now suspect: applying it to seg-0x569F record id=32
   (tail 0xC5DB → 0x72FCB..0x73753) **overlaps** seg-0x5CD9's record id=8
   (0x73271..0x734DA). Either some group's offsets are group-relative (not
   tail-absolute), or a 64-bit wrap/group-origin rule exists — must re-derive from
   primary anchors (thunk `ljmp seg:off` targets + 4-byte tail directory), not from the
   earlier analysis scripts (game_knowledge ranges were derived from the same pipeline
   and may share its errors).
5. Fixup parse output is also suspect: `type_counts` contain values like 49757/64070,
   and implausible splits (record 55: code 47 B / fixup 1975 B) — the "1569 entries,
   14 types" decode needs re-derivation from primary data
   (`docs/overlay_fixups.md` hypotheses are NOT proven).
6. Old-content clusters also mean previous overlay function discoveries (22 functions,
   joystick strings placement) may sit at wrong addresses.

**Consequence**: overlay function bytes in `function_bytes.json`/classification are
untrusted (the 18 "C"-class overlay functions decode as nonsense: negative ENTER
levels, `lidt`, `hlt` — while the 65 resident C functions decode perfectly).

**Remediation plan (ordered)**:
1. Re-derive runtime placement from primary anchors: thunk table `ljmp seg:off`
   (stored segs are pre-relocation; runtime = stored + 0x1000), MZ relocation list,
   4-byte tail directory (51 entries), 18-byte dir `seg`+`tail_off`.
2. Rebuild IDB overlay segments: write raw tail record bytes at verified placements,
   discard all old overlay content, re-run analysis.
3. Re-decode fixup format from primary bytes; validate each applied word against
   expected far-pointer semantics before trusting it.
4. Re-run classification + function discovery on rebuilt overlays; only then trust
   overlay `function_bytes`.

---
(append new findings below)
