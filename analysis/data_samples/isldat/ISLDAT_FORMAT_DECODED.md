# ISLDAT Binary Format - Complete Specification

## Overview

ISLDAT files store vector coastline/river/road data for Falcon 3.0 theaters. The format uses a spatial index grid to efficiently lookup which coastline segments are visible in each terrain tile.

**File analyzed**: `game/israel_theater/ISLDAT.ISR` (6,787 bytes)

## File Structure

### Header (18 bytes at offset 0x00)

```
Offset  Size  Field          Value (ISR)  Purpose
------  ----  -------------  -----------  -------------------------------
0x00    word  data_size      0x1A7A       Size of data section (6,778 bytes)
0x02    word  offset_table1  0x0000       Offset to coastline index grid (from data start)
0x04    word  offset_table2  0x0500       Offset to second index grid (1,280 from data start)
0x06    word  offset_ptrs    0x074E       Offset to pointer table (1,870 from data start)
0x08    byte  flag           0x00         Unknown flag/count
0x09    9B    reserved       zeros        Padding to 18 bytes
```

### Data Section (starts at offset 0x3A = 58 decimal)

The header offsets are **relative to the data section start** (offset 58), not the file start.

#### 1. Coastline Index Grid (1,280 bytes @ data+0x0000)

**Absolute file offset**: 0x3A (58)  
**Size**: 1,280 bytes (0x500)

A spatial index mapping terrain grid cells to coastline list indices. Each byte is an index into the pointer table.

- Grid appears to be organized spatially (adjacent cells have similar or related indices)
- Zero (0x00) = no coastlines in this cell
- Non-zero = index into pointer table to find coastline point list

**Example cells:**
```
Cell[0] = 0x01 -> pointer[1] -> coastline list 1
Cell[1] = 0x01 -> pointer[1] -> coastline list 1 (same)
Cell[3] = 0x05 -> pointer[5] -> coastline list 5
```

#### 2. Second Index Grid (1,280 bytes @ data+0x0500)

**Absolute file offset**: 0x53A (1,338)  
**Size**: 1,280 bytes (0x500)

A second spatial index, likely for rivers or roads (different vector type).

- Same structure as coastline grid
- Allows dual-layer vector rendering (coastlines + rivers/roads)

#### 3. Pointer Table (~590 bytes @ data+0x074E)

**Absolute file offset**: 0x788 (1,928)  
**Entry size**: 2 bytes (word)  
**Entry count**: ~295 pointers

Each entry is a **segment-relative offset** to a coastline point list.

**Observed pointer values:**
```
ptr[00] = 0x7008 (28,680)
ptr[01] = 0x7808 (30,728)
ptr[02] = 0x8008 (32,776)
...
```

**CRITICAL**: These are NOT file offsets! They are offsets within the runtime data segment where ISLDAT is loaded. The loader:

1. Calls `state_word_26400_get_zero` to get target segment
2. Loads entire data section into that segment via `op_dispatch(bx=0xA)`
3. At runtime, code uses `ds:pointer_value` to access point lists

#### 4. Coastline Point Lists (remaining ~4,858 bytes)

Variable-length lists of 2D coordinates, each terminated with `0xFFFF`.

**Format:**
```
word: x coordinate (or pointer offset?)
word: y coordinate
word: x coordinate
word: y coordinate
...
0xFFFF: list terminator
```

**Found 32 terminators** in ISLDAT.ISR at offsets:
```
0x08FA (2,298)
0x0980 (2,432)
0x0A06 (2,566)
0x0A6A (2,666)
0x0AE0 (2,784)
... (27 more)
```

This suggests **32 separate coastline segments** in the Israel theater.

## Runtime Usage

### Loading (isldat_state_load @ 0x12FC4)

```assembly
; 1. Open file handle
mov  ax, 0
mov  bx, 6          ; op_dispatch operation 6 = create/open
call op_dispatch
mov  cs:word_11BDA, ax  ; save handle

; 2. Get target segment
call state_word_26400_get_zero
mov  ds, dx         ; DX = target segment

; 3. Read 18-byte header into ds:0
mov  cx, 4          ; read 4 words
mov  dx, 0
call op_dispatch    ; bx=0xA = read

; 4. Store header fields
mov  ax, [bx+2]
mov  cs:word_11C16, ax  ; offset_table1
mov  ax, [bx+4]
mov  cs:word_11C18, ax  ; offset_table2
mov  ax, [bx+6]
mov  cs:word_11C1A, ax  ; offset_ptrs

; 5. Seek to data section (offset 58)
mov  ax, cs:word_11BDA
mov  bx, 0Eh        ; op_dispatch operation 0xE = seek
call op_dispatch

; 6. Read data section
mov  cx, [bx]       ; size from header word[0]
mov  ax, cs:word_11BDA
mov  bx, 0Ah        ; operation 0xA = read
call op_dispatch

; 7. Close file
mov  bx, 8          ; operation 8 = close
call op_dispatch

; 8. Map window
call slot2_map_window_load
```

### Rendering (pos_neighbor_norm_scan @ 0x14B4F)

```assembly
; Grid cell -> coastline index lookup
mov  ax, cs:word_11C24      ; grid Y coordinate
shr  ax, 1
shr  ax, 1                  ; Y >> 2
add  si, ax                 ; add Y component
add  si, cs:word_11C16      ; add table1 offset
add  si, cs:word_11CC6      ; add base segment offset
lodsb                       ; AL = index from grid

; Index -> pointer lookup
sub  ah, ah
shl  ax, 1                  ; index * 2 (word pointer)
add  ax, cs:word_11C1A      ; add pointer table offset
mov  si, ax
lodsw                       ; AX = pointer to point list

; Walk point list
mov  si, ax
loop_points:
  lodsw                     ; AX = point coordinate
  cmp  ax, 0FFFFh
  jz   done_list            ; terminator found
  mov  di, ax
  push si
  mov  bx, 0C57h
  call pos_diff_norm        ; process point
  pop  si
  jmp  loop_points
done_list:
```

## Key Discoveries

1. **Three-tier index structure**:
   - Spatial grid (byte indices) -> Pointer table (word offsets) -> Point lists (word coords)
   - This allows efficient culling: only process coastlines in visible cells

2. **Dual grid system**:
   - Two 1,280-byte index grids suggest two feature types
   - Likely: coastlines (table1) and rivers/roads (table2)
   - Both reference the same pointer table and point pool

3. **Segment-relative addressing**:
   - Pointer values are NOT file offsets
   - Data loaded into runtime segment, pointers used as `ds:offset`
   - Allows fast pointer-chasing without file I/O translation

4. **Grid dimensions**:
   - 1,280 bytes suggests 32×40 grid OR 40×32 grid
   - Could also be 64×20 or other factors of 1,280
   - Need to cross-reference with heightmap grid (31×31) to determine exact layout

5. **Point format unclear**:
   - Each "point" might be 1 word (packed X,Y) or 2 words (separate X,Y)
   - The `pos_diff_norm` function processes points, need to analyze it
   - Lists might contain line segment endpoints OR polygon vertices

## Remaining Questions

1. What do the pointer values actually point to when loaded in segment?
2. Are points 1-word packed or 2-word separate coordinates?
3. What is the exact grid dimension (32×40? 40×32? other)?
4. How does grid align with 31×31 heightmap grid?
5. What distinguishes coastlines vs rivers vs roads in the two index grids?
6. What is byte[8] flag used for?
7. How does the coordinate system map to world space?

## Status

**ISLDAT Format Understanding: 75%**

- ✅ Header structure decoded
- ✅ Three-tier index structure identified  
- ✅ Loader flow completely traced
- ✅ Runtime lookup algorithm understood
- ⚠️ Point format ambiguous (1-word vs 2-word)
- ⚠️ Grid dimensions unclear (32×40? 40×32?)
- ⚠️ Coordinate system mapping unknown
- ❌ Polygon fill algorithm not found yet

## Next Steps

1. Analyze `pos_diff_norm` function to understand point format
2. Determine grid dimensions by analyzing grid access patterns
3. Find polygon fill algorithm (interior rendering)
4. Map coordinate system to world/screen space
5. Test loading other theater files (HOK, IRQ, KOR, PAN, BOS)
