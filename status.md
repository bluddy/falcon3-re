# Falcon3 Decompilation Status — handover document

**Last updated**: 2026-10-12 (session 9 — see Time Log; always bump + append row)
**Branch**: master (HEAD `eb53f8b` at time of writing)
**Snapshot**: `analysis/ida_falconcd/FALCONCD.EXE.i64` (IDA Pro 9.1, headless only)

> This file is the **entry point for a future agent**. It states the exact current
> state and the exact method. Deep rationale lives in `docs/findings_log.md`
> (append-only history, findings 1–26), detailed procedures in `docs/pipeline.md`.
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
| 2026-10-11 (session 4) | same day | **Findings 20+21: cluster-B FOUND (B0=0xFFFA0)** — all 70 rows placed → 68 segments / 1,053,376 B; **fixups applied: 25,222 × +0x1000** byte-guarded; entries 250 → **192 overlay fns, 1,007 total**; C=97 with relocated DGROUP. **plan 1.2b 5/5 core done** |
| 2026-10-11 (session 5) | same day | **Finding 22: COMPILER REVISED — Borland C++ 2.0 `bcc -c -ml -1 -O`** (user installed; enter/leave = BC; MSC 5.1/6.0 re-tested → no enter, DISPROVEN for C); **sub_1A6D4 44B MATCH** end-to-end via new portcheck `--cc bcc` + `obj_extract.py`; toolchain.md rewritten. C-port queue resumed |
| 2026-10-11 (session 6) | same day | **Finding 23: chained same-module port** — sub_17A85 (79B, 4 fixups masked) + sub_17AD4 (61B incl. adjacency-dependent `call 0xFF7B`) **BOTH MATCH**; BC large-model rules decoded (char* = far!; `(char near*)` → DS conversion; decl-order of `int i=0`; one-expr flags). Fixup masking + ±0x1000 reloc normalization now in portcheck compare. **Verified: 5 routines** |
| 2026-10-11 (session 7) | same day | **Findings 24+25: sub_197EA (69B switch) + sub_19CB0 (55B) MATCH** — case table recovered from EXE via CS-base jump-target matching (CS=0x180F0); union far-ptr arithmetic + decl-order slot rules. **Verified: 7 routines / 382 bytes** |
| 2026-10-11 (session 8) | same day | **Finding 26: keyboard unit 10/10 MATCH (570B)** — contiguous 0x19CB0-0x19EF9 single translation unit ported (`kb_unit_19CB0.c`); assign-in-cond spill rule; **IDA-missed function sub_19D65 discovered via gap arithmetic + registered in IDB** (1008 fns); **totals: 16 verified / 846 bytes** |
| 2026-10-12 (session 9) | ~9 h | **Naming/annotation system built**: `registry/naming.yaml` ledger (16 renames) + `registry/structs.yaml` (5 structs) + globals inventory (1,968 `data_symbols.json`) + `tools/naming.py` (list/resolve/apply/revert/check/push-ida) + **21-test suite green**; C files renamed to semantic names; names pushed into IDB with key-stable re-extract verified; portcheck resolves ida⇄semantic; ground-truth regen runbook + rebuild verdict documented in pipeline.md |

---

## Executive Summary

Falcon 3.0 (`FALCONCD.EXE` + variants) is a **DOS 16-bit far/large-model** game:
**Borland C++ 2.0** for C modules (`bcc -c -ml -1 -O` — finding 22, byte-proven),
**hand-written ASM** for the rest, **RTLink/Plus** overlay linker, **PKWARE DCL**
asset compression, **no embedded CRT**. 1.37 MB: 118 KB resident image + 1.2 MB
overlay/asset tail.

**Where we are** (all proven, see Current State):
- Ground truth: 1,008 functions with exact runtime bytes; resident validated 815/815
  against raw EXE + MZ relocations; overlay system fully decoded and IDB rebuilt
  (68 segments, 25,222 fixups applied, plan 1.2b 5/5).
- **16 C routines / 846 bytes ported byte-exact** through a working portcheck loop,
  including one 570-byte multi-function translation unit and one IDA-missed function.
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
| Functions in ground truth | **1,008** (816 resident + 192 overlay) | `function_bytes.json` |
| Classification | ASM 695 / C 98 / DATA 129 / LEAF 79 / NEARTHUNK 7 | `classification.json` |
| Verified routines | **16 / 846 bytes** | `registry/routines.yaml` (`verified: MATCH`) |
| Rename ledger | 16 entries, all renamed + pushed to IDB | `registry/naming.yaml` |
| Struct definitions | 5 (4 confirmed, 1 hypothesis) | `registry/structs.yaml` |
| Globals inventoried | **1,968** (name=null until renamed) | `data_symbols.json` |
| Tests | **21 green** (`python -m unittest discover -s tests`) | `tests/test_naming.py` |
| Overlay IDB | 68 segments / 1,053,376 B (9 real + 59 synthetic, 2 skipped) | `overlay_placement.json` |
| Overlay fixups applied | 25,222 × +0x1000 (byte-guarded) | finding 21 |
| IDB regen cost | ~5 headless IDA runs (runbook below) | pipeline.md |
| Findings logged | 1–26 (append-only) | `docs/findings_log.md` |
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
`src/kb_unit_19CB0.c` as the model (10 functions, one file).

### 2. Borland C++ 2.0 codegen rules (byte-exact cheat sheet; findings 22–26)

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
idat -A -S tools\mark_overlay_entries.py       <IDB>   # 184 thunk entries -> ~192 fns
idat -A -S tools\apply_overlay_fixups.py       <IDB>   # 25,222 fixups
idat -A -S tools\extract_ida_bytes.py          <IDB>   # regenerate ground truth (keys stable)
venv\Scripts\python tools\classify_routines.py
venv\Scripts\python tools\naming.py push-ida           # re-sync semantic names
# host-side JSON regen only if the EXE changed: prep_overlay_placement.py ->
# prep_overlay_entries.py -> validate_fixup_semantics.py (then IDA steps above)
```
`idat` fails **exit=4** if the IDB is open in interactive IDA — close it first.
(Also: never open Falcon in the MCP-connected IDA — it holds the Gunship DB.)

---

## Verified Routines (16 / 846 bytes)

| IDA name | Semantic name | ea | B | Source | Finding |
|---|---|---|---|---|---|
| sub_16FDD | always_true | 0x16FDD | 4 | `src/sub_16FDD.c` | 08/22 |
| sub_2CB6E | always_false | 0x2CB6E | 4 | `src/sub_2CB6E.c` | 08/22 |
| sub_1A6D4 | long_accumulate | 0x1A6D4 | 44 | `src/sub_1A6D4.c` | 22 (first real port) |
| sub_17A85 | dgroup_record_writer | 0x17A85 | 79 | `src/sub_17AD4.c` (unit) | 23 |
| sub_17AD4 | widen_and_forward | 0x17AD4 | 61 | `src/sub_17AD4.c` (unit) | 23 |
| sub_197EA | key_mapper | 0x197EA | 69 | `src/sub_197EA.c` | 24 |
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

Unverified tracked: `sub_10340` (hand ASM, `not_c-portable`).

## Code Coverage (fresh)

| Region | Functions | Notes |
|--------|-----------|-------|
| Resident image | 816 | entry, overlay mgr, video, input, sim core, keyboard unit |
| Overlay (rebuilt IDB) | 192 | via 184 thunk entries + analysis; cluster-B included |
| **Total** | **1,008** | C-class 98 → 16 ported, **82 remaining queue** |

Remaining tail: ~1.2 MB = RTLink record data + PKWARE assets (formats partially
decoded; `game/` has unpacked assets).

## Game Knowledge Base ✅
- `manual.pdf` (254 pp) → `manual_full.txt` → `registry/game_knowledge.yaml` (379 lines):
  game modes, campaign structure, pilot abilities, weapons, HUD/REO/DED, ACMI, controls.

## Immediate Next Steps (in order)

1. **Port queue** (loop above): next targets — `sub_19EF9` (64B, keyboard-unit tail),
   then overlay C functions (`r33_e85` 45B, `r32_e73` 50B — same DGROUP patterns,
   fixup masking already handles their far ptrs), then the remaining C-class by size.
2. **Gap sweep** for more IDA-missed functions (technique proven by `sub_19D65`:
   contiguous call-displacement arithmetic; extend beyond one unit).
3. **10 straggler thunk entries** (user explicitly deferred; findings 19/26).
4. **Track C setup**: copy gunship's `extract_routines.py`/`replace_routines.py`,
   write `tools/splice.py`, build/locate `mzdiff` (WSL binary exists — see pipeline.md),
   then the first splice + mzdiff verification.
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
