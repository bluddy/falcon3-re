# Falcon3 Toolchain & Build Evidence

## Compiler

**Microsoft C 5.1 for C modules + hand-written ASM**. Evidence:

### Ruled out
- **MSC 6.0**: No `B430CD21` signature, no CRT error strings, libscan found no matches.
- **Borland C++**: No Borland strings in main EXEs (only RESETALL.EXE has Borland 1991 strings).
- **Watcom**: No Watcom signatures detected.

### Confirmed: Microsoft C 5.1 for C modules
- **30 functions use `ENTER` instruction (opcode C8)** with various stack sizes (0x02-0x5A) — **Microsoft C 5.1 hallmark**.
- `ENTER` stack sizes observed: 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0A, 0x0E, 0x10, 0x14, 0x16, 0x1C, 0x38, 0x3C, 0x54, 0x5A — matches MSC 5.1 codegen.

### Hand-written ASM majority
- **84 functions use manual `55 8B EC` (push bp; mov bp, sp)** with **highly variable register save order** — hand-tuned ASM.
- First register saved after `55 8B EC`: SI (66), `mov ax` (37), `mov` (7), DS (7), `sub` (7), `push` (5), etc. — no consistent compiler pattern.
- **0 functions use `55 8B EC 83 EC`** (standard C `sub sp, XX` for locals) — no standard C stack frames.
- 170 prologues with segment overrides (CS/DS/ES/SS) — heavy far-pointer/segment manipulation.

### Calling convention
- **Far model**: 466/817 functions far (`retf`), 488 `retf` instructions.
- **C modules**: Use `ENTER` / `LEAVE` / `RETF` (4 functions with `LEAVE;RETF`).
- **ASM modules**: Manual `push bp; mov bp, sp` + custom register save + `RETF`/`RET`.
- **No standard C stack frames**: **0 functions** use `sub sp, XX` (`83 EC`) for locals.
- Parameter passing: Stack-based `[BP+6]` for far calls, registers for ASM.

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