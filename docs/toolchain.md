# Falcon3 Toolchain & Build Evidence

## Two toolchains — read this first

| Track | Compiler(s) | Role |
|-------|-------------|------|
| **D (ADOPTED — forward path)** | **Modern C++ only**: g++ (`-std=gnu++11 -m32` in CI/MinGW test builds) and **MSVC 14.39 (VS2022, x64)** when building inside dosbox | masm2c-generated C++ + m2c runtime linked into **libdosbox** custom profiles (pipeline.md Track D). **No era compiler, no Ghidra.** |
| B (verification — historical) | Borland C++ 2.0 / MSC 5.1 (sections below) | Byte-for-byte port verification only (`portcheck`, `.cod` compares) — never builds the forward path |

## Compiler — REVISED 2026-10-11 (finding 22): **Borland C++ 2.0**

**C functions: Borland C++ 2.0** (`dos_compilers/bcc2.0`), exact recipe:
```
bcc -c -ml -1 -O        (large model / 80186 / optimize)
```
**Proof**: `sub_1A6D4` (44 B) compiles byte-for-byte identical to the IDB
(`tools/obj_extract.py` on native BCC OBJ; portcheck `--cc bcc` green end-to-end).

### BC codegen fingerprints (present in original, reproduced by BC only)
- `enter size,0` prologue + `leave; retf` epilogue — **requires `-1`/`-2`** (80186+);
  without `-1` BC emits `push bp; mov bp,sp; sub sp,N`
- `mov word ptr [bp-N],0` (imm-zero) for `long = 0` (MSC: xor+stores)
- `adc word [bp-N],0` for unsigned long accumulation (MSC: `cwd` sign-extend)
- `or reg,reg` for zero tests; SI-held loop counters (params not written back)
- **`-O` required**: without it BC emits redundant `jmp short $+2` (`eb 00`)
  before epilogue pops (seen in native OBJs)
- **Pointers**: in `-ml` plain `char *` is FAR (int→far cast yields seg:0!);
  DS-segmented conversion needs an explicitly `near`-typed right side
  (finding 23); intermediate pointer vars spill/hijack registers
- **Same-module far calls** compile to `push cs; call rel16` (4 B); externals to
  `call far imm` (5 B) + fixup — original units bundled adjacent functions

### Ruled out (re-tested with version-verified binaries)
- **Microsoft C 5.10** (Feb 1988 banner verified in `rbin\CL.EXE`): no flag
  combination (`/O /Os /Ot /Ox /Od /Oa /Og /Oe` + combos) emits enter/leave;
  prologues always `push bp`, epilogues `mov sp,bp; pop bp`.
- **Microsoft C 6.00ax** (gunship's install): same — `push bp; mov bp,sp; sub sp,N`.
- **MSC 6.0 CRT signature** `B4 30 CD 21`: irrelevant — Falcon embeds **no CRT**
  (startup is custom ASM), so CRT-derived negatives prove nothing.
- **"No Borland strings in main EXEs"**: same fallacy — strings came from the CRT
  Falcon doesn't link. (RESETALL.EXE separately = Borland C++ 1991.)
- Watcom: no signatures detected (still low-priority).

### What remains true from the old analysis
- **Hand-written ASM majority**: 84 functions with manual `55 8B EC` and highly
  variable register-save order (findings 13: ASM class ≈ 695 incl. data).
- Far/large model, stack args `[BP+6]`, caller-cleanup — unchanged observations.
- The 2 initially verified leaves (`b8 xx cb`) are compiler-agnostic bytes.

### Prior (DISPROVEN) claim — kept for history
~~**Microsoft C 5.1 for C modules**: 30 `ENTER` prologues = "MSC 5.1 hallmark".~~
ENTER turned out to be **Borland's** with `-1`; see findings_log 22. MSC 5.1
remains installed (`dos_compilers/msc5.1`) for `--cc msc` comparison runs only.

### CRT / Startup
- **No standard CRT**: No MSC 6.0 signature `B4 30 CD 21`, no CRT error strings.
- Custom ASM startup (`start` at 0x2B19C) → jumps to thunk table → overlay loader.
- `RESETALL.EXE` is Borland C++ 1991 (separate utility).

## Linker

**RTLink/Plus** (Phar Lap / Rational Systems). Strings in EXE:
```
Internal error in .RTLink(R)/Plus run-time code.
eov0001: ... eov0009:
Overlay Manager Internal Reload Stack Overflow
Overlay Manager Internal Reload Stack Underflow
```
Overlay directory at resident image `0x1AA3:0x0C1F` (file `0x1E24F`): 70 entries × 18 bytes:
```
struct { word seg; word const_12ED; dword tail_off; word const_400;
         word A; word B; word C; word id; word A2; }
```
Fields: `seg` = runtime segment, `tail_off` = offset in tail (relative to `0x1FB51`), `A` = record size, `B` = ?, `C` = group/class (0,5,0xD,0x10,0x12,0x1D,0xFFFF), `id` = thunk table index.

## Overlay Structure (RTLink)

- MZ header: `hdr=0x2C00`, `image=0x1CF51`, tail starts `0x1FB51`, tail len `0x12FA96`.
- Resident image loads at paragraph `0x1000` (IDA linear `0x10000`). Entry `CS:IP = 0x1AA3:0x076C` → linear `0x2B19C`.
- Overlay segments load at runtime paragraphs `0x1CF6, 0x1D0D, 0x1D31, 0x1E10, 0x569F, 0x5CD9, 0x5DFF, 0x5E0B, 0x5E8F, 0x5F6C, 0x606E, ...` relative to load base.
- Thunk table at `0x1AA3:0x157F` (file `0x1EBAF`): 10-byte entries `E8 disp16` (call loader) + `EA off seg` (ljmp) + `word id`.
- 9 distinct overlay groups in 18-byte directory covering ~68 KB of records; tail is 1.2 MB ⇒ majority of tail uses different structure (compression/format **UNKNOWN** — previously misattributed to PKWARE, finding 31).
- CS/DS overlap: multiple overlay groups share runtime paragraphs (e.g., `0x569F` group spans 64 KB). DS can be remapped anywhere; EMS/XMS used for additional memory views.

## Compression

**PKWARE Data Compression Library** (strings: "Copyright 1990-92 PKWARE Inc.", Patent 5,051,745) — the DCL runtime **is linked into the EXE** (2 copyright strings). However: **0 × `PK\x03\x04` signatures exist anywhere in FALCONCD.EXE** (finding 31), and no decompression routine has been confirmed or exercised. Whether/how the 1.2 MB tail is compressed is **UNKNOWN** (HYPOTHESIS: DCL `implode`, based on the linked library alone).

## Code Composition

- **Far/large model**: 466/817 functions far (retf), 488 retf instructions.
- **C evidence**: standard prologue `55 8B EC` (262 in image, 484 in tail), stack args `[BP+6]`, `retf`, `LES BX,[BP+0xA]`, caller cleanup `ADD SP,0xE`.
- **ASM evidence**: register dispatch, `PUSH CS / CALL`, `MOV AH,9 / INT 21h`, `IN AL,DX / INT 15h` (joystick), `CALL WORD PTR CS:[BX]`.
- C/ASM ratio ≈ 60/40 by function count; large functions (`>1KB`) are C-compiled (caller cleanup, stack frames).

## FLIRT / Signatures

IDA 9.1 applied **0 FLIRT signatures** (16-bit MZ sigs limited). No library functions auto-named.

## Other EXEs

- `RESETALL.EXE` (7,433 bytes): **Borland C++ 1991** (garbled strings: "Borland C++ -opyright 1991 Intl Divide err Abnormal program termination").
- `HORNETCD.EXE` / `MIGCD.EXE`: same RTLink structure, different `CS:IP` (0x1A99:076C / 0x1A4E:076C), likely same codebase with different assets.
- `FALCON3.SMP`: unknown (sound/music?).

## Reference Toolchains (from sibling projects)

| Project | Compiler | Assembler | Linker | Notes |
|---------|----------|-----------|--------|-------|
| `f19re` | MSC 5.1 | UASM (JWASM) | LINK 3.65 | Full rebuild, verified with `portcheck.py` + `mzdiff` |
| `gunship_2000` | MSC 6.00ax | MASM 6.11 | LINK 5.10 | Overlay extraction via `extract_overlays.py`, Ghidra placement |

Both use DOSBox + MSC 6.0 install for reproducible builds. Falcon3 toolchain TBD.