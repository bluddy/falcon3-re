# How the Code Interprets Embedded Data (Parser RE)
## How the Code Interprets Embedded Data (Parser RE)

The EXE is not just code: runtime code parses structures **stored inside the EXE
itself** (and external DAT files). Reversing these parsers is a first-class goal —
each one (a) unlocks a data format for the registry, (b) is itself a self-contained,
byte-verifiable porting target, and (c) constrains how a rebuild must lay data out.

Known/anticipated embedded-data parsers, priority order:

| Data interpreted by code | Where it lives | Status |
|---|---|---|
| RTLink overlay directory (70 × 18 B) | resident image `0x1AA3:0x0C1F` (file `0x1E24F`) | ✅ struct decoded statically; **loader code at `0x1AA3:0x0590` not yet read** |
| RTLink thunk dispatch (86 × 10 B) | `0x1AA3:0x157F` | ✅ struct decoded; dispatch code is the gateway resident→overlay |
| Fixup tables (1569 entries, 14 types) | per-record tail | ✅ decoded statically; the applier routine proves the format |
| Tail 4-byte directory (51 entries) | file `0x1FB61` | ⚠️ parsed; runtime use unverified |
| Tail compression (if any) | 1.2 MB tail | ❌ **UNKNOWN** — DCL library linked (2 strings) but 0 × `PK\x03\x04` in file; framing never mapped; nothing decompressed (findings 04 superseded by 31) — test via `blast` carving + runtime dumps |
| External DAT formats (`ARMSTABL.DAT`, mission/save/ACMI files) | `game\` dir (plain files from install) | ❌ parsers in EXE not yet identified — find via string xrefs |
| MZ header + relocation table | file head | ✅ decoded (`mzhdr.py`); DOS applies at load |

Method: locate the parse code (xref from the loader/string), document the format in
`docs/structures.md`, then treat the parser as a normal Track 2 porting candidate.

---