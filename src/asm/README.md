# Annotated assembly (`src/asm/`)

Knowledge-capture protocol **sink #6**: comments annotating hand-ASM routines
(intent, register roles, structure) so analyses survive even without the IDB.

## What lives here

| File | Contents | Status |
|------|----------|--------|
| `frameless_families.asm` | The three frameless families (far-entry thunks, CS-data accessors, lcall dispatch stubs) — 59 routines with disasm + family-level intent comments | ✅ generated (findings 09/13/14) |

## Conventions

- **One file per family or per subsystem**, not per routine (500+ single-routine
  files would rot); routine-level hypotheses go in `registry/routines.yaml`.
- Header comment block = the canonical human analysis (why the code exists,
  what pattern to recognize, classification verdict). Generated member lists +
  disasm below it.
- Byte source of truth is always `analysis/ida_falconcd/function_bytes.json`
  (runtime/relocated bytes) — never re-disassemble raw EXE bytes (finding 15).
- Regeneration: `python tools/gen_asm_families.py` (extend the generator when
  classifying new families).

## Lifecycle

1. Classification (`classify_routines.py`) surfaces a family.
2. Human dissects one/few members → family header written here + finding logged.
3. Generated member table refreshed.
4. When a family member is **ported**: the C source in `src/` carries the
   per-routine annotation (disasm + reasoning) and the `.asm` entry stays as
   historical record — ported status is tracked in `registry/routines.yaml`.

## Not here (yet)

- Per-routine `.asm` transcriptions for Track C (hybrid rebuild) — will be
  produced by a `scripts/extract_routines.py` (gunship-style) when Track C starts.
- IDB function comments (binary, not committed) — convenience only; anything
  that matters must be duplicated into findings/registry/this dir.
