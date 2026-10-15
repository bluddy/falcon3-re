# Verified Facts
Certainty levels used across the knowledge bases: **PROVEN** (byte-level,
reproducible evidence), **STRONG** (multiple independent signals, not yet
byte-verified), **HYPOTHESIS** (educated guess), **UNKNOWN** (we do not know —
do not state as fact), **DISPROVEN**.

| Item | Status | Certainty | Evidence |
|------|--------|-----------|----------|
| Linker | ✅ RTLink/Plus | PROVEN | Strings, 18-byte directory, thunk table, loader disasm (findings 17/18) |
| Compression | ⚠️ **UNKNOWN — nothing decompressed by us** | HYPOTHESIS (PKWARE DCL) / UNKNOWN (format) | 2 × DCL copyright strings only; **0 × `PK\x03\x04` in the whole EXE** (finding 31); `game/` assets came from the game install, not from an extraction we performed |
| CRT | ❌ none embedded | STRONG | No CRT strings at all (startup is custom ASM) — CRT-based negatives are inconclusive (finding 22) |
| Compiler (C) | ✅ **Borland C++ 2.0** `bcc -c -ml -1 -O` | PROVEN | `sub_1A6D4` 44B byte-exact; enter/leave/imm0/or-si fingerprints (finding 22) |
| ~~Compiler (C)~~ | ~~MSC 5.1~~ | DISPROVEN for C | version-verified 5.10 + 6.00ax emit no enter under any flag (finding 22) |
| Compiler (ASM) | ✅ hand-written | PROVEN | 84 × `558BEC` with variable register saves |
| Code model | ✅ far/large | PROVEN | `retf`, stack args `[BP+6]`, caller cleanup |
| Overlays | ✅ RTLink | PROVEN | 70 records, schema + placement + fixups decoded (findings 17–21) |
| RESETALL.EXE | ✅ Borland C++ 1991 | STRONG | Strings/version resource (separate utility) |

---