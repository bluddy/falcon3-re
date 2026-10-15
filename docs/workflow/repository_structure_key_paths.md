# Repository Structure (Key Paths)
## Repository Structure (Key Paths)

```
C:\Users\yotam\projects\falcon3\
├── game/
│   ├── FALCONCD.EXE                # Primary target (1,373,671 B)
│   ├── HORNETCD.EXE / MIGCD.EXE    # Variants (same structure, different assets)
│   ├── RESETALL.EXE                # Borland C++ 1991 utility (separate toolchain)
│   ├── FALCON3.SMP                 # Sound/music (format TBS)
│   ├── manual.pdf                  # 254-page flight manual → manual_full.txt
│   └── ARMSDATA\*.DAT, REPORT.DAT # plain asset files (from game install; DISPLAY.DAT does not exist in game/)
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