# Executive Summary
Falcon 3.0 (`FALCONCD.EXE` + variants) is a **DOS 16-bit far/large-model** game:
**Borland C++ 2.0** for C modules (`bcc -c -ml -1 -O` — finding 22, byte-proven),
**hand-written ASM** for the rest, **RTLink/Plus** overlay linker, a linked-in
**PKWARE DCL** library (string evidence only — the actual compression of the tail
assets is **UNKNOWN**, finding 31), **no embedded CRT**. 1.37 MB: 118 KB resident
image + 1.2 MB overlay/asset tail.

**Where we are** (all proven, see Current State):
- Ground truth: **1,215 functions** with exact runtime bytes (135 recovered
  from runtime far-call entries, finding 33); resident validated
  888/888 against raw EXE + MZ relocations; overlay system fully decoded and IDB
  rebuilt (68 segments, 25,222 fixups applied, plan 1.2b 5/5).
- **43 C routines / 2,282 bytes ported byte-exact** through a working portcheck
  loop, including the completed 2,270-byte keyboard translation unit (38 functions).
- **Key codegen insight (finding 29)**: BC 2.0 produces byte-exact output for functions with
  ≤1 external far call + intra-module `push cs; call rel16` call chains (same TU).
  Multiple external far calls + local buffers trigger spilling/frame growth.
- The **rename/annotation layer exists outside the IDA DB** (ledger + structs + globals
  inventory + tested Python tooling + IDB push), so the fragile binary DB is now a
  regenerable view, not a dependency.
- **Rebuild**: yes via splice (Track C) — verified bytes patched into the original
  scaffold keep all relocations/RTLink structures valid by construction; `mzdiff` is
  the verifier. From-scratch rebuild documented as out of scope.

---