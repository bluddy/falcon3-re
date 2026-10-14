# Falcon3 Decompilation Status — handover document

**Last updated**: 2026-10-13 (session 13 — see Time Log; always bump + append row)
**Branch**: master (HEAD `6fb6902` at time of writing)
**Snapshot**: `analysis/ida_falconcd/FALCONCD.EXE.i64` (IDA Pro 9.1, headless only)
**IDA install**: `C:\Program Files\IDA Professional 9.1\` (idat.exe at
  `C:\Program Files\IDA Professional 9.1\idat.exe`; interactive IDA must NEVER open
  Falcon — it holds the Gunship DB)

> This file is the **entry point for a future agent**. It states the exact current
> state and the exact method. Deep rationale lives in `docs/findings_log.md`
> (append-only history, findings 1–28), detailed procedures in `docs/pipeline.md`.
> Protocol: **Knowledge Capture** — 7 sinks, findings log append-only, status
> Time Log bumped on every change.

---

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
| 2026-10-11 (session 4) | same day | **Findings 20+21: cluster-B FOUND (B0=0xFFFA0)** — all 70 rows placed → 68 segments / 1,053,376 B; **fixups applied: 25,222 × +0x1000** byte-guarded; entries 192 overlay fns, **1,007 total**; C=97 with relocated DGROUP. **plan 1.2b 5/5 core done** |
| 2026-10-11 (session 5) | same day | **Finding 22: COMPILER REVISED — Borland C++ 2.0 `bcc -c -ml -1 -O`** (user installed; enter/leave = BC; MSC 5.1/6.0 re-tested → no enter, DISPROVEN for C); **sub_1A6D4 44B MATCH** end-to-end via new portcheck `--cc bcc` + `obj_extract.py`; toolchain.md rewritten. C-port queue resumed |
| 2026-10-11 (session 6) | same day | **Finding 23: chained same-module port** — sub_17A85 (79B, 4 fixups masked) + sub_17AD4 (61B incl. adjacency-dependent `call 0xFF7B`) **BOTH MATCH**; BC large-model rules decoded (char* = far!; `(char near*)` → DS conversion; decl-order of `int i=0`; one-expr flags). Fixup masking + ±0x1000 reloc normalization now in portcheck compare. **Verified: 5 routines** |
| 2026-10-11 (session 7) | same day | **Findings 24+25: sub_197EA (69B switch) + sub_19CB0 (55B) MATCH** — case table recovered from EXE via CS-base jump-target matching (CS=0x180F0); union far-ptr arithmetic + decl-order slot rules. **Verified: 7 routines / 382 bytes** |
| 2026-10-11 (session 8) | same day | **Finding 26: keyboard unit 10/10 MATCH (570B)** — contiguous 0x19CB0-0x19EF9 single translation unit ported (`kb_unit_19CB0.c`); assign-in-cond spill rule; **IDA-missed function sub_19D65 discovered via gap arithmetic + registered in IDB** (1008 fns); **totals: 16 verified / 846 bytes** |
| 2026-10-12 (session 9) | ~9 h | **Naming/annotation system built**: `registry/naming.yaml` ledger (16 renames) + `registry/structs.yaml` (5 structs) + globals inventory (1,968 `data_symbols.json`) + `tools/naming.py` (list/resolve/apply/revert/check/push-ida) + **21-test suite green**; C files renamed to semantic names; names pushed into IDB with key-stable re-extract verified; portcheck resolves ida⇄semantic; ground-truth regen runbook + rebuild verdict documented in pipeline.md |
| 2026-10-12 (session 10) | ~1 h | **Finding 27: sub_19EF9 (64B) MATCH** — 11th keyboard-unit member (`kb_field_get_26`, reads byte `rec_0026[idx*14+r]` @ +0x26, cwde sign-extend, same `farptr_field_reader` pattern); appended to `kb_unit_19CB0.c` (nothing shifts). **Verified: 17 routines / 910 bytes**. Queue advanced to overlay C-class. |
| 2026-10-13 (session 11) | ~1 day | **Finding 28: keyboard unit COMPLETE — 38/38 ported, 37 MATCH + 1 known-diff (2270B)**; unit boundary confirmed 0x19BFF..0x1A4CA; **11 IDA-missed fns registered** (function_bytes 1008→1021); push-only param SI/DI caching difference resolved via scoped `#pragma option -r-`; array fns matched via `struct kb_ab` param; count-spill via assign-in-cond; kb_record_name_get accepted 2B NUL-peephole diff; **totals: 43 verified / 2282 bytes**; naming ledger 44 entries; temp `_var*.c` cleanup |
| 2026-10-13 (session 12) | ~2 h | **Gap sweep completed** — 235 gaps ≥8B scanned, 60 code-like; **59 new resident functions registered** in IDB via `add_gap_functions.py` (function_bytes 1021→1080); extraction re-run; new C-class candidates added to port queue. |
| 2026-10-13 (session 13) | ~2 h | **Classification re-run** → 107 C-class / 757 ASM; **porting attempt on new C fns** (`sub_1B631`, `sub_1AAA4`, `sub_1C12F`, `sub_1C0E4`) showed multi-external-far-call + local-buffer pattern defeats BCC codegen; **Finding 29**: no new clean TUs — IDB boundaries unreliable for gap-sweep/overlay C fns. Pivot to Track C. |
| 2026-10-13 (session 14) | ~1 h | **Track C tools committed**: `extract_routines.py` (adapted from gunship_2000), `splice.py` (routine replacement in IDB assembly), `mzdiff.py` (EXE byte comparison at verified EAs). Pipeline ready for first splice test. Found raw EXE vs ground truth fixup diff (DGROUP segment 0x9468 vs 0x9478) — expected. |
| 2026-10-13 (session 15) | ~2 h | **DOSBox-Staging debugger build + dynamic trace harvester**: build src/dosbox-staging with debugger enabled; add hooks for overlay loads, file I/O (INT 21h), function entry DS/ES logging; redump menu/mission/sim memory for accurate address matching. Per advice.md §3: segment classification schema (SEG_DGROUP, SEG_OVERLAY_ID, SEG_HEAP_ALLOC), snapshot splicing pipeline. |

---

## Executive Summary

Falcon 3.0 (`FALCONCD.EXE` + variants) is a **DOS 16-bit far/large-model** game:
**Borland C++ 2.0** for C modules (`bcc -c -ml -1 -O` — finding 22, byte-proven),
**hand-written ASM** for the rest, **RTLink/Plus** overlay linker, **PKWARE DCL**
asset compression, **no embedded CRT**. 1.37 MB: 118 KB resident image + 1.2 MB
overlay/asset tail.

**Where we are** (all proven, see Current State):
- Ground truth: **1,080 functions** with exact runtime bytes; resident validated
  888/888 against raw EXE + MZ relocations; overlay system fully decoded and IDB
  rebuilt (68 segments, 25,222 fixups applied, plan 1.2b 5/5).
- **43 C routines / 2,282 bytes ported byte-exact** through a working portcheck
  loop, including the completed 2,270-byte keyboard translation unit (38 functions).
- **Key codegen insight (finding 29)**: BC 2.0 produces byte-exact output for functions with
  ≤1 external far call + intra-module `push cs; call rel16` call chains (same TU).
  Multiple external far calls + local buffers trigger spilling/frame growth.
- The **rename/annotation layer exists outside the IDA DB** (ledger + structs + globals
  inventory + tested Python tooling + IDB push), so the fragile binary DB is now a
  regenerable view, not a dependency.
- **Rebuild**: yes via splice (Track C) — verified bytes patched into the original
  scaffold keep all relocations/RTLink structures valid by construction; `mzdiff` is
  the verifier. From-scratch rebuild documented as out of scope.

---

## Current State at a Glance (exact numbers)

| Metric | Value | Source |
|---|---|---|
| Functions in ground truth | **1,080** (888 resident + 192 overlay + 59 gap-sweep registered) | `function_bytes.json` |
| Classification | ASM 757 / C 107 / DATA 129 / LEAF 80 / NEARTHUNK 7 | `classification.json` |
| Verified routines | **43 / 2,282 bytes** | `registry/routines.yaml` (`verified: MATCH`) |
| Rename ledger | 44 entries, all renamed + pushed to IDB | `registry/naming.yaml` |
| Struct definitions | 5 (4 confirmed, 1 hypothesis) | `registry/structs.yaml` |
| Globals inventoried | **1,968** (name=null until renamed) | `data_symbols.json` |
| Tests | **21 green** (`python -m unittest discover -s tests`) | `tests/test_naming.py` |
| Overlay IDB | 68 segments / 1,053,376 B (9 real + 59 synthetic, 2 skipped) | `overlay_placement.json` |
| Overlay fixups applied | 25,222 × +0x1000 (byte-guarded) | finding 21 |
| IDB regen cost | ~6 headless IDA runs (runbook below) | pipeline.md |
| Findings logged | 1–29 (append-only) | `docs/findings_log.md` |
| Game knowledge | 379-line manual extraction | `registry/game_knowledge.yaml` |

## Verified Facts

| Item | Status | Evidence |
|------|--------|----------|
| Linker | ✅ RTLink/Plus | Strings, 18-byte directory, thunk table, loader disasm (findings 17/18) |
| Compression | ✅ PKWARE DCL | Strings, `PK\x03\x04` in tail; assets already unpacked in `game/` |
| CRT | ❌ none embedded | No CRT strings at all (startup is custom ASM) — CRT-based negatives are inconclusive (finding 22) |
| Compiler (C) | ✅ **Borland C++ 2.0** `bcc -c -ml -1 -O` | `sub_1A6D4` 44B byte-exact; enter/leave/imm0/or-si fingerprints (finding 22) |
| ~~Compiler (C)~~ | ~~MSC 5.1~~ | **DISPROVEN for C** — version-verified 5.10 + 6.00ax emit no enter under any flag (finding 22) |
| Compiler (ASM) | ✅ hand-written | 84 × `558BEC` with variable register saves |
| Code model | ✅ far/large | `retf`, stack args `[BP+6]`, caller cleanup |
| Overlays | ✅ RTLink | 70 records, schema + placement + fixups decoded (findings 17–21) |
| RESETALL.EXE | ✅ Borland C++ 1991 | Separate utility |

---

## THE METHOD (exact procedures)

### 0. Ground truth hierarchy

1. **`analysis/ida_falconcd/function_bytes.json`** — THE byte ground truth
   (runtime bytes = raw EXE + MZ relocs + RTLink fixups). Keys = IDA names forever;
   `name` field = semantic rename (mirrors ledger). **Never hand-edit.**
2. `data_symbols.json` — 1,968 globals (`ida_name` immutable, `name` = rename).
3. `registry/naming.yaml` + `registry/structs.yaml` — rename ledger + structs.
4. The IDB (`.i64`) — analysis view only: **binary, local, NOT committed**,
   regenerable (runbook below). Source files `src/*.c`, `src/asm/*.asm`, and all
   docs are committed; anything that matters must be there, never IDB-only.

### 1. The porting loop (Track B) — the core workflow

```bash
# 1. pick target (C class = Borland-compiled; sort by size)
venv\Scripts\python tools\classify_routines.py
#    candidates: smallest C-class; find_port_targets.py lists reloc-free ones

# 2. disassemble from ground truth (never raw EXE - finding 15)
C:\Python314\python.exe -c "from capstone import *; import json; \
 fb=json.load(open('analysis/ida_falconcd/function_bytes.json')); \
 info=fb['sub_XXXX']; md=Cs(CS_ARCH_X86,CS_MODE_16); \
 [print(i.mnemonic, i.op_str) for i in md.disasm(bytes.fromhex(info['bytes']), info['ea'])]"

# 3. write src/<name>.c  (BC recipe below; annotation header REQUIRED: disasm
#    walkthrough, semantics, ea refs; use semantic names if known, else ida name)

# 4. verify (seg = ea>>4, ofs = ea & 0xF; name may be ida OR semantic)
venv\Scripts\python tools\portcheck_falcon.py <name> --source src\<name>.c \
    --segment 0x<ea>>4> --offset 0x<ea&0xF>
#    iterate on diffs using the BC rules below until: "OK ... MATCH"

# 5. register the learning
#    - renamed? add to registry/naming.yaml, then:
venv\Scripts\python tools\naming.py apply
venv\Scripts\python tools\naming.py check        # must be green (exit 0)
#    - registry/routines.yaml: new entry {ea, seg, ofs, size, far, class,
#      hypothesis, port_status: verified, port_file, verified: MATCH, notes}
#    - new codegen/RE knowledge? append to docs/findings_log.md (NEVER edit old)
#    - bump status.md "Last updated" + Time Log row

# 6. commit (git add specific files; repo rules: no IDB, no game/, no dos_compilers/)
```

Multi-function translation units: when routines call each other with
`push cs; call rel16`, they must live in ONE .c file **in address order** and every
callee must compile to its exact original size (finding 23) — see
`src/kb_unit_19CB0.c` as the model (38 functions, 2,270 B, one file).

### 2. Borland C++ 2.0 codegen rules (byte-exact cheat sheet; findings 22–28)

| # | Rule |
|---|------|
| 1 | Recipe `bcc -c -ml -1 -O` (portcheck default). `-1`/`-2` → `ENTER`/`LEAVE`; without them: `push bp` prologue. `-O` removes a spurious `eb 00` before pops. |
| 2 | In `-ml`, plain `char *` is **far** → `(char *)(int)` yields **segment 0**. DS-segmented conversion needs an explicitly NEAR right side: `dst = (char near *)(expr);` |
| 3 | Never introduce intermediate pointer variables — they spill (frame grows) or hijack SI/DI and reshuffle allocation. Direct casts keep BC's choice identical to the original. |
| 4 | Declaration order picks stack slots: **first-declared local gets [bp-2]**. |
| 5 | `int r = f();` keeps r in **SI**; `if ((r = f()) == -1)` **spills** r to the stack (enter grows). Match the original per-function (siblings differ!). |
| 6 | Same-module far calls → `push cs; call rel16` (4B); external far calls → `call far 0000:0000` (5B, fixup-masked). Original bundled adjacent functions — reproduce the unit. |
| 7 | Expression shape matters: `*dst = (char)(flags &= 3);` as ONE statement (separate statements reorder les-vs-load); long stores emit `mov [bp-hi],dx` first. |
| 8 | Sparse `switch` → search-loop + case/jump tables appended after the function; case values may be missing from C context → read them from the EXE (CS-recovery technique, finding 24). |
| 9 | Comparisons tolerate: FIXUPP-masked operands (call disp/far ptrs/table ptrs), `got+0x1000 == expected` words (MZ/RTLink relocs), trailing post-function bytes (data tables). |
| 10 | Long→far-ptr reinterpretation idiom: `union { long l; char far *p; }` → in-place `add [slot],12` + `les` (a folded cast instead folds +12 into addressing — 3B shorter, wrong). |
| 11 | **Push-only param caching (finding 28)**: under default `-r`, our bcc caches multi-use push-only params into SI/DI; the original build does NOT. Fix: wrap the affected functions in `#pragma option -r-` ... `#pragma option -r` (BCC 2.0 supports per-region pragmas; global `-r-` breaks SI-using fns in the same TU; `register` keyword is ignored under `-r-`). |
| 12 | **Array fns with SI index (finding 28)**: if the original has i→SI with a,b memory-only, pass a,b as a 2-word struct: `f(struct kb_ab ab, int i)` forces a,b to memory (identical stack) leaving i as the sole scalar → SI. `register int i` alone still caches a→DI. |
| 13 | **Plain-assign locals with 2 uses (finding 28)**: our BC may cache them in DI; the original spills them. Wrap in assign-in-cond (`if ((count = f()) <= i)`) to invoke rule 5's spill-forcer. |
| 14 | Known unfixable: `if (p[k] == 0)` char NUL test peepholes to `cmp byte,0` (4B) vs original `mov al/cbw/or ax,ax` (6B); not suppressible — accept as documented diff (finding 28, kb_record_name_get). |

### 3. Naming workflow (renames never touch the ledger's `ida`)

```bash
# add entry to registry/naming.yaml {ida, name, kind, notes}
venv\Scripts\python tools\naming.py apply      # -> src/*.c, src/asm/*.asm, JSON name fields
venv\Scripts\python tools\naming.py check      # consistency gate (exit 1 = broken)
venv\Scripts\python tools\naming.py push-ida   # sync INTO the IDB (headless, saved)
python -m unittest discover -s tests           # 21 tests; run after touching naming.py
```
- portcheck accepts either name (`resolve` handles ida⇄semantic).
- **Never rename ad-hoc in the GUI** — ledger first, then push-ida. (extract_ida_bytes
  keys by previous extract's keys, so pushes can't shift JSON keys — proven.)
- Revert: `naming.py revert <ida_name>` (restores ida text everywhere).

### 4. IDB regeneration runbook (if lost/corrupt — details in pipeline.md)

```
idat -A -S tools\ida_snapshot.py               <IDB>   # fresh analysis (legacy overlays!)
idat -A -S tools\rebuild_overlay_segments.py   <IDB>   # correct layout from committed placement
idat -A -S tools\_add_missed_fn.py             <IDB>   # sub_19D65 (manual fn)
idat -A -S tools\add_missed_functions.py       <IDB>   # 11 kb-unit gap fns (finding 28)
idat -A -S tools\add_gap_functions.py          <IDB>   # 59 gap-sweep fns (finding 28 follow-up)
idat -A -S tools\mark_overlay_entries.py       <IDB>   # 184 thunk entries -> ~192 fns
idat -A -S tools\apply_overlay_fixups.py       <IDB>   # 25,222 fixups
idat -A -S tools\extract_ida_bytes.py          <IDB>   # regenerate ground truth (keys stable)
venv\Scripts\python tools\classify_routines.py
venv\Scripts\python tools\naming.py push-ida           # re-sync semantic names
# host-side JSON regen only if the EXE changed: prep_overlay_placement.py ->
# prep_overlay_entries.py -> validate_fixup_semantics.py (then IDA steps above)
```

### 5. Track C splice pipeline (verification)

```
idat -A -S tools\ida_export.asm                <IDB>   # export full assembly listing
venv\Scripts\python tools\extract_routines.py  listing.asm  src/routines/
venv\Scripts\python tools\splice.py            listing.asm  listing_spliced.asm  src/routines/  --verified registry/routines.yaml
# Assemble listing_spliced.asm → spliced.exe (TASM/MASM + TLINK or BCC)
venv\Scripts\python tools\mzdiff.py            game/FALCONCD.EXE  spliced.exe  --functions analysis/ida_falconcd/function_bytes.json  --routines registry/routines.yaml
```
`idat` fails **exit=4** if the IDB is open in interactive IDA — close it first.
(Also: never open Falcon in the MCP-connected IDA — it holds the Gunship DB.)

---

## Verified Routines (43 / 2,282 bytes)

| IDA name | Semantic name | ea | B | Source | Finding |
|---|---|---|---|---|---|
| sub_16FDD | always_true | 0x16FDD | 4 | `src/sub_16FDD.c` | 08/22 |
| sub_2CB6E | always_false | 0x2CB6E | 4 | `src/sub_2CB6E.c` | 08/22 |
| sub_1A6D4 | long_accumulate | 0x1A6D4 | 44 | `src/sub_1A6D4.c` | 22 (first real port) |
| sub_17A85 | dgroup_record_writer | 0x17A85 | 79 | `src/sub_17AD4.c` (unit) | 23 |
| sub_17AD4 | widen_and_forward | 0x17AD4 | 61 | `src/sub_17AD4.c` (unit) | 23 |
| sub_197EA | key_mapper | 0x197EA | 69 | `src/sub_197EA.c` | 24 |
| sub_19BFF | kb_record_base | 0x19BFF | 11 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19C0A | kb_index_get | 0x19C0A | 14 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19C18 | kb_farptr_get | 0x19C18 | 19 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19C2B | kb_name_copy | 0x19C2B | 33 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19CB0 | farptr_field_reader | 0x19CB0 | 55 | `src/kb_unit_19CB0.c` | 25 |
| sub_19CE7 | kb_field_get_22 | 0x19CE7 | 62 | `src/kb_unit_19CB0.c` | 26 |
| sub_19D25 | kb_field_get_23 | 0x19D25 | 64 | `src/kb_unit_19CB0.c` | 26 |
| sub_19D65 | kb_field_set_23 | 0x19D65 | 65 | `src/kb_unit_19CB0.c` | 26 (IDA-missed fn) |
| sub_19DA6 | kb_field_get_24 | 0x19DA6 | 64 | `src/kb_unit_19CB0.c` | 26 |
| sub_19DE6 | kb_field_set_24 | 0x19DE6 | 65 | `src/kb_unit_19CB0.c` | 26 |
| sub_19E27 | kb_clear_24 | 0x19E27 | 20 | `src/kb_unit_19CB0.c` | 26 |
| sub_19E3B | kb_field_get_25 | 0x19E3B | 64 | `src/kb_unit_19CB0.c` | 26 |
| sub_19E7B | kb_field_set_25_1 | 0x19E7B | 63 | `src/kb_unit_19CB0.c` | 26 |
| sub_19EBA | kb_field_set_25_0 | 0x19EBA | 63 | `src/kb_unit_19CB0.c` | 26 |
| sub_19EF9 | kb_field_get_26 | 0x19EF9 | 64 | `src/kb_unit_19CB0.c` | 27 |
| sub_19F39 | kb_field_set_26 | 0x19F39 | 65 | `src/kb_unit_19CB0.c` | 28 |
| sub_19F7A | kb_clear_26 | 0x19F7A | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19F8E | kb_field_get_27 | 0x19F8E | 64 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19FCE | kb_field_set_27 | 0x19FCE | 65 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A00F | kb_field_set_27_1 | 0x1A00F | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A023 | kb_field_get_28 | 0x1A023 | 80 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A073 | kb_field_set_28 | 0x1A073 | 73 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A0BC | kb_clear_28 | 0x1A0BC | 22 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A0D2 | kb_field_get_2c | 0x1A0D2 | 81 | `src/kb_unit_19CB0.c` | 28 (pragma -r-) |
| sub_1A123 | kb_field_set_2c | 0x1A123 | 83 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A176 | kb_field_get_2d | 0x1A176 | 96 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A1D6 | kb_field_get_31 | 0x1A1D6 | 117 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A24B | kb_field_set_31 | 0x1A24B | 65 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A28C | kb_count_2c | 0x1A28C | 82 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A2DE | kb_array_get_1 | 0x1A2DE | 106 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A348 | kb_array_set_1 | 0x1A348 | 107 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A3B3 | kb_array_get_2 | 0x1A3B3 | 112 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A423 | kb_array_set_2 | 0x1A423 | 113 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A494 | kb_flag_get_10 | 0x1A494 | 14 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A4A2 | kb_flag_set_10_1 | 0x1A4A2 | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A4B6 | kb_flag_set_10_0 | 0x1A4B6 | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A4CA | dgroup_long_get_08 | 0x1A4CA | 19 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |

Known-diff tracked: `sub_19C4C` (kb_record_name_get, 98B vs 100B NUL-peephole, finding 28).
Unverified tracked: `sub_10340` (hand ASM, `not_c-portable`).

## Code Coverage (fresh)

| Region | Functions | Notes |
|--------|-----------|-------|
| Resident image | 888 | entry, overlay mgr, video, input, sim core, keyboard unit (complete) + 59 gap-sweep |
| Overlay (rebuilt IDB) | 192 | via 184 thunk entries + analysis; cluster-B included |
| IDA-missed registered | 72 | kb-unit gap fns (findings 26/28) + 59 gap-sweep fns |
| **Total** | **1,080** | C-class 107 → 43 ported (+1 known-diff), **~64 remaining queue** |

Remaining tail: ~1.2 MB = RTLink record data + PKWARE assets (formats partially
decoded; `game/` has unpacked assets).

## Game Knowledge Base ✅
- `manual.pdf` (254 pp) → `manual_full.txt` → `registry/game_knowledge.yaml` (379 lines):
  game modes, campaign structure, pilot abilities, weapons, HUD/REO/DED, ACMI, controls.

## Immediate Next Steps (in order)

1. **DOSBox-Staging debugger build + dynamic trace harvester** (advice.md §3): build src/dosbox-staging with debugger enabled; instrument CPU core to log: (a) RTLink overlay loads (segment ↔ overlay ID), (b) INT 21h file I/O (filename ↔ function), (c) function entry DS/ES (symbolic classification: SEG_DGROUP, SEG_OVERLAY_ID(n), SEG_HEAP_ALLOC(callsite)). Redump menu/mission/sim for accurate address matching.
2. **Track C first splice test**: Export IDB assembly (`idat -A -Stools/ida_export.asm`), run `extract_routines.py` → `splice.py` with keyboard unit verified routines → reassemble → `mzdiff.py` verification against function_bytes.json ground truth.
3. **Fix mzdiff fixup handling**: Apply RTLink fixups when extracting bytes from EXE for accurate comparison.
4. **10 straggler thunk entries** (user explicitly deferred; findings 19/26).
5. `libscan.py` with compiler libs (MSC 5.1 *and* BC 2.0) for library-function ID.

## Open Items (not blockers — tracked in findings log)

- ~15 cluster-B rows' exact fixup positions; 14 fixup *types* exist — +L only proven
  for the dominant far-pointer type (findings 20/21); exotic before-words (0xC08E…).
- 10 unresolvable overlay thunk entries (their target bytes aren't code where mapped).
- Overlay byte content for 2 skipped rows (zero-span placeholders, finding 19).
- EMS/XMS runtime memory views not representable in the static IDB.
- Batch portcheck driver + per-routine asm transcripts (Track C) not built yet.

## Reference Projects

| Project | Relevance |
|---------|-----------|
| `f19re` | MSC 5.1 full rebuild; portcheck + mzdiff workflow reference |
| `gunship_2000` | RTLink decode source (findings 17), registry/pipeline templates, shared `mzdiff` (WSL `tools/f19re/mzretools/debug/`) |

## Artifacts (committed)

- `function_bytes.json`, `data_symbols.json`, `classification.json`,
  `overlay_placement.json`, `overlay_entries.json`, `fixups_to_apply.json`,
  `rtlink_records.json`, `record_fixup_located.json` — analysis ground truth
- `registry/{naming,routines,structs,game_knowledge,FALCONCD.EXE,OVL_1E10}.yaml`
- `docs/{pipeline,findings_log,toolchain,structures,overlay_fixups,prior_art}.md`
- `src/*.c` (annotated ports), `src/asm/frameless_families.asm` (59 annotated)
- `tools/naming.py`, `portcheck_falcon.py`, `obj_extract.py`, `classify_routines.py`,
  `gen_asm_families.py`, rebuild pipeline (`prep_*`, `rebuild_*`, `mark_*`, `apply_*`,
  `extract_ida_bytes.py`), `tests/test_naming.py`
- Local-only (NOT committed): `game/*.EXE`, `dos_compilers/` (BC 2.0 + MSC 5.1),
  IDB `*.i64*`
