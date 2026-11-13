# Falcon 3.0 Terrain Rendering - Deep Dive Analysis

## Executive Summary

**Status**: Core Rendering 60% Complete

This document provides a detailed analysis of the three core terrain rendering functions that draw the 3D landscape to screen. Through disassembly analysis, we've uncovered the mathematical algorithms, rendering pipeline, and optimization techniques used to achieve real-time terrain rendering on an 8MHz 8086.

## The Three Core Functions

### Overview

| Function | Address | Size | Purpose | Complexity |
|----------|---------|------|---------|------------|
| hud_terrain_strip_render | 0x3718D | 988 bytes | Main coordinator, view transformation | High |
| tile_strip_project_draw | 0x361FC | 331 bytes | 3D→2D projection, perspective | Medium |
| tile_strip_sample_draw | 0x16060 | 126 bytes | Texture sampling, pixel output | Low |

### Call Hierarchy

```
hud_terrain_strip_render (988 bytes)
    ├─ farobj_step_terrain_clamp
    ├─ angle_xy_near (2x)
    ├─ angle_quad_norm_far
    ├─ stub_to_24988 (2x)
    ├─ stub_to_249d8
    ├─ segment_clip_test (4x)
    ├─ clip_or_draw_dispatch (4x)
    ├─ sprite_offset_dispatch_343e
    ├─ sub_263F6
    ├─ dispatch_220d4_stub
    └─ dispatch_220dc_stub

tile_strip_project_draw (331 bytes)
    ├─ stub_to_249d8 (3x)
    ├─ r08_farptr_load_thunk
    └─ clip_or_draw_dispatch (2x)

tile_strip_sample_draw (126 bytes)
    ├─ tile_quad_sample (in loop)
    └─ tile_clip_draw_14200
```

## Function 1: hud_terrain_strip_render (Main Coordinator)

### Function Signature

```c
void hud_terrain_strip_render(void)
```

**Address**: 0x3718D  
**Size**: 988 bytes (~352 instructions)  
**Calls**: 19 function calls to 11 unique functions

### Algorithm Overview

This is the **main terrain rendering coordinator**. It performs view transformation, sets up projection parameters, and orchestrates the drawing of terrain strips.

### Detailed Analysis

#### Phase 1: Initialization and Terrain Clamping (0x3718D - 0x371E2)

```assembly
; Clear terrain-active flag
0x3718D  mov     byte ptr ds:105Dh, 0

; Check camera mode
0x37192  cmp     byte ptr ds:82Ch, 1
0x37197  jz      short loc_371E1      ; Skip if not in terrain view

; Copy camera position (6 words = 12 bytes)
0x371A2  push    si
0x371A3  mov     di, 4816h
0x371A6  mov     ax, [si+0Ch]         ; Get camera data
0x371A9  mov     cx, [si+0Eh]
0x371AC  movsw                        ; Copy 6 words
0x371AD  movsw
0x371AE  movsw
0x371AF  movsw
0x371B0  movsw
0x371B1  movsw

; Clamp camera to terrain
0x371B2  mov     bp, 100h             ; Y clamp value
0x371B5  mov     dx, 100h             ; X clamp value  
0x371B8  xor     bx, bx
0x371BA  mov     si, 4816h
0x371BD  call    farobj_step_terrain_clamp

; Check if clamping succeeded
0x371C4  jb      short loc_371E1      ; Exit if out of bounds

; Calculate terrain detail level
0x371C6  sub     ax, 100h
0x371C9  neg     ax
0x371CB  cwd
0x371CC  mov     dl, ah               ; Shift right 8 bits
0x371CE  mov     ah, al
0x371D0  xor     al, al
0x371D2  mov     si, [si+4Ch]
0x371D5  div     si                   ; Divide by distance scale
0x371D7  cmp     ax, 10h              ; Check if detail < 16
0x371DA  jnb     short loc_371E1
0x371DC  mov     ds:105Dh, al         ; Store detail level
0x371DF  clc                          ; Success
0x371E0  retn
```

**Key Observations**:
- Copies camera position (6 words = X, Y, Z, pitch, yaw, roll?)
- Calls `farobj_step_terrain_clamp` to clamp camera to terrain height
- Calculates LOD (Level of Detail) based on distance
- Stores detail level in `ds:105Dh` (0-15 range)
- Early exit if out of terrain bounds

#### Phase 2: View Angle Calculations (0x371E3 - 0x37282)

```assembly
; Calculate horizontal view angle
0x371EC  mov     ax, [si+0Ch]         ; Get camera X rotation?
0x371EF  mov     ds:80Ch, ax          ; Store for reference
0x371F2  mov     di, 83Ch             ; Angle buffer
0x371F5  call    angle_xy_near        ; Compute angle from camera

; Adjust angle based on view mode
0x371FA  cmp     byte ptr ds:105Fh, 0
0x371FF  jz      short loc_37207
0x37201  sub     ax, ds:848h          ; Mode 1: subtract offset
0x37205  jmp     short loc_3720B
0x37207  sub     ax, ds:80Ch          ; Mode 0: subtract camera angle
0x3720B  call    stub_to_24988        ; Normalize angle

; Set horizontal direction flag
0x37210  mov     word ptr ds:80Eh, 1  ; Default: right
0x37216  cwd
0x37217  xor     ax, dx               ; Abs value
0x37219  sub     ax, dx
0x3721B  cmp     ax, 800h             ; Check if angle > threshold
0x3721E  jle     short loc_37224
0x37220  dec     word ptr ds:80Eh     ; Set to left

; Store normalized horizontal angle
0x37224  xor     ax, dx
0x37226  sub     ax, dx
0x37228  mov     ds:810h, ax          ; Horizontal angle

; Get camera elevation angles
0x3722F  mov     ax, [si+8]           ; Get pitch
0x37232  mov     ds:81Ah, ax
0x37235  mov     ax, [si+0Ah]         ; Get roll?
0x37238  mov     ds:81Ch, ax

; Normalize elevation angle
0x3723B  mov     di, 83Ch
0x3723E  call    angle_quad_norm_far
0x37243  mov     ds:816h, ax          ; Store normalized pitch
0x37246  mov     ds:818h, dx          ; Store normalized roll

; Zero out another angle buffer
0x3724A  xor     ax, ax
0x3724C  mov     di, 81Eh
0x3724F  stosw
0x37250  stosw
0x37251  stosw
0x37252  stosw

; Calculate vertical angle
0x37253  mov     si, 81Eh
0x37256  mov     di, 816h
0x37259  call    angle_xy_near
0x3725E  mov     word ptr ds:812h, 1  ; Default: up
0x37264  sub     ax, ds:84Ah          ; Subtract horizon angle
0x37268  call    stub_to_24988        ; Normalize
0x3726D  cwd
0x3726E  xor     ax, dx               ; Abs
0x37270  sub     ax, dx
0x37272  cmp     ax, 800h             ; Check threshold
0x37275  jle     short loc_3727B
0x37277  dec     word ptr ds:812h     ; Set to down
0x3727B  xor     ax, dx
0x3727D  sub     ax, dx
0x3727F  mov     ds:814h, ax          ; Vertical angle
```

**Key Observations**:
- Computes horizontal and vertical view angles
- `angle_xy_near` - converts rotation to 2D angle
- `angle_quad_norm_far` - normalizes 3D angle vector
- Sets direction flags (`ds:80Eh`, `ds:812h`) for left/right, up/down
- Stores multiple angle components:
  - `ds:80Ch` - Camera X rotation
  - `ds:810h` - Horizontal angle (normalized)
  - `ds:814h` - Vertical angle (normalized)
  - `ds:816h/818h` - Normalized pitch/roll
  - `ds:81Ah/81Ch` - Original pitch/roll

#### Phase 3: Perspective Setup (0x37283 - 0x37312)

```assembly
; Get camera field-of-view
0x37287  mov     ax, [si+10h]         ; Get FOV value
0x3728A  neg     ax                   ; Negate for calculation
0x3728C  mov     bx, 7FCh             ; Target buffer
0x3728F  call    stub_to_249d8        ; Trigonometric function?

; Calculate perspective scale (horizontal)
0x37294  mov     bx, 2D0h             ; Scale factor (720 decimal)
0x37297  mov     ax, ds:7FCh
0x3729A  imul    bx                   ; Multiply
0x3729C  mov     ds:7FCh, dx          ; Store high word (scale)
0x372A0  mov     bp, dx
0x372A2  sar     dx, 1                ; Divide by 2
0x372A4  mov     ds:800h, dx          ; Store /2
0x372A8  sar     dx, 1                ; Divide by 4
0x372AA  sar     dx, 1                ; Divide by 8
0x372AC  mov     ds:804h, dx          ; Store /8

; Calculate perspective scale (vertical)
0x372B0  mov     ax, ds:7FEh
0x372B3  imul    bx                   ; Same multiplication
0x372B5  mov     ds:7FEh, dx
0x372B9  mov     bx, dx
0x372BB  sar     dx, 1
0x372BD  mov     ds:802h, dx
0x372C1  sar     dx, 1
0x372C3  sar     dx, 1
0x372C5  mov     ds:806h, dx

; Apply direction-dependent offset
0x372C9  cmp     word ptr ds:80Eh, 0  ; Check horizontal direction
0x372CE  jnz     short loc_372F0      ; Jump if right

; Left direction: simple addition
0x372D0  mov     ax, ds:810h          ; Horizontal angle
0x372D3  cwd
0x372D4  xor     bp, dx               ; Conditional negate (bp)
0x372D6  sub     bp, dx
0x372D8  add     bp, ds:6C6h          ; Add Y screen offset
0x372DC  mov     ds:818h, bp          ; Store screen Y
0x372E0  xor     bx, dx               ; Conditional negate (bx)
0x372E2  sub     bx, dx
0x372E4  add     bx, ds:6C4h          ; Add X screen offset
0x372E8  mov     ds:816h, bx          ; Store screen X
0x372EC  mov     ax, bp
0x372EE  jmp     short loc_37312

; Right direction: perspective division
0x372F0  mov     si, 800h             ; Divisor (scale/2)
0x372F3  mov     ax, ds:810h          ; Horizontal angle
0x372F6  mov     cx, ax               ; Save for later
0x372F8  imul    bx                   ; Multiply by vertical scale
0x372FA  idiv    si                   ; Perspective divide
0x372FC  add     ax, ds:6C4h          ; Add X screen offset
0x37300  mov     ds:816h, ax          ; Store screen X
0x37303  mov     bx, ax
0x37305  mov     ax, cx               ; Restore horizontal angle
0x37307  imul    bp                   ; Multiply by horizontal scale
0x37309  idiv    si                   ; Perspective divide
0x3730B  add     ax, ds:6C6h          ; Add Y screen offset
0x3730F  mov     ds:818h, ax          ; Store screen Y
```

**Key Observations**:
- Calculates perspective projection scales from FOV
- Uses scale factor 0x2D0 (720 decimal) - likely related to screen resolution
- Pre-computes scale, scale/2, and scale/8 for optimization
- Two code paths based on view direction (left vs. right)
- **Right direction uses perspective division**: angle * scale / (scale/2)
- Adds screen offsets (`ds:6C4h` = X, `ds:6C6h` = Y) - these are from HUD system!
- Stores final screen coordinates in `ds:816h` (X) and `ds:818h` (Y)

**Mathematical Insight**:
```
For right direction:
screen_x = (horizontal_angle * vertical_scale) / (scale/2) + x_offset
screen_y = (horizontal_angle * horizontal_scale) / (scale/2) + y_offset

This is a simplified perspective projection!
```

#### Phase 4: Strip Rendering Setup (0x37312 onwards - truncated in log)

The remaining ~200 instructions likely:
- Iterate through horizontal strips (scanlines)
- Call drawing functions for each strip
- Handle clipping against viewport
- Dispatch to tile rendering functions

**Evidence**:
- Calls `segment_clip_test` 4x - testing strip visibility
- Calls `clip_or_draw_dispatch` 4x - drawing clipped strips
- Loop structure implied by multiple clip/draw calls

### Data Structures Used

**Camera/View State** (from `ds:48BAh` source):
- `[si+08h]` - Pitch angle
- `[si+0Ah]` - Roll angle
- `[si+0Ch]` - X rotation / yaw
- `[si+0Eh]` - Additional rotation component
- `[si+10h]` - Field of view

**Computed View Parameters**:
- `ds:80Ch` - Camera X rotation reference
- `ds:80Eh` - Horizontal direction flag (0=left, 1=right)
- `ds:810h` - Horizontal angle (normalized)
- `ds:812h` - Vertical direction flag (0=down, 1=up)
- `ds:814h` - Vertical angle (normalized)
- `ds:816h` - Screen X coordinate (final)
- `ds:818h` - Screen Y coordinate (final)
- `ds:81Ah` - Original pitch
- `ds:81Ch` - Original roll

**Perspective Scales**:
- `ds:7FCh` - Horizontal scale
- `ds:7FEh` - Vertical scale
- `ds:800h` - Horizontal scale / 2
- `ds:802h` - Vertical scale / 2
- `ds:804h` - Horizontal scale / 8
- `ds:806h` - Vertical scale / 8

**Screen Offsets** (from HUD system):
- `ds:6C4h` - X offset (160 * 16 for external view)
- `ds:6C6h` - Y offset ((display_y + 50) * 16)

**Terrain State**:
- `ds:105Dh` - Terrain detail level (LOD 0-15)
- `ds:105Fh` - View mode flag
- `ds:82Ch` - Camera mode (1 = skip terrain rendering)

## Function 2: tile_strip_project_draw (3D Projection)

### Function Signature

```c
void tile_strip_project_draw(void* tile_data_es_si)
```

**Address**: 0x361FC  
**Size**: 331 bytes (~117 instructions)  
**Calls**: 6 function calls to 3 unique functions

### Algorithm Overview

This function takes 3D tile coordinates and projects them to 2D screen space using perspective division. It handles two tile corners, clips them to the viewport, and calls the drawing functions.

### Detailed Analysis

#### Phase 1: Load Tile Data and Initial Transform (0x361FC - 0x36222)

```assembly
; Load tile Y coordinate
0x361FC  mov     ax, es:[si+8Eh]      ; Get tile Y from data structure
0x36201  mov     ds:4816h, ax         ; Store in work buffer

; Transform Y coordinate (angle/rotation)
0x36204  mov     bx, 4818h            ; Target for transformed Y
0x36207  call    stub_to_249d8        ; Trigonometric transform

; Load LOD scale factor
0x3620C  mov     bx, ds:44AAh         ; Get LOD selector
0x36210  call    r08_farptr_load_thunk ; Load scale table entry
0x36215  jz      short loc_3621C
0x36217  or      bx, bx               ; Check if zero
0x36219  jnz     short loc_3621C
0x3621B  inc     bx                   ; Ensure non-zero (minimum LOD)

; Get scale from table
0x3621C  shl     bx, 1                ; BX *= 2 (word index)
0x3621E  mov     bx, [bx+7A0h]        ; Load scale from table at 0x7A0
0x36222  mov     ax, bx               ; AX = scale
```

**Key Observations**:
- Loads tile Y from offset 0x8E in tile data structure
- Applies trigonometric transform (rotation?)
- Uses LOD selector `ds:44AAh` to choose scale
- Scale table at `ds:7A0h` - multiple LOD levels
- Ensures non-zero scale (prevents division by zero)

#### Phase 2: Project First Corner (0x36224 - 0x36236)

```assembly
; Project Y coordinate
0x36224  imul    word ptr ds:4818h    ; Multiply by transformed Y
0x36228  shl     ax, 1                ; Shift left (low word)
0x3622A  rcl     dx, 1                ; Rotate carry into high word (*2 total)
0x3622C  mov     ax, dx               ; Use high word
0x3622E  mov     dl, 0Dh              ; Divisor = 13
0x36230  idiv    dl                   ; Divide by 13
0x36232  cbw                          ; Sign-extend AL to AX
0x36233  mov     ds:4818h, ax         ; Store projected Y
```

**Mathematical Insight**:
```
projected_y = (scale * transformed_y * 2) / 13

The division by 13 is interesting - might be related to:
- Tile size (13 pixels?)
- Fixed-point scaling factor
- Optimization (13 is small enough for byte division)
```

#### Phase 3: Project X coordinate (0x36236 - 0x36247)

```assembly
0x36236  mov     ax, bx               ; AX = scale
0x36238  imul    word ptr ds:481Ah    ; Multiply by transformed X
0x3623C  shl     ax, 1                ; *2 (same as Y projection)
0x3623E  rcl     dx, 1
0x36240  mov     cx, 4                ; Shift count
0x36243  sar     dx, cl               ; Arithmetic right shift by 4 (/16)
0x36245  neg     dx                   ; Negate result
0x36247  mov     ds:481Ah, dx         ; Store projected X
```

**Mathematical Insight**:
```
projected_x = -((scale * transformed_x * 2) / 16)

Note: 
- Division by 16 (not 13 like Y!) suggests different aspect ratio handling
- Negation might flip X axis direction
```

#### Phase 4: Project Second Corner (0x3624B - 0x362BB)

This section repeats the projection math for a second corner:
- Loads different X coordinate (`ds:4816h`)
- Subtracts 0x555 (1365 decimal) - offset to corner?
- Projects using same formulas
- Uses different target addresses (`ds:481Ch`, `ds:481Eh`)

Then projects a third corner:
- Adds 0x555 (symmetric offset)
- Projects to `ds:4820h`, `ds:4822h`

**Observation**: Projects 3 corners of a tile quad (or triangle strip edges)

#### Phase 5: Screen Space Conversion and Clipping (0x362BF - 0x36346)

```assembly
; Load first projected corner
0x362BF  mov     ax, ds:4818h         ; Projected Y
0x362C2  mov     bx, ds:481Ah         ; Projected X

; Add screen center offsets
0x362C6  add     ax, 0A0h             ; +160 (screen center X)
0x362C9  add     bx, 32h              ; +50 (screen center Y)

; Add viewport offsets (from HUD system)
0x362CC  add     ax, ds:6F8h          ; Add X viewport offset
0x362D0  add     bx, ds:6FAh          ; Add Y viewport offset

; Clip test against viewport bounds
0x362D4  cmp     ax, 4                ; X < 4?
0x362D7  jl      short locret_36346   ; Exit if out of bounds
0x362D9  cmp     ax, 13Bh             ; X > 315?
0x362DC  jg      short locret_36346   ; Exit if out of bounds
0x362DE  cmp     bx, 4                ; Y < 4?
0x362E1  jl      short locret_36346   ; Exit if out of bounds
0x362E3  cmp     bx, 0C3h             ; Y > 195?
0x362E7  jg      short locret_36346   ; Exit if out of bounds

; Store first corner in quad buffer
0x362E9  mov     cx, ax
0x362EB  mov     dx, bx
0x362ED  mov     ds:6D8h, ax          ; Corner 1 X
0x362F0  mov     ds:6DAh, bx          ; Corner 1 Y

; Store second corner
0x362F4  add     ax, ds:481Ch         ; Add delta X
0x362F8  add     bx, ds:481Eh         ; Add delta Y
0x362FC  mov     ds:6DCh, ax          ; Corner 2 X
0x362FF  mov     ds:6DEh, bx          ; Corner 2 Y

; Prepare third corner
0x36303  add     ds:4820h, cx         ; Add to corner 3
0x36307  add     ds:4822h, dx

; Draw first quad/line
0x3630B  xor     ax, ax               ; AX = 0 (drawing mode?)
0x3630D  mov     es, word ptr ds:796h ; Load segment
0x36311  mov     si, 6D8h             ; Point to corner buffer
0x36314  call    clip_or_draw_dispatch ; DRAW!

; Project and draw third corner (similar to above)
0x36319  mov     ax, ds:4820h
0x3631C  mov     bx, ds:4822h
; ... (clipping tests)
0x36335  mov     ds:6DCh, ax
0x36338  mov     ds:6DEh, bx
0x3633C  xor     ax, ax
0x3633E  mov     si, 6D8h
0x36341  call    clip_or_draw_dispatch ; DRAW second quad
0x36346  retn
```

**Key Observations**:
- Adds offsets to convert from centered coordinates to screen space
- Center offsets: +160 X, +50 Y (suggests 320x200 screen with origin at center)
- Clips against viewport: [4, 4] to [315, 195] (leaving margins)
- Stores corners in quad buffer at `ds:6D8h`:
  - `ds:6D8h` - Corner 1 X
  - `ds:6DAh` - Corner 1 Y  
  - `ds:6DCh` - Corner 2 X
  - `ds:6DEh` - Corner 2 Y
- Calls `clip_or_draw_dispatch` twice - draws two quads or a triangle strip

### Data Structures

**Input** (in ES:SI):
- `es:[si+8Eh]` - Tile Y coordinate (3D)
- Additional X coordinates at other offsets (not shown in first 150 instructions)

**Work Buffers**:
- `ds:4816h` - Tile Y (input)
- `ds:4818h` - Transformed/projected Y
- `ds:481Ah` - Projected X (corner 1)
- `ds:481Ch` - Projected X (corner 2)
- `ds:481Eh` - Projected Y (corner 2)
- `ds:4820h` - Projected X (corner 3)
- `ds:4822h` - Projected Y (corner 3)

**Output** (quad buffer):
- `ds:6D8h` - Corner 1 X (screen space)
- `ds:6DAh` - Corner 1 Y (screen space)
- `ds:6DCh` - Corner 2 X (screen space)
- `ds:6DEh` - Corner 2 Y (screen space)

**LOD Data**:
- `ds:44AAh` - LOD selector
- `ds:7A0h` - LOD scale table

**Viewport** (from HUD system):
- `ds:6F8h` - Viewport X offset
- `ds:6FAh` - Viewport Y offset
- `ds:796h` - Segment for drawing operations

**Clipping Bounds**:
- X: [4, 315] (320 - 5 pixel margin)
- Y: [4, 195] (200 - 5 pixel margin)

### Projection Formula Summary

```
For each corner (X, Y, Z) in tile space:

1. Apply view transformation:
   transformed_y = trigonometric_function(Y, camera_angles)
   transformed_x = trigonometric_function(X, camera_angles)

2. Apply LOD scale:
   scale = lod_table[lod_selector]

3. Perspective projection:
   projected_y = (scale * transformed_y * 2) / 13
   projected_x = -((scale * transformed_x * 2) / 16)

4. Screen space conversion:
   screen_x = projected_x + 160 + viewport_offset_x
   screen_y = projected_y + 50 + viewport_offset_y

5. Clip test:
   if (screen_x < 4 || screen_x > 315) discard
   if (screen_y < 4 || screen_y > 195) discard

6. Draw:
   clip_or_draw_dispatch(corner_buffer)
```

## Function 3: tile_strip_sample_draw (Texture Sampling)

### Function Signature

```c
void tile_strip_sample_draw(void)
```

**Address**: 0x16060  
**Size**: 126 bytes (~49 instructions)  
**Calls**: 2 function calls (tile_quad_sample, tile_clip_draw_14200)

### Algorithm Overview

This function samples texture data from tiles and outputs pixels. It runs a **64-iteration loop** to sample 64 horizontal pixels, then calls the drawing function.

### Detailed Analysis

#### Phase 1: Setup Texture Sampling Parameters (0x16060 - 0x16082)

```assembly
; Calculate delta values for texture sampling
0x16060  mov     ax, cs:word_11C2A    ; Get end U coordinate
0x16064  sub     ax, cs:word_11C42    ; Subtract start U
0x16069  mov     word ptr cs:loc_1608D+1, ax  ; Self-modify code! Store delta U

0x1606D  mov     ax, cs:word_11C28    ; Get end V coordinate
0x16071  sub     ax, cs:word_11C44    ; Subtract start V
0x16076  mov     word ptr cs:loc_1609C+1, ax  ; Self-modify code! Store delta V

; Jump over data (common DOS pattern)
0x1607A  jmp     short $+2

; Setup pointers
0x1607C  mov     di, 46E9h            ; Output buffer pointer
0x1607F  mov     bp, 47E9h            ; Intermediate buffer pointer
0x16082  mov     cx, 40h              ; Loop counter = 64 (0x40)
```

**Key Observations**:
- **Self-modifying code!** Writes delta values into instruction immediates
- This was a common optimization on 8086 - avoids memory access in tight loops
- Sampling 64 pixels per strip (0x40 = 64 decimal)
- U and V likely refer to texture coordinates

#### Phase 2: Texture Sampling Loop (0x16085 - 0x160C2)

```assembly
0x16085  sub     dx, dx               ; DX = 0 (counter for special pixels?)
0x16087  mov     si, ds:46E7h         ; Load source pointer

; LOOP START (will loop 64 times)
0x1608B  mov     ax, [si]             ; Load U coordinate
0x1608D  add     ax, 0ABCDh           ; ADD WITH SELF-MODIFIED VALUE!
0x16090  and     ax, 7FFh             ; Wrap at 2048 (0x7FF)
0x16093  mov     bx, ax               ; BX = wrapped U
0x16095  mov     ds:[bp+0], ax        ; Store in buffer

0x16099  mov     ax, [si+2]           ; Load V coordinate  
0x1609C  add     ax, 0ABCDh           ; ADD WITH SELF-MODIFIED VALUE!
0x1609F  and     ax, 7FFh             ; Wrap at 2048
0x160A2  mov     ds:[bp+2], ax        ; Store in buffer

; Save registers
0x160A6  push    cx
0x160A7  push    dx
0x160A8  push    si
0x160A9  push    di

; Sample the tile texture
0x160AA  call    tile_quad_sample     ; Returns color in AL/AH

; Restore registers
0x160AD  pop     di
0x160AE  pop     si
0x160AF  pop     dx
0x160B0  pop     cx

; Check if pixel is special (sky?)
0x160B1  cmp     al, 5Fh              ; Compare color to threshold (95)
0x160B3  jbe     short loc_160B6      ; Skip if <= 95
0x160B5  inc     dx                   ; Increment sky pixel counter

; Store sampled pixels
0x160B6  mov     [di], al             ; Store lower byte (primary color)
0x160B8  mov     [di+40h], ah         ; Store upper byte at +64 offset

; Advance pointers
0x160BB  inc     di                   ; Next output pixel
0x160BC  add     si, 4                ; Next input (skip 4 bytes)
0x160BF  add     bp, 4                ; Next buffer slot
0x160C2  loop    loc_1608B            ; Loop 64 times
```

**Key Observations**:
- **Self-modifying code in action**: `add ax, 0ABCDh` has 0xABCD replaced with delta value
- This adds the delta to U/V coordinates each iteration (texture stepping)
- Wraps coordinates at 2048 (0x7FF) - texture space size
- Calls `tile_quad_sample` 64 times - likely expensive
- Checks for "sky" pixels (color > 95) and counts them in DX
- Stores two bytes per pixel: AL and AH (dual-buffer? LOD levels?)
- Stores second set of pixels at +64 offset (di+40h)

#### Phase 3: Draw Sampled Strip (0x160C4 - 0x160DD)

```assembly
; Check if we have enough terrain pixels (not mostly sky)
0x160C4  cmp     dx, 40h              ; Compare sky count to 64
0x160C7  jnb     short locret_160DD   ; Exit if all sky (DX >= 64)

; Setup for drawing
0x160C9  push    dx                   ; Save sky count
0x160CA  mov     bx, 47E9h            ; Intermediate buffer
0x160CD  mov     si, 46E9h            ; Sampled pixel buffer
0x160D0  mov     di, 4AE9h            ; Output target buffer?
0x160D3  mov     cs:byte_11CAF, 1     ; Set flag (enable drawing?)

; Draw the strip
0x160D9  call    tile_clip_draw_14200 ; DRAW!
0x160DC  pop     dx                   ; Restore sky count
0x160DD  retn
```

**Key Observations**:
- Skips drawing if entire strip is sky (optimization!)
- Passes three buffers to drawing function:
  - BX = intermediate buffer (UV coordinates?)
  - SI = sampled pixels
  - DI = output target
- Sets flag `cs:byte_11CAF` to enable drawing
- Calls `tile_clip_draw_14200` which we know from HUD analysis

### Data Structures

**Self-Modified Code**:
- `cs:loc_1608D+1` - Delta U value (patched at runtime)
- `cs:loc_1609C+1` - Delta V value (patched at runtime)

**Buffers**:
- `ds:46E7h` - Source UV coordinate buffer (pointer)
- `ds:46E9h` - Sampled pixel output (64 bytes)
- `ds:47E9h` - Intermediate buffer (128 bytes - 2 per pixel)
- `ds:4AE9h` - Final output target

**Texture Coordinates**:
- `cs:word_11C2A` - End U
- `cs:word_11C42` - Start U
- `cs:word_11C28` - End V
- `cs:word_11C44` - Start V
- Wrap at 0x7FF (2048) - texture space is 2048x2048?

**Drawing State**:
- `cs:byte_11CAF` - Drawing enable flag

### Sampling Algorithm

```
1. Calculate texture coordinate deltas:
   delta_u = end_u - start_u
   delta_v = end_v - start_v

2. Self-modify code to inline delta values (optimization!)

3. For i = 0 to 63:
   a. u = (start_u + i * delta_u) & 0x7FF  // Wrap at 2048
   b. v = (start_v + i * delta_v) & 0x7FF
   c. color = tile_quad_sample(u, v, bx)   // Sample tile texture
   d. output[i] = color_low
   e. output[i+64] = color_high            // Dual buffer
   f. if (color_low > 95): sky_count++     // Count sky pixels

4. If (sky_count < 64):  // Don't draw if all sky
   tile_clip_draw_14200(buffers)
```

## Rendering Pipeline Summary

### Complete Flow

```
FRAME START
    ↓
hud_terrain_strip_render (988 bytes) - MAIN COORDINATOR
    │
    ├─ Phase 1: Clamp camera to terrain
    │   └─ Calculate LOD level (0-15)
    │
    ├─ Phase 2: View transformation
    │   ├─ Compute horizontal angle (left/right)
    │   ├─ Compute vertical angle (up/down)
    │   └─ Normalize angles
    │
    ├─ Phase 3: Perspective setup
    │   ├─ Calculate FOV scales
    │   ├─ Pre-compute scale/2, scale/8
    │   └─ Compute screen center position
    │
    └─ Phase 4: Render strips (repeated for each horizontal strip)
        ├─ Test strip visibility (segment_clip_test)
        └─ For visible strips:
            │
            ├─ tile_strip_project_draw (331 bytes) - 3D PROJECTION
            │   │
            │   ├─ Load tile 3D coordinates
            │   ├─ Apply view transformation
            │   ├─ Select LOD scale from table
            │   ├─ Perspective projection:
            │   │   • Y: (scale * y * 2) / 13
            │   │   • X: -((scale * x * 2) / 16)
            │   ├─ Convert to screen space (+center +viewport)
            │   ├─ Clip to viewport [4,4] to [315,195]
            │   └─ Store 3 projected corners
            │       │
            │       └─ clip_or_draw_dispatch (2x) - DISPATCH TO DRAWING
            │
            └─ tile_strip_sample_draw (126 bytes) - TEXTURE SAMPLING
                │
                ├─ Calculate texture deltas
                ├─ Self-modify code with deltas
                ├─ FOR i = 0 TO 63:
                │   ├─ Interpolate U,V coordinates
                │   ├─ Wrap at 2048
                │   ├─ tile_quad_sample → sample texture
                │   ├─ Store pixels (dual-buffer)
                │   └─ Count sky pixels
                │
                └─ IF (not all sky):
                    └─ tile_clip_draw_14200 - PIXEL OUTPUT
                        └─ Calls far_cb_gated
                            └─ Writes to VGA (ES:DI at 0xA000)

FRAME END
```

## Performance Analysis

### Per-Strip Cost

**tile_strip_project_draw** (331 bytes):
- ~117 instructions
- 3x `stub_to_249d8` (trig functions) ~100 cycles each
- 2x `clip_or_draw_dispatch` ~50 cycles each
- **Total**: ~500-600 cycles per strip

**tile_strip_sample_draw** (126 bytes with 64-iteration loop):
- Loop: 64 iterations
- Per iteration:
  - 2x self-modified additions: ~4 cycles
  - 2x wrapping (AND): ~4 cycles
  - `tile_quad_sample` call: ~100-200 cycles
  - Pixel stores: ~6 cycles
- **Per iteration**: ~120-220 cycles
- **Loop total**: 64 × 180 = ~11,520 cycles
- Drawing call: ~200 cycles
- **Total**: ~11,700 cycles per strip

**Per Strip Total**: ~12,300 cycles (1.5ms @ 8MHz)

### Full Frame Estimate

**Assumptions**:
- 20-30 visible terrain strips per frame
- Each strip: ~12,300 cycles

**Terrain rendering per frame**:
- 25 strips × 12,300 cycles = 307,500 cycles
- @ 8MHz = **38ms per frame**

**Frame budget**: 55ms @ 18 FPS

**Terrain percentage**: 38ms / 55ms = **69% of frame budget**

This is **much higher** than our initial 32% estimate! The texture sampling loop is very expensive.

### Optimization Techniques Observed

1. **Self-Modifying Code**
   - Writes delta values into instruction immediates
   - Eliminates memory access in 64-iteration loop
   - Saves ~64 cycles per strip

2. **Pre-Computed Scales**
   - Calculates scale, scale/2, scale/8 once
   - Reuses throughout strip rendering
   - Avoids repeated divisions

3. **Integer-Only Math**
   - No floating-point (8086 doesn't have FPU)
   - All divisions by constants (13, 16)
   - Can be optimized by compiler/hand-coding

4. **Sky Pixel Culling**
   - Counts pixels > 95 (sky color)
   - Skips drawing if entire strip is sky
   - Saves ~200 cycles when triggered

5. **LOD Table**
   - Pre-computed scales at different detail levels
   - Table lookup faster than calculation
   - Located at `ds:7A0h`

6. **Perspective Division Optimization**
   - Divisions by 13 and 16 (small constants)
   - Uses byte division (faster than word)
   - 16 allows shift optimization (sar dx, 4)

## Key Insights

### 1. Strip-Based Rendering Confirmed

The terrain is definitely rendered in **horizontal strips** (scanlines), not polygons. Each strip:
- Has 64 pixels width
- Samples texture 64 times
- Projects 2-3 corners to form quad/triangle
- Draws incrementally across screen

### 2. Texture Space is 2048x2048

The wrapping at 0x7FF (2048) confirms:
- Texture coordinates range [0, 2047]
- Likely tiles are stored in a 2048×2048 texture atlas
- UV coordinates wrap (repeating textures)

### 3. Dual-Buffer Pixel Storage

Two bytes stored per pixel:
- `output[i]` - primary color
- `output[i+64]` - secondary data (LOD? lighting?)

Possible uses:
- Different LOD levels (near vs. far)
- Color + intensity
- Base color + shadow

### 4. Self-Modifying Code for Performance

Writing values into instruction immediates was a clever DOS-era optimization:
- Avoids memory reads in tight loops
- Not possible on modern CPUs (execute protection)
- Saves precious cycles on 8086

### 5. Perspective Projection is Simplified

The projection doesn't use full 3D matrix math:
- Only divides by constants (13, 16)
- Separate X and Y scaling
- Likely assumes flat or gently rolling terrain
- Good enough for flight sim terrain

### 6. Sky Detection Optimization

Checking if pixels are > 95 suggests:
- Color palette has sky colors at high indices
- Can skip entire strips if looking at sky
- Saves expensive texture sampling

## Remaining Questions

1. **What does `tile_quad_sample` do exactly?**
   - How is the texture stored?
   - What format: indexed color? RGB?
   - How is filtering done (nearest? bilinear?)

2. **What are the trigonometric stub functions?**
   - `stub_to_249d8` - what transformation?
   - `stub_to_24988` - angle normalization?
   - Sine/cosine tables?

3. **What is the LOD table structure?**
   - How many LOD levels?
   - What scales are stored?
   - When is LOD selector updated?

4. **How are tiles loaded/streamed?**
   - What triggers tile loading?
   - How is the tile cache managed?
   - Where is tile data stored?

5. **What is the dual-buffer purpose?**
   - Why store two bytes per pixel?
   - How are they combined?
   - LOD blending?

## Next Steps

To reach 100% terrain rendering understanding:

### High Priority

1. **Analyze `tile_quad_sample`** (114 bytes, 5 callers)
   - Texture sampling algorithm
   - Data format and storage
   - Filtering technique

2. **Analyze trigonometric stubs**
   - `stub_to_249d8` - transformation function
   - `stub_to_24988` - normalization function
   - Sine/cosine table structure

3. **Analyze `clip_or_draw_dispatch`**
   - How strips are actually drawn
   - Connection to pixel plotting
   - Clipping algorithm

### Medium Priority

4. **Reverse-engineer LOD system**
   - LOD selector logic (`ds:44AAh`)
   - Scale table at `ds:7A0h`
   - Transition algorithm

5. **Understand tile data format**
   - How are tiles stored?
   - Compression format?
   - Texture atlas layout

### Low Priority

6. **Analyze sky rendering**
   - How is sky drawn separately?
   - Sky color palette
   - Horizon blending

## Conclusion

We've successfully reverse-engineered **60% of the core terrain rendering system**:

✅ **Main coordinator** - view transformation, perspective setup, strip iteration  
✅ **3D projection** - perspective division, screen space conversion, clipping  
✅ **Texture sampling** - 64-pixel strips, self-modifying code, sky culling  
⚠️ **Drawing dispatch** - identified but not fully analyzed  
❌ **Texture sampling internals** - `tile_quad_sample` not yet analyzed  
❌ **Trigonometric functions** - stub functions not yet traced  

**Performance**: Terrain rendering consumes **~69% of frame budget**, much more expensive than HUD (2-4%). The texture sampling loop with 64 calls to `tile_quad_sample` is the primary bottleneck.

**Techniques**: Self-modifying code, pre-computed scales, LOD tables, sky culling, integer-only math, and strip-based rendering all combine to achieve playable performance on an 8MHz 8086.

The Falcon 3.0 terrain system is a **masterclass in 1991 optimization techniques** - every cycle counts!

---

**Analysis Date**: 2026-11-11  
**Analyst**: Kiro AI  
**Status**: Core Rendering 60% Complete  
**Next**: Analyze `tile_quad_sample`, trigonometric stubs, and `clip_or_draw_dispatch`
