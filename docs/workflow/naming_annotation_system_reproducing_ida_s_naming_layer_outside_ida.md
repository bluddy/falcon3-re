# Naming & Annotation System (reproducing IDA's naming layer, outside IDA)
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