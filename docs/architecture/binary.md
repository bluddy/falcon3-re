# Binary, Memory Model & Overlay System

*See also: `docs/structures.md` for MZ header, RTLink structs.*

---

## 1. Toolchain

| Fact | Value | Certainty |
|---|---|---|
| Compiler (C modules) | Borland C++ 2.0 (`bcc -c -ml -1 -O`) | PROVEN (finding 22) |
| ASM modules | Hand-written x86 real-mode ASM | STRONG |
| Linker | RTLink/Plus overlay linker | PROVEN |
| Compression | PKWARE DCL 1.11 (Patent 5,051,745) linked in | PROVEN (strings) |
| Compressed tail format | UNKNOWN — no PK signatures found | UNKNOWN (finding 31) |
| Memory model | DOS real mode, far/large (CS≠DS≠SS possible) | PROVEN |
| CRT | No standard CRT — custom asm startup | PROVEN |
| Sizes | 1,375,101 B total: 118,609 B resident + 1,243,798 B tail | PROVEN |

### File Layout

```
Offset       Size      Description
0x000000     0x2C00    MZ header (704 paragraphs) + 2,717 relocations
0x002C00     0x1CF51   Load image (resident code + data = 118,609 B)
0x01E24F     1,260 B   18-byte RTLink directory (70 records × 18 B)
0x01FB51     ...       RTLink tail: overlay data + fixup tables
0x01FB61     204 B     4-byte initial overlay load list (51 entries)
```

Entry point (IDA linear): `0x2B19C` = `0x1AA3:0x076C`

---

## 2. Memory Model (DOS real mode)

```
Paragraph  Linear (IDA)   Segment          Description
0x0000     0x00000        BIOS/DOS         BDA keyboard flags at 0x0000:0x0417
0x1000     0x10000        load base        MZ image loaded here
0x1AA3     0x1AA30        resident base    Entry, thunk table, overlay dir, loader
                0x2B19C  entry point      startup at 0x1AA3:0x076C
                0x2BAFF  thunk table      0x1AA3:0x157F (86 × 10B entries)
                0x2CF60  OVL_1CF6         Core overlay stubs
0x7A32     0x7A320        DGROUP           DS=SS=DGROUP throughout (finding 121, PROVEN)
0x85AE0    (runtime)      VGRAPH           Graphics driver heap block
           (runtime)      R05_1E10..       Game overlays loaded on demand
```

**DGROUP**: global data/stack segment, paragraph 0x7A32. `DS = 0x7A32` at startup, preserved throughout. `SS = DS = DGROUP`. Never changes at runtime.

**IDA addressing**: IDA maps at `0x10000` base. All IDA linear addresses = `link_para × 16 + 0x10000`. E.g. DGROUP: `0x7A32 × 16 + 0x10000 = 0x7A320`.

**Seg020 base**: `0x1F6C0` (DS for `op_dispatch` and many resident functions). Functions at addresses `0x20xxx` are in this segment; near offsets in CS tables are relative to `0x1F6C0`.

---

## 3. Overlay System (RTLink/Plus)

**PROVEN.** RTLink/Plus manages ~1.2 MB of overlays loaded on demand.

### Thunk Table (0x1AA3:0x157F, 86 entries)

Each 10-byte entry:
```
+0  E8 disp16    CALL rel16 → overlay loader at 0x1AA3:0x058D (linear 0x1DBBD)
+3  EA off seg   LJMP far → overlay function (patched after each load)
+8  word         RTLink record ID
```

Call sequence: thunk → loader checks residency → if evicted: load from disk, patch LJMP → JMP target. The thunk EA is the stable callable address.

### Overlay Directory (70 × 18B at linear 0x2E24F)

Each entry: `{seg, 0x12ED, file_para_fixups, 0x0400, A=size, B, C=group, id, A2}`.
Group codes: `0xFFFF`=startup/core, `5`=R05 primary overlays (~40KB), `0xD/0x10/0x12`=graphics/sound/input.

### Key Segments

| IDA segment | Link para | Group | Contents |
|---|---|---|---|
| Resident seg000-seg020 | 0x1000-0x1F6C | — | Core: IRQ, mouse, farobj primitives, 3D math |
| R05_1E10 | 0x1E10 | C=5 | Main game objects, farobj entity ops |
| R05_1EFE..R05_1F64 | 0x1EFE..0x1F64 | C=5 | Rendering, projection, game loop |
| R05_2ACF..R05_2B83 | — | C=5 | Terrain sampling, tile rendering |
| R05_3xxx..R05_4xxx | — | C=5 | Flight physics, entity behavior |
| R06_xxx | — | C=5 | Menu/UI subsystem |
| R07 (seg006-seg007) | — | C=0xD | Sound (OPL/SBI) |
| R12_xxx | — | — | State record entries |
| R14_5E0B | 0x5E0B | C=0xD | Stream read, farptr call gate |
| R17_5E8F | 0x5E8F | C=0x10 | UI event loop |
| R30_569F | 0x569F | C=0xFFFF | Loadout menu, record fields |
| VGRAPH | 0x75AE | (heap) | Graphics driver (runtime-loaded) |

---

## 4. Calling Conventions

### Far vs Near

```
push cs; call near ptr fn   → Near intra-segment (most common, same CS)
call far ptr fn             → Far inter-segment (crosses segment boundaries)
retf / retn                 → Far / near return
push es; push cs; call near ptr fn; pop es; retf  → Far-callable wrapper for near leaf
```

### Argument Passing (cdecl)

- **Stack**: caller cleans (`add sp, N` after call), parameters pushed right-to-left
- **Return**: AX (16-bit), DX:AX (32-bit or far ptr returned as seg:off), ES:DI (far pointer)
- **Callee-saved**: DS (always DGROUP), BP (frame pointer if used)
- **Scratch**: AX, BX, CX, DX, SI, DI (may be used freely)

### Register Conventions (hand-ASM leaves)

```
AX = param0 / return value
BX = param1 (or segment)
CX = param2 (count / loop)
DX = param3 (high word of 32-bit / segment)
SI = source pointer
DI = destination pointer
DS = DGROUP (preserved; sometimes temporarily changed for data access)
ES = scratch segment (save/restore if needed)
```

### Angle Encoding (14-bit fixed-point)

All heading/pitch/roll stored as 14-bit values in uint16:
- Unsigned heading/roll: 0..16383, wraps via `and ax, 0x3FFF`
- Signed pitch: −8192..8191 via `and ax, 0x3FFF; add ax, 0xE000; xor ax, 0xE000`
- Helper `fixed_angle_mask_3fff` (0x24980): unsigned 14-bit mask
- Helper `fixed_angle_fold_e000` (0x24988): signed folding

### Fixed-Point Math

16.16 format multiply-accumulate pattern (from `fixed_matrix_mul`):
```asm
imul bx              ; 32-bit product in DX:AX
add  ax, 4000h       ; round to nearest
adc  dx, 0
shl  ax, 1           ; normalize
rcl  dx, 1           ; DX = hi word of normalized product
```

### Op_dispatch Calling Variants

| Function | Signature | Use case |
|---|---|---|
| `op_dispatch` (0x2257B) | AX=handle, BX=op×2, CX=count, DX=buf_offset | Near call in-segment |
| `op_dispatch_far_entry` (0x22598) | Stack: BX,AX,CX,DX,DS | Far call with explicit DS (54 callers) |
| `op_dispatch_far_wide` (0x225B6) | Stack: BX,AX(handle),DX,CX, BL→CH(seek method) | Far call for lseek |
