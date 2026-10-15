# Artifacts
## Artifacts (committed)

- `function_bytes.json`, `data_symbols.json`, `classification.json`,
  `overlay_placement.json`, `overlay_entries.json`, `fixups_to_apply.json`,
  `rtlink_records.json`, `record_fixup_located.json` — analysis ground truth
- `registry/{naming,routines,structs,game_knowledge,FALCONCD.EXE,OVL_1E10}.yaml`
- `docs/{pipeline,findings_log,toolchain,structures,overlay_fixups,prior_art,advice,memdump}.md`
- `src/*.c` (annotated ports), `src/asm/frameless_families.asm` (59 annotated)
- `tools/naming.py`, `portcheck_falcon.py`, `obj_extract.py`, `classify_routines.py`,
  `gen_asm_families.py`, rebuild pipeline (`prep_*`, `rebuild_*`, `mark_*`, `apply_*`,
  `extract_ida_bytes.py`), `tests/test_naming.py`
- `tools/build_dosbox_debugger.ps1` (instrumented dosbox-staging build),
  `tools/memdump_inventory.py` + `analysis/memdump/inventory.json` (dump inventory)
- `tools/mine_traces.py`, `tools/verify_boundaries.py`,
  `tools/apply_trace_functions.py` + `analysis/traces/*` (trace mining +
  boundary repair, findings 32/33)
- `docs/memdump.md` (dynamic-dump tracker)
- Local-only (NOT committed): `game/*.EXE`, `dos_compilers/` (BC 2.0 + MSC 5.1),
  IDB `*.i64*`