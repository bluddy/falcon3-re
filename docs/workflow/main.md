# The Method
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