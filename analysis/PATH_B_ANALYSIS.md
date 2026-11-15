# R15 Simulation Loop - Path B Deep Dive

**Date**: 2026-11-11  
**Purpose**: Understand the 13 unique functions executed in Path B (external view mode)

---

## Executive Summary

Path B represents **external view mode** - when the player is viewing from outside the aircraft (chase camera, flyby camera, external views). This mode requires additional processing for:
1. **View transformation** - Converting world coordinates to camera space
2. **Terrain rendering from external perspective** - Different LOD and culling
3. **Camera state management** - Saving/restoring far pointer state for complex rendering
4. **Additional visual effects** - Scroll rotation, vector normalization

---

## The 13 Path B Unique Functions

### 1. stub_to_205c3 (0x205BF) - 4 bytes
```assembly
call    dispatch_22084_near
retf
```

**Purpose**: Tiny dispatcher stub  
**Callers**: 20 (HUD metrics, explosions, terrain, map overlay)  
**Analysis**: Simple far call wrapper to near dispatcher. Used by multiple HUD and visual effect systems.

---

### 2. undoc_207DD (0x207DD) - 102 bytes ⭐ VIEW TRANSFORMATION
```assembly
push    ds
push    es
mov     ax, 7B0Eh          ; Segment for trig/view data
mov     ds, ax
mov     es, ax
call    view_scroll_rotate_apply     ; Apply scroll/rotation to view
mov     bx, ds:word_7E968           ; Get rotation angles
mov     cx, ds:word_7E966
call    angle_wrap_mask_3fff         ; Wrap angles to 0-0x3FFF range
call    trig_scroll_project_3452     ; Project using trig tables
mov     ax, ds:word_7E536           ; Get view offsets
mov     bx, ds:word_7E538
mov     cx, ax
mov     dx, bx
neg     cx                           ; Negate for inverse transform
neg     dx
mov     si, cs:word_1F6D4           ; Add base offsets
add     si, ds:word_7E53E
add     ax, si
add     cx, si
mov     si, cs:word_1F6D6
add     si, ds:word_7E540
add     bx, si
add     dx, si
mov     ds:word_7B318, ax           ; Store 4 transformed coordinates
mov     ds:word_7B31A, bx
mov     ds:word_7B31C, cx
mov     ds:word_7B31E, dx
mov     si, 238h
call    sub_21DB2                    ; Clip/cull check
jb      short exit
mov     al, ds:byte_7E54E           ; Get render mode byte
mov     si, 238h
call    dispatch_220a4_near         ; Dispatch render
exit:
pop     es
pop     ds
retf
```

**Purpose**: **Camera view transformation for external view**  
**Key Operations**:
- Apply camera rotation and position
- Transform world coordinates to camera space
- Store 4 key view coordinates (likely frustum corners or viewport bounds)
- Dispatch appropriate renderer based on mode

**Certainty**: STRONG - This is clearly handling view transformation math

---

### 3. sub_128CD (0x128CD) - 67 bytes ⭐ TERRAIN SETUP
```assembly
push    es
push    ds
mov     ax, 71C1h               ; Terrain segment
mov     es, ax
mov     di, 0C57h               ; Target offset
mov     cs:word_11CAA, di       ; Store pointer
mov     cs:word_11CAC, ax
push    si
movsw                           ; Copy 12 bytes (6 words)
movsw
movsw
movsw
movsw
movsw
pop     si
mov     ax, [bx]               ; Get altitude
mov     cs:word_11C98, ax
mov     ax, [bx+2]
call    fixed_neg_clamp_f000    ; Clamp negative altitude
mov     cs:word_11C96, ax
mov     ax, [si+8]             ; Get position
mov     dx, [si+0Ah]
mov     cs:word_11CF8, ax       ; Store position
mov     cs:word_11CFA, dx
call    terrain_pos_grid_build  ; Build terrain grid from position
call    terrain_matrix_advance_11d04  ; Advance terrain matrix
pop     ds
pop     es
retf
```

**Purpose**: **Terrain grid setup for external view**  
**Key Operations**:
- Copy 12 bytes of data (likely camera position/orientation)
- Get and clamp altitude values
- Extract XY position
- Build terrain grid based on camera position (not aircraft position)
- Advance terrain rendering matrix

**Certainty**: STRONG - Terrain system preparation with camera as reference point

---

### 4. undoc_109660 (0x109660) - 107 bytes
```assembly
push    ds
push    es
mov     ax, cs:word_1092D4
mov     ds, ax
mov     es, ax
mov     si, 6D60h
mov     di, 6D88h
call    undoc_129F7            ; Transform/process
mov     di, 6E00h
call    sub_1096CB             ; Process to different buffer
mov     cx, 13h                ; Loop 19 times
loop:
    mov     si, 6D74h
    mov     di, 6D88h
    call    undoc_129F7
    mov     si, 6D60h
    mov     di, 6E00h
    call    sub_12B12
    mov     di, 6E78h
    call    sub_1096CB
    mov     cx, 13h
    sub     bx, bx
    inner_loop:
        call    sub_1096EB
        inc     bx
        loop    inner_loop
    mov     si, 6D74h          ; Copy results back
    mov     di, 6D60h
    mov     cx, 0Ah
    rep movsw
    mov     si, 6E78h
    mov     di, 6E00h
    mov     cx, 3Ch
    rep movsw
    loop    outer_loop
call    dispatch_220dc_stub
pop     es
pop     ds
retn
```

**Purpose**: **Iterative buffer processing** (possibly smoothing, interpolation, or progressive refinement)  
**Key Operations**:
- 19 outer iterations
- Multiple buffer transformations (6D60, 6D88, 6E00, 6E78)
- Inner loop processes indexed elements
- Copy results back to source buffers
- Final dispatch call

**Certainty**: MEDIUM - Complex iterative processing, possibly for view smoothing or LOD transitions

---

### 5. sub_12910 (0x12910) - 43 bytes ⭐ TERRAIN FRAME UPDATE
```assembly
push    ds
push    es
mov     bx, 71C1h              ; Terrain segment
mov     ds, bx
mov     es, bx
call    pos_neighbor_norm_scan  ; Scan neighbor tiles
cmp     cs:byte_11CF3, 0       ; Check flag
jnz     skip
mov     ax, cs:word_11CC8
xor     bl, bl
call    terrain_frame_counter_inc  ; Increment frame counter
skip:
mov     cs:byte_11C69, 0       ; Clear flag
call    terrain_attr_walk_13110    ; Walk terrain attributes
pop     es
pop     ds
retf
```

**Purpose**: **Terrain update for external view frame**  
**Key Operations**:
- Scan neighboring terrain tiles
- Conditionally increment terrain frame counter
- Walk terrain attributes (likely for LOD, visibility, streaming)

**Certainty**: STRONG - Terrain system per-frame update

---

### 6. sub_1FE68 (0x1FE68) - 7 bytes ⭐ FLAG SETTER
```assembly
mov     cs:byte_1F75D, 1
retf
```

**Purpose**: **Set rendering flag to TRUE**  
**Analysis**: Sets flag at cs:0x1F75D to 1. Called at 0x108D67 in Path B, right after active_farptr_set.

**Certainty**: PROVEN - Simple flag setter

---

### 7. sub_1FE6F (0x1FE6F) - 7 bytes ⭐ FLAG CLEARER
```assembly
mov     cs:byte_1F75D, 0
retf
```

**Purpose**: **Clear rendering flag to FALSE**  
**Analysis**: Clears flag at cs:0x1F75D to 0. Called at 0x108DB4 in Path B, right after active_farptr_restore.

**Certainty**: PROVEN - Simple flag clearer

**Pattern**: Functions #6 and #7 bracket the far pointer save/restore section!
```
active_farptr_set      ; Save state
sub_1FE68              ; Set flag = 1
... (rendering code)
active_farptr_restore  ; Restore state  
sub_1FE6F              ; Set flag = 0
```

This flag likely controls whether subsequent rendering uses the saved far pointer state or the current state.

---

### 8. vec_delta_norm_1f6ee (0x210FE) - 442 bytes ⭐ VECTOR NORMALIZATION
```assembly
; Calculate delta vectors (target - source) for X, Y, Z
mov     cx, cs:word_1F6E6      ; Shift count for normalization
mov     ax, [si]               ; X component
mov     dx, [si+2]
sub     ax, es:[bx]
sbb     dx, es:[bx+2]
; Shift right CX times with sign preservation
jcxz    store_x
push    cx
or      dx, dx
jns     positive_x
neg     dx
neg     ax
sbb     dx, 0
loop shift_x_neg:
    shr     dx, 1
    rcr     ax, 1
    loop    shift_x_neg
neg     dx
neg     ax
sbb     dx, 0
jmp     store_x
positive_x:
loop shift_x_pos:
    shr     dx, 1
    rcr     ax, 1
    loop    shift_x_pos
store_x:
mov     es:[di+4], ax
mov     cs:word_1F6F2, dx
; ... repeat for Y and Z components ...
; Find maximum absolute component
; Normalize all components by max
retf
```

**Purpose**: **Normalize 3D vector delta** (target position - source position)  
**Key Operations**:
- Calculate deltas for X, Y, Z
- Apply signed shift normalization
- Find maximum component
- Normalize all components by maximum

**Certainty**: STRONG - This is vector math for direction/distance calculations

---

### 9-11. sub_210FE, sub_1FF5D, sub_21240 (Not Yet Analyzed)

Need to extract and analyze these remaining functions.

---

### 12. sub_20BCE (0x20BCE) - Unknown

**Analysis Pending**

---

### 13. active_farptr_set/restore (0x1F0C0, 0x1F0D7)

Already known - these save and restore far pointer state for complex rendering that spans multiple segments.

---

## Path B Execution Flow

```
1. stub_to_205c3              ; Dispatcher stub
2. undoc_207DD                ; VIEW TRANSFORMATION ⭐
   - Apply camera rotation
   - Transform coordinates
   - Dispatch renderer

3. sub_128CD                  ; TERRAIN SETUP ⭐
   - Copy camera data
   - Build terrain grid from camera position
   - Advance terrain matrix

4. undoc_109660               ; ITERATIVE PROCESSING
   - 19 iterations of buffer transforms
   - Possibly view smoothing/interpolation

5. sub_12910                  ; TERRAIN FRAME UPDATE ⭐
   - Scan neighbor tiles
   - Update frame counter
   - Walk attributes

6. sub_1FE68                  ; Set flag = 1
7. active_farptr_set          ; Save far pointer state

   [... main rendering with saved state ...]

8. active_farptr_restore      ; Restore far pointer state
9. sub_1FE6F                  ; Clear flag = 0

10. sub_210FE                 ; VECTOR NORMALIZATION ⭐
    - Calculate normalized direction vector

11. sub_1FF5D                 ; Unknown
12. sub_21240                 ; Unknown
13. sub_20BCE                 ; Unknown
```

---

## Key Insights

### 1. External View = Camera-Based Rendering
Path B processes the simulation from the **camera's perspective** instead of the aircraft's:
- **View transformation** (undoc_207DD): Transforms world to camera space
- **Terrain from camera** (sub_128CD): Builds terrain grid from camera position, not aircraft
- **Different culling**: Camera frustum instead of cockpit view cone

### 2. Bracketed Far Pointer State
The flag set/clear pattern brackets the far pointer save/restore:
```
Set flag → Save state → Render → Restore state → Clear flag
```
This allows the rendering code to know it's using saved state vs current state.

### 3. Additional Processing Overhead
Path B has **9 extra function calls** beyond Path A, explaining the 24% overhead:
- 1 view transformation
- 1 terrain setup  
- 1 iterative processing (19 iterations)
- 1 terrain frame update
- 2 flag set/clear
- 1 vector normalization
- 3 unknown (likely more rendering/effects)

### 4. Why External View Needs Path B

**Path A** (Cockpit):
- Aircraft is always at origin (0,0,0) in view space
- Camera is fixed relative to aircraft
- Simple perspective projection

**Path B** (External):
- Camera is separate entity in world space
- Must transform aircraft position relative to camera
- Camera can be anywhere, looking at aircraft from any angle
- Requires full 3D transformation pipeline

---

## Questions Answered

### Q: What sets r15_external_view_flag?
**A**: View mode selection in the UI or keybindings (F1-F8 keys typically). Need to trace writes to cs:0x107762.

### Q: Why does Path B need far pointer save/restore?
**A**: External view rendering may need to access multiple overlay segments for:
- Camera transformation matrices
- Terrain LOD data from different perspective
- Visual effects (explosions, smoke) visible from external view

### Q: What are the 13 unique functions?
**A**: Analyzed 8 so far:
- **View transformation** (1 function)
- **Terrain setup for camera** (2 functions)  
- **Iterative processing** (1 function, possibly smoothing)
- **Flag management** (2 functions)
- **Vector math** (1 function)
- **Unknown** (3 functions remaining)
- **Far pointer management** (2 functions, already known)

---

## Next Steps

1. ☐ Extract and analyze remaining 3 unknown functions (sub_1FF5D, sub_21240, sub_20BCE)
2. ☐ Trace writes to r15_external_view_flag (cs:0x107762)
3. ☐ Identify camera state structure and storage
4. ☐ Document view transformation matrix format
5. ☐ Test hypothesis: Does pressing F2/F3/F4 toggle this flag?

---

## Certainty Levels

| Function | Certainty | Purpose |
|----------|-----------|---------|
| stub_to_205c3 | PROVEN | Dispatcher stub |
| undoc_207DD | STRONG | View transformation |
| sub_128CD | STRONG | Terrain setup for camera |
| undoc_109660 | MEDIUM | Iterative processing |
| sub_12910 | STRONG | Terrain frame update |
| sub_1FE68 | PROVEN | Set flag = 1 |
| sub_1FE6F | PROVEN | Clear flag = 0 |
| vec_delta_norm_1f6ee | STRONG | Vector normalization |
| active_farptr_set/restore | PROVEN | State management |
| sub_1FF5D | UNKNOWN | Needs analysis |
| sub_21240 | UNKNOWN | Needs analysis |
| sub_20BCE | UNKNOWN | Needs analysis |

---

*Analysis Date*: 2026-11-11  
*Analyst*: Kiro AI  
*Status*: 67% complete (8/12 functions analyzed, excluding far pointer functions)
