# Falcon 3.0 Reverse Engineering — Complete Pipeline Documentation

## Overview

Two active tracks plus one planned:

| Track | Goal | Method | Status |
|-------|------|--------|--------|
| **Track A** | Analysis & knowledge extraction | IDA Pro 9.1 headless → survey/fixup JSON → registry YAML | ✅ Working (839 functions, 83 KB code, 1569 RTLink fixups applied) |
| **Track B** | Per-routine C ports verified byte-for-byte | C → DOSBox-X MSC 5.1 → `.cod` → byte compare vs IDA ground truth | ✅ Working — **2 game routines matched** (`sub_16FDD`, `sub_2CB6E`) |
| **Track C** | Hybrid rebuild + `mzdiff` verification | IDA listing → UASM asm + C replacements → link → `mzdiff` | ⏳ Planned (borrowed from `gunship_2000`) |

Comparison to sibling projects:

- `f19re` — same compiler (MSC 5.1), full rebuild with `portcheck.py` + `mzdiff`. **Our Track B/C template.**
- `gunship_2000` — same linker family (RTLink/Plus), its `docs/PIPELINE.md` is the template for this file. Track C below is adapted from its Track 2 (`extract_routines.py` → `replace_routines.py` → assemble → link → `mzdiff`).

---

## Knowledge Capture Protocol (MOST IMPORTANT — never lose a learning)

Every finding has exactly one canonical sink. Fill them **as you learn**, and update
them **as you disprove**; the findings log is append-only history, the registries are
current state.

| # | Sink | Holds | Write when |
|---|------|-------|-----------|
| 1 | `docs/findings_log.md` | Chronological history: hypotheses, evidence, confirmations, **disprovals, dead ends** | Every session, append only. Mark disproved entries `DISPROVEN` — never delete |
| 2 | `registry/routines.yaml` + `registry/naming.yaml` | Port ledger `{ea, class, port_status, ...}` + **rename ledger** (ida -> name) | Classify/port/verify a routine; rename via `naming.py` |
| 3 | `registry/game_knowledge.yaml`, `registry/structs.yaml`, `registry/FALCONCD.EXE.yaml` | Game systems, **struct definitions**, file-level facts | Game mechanic decoded / struct fields pinned down |
| 4 | `docs/structures.md` | Byte-level struct **narrative/history** (fields themselves go to registry/structs.yaml) | A format is decoded (even partially - mark what's unverified) |
| 5 | C sources in `src/` | **Renames + comments**: semantic names (via `naming.py apply`), disasm/args/logic annotation headers | As part of porting; renames go through registry/naming.yaml first |
| 6 | ASM listings/transcriptions | **Comments** annotating hand-ASM routines (intent, register roles) | As routines are transcribed/classified |
| 7 | `status.md` | **Bump `Last updated` + append a Time Log row every status change** (so staleness is measurable) | Whenever project state changes meaningfully |

Rules of thumb:
- **Hypothesis made** → registry entry (`class`/`hypothesis`) + findings log line.
- **Hypothesis disproved** → flip the registry value, leave a `notes:` trail, append the
  disproval to the findings log (see Finding 09 for the pattern).
- **Routine verified** → `port_status: verified`, source file kept in `src/`,
  byte recipe noted (e.g. `/AL + int far`).
- **Rename** lands in three places consistently: registry `hypothesis`, the C/ASM file,
  and (if it changes understanding) a findings-log entry.
- Structures never overwrite — extend `structures.md` sections and mark decode status.

---

## Ground Truth & Reproducibility

**Authoritative byte source: `analysis/ida_falconcd/function_bytes.json`** (committed,
text) — per-function bytes *as they exist at runtime* (raw EXE + MZ relocations +
RTLink fixups). `portcheck_falcon.py` compares C output against it. The IDB is the
*analysis* ground truth (boundaries, names, segments, fixups, comments) but is
**binary, local-only, and never committed** — everything that must survive lives in
committed JSON/C/YAML/markdown instead.

| Artifact | Role | In git? |
|---|---|---|
| `game/FALCONCD.EXE` (+variants) | primary raw input | ❌ local (`game/` ignored) |
| `FALCONCD.EXE.i64` (+.id0/.id1/…) | analysis DB: boundaries, names, fixup state, comments | ❌ local (binary, regenerable) |
| `function_bytes.json` | **byte ground truth for portcheck** | ✅ |
| `classification.json`, `overlay_placement.json`, `overlay_entries.json`, `fixups_to_apply.json`, `rtlink_records.json`, `record_fixup_located.json`… | derived analysis state | ✅ |
| `survey.json`, `functions.tsv`, `prologues.json`… | regenerable intermediates | ❌ (ignored, rerun scripts) |
| `src/*.c`, `src/asm/*.asm` | ported code + annotations (protocol sinks 5/6) | ✅ |
| `registry/*.yaml`, `docs/*`, `findings_log.md` | hypotheses + history (sinks 1–4) | ✅ |

### IDB regeneration runbook (fresh clone / lost IDB)

Prereqs: local `game/FALCONCD.EXE`, IDA Pro 9.1 at
`C:\Program Files\IDA Professional 9.1\idat.exe`. Committed JSONs make the host-side
steps unnecessary unless the EXE itself changed.

```
:: 1. fresh analysis (creates survey.json etc.; legacy overlay layout - will be replaced)
idat -A -S tools\ida_snapshot.py       analysis\ida_falconcd\FALCONCD.EXE.i64

:: 2. IDA: rebuild overlays from committed placement + mark entries + fixups + extract
idat -A -S tools\rebuild_overlay_segments.py    analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\_add_missed_fn.py              analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\mark_overlay_entries.py        analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\apply_overlay_fixups.py        analysis\ida_falconcd\FALCONCD.EXE.i64
idat -A -S tools\extract_ida_bytes.py           analysis\ida_falconcd\FALCONCD.EXE.i64

:: 3. host: classification + sanity portcheck
venv\Scripts\python tools\classify_routines.py
venv\Scripts\python tools\portcheck_falcon.py sub_16FDD --source src\sub_16FDD.c --segment 0x16FD --offset 0xD
```
(Host-side regen of the committed JSONs, only if the EXE changed:
`prep_overlay_placement.py` → `prep_overlay_entries.py` → `validate_fixup_semantics.py`,
then steps 2–3.)

**Rules**: any IDB-modifying step → re-run `extract_ida_bytes.py` + `classify_routines.py`
and commit both; names/comments set only in the IDB are conveniences — canonical text
belongs in `src/asm/`, `registry/`, or `docs/` (IDB is never the only copy).
**The IDB is not committed** (binary, `*.i64` ignored): losing it costs one runbook
pass (~6 headless IDA runs), not the knowledge.

### Can this rebuild the binary? (rebuild verdict)

- **YES — code, via splice (Track C).** Every routine is either C-ported
  (byte-verified by portcheck) or will be hand-ASM-transcribed; patched into a
  copy of the original EXE at its file offset. Because patched bytes are
  byte-identical by construction, all 2717 MZ relocations, the RTLink directory
  and the whole 1.2 MB tail remain valid unchanged → the spliced EXE is
  byte-identical over the regenerated fraction. As coverage grows → full image.
  `mzdiff` proves it instruction-by-instruction.
- **From-scratch rebuild (no original EXE)** additionally needs: all data
  (non-function bytes) regenerated, MZ relocation table recomputed, RTLink
  container (directory/thunks/fixup tables) re-emitted, PKWARE assets packed.
  Not required for the splice path; the RTLink linker itself does not exist as a
  binary, so a faithful relink is off the table either way.
- Current code coverage: 16 routines / 846 bytes verified out of ~83 KB resident
  code (≈1%) — the methodology is proven, the volume is the remaining work.

---

## Naming & Annotation System (reproducing IDA's naming layer, outside IDA)

Per the ground-truth rules above, all symbols/annotations live in **committed text**,
never only in the DB:

| Layer | File | Role |
|---|---|---|
| Rename ledger | `registry/naming.yaml` | `ida` (immutable machine ID) → `name` (semantic), kind= function/global/struct/field, notes=why. Single source of truth. |
| Struct annotations | `registry/structs.yaml` | Machine-readable structs: size, fields (offset/size/type/comment), status confirmed/hypothesis. Validated by `check`. |
| Globals inventory | `analysis/.../data_symbols.json` | 1,968 data symbols: `ida_name` immutable, `name` = rename or null |
| Function bytes | `analysis/.../function_bytes.json` | keys = IDA names forever; per-entry `name` field mirrors the ledger |
| C sources | `src/*.c` | **renamed to semantic identifiers** + annotation comments (see below) |
| ASM family notes | `src/asm/*.asm` | ida names + disasm + family intent (generated members, hand headers) |
| Port status | `registry/routines.yaml` | ea + port metadata; `hypothesis` must equal ledger `name` (check enforces) |

### Tooling: `tools/naming.py`

```bash
python tools/naming.py list                # show ledger
python tools/naming.py resolve <name>      # ida <-> semantic (either direction)
python tools/naming.py apply [--dry-run]   # propagate ledger -> C/asm/JSON/...
python tools/naming.py revert <ida_name>   # drop a rename, restore ida text
python tools/naming.py check               # consistency (exit 1 = broken); run in CI/pre-commit
python tools/naming.py push-ida            # write semantic names into the IDB (headless)
python -m unittest discover -s tests       # test suite for the whole system (21 tests)
```

- `portcheck_falcon.py` resolves through the ledger: `portcheck sub_19D25` and
  `portcheck kb_field_get_23` are equivalent (extract with C name, compare vs IDA name).
- Renames are **word-boundary** replacements (safe for `sub_1` vs `sub_12`), applied
  to `src/**.c` and `src/asm/**.asm` only — `docs/`/findings keep historical IDA names
  on purpose (ea anchors them).
- `push-ida` is safe because `extract_ida_bytes.py` keys functions by the *previous
  extract's* keys (ea map), so IDB display-name changes never shift JSON keys or
  drop `name` fields. **Convention: never rename ad-hoc in the GUI** — add to the
  ledger first, then `push-ida` (GUI renames only for non-ledger cosmetic names).

### Annotation conventions (per knowledge-capture sinks 5/6)

- **C files** (`src/*.c`): semantic names for functions/globals/locals (applied via
  `apply`); **header comment** = disasm walkthrough, semantics, byte-exact codegen
  recipe (see `src/kb_unit_19CB0.c`); **arguments**: named in the signature (they
  are real C params — no excuse); **logic**: comment blocks explaining *why*, with
  ea references (`@ 0x19CB0`); **local blocks**: descriptive local names +
  `/* loop: ... */` comments in place of IDA-style labels.
- **ASM family files** (`src/asm/*.asm`): family-level intent headers; per-routine
  comments carry args (`; args: [bp+6]=key`) and register roles; labels as
  `name:` where flow needs naming. Track-C per-routine transcripts come later.
- **Structs**: narrative + history in `docs/structures.md`; the *fields themselves*
  go in `registry/structs.yaml` (so tools and future IDA-struct-push can consume them).

---

## Repository Structure (Key Paths)

```
C:\Users\yotam\projects\falcon3\
├── game/
│   ├── FALCONCD.EXE                # Primary target (1,373,671 B)
│   ├── HORNETCD.EXE / MIGCD.EXE    # Variants (same structure, different assets)
│   ├── RESETALL.EXE                # Borland C++ 1991 utility (separate toolchain)
│   ├── FALCON3.SMP                 # Sound/music (format TBS)
│   ├── manual.pdf                  # 254-page flight manual → manual_full.txt
│   └── DISPLAY.DAT, ARMSDATA\*.DAT # PKWARE-packed assets (already unpacked)
├── analysis/
│   └── ida_falconcd/
│       ├── FALCONCD.EXE.i64        # IDA Pro 9.1 DB (fixups applied) — GROUND TRUTH
│       ├── FALCONCD.EXE            # Copy of original (IDA input)
│       ├── survey.json             # 839 functions, segments, strings, overlays
│       ├── functions.tsv           # ea/end/size/name/far/thunk/nret/nretf
│       ├── function_bytes.json     # Per-function bytes FROM IDA DB (relocated!)
│       ├── overlays.json           # RTLink 18-byte directory parsed (70 records)
│       ├── rtlink_records.json     # Record data + fixup tables (1569 entries)
│       ├── fixup_tables_*.json     # Parsed fixup tables (14 types)
│       ├── prologues.json / epilogues.json
│       └── *.log                   # IDA headless run logs
├── tools/
│   ├── ida_snapshot.py             # IDA headless: full analysis + survey export
│   ├── apply_fixups_ida.py         # Applies 1569 RTLink fixups inside IDA DB
│   ├── extract_ida_bytes.py        # IDA → function_bytes.json (ground truth)
│   ├── portcheck_falcon.py         # Track B: single-routine C verify
│   ├── compile_msc51.py            # Standalone MSC 5.1 compile wrapper
│   ├── extract_fixups.py           # RTLink fixup table extraction
│   ├── analyze_all_records.py      # Record/segment-group analysis
│   ├── rtlink_scan.py              # RTLink directory scanner
│   ├── libscan.py                  # FLIRT-style library matching (MSC 5.1 TODO)
│   ├── mzhdr.py / mzparse.py       # MZ header/reloc tools
│   └── fingerprint.py              # Compiler fingerprinting
├── src/                            # C ports (8.3 names, one function per file)
│   ├── asm/                        # annotated hand-ASM family notes (sink #6)
│   ├── hello.c, getans.c           # Pipeline smoke tests
│   └── sub_*.c                     # Attempted game-routine ports
├── dos_compilers/
│   └── msc5.1/                     # MSC 5.1 installed (RBIN\CL.EXE, LIB\, INCLUDE\)
│       └── compile.log             # Last compile log (debug)
├── registry/
│   ├── routines.yaml                # Per-routine convergence ledger (class/hypothesis/status)
│   ├── game_knowledge.yaml          # 379 lines: modes, weapons, campaign, controls
│   ├── FALCONCD.EXE.yaml            # Per-file registry
│   └── OVL_1E10.yaml                # Per-overlay registry
├── docs/
│   ├── pipeline.md                  # THIS FILE
│   ├── findings_log.md              # Append-only history of findings/disprovals
│   ├── toolchain.md                 # Compiler/linker evidence
│   ├── structures.md                # MZ/RTLink/data structures (byte-level formats)
│   ├── overlay_fixups.md            # 14 fixup types decoded
│   └── prior_art.md                 # Previous attempt history
├── status.md / plan.md             # Current status + phased plan
└── venv\                           # Python 3.14 venv (pymupdf, etc.)
```

---

## Track A: Analysis & Knowledge Extraction

### Prerequisites
- IDA Professional 9.1 at `C:\Program Files\IDA Professional 9.1\idat.exe` (headless)
- **NEVER open FALCONCD.EXE in the MCP-connected interactive IDA** (it holds `GS2.exe.i64` for the ongoing Gunship decompilation). Always run `idat.exe` as a separate headless process.
- Python venv

### Steps

1. **Headless snapshot + full analysis**
   ```
   idat.exe -A -S"tools\ida_snapshot.py" analysis\ida_falconcd\FALCONCD.EXE.i64
   ```
   Produces `survey.json`, `functions.tsv`, `overlays.json`, etc.

2. **RTLink fixup extraction** (static, no IDA needed)
   ```
   venv\Scripts\python tools\extract_fixups.py     # → fixup_tables_*.json
   venv\Scripts\python tools\analyze_all_records.py
   ```

3. **Apply RTLink fixups inside IDA**
   ```
   idat.exe -A -S"tools\apply_fixups_ida.py" analysis\ida_falconcd\FALCONCD.EXE.i64
   ```
   1569 fixups across 21 records → overlay code relocated to runtime paragraphs.

4. **Extract ground-truth function bytes**
   ```
   idat.exe -A -S"tools\extract_ida_bytes.py" analysis\ida_falconcd\FALCONCD.EXE.i64
   ```
   → `function_bytes.json` (839 functions, bytes **as relocated in IDA**).

5. **Knowledge base update** — extract manual text, fold into `registry/game_knowledge.yaml`:
   ```
   venv\Scripts\python -c "...pymupdf open('game/manual.pdf')..." > manual_full.txt
   ```

### IDA Coordinate System (CRITICAL)

| Fact | Value |
|------|-------|
| IDA image base | `0x10000` (paragraph `0x1000`) |
| Function EA (linear) | from `survey.json` `ea` field |
| segment / offset | `seg = ea >> 4`, `ofs = ea & 0xF` |
| Raw EXE file offset | `hdr + (ea - 0x10000)` where `hdr = 0x2C00` (704 paragraphs × 16) |
| Entry point | linear `0x2B19C` (`CS:IP = 0x1AA3:0x076C`) |

**Trap**: raw EXE bytes ≠ IDA bytes. The MZ loader applies 2717 relocations at load time
(spread across segments `0x1AA3`, `0xE56`, `0x80F`, …) and IDA applies them too. Always
compare against `function_bytes.json`, never against a naive file-offset read.

---

## Track B: Per-Routine C Ports (MSC 5.1)

### Prerequisites
- DOSBox-X at `C:\dosbox-x\dosbox-x.exe`
- MSC 5.1 at `dos_compilers\msc5.1\` (mounted as `C:\` in DOSBox; compiler in `RBIN\CL.EXE`)
- `analysis/ida_falconcd/function_bytes.json` (regenerate if IDB changes — Step A4)

### DOSBox-X Config (generated on the fly by `portcheck_falcon.py`)

```ini
[autoexec]
mount c C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1
c:
path c:\rbin;c:\rbinb
set INCLUDE=c:\include
set LIB=c:\lib
rbin\cl /c /Gs /Fc<NAME8> /Ic:\include <file.c> > compile.log
exit
```

- `/c` compile only, `/Gs` no stack probes, `/Fc` generate `.cod` listing
- Output: `<NAME8>.OBJ` + `<NAME8>.COD` **in the MSC root (C:\)** — not in the source dir

### Single-Routine Verify

```bash
venv\Scripts\python tools\portcheck_falcon.py <routine> --source src\<name>.c --segment 0x<seg> --offset 0x<ofs>
```

Internal flow:
1. Copy source into MSC dir under 8.3 name (first 8 chars of routine name!)
2. Run DOSBox-X compile
3. Parse `.cod` listing for `_routine` PROC…ENDP block → code bytes
4. Load reference bytes from `function_bytes.json` (fallback: raw EXE)
5. Byte-compare → `OK` / `FAIL` with hex dumps

### Naming Rules (CRITICAL — all tripped over these)

| Rule | Example |
|------|---------|
| C filename = routine name truncated to 8 chars | `sub_16FDD` → `sub_16FD.c`, `.cod` = `SUB_16FD.COD` |
| C **function name** must match routine name parsed from `.cod` (`_name PROC`) | declare `int sub_16FD(void)`, NOT `sub_16FDD` |
| Leading underscore is MSC's C decoration — don't write it | `.cod` shows `_sub_16FD` |
| One function per file | Multiple routines in one `.cod` confuse extraction |
| arg `--segment`/`--offset` from `survey.json`: `seg = ea>>4`, `ofs = ea&0xF` | `ea=0x16FDD` → `0x16FD` / `0xD` |

### MSC 5.1 C Syntax Rules

| Issue | Fix |
|-------|-----|
| `__far` rejected (`error C2054`) | MSC 5.1 has no `__far`; qualifier is `far` after return type: `int far func(void)` |
| `far int func(void)` rejected (`C2062`) | Order matters: `int far func(void)` |
| Default model gives near calls (`RET C3`) but original is far (`RETF CB`) | Declare routine `far` and/or compile with `/AL` (large model) |
| No `byte` / `uint` types | `unsigned char` / `unsigned int` |
| No standard CRT linked in original | Don't include `<stdio.h>`; keep routines freestanding |

### Smoke Tests (verified ✅)

| Source | Output bytes | Result |
|--------|-------------|--------|
| `hello.c` (`main(){return 0;}` w/ constant folded to 42) | `b8 2a 00 c3` | ✅ compile+extract works |
| `getans.c` (`int getans(){return 42;}`) | `b8 2a 00 c3` | ✅ compile+extract works |

### Verified Game Routines

| Routine | Original (IDA) | C source | Result |
|---------|----------------|----------|--------|
| `sub_16FDD` | `b8 01 00 cb` (mov ax,1; retf) | `int far sub_16FDD(void){return 1;}` | ✅ MATCH |
| `sub_2CB6E` | `b8 ff ff cb` (mov ax,-1; retf) | `int far sub_2CB6E(void){return -1;}` | ✅ MATCH |

**Key insight**: compile with `/AL` (large model) so returns are `RETF`, and declare
`int far func(void)` (qualifier *after* return type). Without this, near `RET` never matches.

### Attempted Game Routines (diagnostics)

| Routine | Original (IDA) | Diagnosis |
|---------|----------------|-----------|
| `sub_10340` | `d1 e3 2e 89 87 25 00 cb` (hand-ASM: `sal bx,1; mov cs:[bx+25h],ax; retf`) | **Hand-written ASM, not C** — skip or port as `.asm` |

---

## Convergence Model (adapted from gunship_2000)

The GS2000 workflow converges on ground truth via two mutually-checking tracks:

- **Track 1** = end-to-end byte-identical rebuild → *prevents veering from ground truth*.
- **Track 2** = incremental C ports → each verified port + registry rename records a
  learning/hypothesis; over time the C files and registry become the knowledge store,
  and Track 1 keeps re-proving nothing drifted.

### Falcon3 gap analysis vs this model

| GS2000 element | Falcon3 status | Action |
|---|---|---|
| Track 1: relink original binary | ❌ **No relink — original linker is RTLink/Plus, no binary available** | Use **splice-in-place** Track 1 (below) |
| Full asm skeleton (IDA .lst → UASM) | ❌ We have `function_bytes.json`/TSV, no instruction listing, no data/code boundary map | IDA listing export + `lst2asm`-style generator (adapt gunship scripts) |
| Track 2 batch driver | ⚠️ `portcheck_falcon.py` verifies one routine at a time | Add batch driver + pass/fail convergence metric |
| Registry with per-routine hypotheses | ⚠️ Schema + first entries exist (`registry/routines.yaml`); 3/839 tracked | Keep filling on classify/verify; renames land there + in C files |
| `mzdiff` verification | ✅ **Reusable, not game-specific** — WSL binary exists (see below) | Only `.map` files are per-EXE (`mzmap` makes them, can ingest IDA `.lst`) |
| Ghidra decompile → draft C | ❌ Not wired in (Ghidra installed; gunship has `ghidra_dump_to_lst_final.py`) | Add dump script, human-verify via portcheck |
| Coverage ground truth | ⚠️ Resident **proven** (815/815 = raw+relocs, finding 15); **overlay IDB layout wrong** (finding 16) | Rebuild overlay placement from primary anchors (plan 1.2b) |

### Track 1 without RTLink: splice-in-place

We cannot relink with RTLink/Plus, but Track 1's purpose — *prove we haven't veered* —
is achievable without it:

1. Original FALCONCD.EXE is an **immutable scaffold** (MZ header, 2717 relocations,
   RTLink directory, 1.2 MB overlay tail all verbatim).
2. Overwrite a routine's file-offset range (`hdr + (ea - 0x10000)`, length = IDA size)
   with our reassembled/recompiled bytes.
3. Require **byte-identity at every patched site** (portcheck already enforces this).
4. Verify the whole image with `mzdiff` (instruction-stream diff + `mzmap` maps).
5. Functional smoke test in DOSBox-X.

Because portcheck guarantees identical bytes, all MZ relocations and the RTLink tail
remain valid for free — no RTLink needed. As verified routines accumulate, the
"regenerated" fraction of the resident image grows toward 100% while the container
stays ground truth. This is GS2000's assurance inverted: *original-around-us* instead
of *rebuild-matching-it*.

---

## How the Code Interprets Embedded Data (Parser RE)

The EXE is not just code: runtime code parses structures **stored inside the EXE
itself** (and external DAT files). Reversing these parsers is a first-class goal —
each one (a) unlocks a data format for the registry, (b) is itself a self-contained,
byte-verifiable porting target, and (c) constrains how a rebuild must lay data out.

Known/anticipated embedded-data parsers, priority order:

| Data interpreted by code | Where it lives | Status |
|---|---|---|
| RTLink overlay directory (70 × 18 B) | resident image `0x1AA3:0x0C1F` (file `0x1E24F`) | ✅ struct decoded statically; **loader code at `0x1AA3:0x0590` not yet read** |
| RTLink thunk dispatch (86 × 10 B) | `0x1AA3:0x157F` | ✅ struct decoded; dispatch code is the gateway resident→overlay |
| Fixup tables (1569 entries, 14 types) | per-record tail | ✅ decoded statically; the applier routine proves the format |
| Tail 4-byte directory (51 entries) | file `0x1FB61` | ⚠️ parsed; runtime use unverified |
| PKWARE DCL streams | `PK\x03\x04` in tail + Huffman tables in code | ⚠️ library identified; stream framing per-asset not mapped |
| External DAT formats (`ARMSTABL.DAT`, `DISPLAY.DAT`, mission/save/ACMI files) | `game\` dir (already unpacked) | ❌ parsers in EXE not yet identified — find via string xrefs |
| MZ header + relocation table | file head | ✅ decoded (`mzhdr.py`); DOS applies at load |

Method: locate the parse code (xref from the loader/string), document the format in
`docs/structures.md`, then treat the parser as a normal Track 2 porting candidate.

---

## Track C: Splice Rebuild + mzdiff (PLANNED — adapted from gunship_2000)

Goal: replace verified C routines **inside** the original MZ image (splice-in-place,
see "Convergence Model" above) and prove no drift with `mzdiff`, which compares
instruction streams via segment maps rather than raw bytes — relocation-tolerant.

### mzdiff availability (verified 2026-10-11) — NOT game-specific

`mzdiff`/`mzmap` are **generic MZ tools** from `f19re/mzretools`; only the `.map`
files are per-EXECUTABLE (`mzmap` generates them and can ingest an IDA `.lst` directly).
No build needed — reuse the existing WSL binary (GS2000's doc says `build/mzdiff`;
actual location is **`debug/`**):

```
/mnt/c/Users/yotam/projects/gunship_2000/tools/f19re/mzretools/debug/mzdiff   # v1.0.20 ✅ runs
/mnt/c/Users/yotam/projects/gunship_2000/tools/f19re/mzretools/debug/mzmap    # v1.0.20 ✅ runs
```

Usage:
```
mzmap FALCONCD.EXE falconcd.map            # once per EXE (or feed IDA .lst)
mzdiff [--map ref.map] [--tmap tgt.map] [--loose] [--verbose] ref.exe[:entry] tgt.exe[:entry]
```

### Components to build

1. **IDA listing export** → `.lst` (mzmap can use it directly as a map; also feeds
   the asm-skeleton generator below)
2. **`extract_routines.py`** (borrow gunship): parse MSC `.cod` → per-routine `.asm` + auto-`EXTRN` for far calls
3. **`replace_routines.py`** (borrow gunship): take IDA-generated asm skeleton, swap target routines with C-generated asm
4. **Splice driver** (`tools/splice.py`, new): write verified routine bytes into a
   copy of FALCONCD.EXE at `hdr + (ea - 0x10000)`; refuse if bytes differ
5. **Assemble**: UASM (`uasm -0 -q`) for transcribed hand-ASM routines → extract bytes → splice
   - Note: no RTLink binary ⇒ a faithful final *link* is impossible; splice sidesteps it
     (header/relocs/tail verbatim, code byte-identical ⇒ structurally valid by construction)
6. **`mzdiff` whole-image check**: `mzdiff falconcd.map original.exe splice.exe` —
   instruction-stream equality across the resident image

### Why not just byte-compare the whole EXE?
- RTLink overlay records + fixups live in a 1.2 MB tail whose full structure is not yet
  decoded (68 KB of records known, rest likely PKWARE assets)
- Relocations (2717 MZ + 1569 RTLink) make naive whole-file diffs useless
- `mzdiff` normalizes via segment maps → compares the *code stream*
- Splice guard: byte-identity at each patch site ⇒ relocs/tail stay valid automatically

### Verification levels

| Level | Tool | What it proves |
|-------|------|----------------|
| 1. Routine bytes | `portcheck_falcon.py` | C compiles to identical instruction bytes |
| 2. Routine asm roundtrip | `extract_routines.py` + UASM + byte diff | `.cod` → `.asm` → `.obj` lossless |
| 3. Resident image | `mzdiff ref.exe target.exe --loose` | Replacements don't disturb neighbors |
| 4. Full functional | Run in DOSBox-X | Game plays |

---

## Key Scripts Reference

| Script | Purpose | Track |
|--------|---------|-------|
| `tools/ida_snapshot.py` | IDA headless: full analysis → survey.json/functions.tsv | A |
| `tools/extract_fixups.py` | Parse RTLink fixup tables statically | A |
| `tools/analyze_all_records.py` | Record/segment-group analysis | A |
| `tools/rtlink_scan.py` | RTLink directory scanner | A |
| `tools/prep_overlay_placement.py` | Per-record file base + runtime block + addr assignment → `overlay_placement.json` | A |
| `tools/find_cluster_b.py` | Locate cluster-B rows (B0=0xFFFA0, finding 20) | A |
| `tools/rebuild_overlay_segments.py` | Rebuild IDB overlay segments from raw bytes (finding 19) | A |
| `tools/prep_overlay_entries.py` | Thunk targets → entry_ea map → `overlay_entries.json` | A |
| `tools/mark_overlay_entries.py` | Content-driven entry marking (fallback row candidates) | A |
| `tools/validate_fixup_semantics.py` | Host-side fixup semantics check → `fixups_to_apply.json` | A |
| `tools/apply_overlay_fixups.py` | Apply +0x1000 fixups in IDB (byte-guarded, RTFIX marker) | A |
| `tools/extract_ida_bytes.py` | Live IDA functions → function_bytes.json (ground truth) | A |
| `tools/classify_routines.py` | All functions → C/ASM/DATA/LEAF/NEARTHUNK + port queue | A |
| `tools/portcheck_falcon.py` | Single-routine C verify (Track B driver) | B |
| `tools/compile_msc51.py` | Standalone MSC 5.1 compile wrapper | B |
| `tools/libscan.py` | Library signature matching (needs MSC 5.1 libs) | A/B |
| `tools/mzhdr.py`, `mzparse.py` | MZ header/relocation tools | A |
| ~~`tools/apply_fixups_ida.py`~~ | SUPERSEDED (old mis-based fixups; segments rebuilt) | A |
| `scripts/extract_routines.py` | **TODO (copy gunship)** `.cod` → `.asm` + EXTRN | C |
| `scripts/replace_routines.py` | **TODO (copy gunship)** hybrid asm builder | C |
| `tools/splice.py` | **TODO** patch verified bytes into EXE copy (Track 1) | C |
| `mzdiff` / `mzmap` (WSL, shared w/ gunship) | Instruction-stream diff / segment map gen — generic, not game-specific | C |

---

## Environment / Paths

| Variable | Value |
|----------|-------|
| Repo root | `C:\Users\yotam\projects\falcon3` |
| IDA 9.1 headless | `C:\Program Files\IDA Professional 9.1\idat.exe` |
| DOSBox-X | `C:\dosbox-x\dosbox-x.exe` |
| MSC 5.1 root | `C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1` (RBIN\CL.EXE) |
| Python venv | `C:\Users\yotam\projects\falcon3\venv\Scripts\python.exe` |
| Ground truth bytes | `analysis\ida_falconcd\function_bytes.json` |
| mzretools | Shared WSL binaries: `/mnt/c/.../gunship_2000/tools/f19re/mzretools/debug/{mzdiff,mzmap}` v1.0.20 (source: `C:\Users\yotam\projects\f19re\mzretools`) |
| Reference projects | `C:\Users\yotam\projects\f19re` (MSC 5.1 rebuild), `C:\Users\yotam\projects\gunship_2000` (RTLink + registry + this doc's template) |

Shell notes: Windows PowerShell 5.1 — **no heredocs**; write script files first.
`ls`/`wc`/`grep` Unix tools absent — use Python one-liners or Glob/Grep tools.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not extract bytes for X` | `.COD` not found or function name mismatch | Check `dos_compilers\msc5.1\X*.COD` exists; C function must be `X` (8-char truncated) |
| `error C2054: expected '(' to follow '__far'` | MSC 5.1 has no `__far` | Use `int far func(void)` |
| `error C2062: type 'int' unexpected` | Wrong qualifier order (`far int`) | `int far func(void)` |
| portcheck MISMATCH expected=raw-exe bytes | Compared pre-relocation file bytes | Use `function_bytes.json` (auto-loaded; regen via `extract_ida_bytes.py`) |
| portcheck `ret` vs `retf` mismatch | Compiled near, original far | Fixed: compile line now uses `/AL`, declare `int far func(void)` |
| MISMATCH on small `sub_*` | Function is hand-written ASM, not C | Check bytes for `55 8b ec` / `ENTER` prologue vs ad-hoc; port as asm instead |
| DOSBox compile fails, empty log | Config path escaping | Paths in config need `\\` doubled; run with `cwd=repo root` |
| IDA hangs / conflicts | Interactive IDA holds another DB | Only run `idat.exe` headless; never open falcon in MCP IDA |
| `fixup` mismatches in survey bytes | Survey era vs fixup-era IDB | Always extract fresh `function_bytes.json` after re-running fixups |
| Routine has far call (`9a xx xx seg off`), bytes never match | IDA bytes have load-base `+0x1000` in relocated words (finding 15) | Normalize: allow ±0x1000 on words at MZ reloc positions, or compare vs raw-EXE+relocs |
| Splicing bytes from `function_bytes.json` breaks relocations | Those are *relocated* (runtime) bytes | Splice **unrelocated** file bytes — DOS re-applies relocs at load |
| Overlay function bytes decode as garbage | Overlay fixups possibly mis-applied (finding 16) | Don't trust overlay function bytes until re-audited; resident 815 proven good |

---

## Next Steps for Future Agents

1. ~~**Fix near/far**~~ ✅ Done: `/AL` + `int far` → `sub_16FDD` and `sub_2CB6E` both MATCH.
2. **Pick easy targets**: filter `functions.tsv` for size ≤ 10, `far=1`, `nretf=1`,
   no thunk — verify constants/globals getters next (IDB names via `function_bytes.json`).
3. **Classify hand-ASM vs C**: `prologues.json`/`epilogues.json` already extracted;
   C-compiled candidates are the ones with `ENTER` or consistent frames.
4. **Track C setup**: copy gunship's `extract_routines.py`/`replace_routines.py` into
   `scripts/`; write `tools/splice.py`; `mzdiff`/`mzmap` already available in WSL at
   `gunship_2000/tools/f19re/mzretools/debug/` — just run `mzmap FALCONCD.EXE falconcd.map` once.
5. **Extend `libscan.py`** with MSC 5.1 libraries from the `f19re` toolchain.
6. **Registry**: once routines verify, record them in `registry/FALCONCD.EXE.yaml`
   (name, ea, bytes hash, port status) per gunship's registry YAML format.

---

## Version / Date

- Document created: 2026-10-11
- Pipeline status: Track A working (839 funcs, fixups applied), **Track B working (2 routine matches)**, Track C planned
- Template: `gunship_2000/docs/PIPELINE.md`
