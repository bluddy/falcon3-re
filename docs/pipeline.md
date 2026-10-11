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
│   ├── hello.c, getans.c           # Pipeline smoke tests
│   └── sub_*.c                     # Attempted game-routine ports
├── dos_compilers/
│   └── msc5.1/                     # MSC 5.1 installed (RBIN\CL.EXE, LIB\, INCLUDE\)
│       └── compile.log             # Last compile log (debug)
├── registry/
│   ├── game_knowledge.yaml         # 379 lines: modes, weapons, campaign, controls
│   ├── FALCONCD.EXE.yaml           # Per-file registry
│   └── OVL_1E10.yaml               # Per-overlay registry
├── docs/
│   ├── pipeline.md                 # THIS FILE
│   ├── toolchain.md                # Compiler/linker evidence
│   ├── structures.md               # MZ/RTLink/data structures
│   ├── overlay_fixups.md           # 14 fixup types decoded
│   └── prior_art.md                # Previous attempt history
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

## Track C: Hybrid Rebuild + mzdiff (PLANNED — adapted from gunship_2000)

Goal: replace verified C routines **inside** a full assembled image and diff against
the original with `mzdiff` (from `f19re/mzretools`), which compares instruction streams
with segment maps rather than raw bytes — tolerant of relocations.

### Components to build

1. **IDA listing export** → `.lst` (or reuse `functions.tsv` + `function_bytes.json`)
2. **`extract_routines.py`** (borrow gunship): parse MSC `.cod` → per-routine `.asm` + auto-`EXTRN` for far calls
3. **`replace_routines.py`** (borrow gunship): take IDA-generated asm skeleton, swap target routines with C-generated asm
4. **Assemble**: UASM (`uasm -0 -q`) → `.obj`
   - *Difference from gunship*: Falcon's original linker is **RTLink/Plus, not LINK.EXE**.
     No RTLink binary is available, so a faithful final link is **not possible yet**.
     Options: (a) link resident-only image with LINK 3.65 + compare code sections with
     `mzdiff --loose`; (b) locate/replace routines in-place in the MZ image and run
     `mzdiff` on the image before/after patch.
5. **`mzdiff`**: build `f19re/mzretools` (MSVC or WSL) once, reuse gunship's build if present:
   - WSL: `/mnt/c/Users/yotam/projects/gunship_2000/tools/f19re/mzretools/build/mzdiff`
   - or build our own copy: `dos_compilers` sibling `tools/mzretools/` + `./build.sh`
   - Usage: `mzdiff [options] reference.exe[:entrypoint] target.exe[:entrypoint]`
     with `--loose --sdiff N --map <map>` for instruction-level comparison
6. **`mzmap`**: generate segment maps (`.tgt` / `.map`) for both EXEs so `mzdiff` can map
   segment aliasing (CS/DS overlap is common in Falcon — overlay segments share paragraphs)

### Why not just byte-compare the whole EXE?
- RTLink overlay records + fixups live in a 1.2 MB tail whose full structure is not yet
  decoded (68 KB of records known, rest likely PKWARE assets)
- Relocations (2717 MZ + 1569 RTLink) make naive whole-file diffs useless
- `mzdiff` normalizes via segment maps → compares the *code stream*

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
| `tools/apply_fixups_ida.py` | Apply 1569 RTLink fixups inside IDA | A |
| `tools/extract_ida_bytes.py` | IDA → function_bytes.json (relocated ground truth) | A |
| `tools/extract_fixups.py` | Parse RTLink fixup tables statically | A |
| `tools/analyze_all_records.py` | Record/segment-group analysis | A |
| `tools/rtlink_scan.py` | RTLink directory scanner | A |
| `tools/portcheck_falcon.py` | Single-routine C verify (Track B driver) | B |
| `tools/compile_msc51.py` | Standalone MSC 5.1 compile wrapper | B |
| `tools/libscan.py` | Library signature matching (needs MSC 5.1 libs) | A/B |
| `tools/mzhdr.py`, `mzparse.py` | MZ header/relocation tools | A |
| `scripts/extract_routines.py` | **TODO (copy gunship)** `.cod` → `.asm` + EXTRN | C |
| `scripts/replace_routines.py` | **TODO (copy gunship)** hybrid asm builder | C |
| `mzdiff` (mzretools) | Instruction-stream diff with segment maps | C |

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
| mzretools source | `C:\Users\yotam\projects\f19re\mzretools` (+ gunship copy with build/) |
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

---

## Next Steps for Future Agents

1. ~~**Fix near/far**~~ ✅ Done: `/AL` + `int far` → `sub_16FDD` and `sub_2CB6E` both MATCH.
2. **Pick easy targets**: filter `functions.tsv` for size ≤ 10, `far=1`, `nretf=1`,
   no thunk — verify constants/globals getters next (IDB names via `function_bytes.json`).
3. **Classify hand-ASM vs C**: `prologues.json`/`epilogues.json` already extracted;
   C-compiled candidates are the ones with `ENTER` or consistent frames.
4. **Copy gunship's `extract_routines.py` / `replace_routines.py`** into `scripts/`
   and build `mzretools` (or symlink gunship's) to start Track C.
5. **Extend `libscan.py`** with MSC 5.1 libraries from the `f19re` toolchain.
6. **Registry**: once routines verify, record them in `registry/FALCONCD.EXE.yaml`
   (name, ea, bytes hash, port status) per gunship's registry YAML format.

---

## Version / Date

- Document created: 2026-10-11
- Pipeline status: Track A working (839 funcs, fixups applied), **Track B working (2 routine matches)**, Track C planned
- Template: `gunship_2000/docs/PIPELINE.md`
