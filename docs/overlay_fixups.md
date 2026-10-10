# RTLink Fixup Stub Analysis - Complete

## Record Layout in Tail

The RTLink tail (1.2 MB at file offset 0x1FB51) contains **68 overlay records** interleaved by segment in file offset order. Each record consists of:
1. **Record data** (A bytes at `tail + off`) - code + optional entry table
2. **Fixup stub** (gap to next record in FILE OFFSET order) - loader/relocation code

## Segment Groups (by C field)

| C | Records | Code Bytes | Fixup Bytes | Segments | Description |
|---|---------|------------|-------------|----------|-------------|
| 0x0000 | 8 | 35,255 | ~13 KB | 0x1CF6, 0x1E10 | Core overlays (adjacent to resident) |
| 0x0005 | 9 | 1,727 | 144 | 0x5CD9, 0x5DFF | Small overlays |
| 0x000D | 2 | 1,029 | 115 | 0x5E0B | |
| 0x0010 | 2 | 589 | 187 | 0x5E8F | |
| 0x0012 | 8 | 390 | 106 | 0x5F6C | UI/menu overlays |
| 0x001D | 38 | 23,949 | 4,049 | 0x569F | Large sparse segment (64 KB span) |
| 0xFFFF | 1 | 5,438 | 5,347 | 0x606E | Final overlay |

**Total**: 68 records, ~68 KB code, ~10 KB fixup stubs

## Records with Entry Tables (Repeated Segment in Header)

| ID | Segment | Repeated Seg | Entries | Description |
|----|---------|--------------|---------|-------------|
| 52 | 0x569F | 0x1D0D | 102 | Main entry table for segment 0x569F |
| 68 | 0x569F | 0x1F64 | 103 | Secondary entry table |
| 69 | 0x569F | 0x1F64 | 99 | |
| 8 | 0x5CD9 | 0x400C | 73 | Entry table for segment 0x5CD9 |

## Large Fixup Stubs (>200 bytes)

| ID | Segment | Fixup Size | Next ID | Description |
|----|---------|------------|---------|-------------|
| 71 | 0x606E | 5,347 | 8 | **Largest** - fixup for id7 group (id7 spans ids 62-71) |
| 31 | 0x1E10 | 1,744 | 32 | Large fixup for id31 (14 KB record) |
| 55 | 0x569F | 494 | 56 | |
| 32 | 0x569F | 591 | 33 | |
| 55 | 0x569F | 494 | 56 | |
| 50 | 0x569F | 349 | 51 | |
| 29 | 0x1E10 | 266 | 30 | |
| 58 | 0x569F | 223 | 59 | Contains strings ("FORWARD AND BACK") |
| 32 | 0x569F | 591 | 33 | |

## Fixup Stub Format

The fixup stubs are **executable x86 code** (16-bit) that the RTLink overlay loader executes after loading the record data. They perform:

1. **DOS file operations** (INT 21h):
   - AH=3Fh: Read from file
   - AH=3Eh: Close file
   - AH=40h: Write to file
   - AH=42h: Seek

2. **Segment relocation**:
   - Load pointers from CS:[0002], CS:[0004] (overlay header in PSP)
   - Apply segment base to far pointers in record code

3. **Register cleanup**: POP ES, DS, DI, SI, BP before return

Example (id52 fixup stub, 117 bytes):
```
MOV AH, 40h      ; DOS write
MOV DX, 0
INT 21h
MOV AH, 42h      ; DOS seek
MOV CX, 0
MOV DX, 0
MOV BX, CS:[0002]
INT 21h
MOV CX, 0FE00h
MOV BX, CS:[0002]
INT 21h
MOV AH, 3Fh      ; DOS read
MOV DX, 0
INT 21h
MOV AH, 3Eh      ; DOS close
MOV BX, CS:[0004]
INT 21h
MOV AH, 3Eh
MOV BX, CS:[0002]
INT 21h
POP ES
POP DS
POP DI
POP SI
POP BP
```

## Record File Offset Layout (Interleaved)

Records are **not stored sequentially by ID** - they're interleaved by segment in file offset order:

```
Tail start (0x1FB51):
  0x006D: id52 (569f, 408B) -> fixup 117B
  0x027A: id53 (569f, 750B) -> fixup 200B
  0x0630: id54 (569f, 285B) -> fixup 83B
  ...
  0x1FB6: id3  (1CF6, 89B)   -> fixup 13B
  0x201C: id4  (1CF6, 282B)  -> fixup 1B
  0x2137: id5  (1CF6, 277B)  -> overlaps id61!
  0x2158: id61 (569F, 1210B) -> overlaps id5!
  0x2267: id6  (1CF6, 59B)
  0x22A5: id7  (1E10, 16KB)  -> spans 0x22A5-0x616E, encompasses ids 62-71!
  0x2761: id62 (569f)        -> inside id7
  ...
  0x3AC0: id71 (606E) -> fixup 5347B (id7's fixup stub!)
  0x64E1: id8  (5CD9) ...
```

**Key insight**: Record id7 (16 KB at segment 0x1E10) is a **composite overlay** that spans file offsets 0x22A5-0x616E, encompassing all 569F segment records (ids 62-71). Its fixup stub is the 5,347-byte gap after the last 569F record (id71), which is also id71's fixup stub.

## Fixup Stub Binary Files

Extracted to `analysis/ida_falconcd/fixup_stubs/fixup_id{id:03d}_next{next_id}.bin` (63 files).

## Application for Decompilation

To properly analyze overlay code in IDA:
1. Load record data at runtime segment:offset
2. Apply fixup stub relocations manually (or script):
   - Find far segment references in code (e.g., `MOV AX, SEGxxxx`, `CALL SEG:OFF`)
   - Apply segment base relocation (add load segment base)
   - Fixup stubs show which offsets need relocation (via CS:[0002]/CS:[0004] references)
3. For composite overlays (id7), apply fixups from the composite stub (id71's 5KB stub)

## Files Generated

- `analysis/ida_falconcd/rtlink_records.json` - Complete record map
- `analysis/ida_falconcd/fixup_stubs/fixup_id{id:03d}_next{next_id}.bin` - 63 binary fixup stubs