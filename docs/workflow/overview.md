# Overview
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