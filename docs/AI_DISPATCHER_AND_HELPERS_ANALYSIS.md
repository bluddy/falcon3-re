# AI Dispatcher and Helper Functions Analysis
**Date**: 2025-01-15  
**Analysis**: IDA Pro script debugging revealed incorrect function sizes in registry

## Executive Summary

Investigated why IDA Python scripts were failing with exit code 1. Root cause: The registry claimed `ai_entity_behavior_dispatcher` was 2580 bytes, but IDA shows it's only **75 bytes**. The "dispatcher" is actually **four separate functions** totaling 1153 bytes:

1. **ai_heading_adjustment_gate** @ 0x3CE92 (75B)
2. **ai_entity_data_copy_18byte** @ 0x3CEDD (23B)
3. **ai_grid_position_update** @ 0x3CEF4 (169B)
4. **ai_state_processor_core** @ 0x3CF9D (886B)

Additionally discovered that `ai_behavior_mirror_to_target` (0x3D1C5) and `ai_target_tracking_update` (0x3D1B6) are **not standalone functions** but internal labels within `ai_state_processor_core`.

---

## Function Analysis

### 1. ai_heading_adjustment_gate @ 0x3CE92 (75 bytes)

**Purpose**: Per-frame heading/turn rate adjustment with RFM-based scaling

**Structure**:
```assembly
push    es
mov     ax, [si+2]           ; Get segment
mov     di, [si+4]           ; Get farobj offset
mov     es, ax
mov     ax, [si+1Dh]         ; Read entity heading
sub     ax, es:[di+0Ch]      ; Compare with farobj heading
call    stub_to_24988        ; Normalize angle?
mov     bx, ax
cmp     ax, 0
jnz     adjust_heading
pop     es
retn

adjust_heading:
push    ax
mov     ax, [si+4Ch]         ; Entity turn rate
mov     cx, cs:word_3B832    ; RFM turn rate scalar ← NEW DISCOVERY
imul    cx
mov     cl, ah
mov     ch, dl               ; Extract high word (multiply-shift pattern)
pop     ax
cmp     ax, cx               ; Clamp to limit
jge     apply_limit
neg     cx
cmp     ax, cx
jle     apply_limit
jmp     write_back

apply_limit:
mov     ax, cx

write_back:
add     ax, es:[di+0Ch]
call    stub_to_24988
mov     es:[di+0Ch], ax
pop     es
retn
```

**Key Findings**:
- Uses **cs:word_3B832** (RFM turn rate scalar) - previously unknown purpose
- Multiply-shift pattern: `(turn_rate * scalar) >> 8`
- Clamps turn adjustment to calculated limit
- Entity context fields:
  - **+0x1D**: Current heading
  - **+0x4C**: Turn rate capability
- Farobj field:
  - **+0x0C**: Heading (updated each frame)

**RFM Global Discovery**:
```yaml
- address: 0x3B832
  segment: CS
  name: rfm_turn_rate_scalar
  doc: |
    RFM-sourced turn rate scaling factor. Used to scale entity turn rate when 
    updating heading. Higher values = more aggressive turning. Likely 
    difficulty-dependent (loaded from DEFBFM1-6.RFM files).
```

---

### 2. ai_entity_data_copy_18byte @ 0x3CEDD (23 bytes)

**Purpose**: Simple memory synchronization between farobj and entity

**Structure**:
```assembly
push    ds
push    es
push    si
mov     di, [si+6]           ; Target: farobj pointer
mov     ax, [si+2]           ; Source segment
mov     si, [si+4]           ; Source offset
mov     ds, ax
mov     cx, 9                ; 9 words = 18 bytes
rep movsw
pop     si
pop     es
pop     ds
retn
```

**Key Findings**:
- Fast block copy using `rep movsw`
- 18 bytes (9 words) transferred
- Direction: entity data ([si+4]) → farobj ([si+6])
- Called during entity state synchronization

---

### 3. ai_grid_position_update @ 0x3CEF4 (169 bytes)

**Purpose**: World grid position update with wraparound and altitude-based field setting

**Structure**:
```
1. Initialize dirty flag (bp = 0)
2. Update X coordinate:
   - Add velocity: [si+33h] += [di+50h]
   - Check underflow (< 0): dec [si+31h], add 0x3334, set dirty
   - Check overflow (>= 0x3334): inc [si+31h], sub 0x3334, set dirty
3. Update Y coordinate:
   - Add velocity: [si+35h] += [di+52h]
   - Check underflow/overflow same as X
4. Set dirty flag if position changed: [si+8] |= 1
5. Copy 18 bytes from farobj to entity
6. Read altitude from [si+14h]
7. Call far_obj_field_call
8. If result == 3:
   - Set field based on altitude:
     - < 0x139: field = 0
     - 0x139-0x1FA: field = (alt - 0x11A) >> 5
     - >= 0x1FA: field = 7
```

**Key Findings**:
- **Grid wraparound**: 0x3334 = 13,108 decimal (world size?)
- Entity context fields:
  - **+0x31**: Grid X (tile coordinate)
  - **+0x32**: Grid Y (tile coordinate)  
  - **+0x33**: Grid X fraction (subpixel)
  - **+0x35**: Grid Y fraction (subpixel)
  - **+0x8 bit 0**: Position dirty flag
  - **+0x14**: Altitude
- Farobj fields:
  - **+0x50**: X velocity
  - **+0x52**: Y velocity

**Altitude Ranges** (in hex):
- **Ground**: < 0x139 (313 decimal) = LOD 0
- **Low**: 0x139-0x1FA (313-506) = LOD scaled
- **High**: >= 0x1FA (506+) = LOD 7

---

### 4. ai_state_processor_core @ 0x3CF9D (886 bytes)

**Entry Points** (internal labels, not separate functions):
- **0x3CF9D**: Main entry (checks entity type)
- **0x3CFAA**: ai_behavior_state_machine (behavior flag processing)
- **0x3D180**: ai_target_tracking_update (target validity checks)
- **0x3D1C5**: ai_behavior_mirror_to_target (wingman behavior sync)

**ai_behavior_mirror_to_target** (internal @ 0x3D1C5):
```assembly
call    ai_record_field_read     ; Get target/leader entity
mov     al, [di+0Ah]             ; Read target behavior flags
and     al, 0FCh                 ; Mask bits 0-1
and     byte ptr [si+0Ah], 3     ; Keep our bits 0-1
or      [si+0Ah], al             ; Copy target bits 2-7

mov     al, [di+0Bh]
and     al, 80h                  ; Copy only bit 7
or      [si+0Bh], al

; Copy additional fields
mov     al, [di+39h]
mov     [si+39h], al
mov     ax, [di+37h]
mov     [si+37h], ax
mov     al, [di+1Ah]
mov     [si+1Ah], al
mov     al, [di+1Bh]
mov     [si+1Bh], al
mov     al, [di+1Ch]
mov     [si+1Ch], al

cmp     word ptr [si+0Ch], 0
jnz     done
call    near ptr ai_state_calculate_helper
done:
retn
```

**Key Findings**:
- Wingman AI copies leader's behavior
- Behavior flag masking:
  - **+0x0A bits 2-7**: Copied from leader (Ground/Landing/Cruise/Combat/etc.)
  - **+0x0A bits 0-1**: Retained (entity-specific state)
  - **+0x0B bit 7**: Copied from leader
- Additional copied fields: +0x39, +0x37, +0x1A/1B/1C

---

## Registry Corrections

### Functions Updated
```yaml
  - address: 0x03ce92
    name: ai_heading_adjustment_gate
    size: 75  # WAS: 2580 (incorrect - included 3 following functions)
    
  - address: 0x03cedd
    name: ai_entity_data_copy_18byte
    size: 23  # NEW: was not in registry
    
  - address: 0x03cef4
    name: ai_grid_position_update
    size: 169  # NEW: was not in registry
    
  - address: 0x03cf9d
    name: ai_state_processor_core
    size: 886  # Confirmed correct
```

### Functions Removed (internal labels, not functions)
- **0x3D1B6**: ai_target_tracking_update (internal @ 0x3D180 within ai_state_processor_core)
- **0x3D1C5**: ai_behavior_mirror_to_target (internal label within ai_state_processor_core)

---

## Global Variables Updated

### cs:word_3B832 - RFM Turn Rate Scalar
**Previous**: Unknown purpose  
**Now**: Turn rate scaling factor for heading adjustment

**Usage**:
```c
// Pseudocode
int turn_rate = entity->turn_rate;         // +0x4C
int scalar = rfm_turn_rate_scalar;         // cs:word_3B832
int scaled = (turn_rate * scalar) >> 8;    // Multiply-shift
int heading_delta = clamp(current - target, -scaled, +scaled);
entity->heading += heading_delta;
```

**Impact**: This is the **second RFM scalar** we've found (first was cs:word_3B830). Both use multiply-shift patterns, confirming RFM files contain difficulty-tuned AI aggression parameters.

---

## IDA Script Issues Resolved

**Problem**: Scripts exiting with code 1, no output  
**Cause**: Function address lookup failed because registry size was wrong  
**Solution**: 
1. Created diagnostic script to check actual IDA function boundaries
2. Discovered 4 functions where registry listed 1
3. Fixed registry entries with correct sizes

**Lesson**: Always verify function boundaries in IDA before assuming registry is correct. Use `idaapi.get_func()` to get actual start/end addresses.

---

## Next Steps

1. ✅ **Fixed registry entries** for dispatcher region
2. ✅ **Documented cs:word_3B832** purpose
3. **Continue analyzing remaining AI functions**:
   - ai_behavior_decision_tree @ 0x3EBA5 (814B, 87 comparisons)
   - Support functions (geometry, data access, helpers)
   - Total remaining: ~37 functions

4. **Runtime analysis** (bookmarked in BOOKMARKS.md):
   - Confirm RFM scalar values across DEFBFM1-6.RFM
   - Test wraparound at 0x3334 world boundary
   - Verify altitude LOD thresholds

---

## Technical Insights

### Multiply-Shift Pattern
Both RFM scalars use this pattern:
```assembly
mov     ax, value
mov     cx, cs:word_3B832
imul    cx
; Result in DX:AX, extract high byte(s)
```

This is **fixed-point multiplication** where the scalar is treated as a fractional value (8.8 or similar format). Common in DOS-era games for performance (no FPU required).

### World Grid System
- **Tile coordinates**: Byte values (+0x31, +0x32)
- **Fractional position**: Word values (+0x33, +0x35)
- **Wraparound**: 0x3334 = 52 tiles × 256 subunits?
- **Dirty tracking**: Bit flag for when tile boundaries crossed

This suggests a **tile-based world** with fractional positioning for smooth movement.

---

## Files Modified

- `registry/functions.yaml`: Fixed 4 function entries, removed 2 invalid entries
- `registry/globals.yaml`: Updated cs:word_3B832 documentation
- `docs/AI_DISPATCHER_AND_HELPERS_ANALYSIS.md`: This document

## Scripts Created

- `diagnose_function.py`: Check if function exists at address
- `check_gap_after_dispatcher.py`: Analyze memory between functions
- `export_real_dispatcher.py`: Export correct disassembly
- `analyze_mirror_to_target.py`: Check function boundaries

---

**Status**: Dispatcher region fully analyzed. Ready to continue with remaining AI functions.
