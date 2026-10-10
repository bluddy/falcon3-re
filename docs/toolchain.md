# Falcon3 Toolchain & Build Evidence

## Compiler

**Not Microsoft C 6.0**. Evidence:
- MSC 6.0 CRT signature `B4 30 CD 21 3C 02 73` (mov ah,30h / int 21h / cmp al,2 / jnc) **absent** from FALCONCD.EXE (0 hits for `B430CD21`).
- No CRT error strings: "Microsoft", "Borland", "R6000", "Abnormal program termination", "run-time error" — none present in FALCONCD/HORNETCD/MIGCD.
- MSC 6.0 `crt0.asm` uses `extrn __acrtmsg:abs` to pull in the message module; absence of messages ⇒ no standard MSC 6.0 CRT linked.
- `libscan.py` fuzzy match (174s) against MSC 6.0 libraries (MLIBCE/LLIBCE/SLIBCE/CLIBCE = 610 modules each) found only one false-positive 90% hit (`qcfpvars.asm`, all-zero block).

**Likely**: hand-written ASM + C in far/large model, custom startup (no standard CRT). Falcon3 predates MSC 7.0 (1992); possible compilers: **Microsoft C 5.1**, **Borland C++ 2.0/3.0**, **Watcom C**, or pure MASM/TASM with C modules. No compiler fingerprints matched yet.

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
- 9 distinct overlay groups in 18-byte directory covering ~68 KB of records; tail is 1.2 MB ⇒ majority of tail uses different structure (likely PKWARE-compressed assets, `DISPLAY.DAT` etc.).
- CS/DS overlap: multiple overlay groups share runtime paragraphs (e.g., `0x569F` group spans 64 KB). DS can be remapped anywhere; EMS/XMS used for additional memory views.

## Compression

**PKWARE Data Compression Library** (strings: "Copyright 1990-92 PKWARE Inc.", Patent 5,051,745). Multiple `PK\x03\x04` signatures in tail.

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