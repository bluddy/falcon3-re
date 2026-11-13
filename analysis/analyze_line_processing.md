# Assembly Analysis: Line Processing Code

## Goal
Verify the wrap-from-end index algorithm in actual assembly code:
```c
if (index < 0) index = vertex_count + index;
```

## Key Function: sub_26B2E (3D Object Renderer)

### File Header Access (0x26B86-0x26B93)

```asm
0x26B86: mov    ds, cs:word_1F712      ; Restore data segment (object data)
0x26B8B: mov    si, cs:word_1F716      ; SI = pointer to object header
0x26B90: mov    si, [si+4]             ; SI = header[4] - LINE SECTION OFFSET!
0x26B93: lodsw                          ; AX = next word from line section
0x26B94: cmp    ax, 0FFFFh             ; Check for terminator
0x26B97: jnz    loc_26B9C              ; If not terminator, process
0x26B99: jmp    loc_26C1F              ; Done, exit
```

**KEY INSIGHT**: `[si+4]` loads the line section offset from the header!

Looking at our file structure:
```
Offset 0x00: vertex_count (int16)
Offset 0x02: vertex_data_offset (int16)
Offset 0x04: line_data_offset (int16)    <-- THIS!
```

### Line Processing Section (0x26B9C-0x26C1C)

```asm
0x26B9C: push   si                     ; Save line section pointer
0x26B9D: mov    si, ax                 ; SI = value from line section
0x26B9F: lodsw                          ; AX = next word (probably flags/count)
0x26BA0: call   state_flag_unpack_1f735 ; Process flags
...
0x26C09: call   cs:off_27974[bx]       ; Indirect call to line processor
...
0x26C1B: pop    si                     ; Restore line section pointer
0x26C1C: jmp    loc_26B93              ; Loop back to read next line
```

This shows an **outer loop** that processes line section entries, but NOT the individual lines themselves.

## The Missing Link: Where Are Individual Lines Processed?

The function at 0x297 8E (line_record_draw_loop) is called via `cs:off_27974[bx]`.

Looking at that code:
```asm
0x2978E: lodsw                          ; AX = line count
0x2978F: mov    cx, ax                 ; CX = line count (loop counter)
0x29791: cmp    cs:byte_1F73A, 0      ; Check rendering mode flag
0x29797: jnz    loc_2979C              ; Branch to polygon processing
0x29799: jmp    loc_298C4              ; Branch to line processing
```

**At 0x298C4**, we should find the actual line loop!

Let me extract that section...

## Line Processing Loop (0x298C4 onwards)

From the disassembly:
```asm
0x298C4: mov    ax, 5D1Eh              ; Setup for line processing
0x298C7: mov    cs:word_2796E, ax
0x298CB: mov    ax, 603Eh
0x298CE: mov    cs:word_27970, ax
0x298D2: mov    cs:word_2796C, 0
0x298D9: call   record_span_mask_rebuild
0x298DC: push   ds
0x298DD: push   es
0x298DE: pop    ds
0x298DF: cmp    cx, 3                  ; CX still has line count
0x298E2: jl     loc_29915              ; Less than 3 lines, skip polygon rendering
...
```

The code at 0x298C4+ appears to be setting up for drawing, but it's calling other functions. The actual "load vertex index and resolve" code must be in the called functions or I'm missing a section.

## Alternative: Look for the "farobj_di_441e_init" Function

At 0x26B7B, there's a call to `farobj_di_441e_init`. The name suggests it initializes something at address 0x441E. This address appears frequently (0x28B08, 0x2978E, 0x29A00).

Address 0x441E is likely the **transformed vertex buffer** (in segment 0x7B0E which is ES).

## Critical Observation: The Transform Loop (0x26B63-0x26B71)

```asm
0x26B5D: mov    cx, [si]               ; CX = vertex_count (from header offset 0)
0x26B5F: mov    si, [si+2]             ; SI = vertex_data_offset (from header offset 2)
0x26B62: push   cx
0x26B63: push   cx
0x26B64: call   fixed_vec3_transform_es ; Transform one vertex
0x26B67: mov    word ptr es:[di+2], 0  ; Clear a word (Z component adjustment?)
0x26B6D: add    di, 6                  ; Move to next vertex (6 bytes = 3 int16)
0x26B70: pop    cx
0x26B71: loop   loc_26B63              ; Repeat for all vertices
0x26B73: pop    cx                     ; CX = vertex_count (restored)
```

**IMPORTANT**: After this loop, `CX` contains the vertex count!

## The Line Drawing Function: sub_28B08 @ 0x28B08

```asm
0x28B08: mov    di, 441Eh              ; DI = base of transformed vertices
0x28B0B:        2Eh, 2Eh, 2Eh           ; (garbage bytes from IDA?)
0x28B12: mov    cs:word_27966, 0       ; Clear flag
0x28B19: push   cx                     ; CX = line count (save it)
0x28B1A:        0B9h, 0B9h, 0B9h        ; (more garbage?)
0x28B1D:        0ADh, 0ADh, 0ADh        ; lodsw instruction repeated?
```

The garbage bytes suggest IDA couldn't fully disassemble this section. This could be:
1. Data embedded in code
2. Obfuscation
3. Self-modifying code
4. Compressed or packed code

## HYPOTHESIS: Index Resolution Happens in Data Setup, Not Runtime

Looking at the code flow:
1. Vertices are transformed and stored at 0x441E (6 bytes each, sequential)
2. Line records are loaded but NOT directly in a simple loop
3. There are indirect calls via function tables

**POSSIBILITY**: The negative indices might be resolved when the data is LOADED, not when it's drawn!

Let me look for file loading code...

## Next Steps

1. Find the code that LOADS the .OBJ files from disk
2. Look for preprocessing that might resolve indices
3. Check if there's a different code path for different line formats
4. Examine the "line table build" functions more carefully

## Alternative Theory: Indices Are Already Resolved

What if the file format stores negative indices, but the loader converts them?

Let me check if there's a loader function for FALCOBJ.BIN files...
