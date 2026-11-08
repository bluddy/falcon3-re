# Falcon3 File Structures

## MZ Header (FALCONCD.EXE)

```
Offset  Size  Field                  Value
0x00    2     magic                  0x5A4D ('MZ')
0x02    2     last_page              0x0151
0x04    2     pages                  0x00FE (254)
0x06    2     nreloc                 0x0A9D (2717)
0x08    2     hdr_paras              0x02C0 (704)
0x0A    2     min_alloc              0x58D7
0x0C    2     max_alloc              0xFFFF
0x0E    2     init_ss                0x752C
0x10    2     init_sp                0x0800
0x12    2     checksum               0x0000
0x14    2     init_ip                0x076C
0x16    2     init_cs                0x1AA3
0x18    2     reloc_off              0x001E
0x1A    2     overlay_no             0x0000
```

Derived:
- Header size = 0x2C00 bytes (704 paragraphs)
- Load module size = (pages-1)*512 + last_page - hdr = 0x1CF51 bytes (118,609)
- Tail start = hdr + image = 0x1FB51
- Tail length = file_size - tail_start = 0x12FA96 (1,243,798 bytes)
- Entry point linear = 0x1AA3*16 + 0x076C = 0x1B19C (relative to image start)
- In IDA (load base = 0x10000): entry = 0x2B19C

## Relocation Table

2717 entries at file offset 0x1E. Each entry: `word offset, word segment` (relative to load base). Used by DOS loader to fix segment references. IDA creates ~64 segments from these.

## Entry Point Bootstrap

```
0x1AA3:076C  EA 7F 15 A3 1A    ljmp 0x1AA3:0x157F   ; jump to thunk table
```

## Thunk Table (Overlay Manager Call Stubs)

At `0x1AA3:0x157F` (file `0x1EBAF`). 10 bytes per thunk:
```
E8 xx xx          call overlay_loader      ; 0x1AA3:0x0590 (file 0x1DBC0)
EA yy yy zz zz    ljmp seg:off             ; target in overlay
WW WW             word record_id           ; matches 18-byte dir.id
```

Examples:
| id | ljmp target     | loader call |
|----|-----------------|-------------|
| 1  | 1D31:000A       | 0x058D      |
| 2  | 1CF6:04BF       | 0x058D      |
| 2  | 1CF6:0D01       | 0x058D      |
| 4  | 1CF6:000A       | 0x058D      |
| 5  | 1EFE:0205       | 0x058D      |
| 7  | 5CD9:09B7       | 0x058D      |
| 0xC| 5DFF:0F41       | 0x058D      |

## 18-Byte Overlay Directory (Resident Image)

At `0x1AA3:0x0C1F` = file `0x1E24F`. 70 entries:
```c
struct {
  uint16_t seg;        // runtime segment (relative to load base)
  uint16_t const_12ED; // always 0x12ED
  uint32_t tail_off;   // offset from tail start (0x1FB51)
  uint16_t const_400;  // always 0x0400
  uint16_t A;          // record size (bytes)
  uint16_t B;          // ? (fixup count? data size?)
  uint16_t C;          // group/class: 0,5,0xD,0x10,0x12,0x1D,0xFFFF
  uint16_t id;         // thunk table index (1-based)
  uint16_t A2;         // duplicate of A
};
```

Group summary (C, seg, count, span, total bytes):
```
C=0000  seg=1CF6  4  0x1FB6..0x22A2   707
C=0000  seg=1E10  4  0x22A5..0xBF0B  34,548
C=0005  seg=5CD9  3  0x64E1..0x674A    585
C=0005  seg=5DFF  6  0x6752..0x7084  1,142
C=000D  seg=5E0B  2  0x6B7C..0x6FAF  1,029
C=0010  seg=5E8F  2  0x70A8..0x7368    589
C=0012  seg=5F6C  8  0x73B0..0x7595    390
C=001D  seg=569F 39  0x006D..0xFF82  23,949
C=FFFF  seg=1CF6  1  0x0000..0x0000      0 (empty)
C=FFFF  seg=606E  1  0x3AC0..0x4FFE   5,438
```

Total record data: ~68 KB. Tail is 1.2 MB → remaining data is undecoded bulk (compression/format **UNKNOWN**, finding 31 — previously assumed PKWARE-compressed `DISPLAY.DAT`, which does not exist in `game/`).

## 4-Byte Directory (Tail Start) — REINTERPRETED, see finding 17

~~At tail + 0x10 = file `0x1FB61`. 51 entries of `uint16_t off, uint16_t seg`:~~
**This "directory" is actually record idx1's FIXUP TABLE** at file 0x1FB60
(w2=0x1F.B6 × 16): 50 dword (off,seg) pairs targeting seg 0x1CF6/0x1D0D/0x1D31 —
content identical to what we listed here. Record idx1's *data* starts at
0x1FC30 = filename string table (`MYTEMP`, `DISPLAY.DAT`, `FALCON3.`).
(True runtime locations of records = finding 17; file base per-row validation open.)

## RTLink Record Header (9 words / 18 bytes) — from gunship_2000 (finding 17)

```c
struct rtlink_rec {          // 70 entries at file 0x1E24F (ids 2..71 = index+2)
  uint16_t w0;               // load base (LINK para) — runtime = w0 + 0x1000
  uint16_t w1;               // filename ptr (constant 0x12ED region)
  uint16_t w2;               // file para of fixup table (file_off = w2*16);
                             //   chain rows 0..49: direct; cluster-B rows 50..69:
                             //   window = 0x100000 + w2*16, fixups-first like every
                             //   other row (finding 118; finding 20's 0xFFFA0 was 0x60
                             //   early, and row69's "code-first" was that same error)
  uint16_t w3;               // low: 0x0400; HIGH BYTE = flags: 0x04 transient, 0x01 startup
  uint16_t w4;               // allocated span (PARAS)
  uint16_t w5;               // fixup count in DWORDS  => fixup bytes = w5*4
  uint16_t w6;               // 0xFFFF
  uint16_t w7;               // id (2..71); loader indexes table by 0-based idx: ax*18+0xC1F
  uint16_t w8;               // data size in paras (== w4 for most; row69 w8 < w4 = BSS tail)
};
// record layout: [fixup table w5 dwords][align16][data]   (ALL rows, incl. 69)
// data_start = w2*16 + align16(w5*4)
```
Runtime placement (finding 18, CONFIRMED):
```
block = [(0x1000 + w0) << 4, + w4*16)      // transient records sharing w0 OVERLAP
thunk word = 0-based dir row index         // loader loads row[word], jumps to ljmp target
fixup seg field ∈ [w0, w0 + w4) (any paragraph in the record's block)
```
Fixup application (finding 21, APPLIED to IDB — 25,222 patches):
```
location = (seg + 0x1000) << 4 + off       // link-time seg -> IDA runtime (+L)
word[loc] += 0x1000                        // dominant far-pointer type; ~14 types exist,
                                           // exotic before-words pending per-type decode
// guard: only where IDB byte == file byte (clip-shadow overlaps skipped: 177+144)
```
Thunk table: 10B = `E8 disp16; EA off seg; dw index` — index = 0-based dir row
(verified: rows 6,7,8 → seg 5CD9 targets etc.). Thunk ljmp operands are NOT MZ-relocated
(the loader patches them; runtime para = stored + 0x1000).

## Record Layout in Tail

Each record at `tail + off` (from 18-byte dir):
- First `A` bytes = code/data
- Followed by fixup table (size related to `B`?)
- Gaps between records variable (3-883 bytes)

Not yet fully decoded: record headers, fixup format, segment grouping logic for C=0x1D (39 records spanning 64 KB of address space but only 24 KB data).

## String Table (Resident Image, partial)

```
0x2AA54: "Cannot find overlay file \""
0x2AA6F: "eov0002: "
0x2AA79: "Open error on overlay file \""
0x2AA96: "eov0003: "
0x2AAA0: "Read error on overlay file \""
0x2AABD: "eov0007: "
0x2AAC7: "Commit error - section "
0x2AAE2: "H intersects committed section "
0x2AB13: "Vector at xxxx:xxxx is corrupted.\r\n"
0x2AB37: "eov0004: "
0x2AB41: "Overlay Manager Internal Reload Stack Overflow\r\n      -- use RELOAD to increase size\r\n"
0x2AB98: "eov0005: "
0x2ABA2: "Overlay Manager Internal Reload Stack Underflow.\r\n"
0x2B4A8: "C,P,EPATH,A"
0x2CB83: "Fatal Error $\r\nPress any key to terminate.$ege0001: "
0x2CBB8: "Internal error in .RTLink(R)/Plus run-time code.\r\n"
0x2E2F4: "ARMSDATA\\ARMSmmaa.DAT"
0x2E30A: "  mm   aa ARMSDATA\\ARMSTABL.DAT"
```

## Joystick Calibration Strings (Overlay, linear 0x67B00+)

```
"HEN PRESS BUTTON"
"MOVE THROTTLE ALL THE WAY FORWARD AND BACK"
"THEN PRESS BUTTON"
"MOVE RUDDER ALL THE WAY RIGHT AND THEN LEFT"
"AND PRESS BUTTON"
"HE JOYSTICK IS NOT"
"ESPONDING."
"E HAVE DETECTED A SEPARATE THROTTLE CONTROL "
"ON YOUR SYSTEM. DO YOU WANT TO ACTIVATE IT , Y/N?"
"E HAVE DETECTED A SEPARATE RUDDER CONTROL "
"N YOUR SYSTEM. DO YOU WANT TO ACTIVATE IT , Y/N?"
```

## Memory Map (Runtime)

| Range (paragraphs) | Linear (base 0x10000) | Content |
|--------------------|------------------------|---------|
| 0x1000 – 0x2CF5    | 0x10000 – 0x2CF51      | Resident image (118 KB) |
| 0x2CF6 – 0x2E0F    | 0x2CF60 – 0x2E0FF      | Overlay seg 0x1CF6 (core) |
| 0x2E10 – 0x3AB8    | 0x2E100 – 0x3AB8F      | Overlay seg 0x1E10 (large) |
| 0x569F – 0x5D9E    | 0x569F0 – 0x5D9EF      | Overlay seg 0x569F (64 KB, sparse) |
| 0x5CD9 – 0x5DFF    | 0x5CD90 – 0x5DFFF      | Overlay seg 0x5CD9/0x5DFF |
| 0x5E0B – 0x5E8E    | 0x5E0B0 – 0x5E8EF      | Overlay seg 0x5E0B/0x5E8F |
| 0x5E8F – 0x5F6B    | 0x5E8F0 – 0x5F6BF      | Overlay seg 0x5E8F/0x5F6C |
| 0x606E – 0x61C1    | 0x606E0 – 0x61C1F      | Overlay seg 0x606E |
| ... up to 0x85AC   | ... 0x85AC1            | Reloc-created placeholders (empty) |

DS can be set to any paragraph; EMS (INT 67h) and XMS (INT 2Fh multiplex) used for extended memory.

## ISLDAT (Per-Theater Coastline/Water-Body Vectors) — finding 105

8 files in `game\`: BOS 7875, HOK 7983, IRQ 7645, ISR 6787, KOR 7601, NEL 2037,
PAK 1297, PAN 7885 bytes. Filename chosen by theater manifest (`game\ISRAEL.MFF/MFI/MFM`);
loader = `isldat_state_load` (sub_12FC4, finding 106): reads block id 0x27 (farptr table
7075:id*4 = 0x9C) via `op_dispatch`, 9B header → `word_11C16/11C18/11C1A/byte_11C0A`,
body → `state_seg` (71C1:0000). Fully decoded from file bytes + resident asm consumers;
**validated 8/8 theaters by `tools/parse_isldat.py` (ALL OK, zero errors/warnings)**.

### Header (9 bytes)

```
+00 u16 body_len      (= file_size - 9)
+02 u16 grid_base     (0 in all 8; written to word_11C16, added to grid indices by walk)
+04 u16 t1_base       (always 0x500)
+06 u16 t2_base       (0x504..0x7CA, first list starts right after t2 table)
+08 u8  swap_flag     (1 for HOK/KOR/PAN; byteswaps ONLY the state_table_apply
                        3-byte records at body+0x56 — grids/lists/records stay LE)
```

### Body layout (loaded at `state_seg`:0000 = 71C1:0000 by `isldat_state_load`; grid base `word_11C16` = 0)

```
0x0000  gridB (fine)   4 quadrant blocks x 256B (16x16 cells/quadrant)
0x0400  gridA (coarse) 4 quadrant blocks x  64B ( 8x8 cells/quadrant)
then    t1 table, t2 table, then all record lists (FFFF-terminated), then
        feature records packed back-to-back (header + points + op-stream +
        sub-records inline; each sub ends exactly at the next record / list end)
```

Grid walk (asm `pos_neighbor_norm_scan` 0x14B17; X,Y = quadrant-local cell
coords; physical scale pending matrix decode):

```
q     = ((AX + 0x800) & 0x3FFF) rol 4 & 3        ; AX = caller arg (source OPEN)
gridB = body[0x000 + q*0x100 + (Y&~1)*8 + (X>>1)] -> byte = t1 list index
gridA = body[0x400 + q*0x40  + (Y&~3)*2 + (X>>2)] -> byte = t2 list index
word_11CC4 = q<<8 (gridB base), word_11CC6 = q*64+0x400 (gridA base)
; X,Y: X=word_11C24 (col), Y=word_11C26 (row)
```

### Tables (t1, t2) — extent by FIXED POINT (correction: NOT FFFF-scan)

Each table is K u16 entries. **K = the unique value where
`min(u16[base .. base+2K-2]) == base + 2K`** — i.e. the first list word sits
immediately after the table, so the table's own extent is the fixed point of
"first list ptr". A naive "scan to first FFFF" is WRONG (HOK t1 would yield
82→86, PAN 85→..., because FFFF list terminators in list space fake a larger
table). Invariant (all 8 files): `grid_max < K` for both grids.

Each entry is a pointer to an **FFFF-terminated list** of feature-record offsets
(body-relative). t1 lists → fine pool (pool B, from gridB); t2 lists → coarse
pool (pool A, from gridA); pools are disjoint (no shared records). Entry order
in the table is NOT monotonic (HOK/PAN shuffled). Value 0 grids (PAK) → all
lists empty.

### Feature record (header 0x36 + points + op-stream)

```
+00 i32 x            ; 16.16 nm fixed (world wrap 512 nm); asm reads dword at +0/+4/+8
+04 i32 y            ; (CORRECTION: earlier session misread +00 as u16 flags)
+08 i32 z            ; ~ -50 LSB (0xFFFFFFCE) = sea marker on all observed records
+0C i32 const_0
+10 12B zero padding
+1E u16 const_FFFF
+20 u16 attr         ; 0x14 always; also 0x32 (HOK/IRQ/ISR/PAN), 0x64 (BOS/HOK/KOR),
                     ;   0xC8 (BOS/HOK) — semantics unknown
+22 u16 self+0x26    ; engine self-relative ptr (-> the FFFF at +26)
+24 u16 const_000B
+26 u16 const_FFFF
+28 u16 const_0
+2A u16 self+0x2E    ; engine self-relative ptr (-> point_count)
+2C u16 const_4
+2E u16 point_count
+30 u16 self+0x38    ; points ptr (absolute body offset)
+32 u16 points+6*count ; op-stream ptr (absolute)
+34 u16 const_0
+38 points: count x { i16 p0, i16 mid=0 (always), i16 p2 }   ; 6B/point
then   op-stream: u16 sub-record offsets, FFFF-terminated
then   sub-records inline (each ends at next sub/record boundary)
```

### Sub-record

```
+00 u16 flags   ; 0x1000/0x1002 = node chain; 0x0000/0x0002 = SINGLE node
+02 u16 opcode  ; 0x0000/0x0001/0x0002 observed (0x0001 dominant) — semantics unknown
then nodes:
  flags & 0x1000 : nodes until u16 FFFF
  flags & 0x1000 = 0 : EXACTLY ONE node, NO terminator (record boundary follows)
```

Node = closed ring of line-table entries (built at runtime at `es:441E`, stride 0x10):

```
u16 count
(count+1) x u16 line-table offset   ; all multiples of 0x10, last == first (closed)
```

**196/196 sub-records across all 8 theaters validate** under the flags rule.

### Geometry: convex decomposition + clipped tiles (finding 118)

Line-table entry index == point index (offset/0x10), so a ring is a closed
polygon over the record's own points. **Every ring is convex** (ISR 75/75; the
handful of non-convex hits elsewhere are collinear/degenerate). A record's rings
are a convex decomposition of one area: interior edges are shared by exactly
two rings, so

```
outline = edges used by exactly one ring
```

- **Lakes (0x64)** are self-contained: the outline is the closed shore.
- **Coast (0x14) and river/border records are TILES** clipped to a local box
  (ISR x ±4388, z ±5109; IRQ ±5502). The clip appears as unshared,
  axis-aligned edges lying on the record's bounding box — tile seams, not
  shoreline. Drop them; what remains is the coastline (open runs from box side
  to box side). Example ISR 0x1542: (4388,327)→(851,2947)→(-3340,1506)→(-4388,1703).
- Tiles step on a regular world grid (ISR column X=-23.18 nm, Y spaced 5.12 nm).

Extractor: `tools/extract_isldat_coast_edges.py` → `analysis/isldat_coast_edges/<T>.{json,svg}`
(record-local units). **Open:** the local→world scale/orientation — brute-force
endpoint stitching across neighbouring tiles finds no consistent fit, so take it
from the live `es:441E` table in an in-flight memdump.

### Runtime consumers (resident asm)

```
isldat_state_load      (0x12FC4)  block 0x27 -> 9B header + body -> state_seg 71C1:0
pos_neighbor_norm_scan (0x14B17)  grid walk -> record offsets (state_seg=71C1 body seg)
pos_diff_norm          (0x28874)  reads record XYZ dwords at +0/+4/+8
line_draw_441e         (0x28B08)  record points -> es:441E line-table entries (stride 0x10)
loc_2978E / line_from_points (0x29F20)   entry chain build (flags bits 8/4/2/1)
line_table_build_dispatch (0x29B82), record_span_build_and_dispatch (0x29917),
record_span_mask_rebuild (0x299D5)   node payload = count x (offset+0x441E)
state_table_apply_71c1 (0x1303A)  ALTERNATE view of grid-B q0 bytes (NOT the coastline
    walk): byte @ 0x65+n, 3-byte record @ 0x56+3n (b0/b1 byteswapped if swap_flag),
    fallback record @ 0x53; copies 0x46B from 7A32h:0xD2*n+0x7D0; semantics open
```

### Per-theater stats (from `tools/parse_isldat.py`)

```
file  size  swap t1(K) t2(K) gridA<= gridB<=  recs(fine/coarse) subs nodes
BOS   7875   0   58    35     34      57      14/ 7           21   159
HOK   7983   1   82    15     14      81      24/ 5           30   138
IRQ   7645   0   56    19     18      55      21/ 7           38    95
ISR   6787   0   67    37     36      63      21/11           35    75
KOR   7601   1   77    35     34      76      21/ 8           29   104
NEL   2037   0    4     1      0       3       2/ 0            2    18
PAK   1297   0    1     1      0       0       0/ 0            0     0
PAN   7885   1   85    25     24      84      22/ 9           41   107
```

### Open questions

- Loader function (file open + header parse into `word_11C18/11C1A`, `byte_11C0A`)
- Point coordinate transform (matrix via `pos_diff_norm`/`line_draw_441e`) — the
  per-record shape is solved (convex tiles, above); the local→world transform is not
- `attr` / `opcode` / `flags` low bits / `const_000B` / `const_4` semantics
- Geographic silhouette check vs `game\israel.ipl` / `analysis/map_ISRAEL.svg`

## Other Files

- `HORNETCD.EXE`: same structure, CS:IP=0x1A99:0x076C
- `MIGCD.EXE`: same structure, CS:IP=0x1A4E:0x076C
- `RESETALL.EXE`: Borland C++ 1991, tiny (7 KB)
- `FALCON3.SMP`: unknown format
- `cockpit_*.BIN` (64 KB each): video memory dumps?
- `MEMDUMP_*.BIN` / `falcon_*.BIN` (1 MB each): DOSBox memory snapshots