# Borland C++ 2.0 Codegen Rules
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