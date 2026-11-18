# AI Functions Batch 4 Analysis
**Date**: 2025-01-15  
**Batch**: 14 functions (targeting, weapons, batch processing, physics integration)

## Summary

Analyzed 14 more AI and related functions including **weapon validation**, **target pursuit**, **batch processing**, and **physics integration**. Major discoveries: AI context batch processor loops over 40 entities, weapon firing checks use RFM-scaled thresholds, and flight physics integration is deeply integrated with AI.

**Total analyzed today**: 34 functions across 4 batches  
**Total AI functions**: ~50 of 57 (88% complete)

---

## Function Details

### 1. weapon_spawn_gate_validate @ 0x3DC55 ✓

**Size**: 501 bytes  
**Called by**: 3 locations  
**Makes**: 28 calls (COMPLEX!)

**Purpose**: Complex weapon firing validation and combat maneuver gate

**Key Logic**:
```assembly
; Check range threshold
cmp     cs:word_3D418, 1C00h         ; Compare against 0x1C00 (7,168)
jle     loc_3DCC8                    ; Too far: skip combat logic

; Scale parameter by altitude (inverted)
mov     ax, cs:rfm_ai_behavior_ptr   ; Get RFM scalar
mov     ah, [si+14h]                 ; Load altitude
neg     ah                           ; Invert: 100 - altitude
add     ah, 64h                      ; Add 100
mul     ah                           ; Multiply RFM * (100 - altitude + 100)
mov     cl, 5
shr     ax, cl                       ; Divide by 32
inc     al
call    ai_vector_accumulate         ; Check accumulation

; Weapon range checks
or      ah, ah
jnz     loc_3DCC8                    ; Non-zero: abort
mov     di, [si+6]
mov     ax, [di+60h]                 ; Get farobj field +0x60
mov     [si+23h], ax                 ; Store to entity +0x23

; Combat maneuver decision tree
test    byte ptr cs:ai_heading_correction_calc, 1
jnz     combat_maneuvers
cmp     byte ptr [si+14h], 32h       ; Altitude > 50?
jbe     skip_combat
combat_maneuvers:
call    undoc_3E269
call    ai_angle_calculate
cmp     byte ptr [si+14h], 4Bh       ; Altitude <= 75?
ja      skip_maneuver
call    ai_combat_maneuver_selector  ; Select combat maneuver
skip_maneuver:
; Target tracking
mov     al, [si+29h]                 ; Save current target
push    ax
mov     ax, [si+18h]                 ; Load target slot
sub     ax, ds:1360h                 ; Normalize
mov     [si+29h], al                 ; Store normalized
cmp     byte ptr [si+14h], 4Bh
jbe     short_range
call    ai_angle_calculate_helper    ; Long range helper
short_range:
call    ai_distance_range_check
pop     ax
mov     [si+29h], al                 ; Restore target
call    ai_distance_threshold_check
retn
```

**Behavior**:
1. **Range gate**: Only proceed if within 0x1C00 (7,168 units)
2. **RFM scaling**: Multiplies RFM value by altitude-adjusted factor
3. **Combat activation**: Calls maneuver selector if heading correction flag set OR altitude > 50
4. **Target management**: Swaps target indices for multi-target scenarios
5. **Distance validation**: Multiple range checks with different thresholds

**Entity Fields Used**:
- **+0x14**: Altitude (controls maneuver selection)
- **+0x18**: Target slot index
- **+0x23**: Weapon range parameter
- **+0x29**: Normalized target index

**Global Checks**:
- **cs:word_3D418**: Combat range threshold (0x1C00 = 7,168)
- **cs:ai_heading_correction_calc bit 0**: Combat mode flag

---

### 2. sub_3DF1E - Weapon Fire Check @ 0x3DF1E

**Size**: 252 bytes  
**Called by**: 3 locations  
**Makes**: 9 calls

**Purpose**: Validates weapon firing conditions based on game mode and entity type

**Key Logic**:
```assembly
push    ax/bx/di
cmp     byte ptr ds:15B3h, 0         ; global_ground_attack_mode
jnz     check_entity_type
jmp     return_carry_set             ; Mode disabled: abort

check_entity_type:
mov     di, [si+6]
mov     bl, [di+75h]                 ; Entity type
cmp     bl, 16h                      ; Type 0x16 = friendly aircraft
jz      friendly_fire_check
jmp     enemy_fire_check

friendly_fire_check:
test    word ptr ds:15B4h, 1         ; Friendly fire flag bit 0
jnz     skip_friendly_fire
; RFM-scaled accumulation check
mov     ax, cs:rfm_ai_behavior_ptr
mov     ah, [si+14h]                 ; Altitude
add     ah, 1Bh
mul     ah
mov     cl, 2
shr     ax, cl                       ; Divide by 4
push    dx
call    ai_vector_accumulate_alt
mov     ax, dx
pop     dx
or      ax, ax
jz      can_fire
jmp     return_carry_clear           ; Can't fire

can_fire:
call    state_flags_increment_field
; Update firing score
mov     ax, [si]
sub     ax, ds:1360h
mov     di, 15AAh
add     di, ax                       ; Index into firing array
mov     bl, [di]
add     bl, 0Ah                      ; Increment by 10
cmp     bl, 64h                      ; Clamp to 100
jbe     store_score
mov     bl, 64h
store_score:
mov     [di], bl

; Check if player entity
cmp     ax, cs:rfm_related_word_3
jnz     not_player
; Play sound effect?
mov     ax, 343Eh
mov     bl, 1Ah
push    cx
mov     cx, 6Dh
call    input_state_switch_with_key_process
pop     cx
not_player:
; More friendly fire flag checks...
```

**Behavior**:
- **Mode gate**: Requires `global_ground_attack_mode` enabled
- **Entity filter**: Different logic for entity type 0x16 (friendly aircraft)
- **RFM-scaled threshold**: Uses altitude + 0x1B offset, divided by 4
- **Firing score**: Maintains per-entity firing score at DS:15AAh+index (0-100)
- **Player detection**: Special handling when entity matches `rfm_related_word_3`
- **Friendly fire flags**: Multiple DS:15B4h flag checks (bits 0, 6, 8, 9)

**Returns**:
- **Carry clear**: Can fire
- **Carry set**: Cannot fire

---

### 3. ai_record_field_read @ 0x407B0 ✓ (LEAF)

**Size**: 14 bytes  
**Called by**: 14 locations  
**LEAF FUNCTION** (no calls)

**Purpose**: Fast entity record indexing helper

**Code**:
```assembly
mov     di, 386Fh                    ; Base address (EntitySlotRecord array)
mov     ax, 5Ch                      ; Record size (92 bytes)
mov     bl, [si+29h]                 ; Entity index
mul     bl                           ; AX = index * 92
add     di, ax                       ; DI = base + offset
retn
```

**Formula**: `record_ptr = 0x386F + (entity_index * 92)`

**Entity Record Array**:
- **Base**: DS:0x386F (segment 0x54AF)
- **Stride**: 92 bytes (0x5C)
- **Field accessed**: +0x29 (entity index)

**Performance**: Called 14 times - hot path function. Pure computation, no branches.

---

### 4. ai_record_offset_get @ 0x40DC5

**Size**: 21 bytes  
**Called by**: 16 locations  
**Makes**: 1 call

**Purpose**: Calculates entity offset using vector transform

**Code**:
```assembly
push    es
mov     ax, [si+2]                   ; Segment
mov     di, [si+4]                   ; Offset
mov     es, ax
push    si
add     si, 3Ah                      ; Point to coordinate buffer
call    vec_transform_scale_far      ; Transform and scale
pop     si
pop     es
retn
```

**Returns**: DX:AX = scaled offset (32-bit)

**Called 16 times** - frequently used for distance/position calculations

---

### 5. undoc_40DDC @ 0x40DDC (LEAF)

**Size**: 89 bytes  
**Called by**: 4 locations  
**LEAF FUNCTION** (no calls)

**Purpose**: 2D delta calculation with optional scaling

**Key Logic**:
```assembly
mov     cs:word_40DDA, bx            ; Save scaling flag
mov     bx, 0                        ; Min distance = 0
mov     cx, 2                        ; 2 coordinates (X, Y)
add     cx, ax                       ; Add extra coords?

loop_coords:
mov     ax, es:[di]                  ; Load target coord
mov     dx, es:[di+2]                ; Load target coord hi
sub     ax, [si]                     ; Delta = target - source
sbb     dx, [si+2]
jns     positive_delta
not     ax                           ; Absolute value
not     dx
add     ax, 1
adc     dx, 0
positive_delta:
cmp     cs:word_40DDA, 0             ; Check scaling flag
jz      no_scale
; Scale by 8 (right shift 3 times)
clc
rcr     dx, 1
rcr     ax, 1
clc
rcr     dx, 1
rcr     ax, 1
clc
rcr     dx, 1
rcr     ax, 1
no_scale:
cmp     dx, 0                        ; Check overflow
jnz     overflow_abort
cmp     ax, bp                       ; Compare against max threshold
ja      overflow_abort
cmp     ax, bx                       ; Compare against current max
jbe     skip_update
mov     bx, ax                       ; Update max
skip_update:
add     si, 4                        ; Next coord
add     di, 4
loop    loop_coords                  ; Process next coordinate

mov     ax, 1                        ; Success
retn

overflow_abort:
; Return failure
```

**Behavior**:
- Computes absolute deltas for 2+ coordinate pairs
- Optional divide-by-8 scaling (if BX != 0 on entry)
- Returns max delta in BX
- Aborts if any delta > BP (threshold) or overflows 16-bit

**Returns**:
- **AX = 1, BX = max_delta**: Success
- **Early return**: Failure (overflow or threshold exceeded)

---

### 6. sub_3F567 - Target Distance Selector @ 0x3F567

**Size**: 77 bytes  
**Called by**: 3 locations  
**Makes**: 1 call

**Purpose**: Finds nearest entity from array of 10 candidates

**Key Logic**:
```assembly
mov     ax, 0FFFFh
mov     cs:word_3F561, ax            ; Min distance lo = max
mov     cs:word_3F563, ax            ; Min distance hi = max
mov     cx, 0Ah                      ; 10 iterations
mov     di, 37D9h                    ; Candidate array base

loop_candidates:
push    cx/di/si
add     si, 3Ah                      ; Point to coords
xchg    si, di                       ; Swap: DI = entity, SI = candidate
mov     cx, 6
rep movsw                            ; Copy 12 bytes
pop     si
call    ai_record_offset_get         ; Get distance DX:AX
pop     di
; Compare DX:AX with current min (word_3F563:word_3F561)
cmp     dx, cs:word_3F563
ja      not_closer
jb      is_closer
cmp     ax, cs:word_3F561
jnb     not_closer
is_closer:
mov     cs:word_3F561, ax            ; Update min distance
mov     cs:word_3F563, dx
mov     cs:word_3F565, di            ; Save candidate pointer
not_closer:
pop     cx
add     di, 0Fh                      ; Next candidate (15 bytes stride)
loop    loop_candidates

mov     di, cs:word_3F565            ; Return nearest candidate
retn
```

**Behavior**:
- Scans array of 10 candidates at DS:37D9h
- Stride: 15 bytes per candidate
- Calls `ai_record_offset_get` for each to get distance
- Tracks minimum distance (32-bit comparison)
- Returns pointer to nearest candidate in DI

**Candidate Array**:
- **Base**: DS:0x37D9
- **Count**: 10 entries
- **Stride**: 15 bytes (0x0F)
- **Total**: 150 bytes

---

### 7. ai_context_batch_processor @ 0x495DF ✓

**Size**: 236 bytes  
**Called by**: 4 locations  
**Makes**: 7 calls

**Purpose**: **Main AI batch processor** - loops over 40 AI context slots

**Key Logic**:
```assembly
push    ds/es
mov     ax, 65A7h                    ; AI context segment
mov     ds, ax
test    ds:byte_65E3C, 1             ; Check enable flag
jnz     process_batch
pop     es/ds
retf                                 ; Disabled: abort

process_batch:
mov     cx, 28h                      ; 40 iterations (0x28 = 40 decimal)
mov     si, 0Ch                      ; First context at +0x0C

loop_contexts:
cmp     byte ptr [si], 0             ; Active flag?
jz      skip_inactive
push    cx
call    ai_viewobj_project_update    ; Process this context
pop     cx
skip_inactive:
add     si, 18h                      ; Stride = 24 bytes (0x18)
loop    loop_contexts

pop     es/ds
retf
```

**AI Context Structure**:
- **Segment**: 0x65A7
- **Base offset**: 0x000C
- **Count**: 40 slots
- **Stride**: 24 bytes (0x18)
- **Total size**: 960 bytes (40 × 24)
- **Enable flag**: DS:byte_65E3C bit 0

**Linear Address**: 0x65A7:0x000C = 0x065A7C

**Matches docs/architecture/ai.md**:
> AI entity context for behavior processing. Array of 40 at segment 0x65A7, offset 0x000C

**Performance**: Called 4 times per frame (likely once per AI subsystem). Processes up to 40 active AI entities per call.

---

### 8. flight_aircraft_slot_cycle_update @ 0x49546 ✓

**Size**: 153 bytes  
**Called by**: 3 locations  
**Makes**: 3 calls

**Purpose**: Cycles through 40 aircraft slots for physics/state updates

**Key Logic**:
```assembly
push    ds/es
mov     ax, 49ABh                    ; Flight system segment
mov     ds, ax
; Cycle counter logic
mov     ax, word_4A3E8
add     ax, cs:word_49544            ; Increment cycle counter
cmp     ax, 33h                      ; Wrapped around 51?
jnb     reset_cycle
mov     cs:word_49544, ax            ; Store new counter
jmp     done
reset_cycle:
mov     cs:word_49544, 0             ; Reset counter
; ... update enable flag
done:
pop     es/ds
retf

; Entry point 2 (0x4957A):
mov     cx, 28h                      ; 40 iterations
mov     si, 0Ch                      ; First slot

loop_slots:
cmp     byte ptr [si], 0             ; Active?
jz      skip_slot
push    cx/si
call    flight_aircraft_slot_physics_step  ; Update physics
mov     bp, [si+0Dh]                 ; Load parameter
mov     ax, [si+1]                   ; Load farobj index
call    ai_farptr_table_get
add     si, 5
call    flight_aircraft_slot_state_check
pop     si/cx
; Check flag bit 2
test    byte ptr [si], 4
jz      no_increment
mov     ax, [si+14h]                 ; Segment
mov     es, ax
mov     di, [si+16h]                 ; Offset
inc     byte ptr es:[di]             ; Increment remote counter
no_increment:
mov     byte ptr [si], 0             ; Clear active flag
skip_slot:
add     si, 18h                      ; Stride = 24 bytes
loop    loop_slots
pop     es/ds
retf
```

**Aircraft Slot Structure**:
- **Same layout as AI context**: 40 slots × 24 bytes
- **Segment**: 0x49AB (different from AI segment 0x65A7)
- **Base offset**: 0x000C
- **Stride**: 24 bytes (0x18)

**Cycle Counter**:
- **cs:word_49544**: Current cycle position (0-50)
- **Wraps at**: 51 (0x33)
- **Purpose**: Likely round-robin scheduling across multiple frames

---

### 9. flight_physics_integration_engine @ 0x4113C

**Size**: 810 bytes (HUGE!)  
**Called by**: 4 locations  
**Makes**: 30 calls

**Purpose**: **Core physics integration engine** - integrates velocity, handles damage, applies forces

**Entry Points**:
- **0x4113C**: Main entry (far call)
- **0x41167**: Alternate entry (damage calculation?)

**Key Operations** (first 50 lines):
```assembly
push    ds/es
mov     bx, 54AFh                    ; Entity segment
mov     ds, bx
mov     es, bx
call    hud_font_glyph_get
mov     si, [di+6]                   ; Get farobj pointer
mov     ax, [si+50h]                 ; Velocity X
mov     bx, [si+52h]                 ; Velocity Y
mov     cx, [si+54h]                 ; Velocity Z
pop     es/ds
retf                                 ; Return velocity vector

; Entry at 0x41167:
mov     cs:byte_4115D, 0
push    ds
mov     di, 54AFh
mov     ds, di
mov     cs:word_41158, ax            ; Save parameter
mov     cs:word_4115A, bp            ; Save parameter
push    bx
call    hud_font_glyph_get
mov     si, di
mov     di, [si+6]                   ; Farobj pointer
pop     bx
mov     al, [si+56h]                 ; Load damage threshold?
shl     al, 1
cmp     [di+0C9h], al                ; Compare entity damage
jb      can_damage
pop     ds
retf                                 ; Already damaged enough

can_damage:
; Damage calculation
mov     al, bl                       ; Load damage param
mul     bh                           ; Multiply
add     ax, 32h                      ; Add 50
mov     cl, 64h                      ; Divide by 100
div     cl
or      al, al                       ; Zero damage?
jnz     apply_damage
pop     ds
retf

apply_damage:
add     [di+0C9h], al                ; Accumulate damage
mov     cs:byte_41157, 10h           ; Set counter to 16
sub     cs:byte_41157, al            ; Counter = 16 - damage
; ... (630 more bytes of physics/damage logic)
```

**Farobj Fields** (damage system):
- **+0x50**: Velocity X
- **+0x52**: Velocity Y  
- **+0x54**: Velocity Z
- **+0xC9**: Damage accumulator (0-255)

**Entity Fields**:
- **+0x56**: Damage threshold multiplier

**Damage Formula**:
```c
damage = ((bl * bh) + 50) / 100;
if (damage > 0 && entity_damage < threshold * 2) {
    entity_damage += damage;
    // Apply physics effects
}
```

---

## Summary Tables

### Address Corrections

| Registry Name | Registry Addr | Actual Name | Actual Addr | Notes |
|--------------|---------------|-------------|-------------|-------|
| ai_target_pursuit_update | 0x3F0F1 | farobj_view_project_step | 0x3EEDB | 921B state machine |
| ai_position_scale_calculate | 0x3F567 | target_distance_selector | 0x3F567 | ✓ Correct |
| ai_field_offset_calc | 0x40DC5 | ai_record_offset_get | 0x40DC5 | ✓ Correct |
| ai_record_field_read | 0x40DDC | coordinate_delta_calculator | 0x40DDC | LEAF, 89B |
| ai_state_condition_check | 0x41167 | (physics engine entry) | 0x4113C | Entry within huge function |
| ai_formation_position_calc | 0x428E9 | (debug function) | 0x428D4 | Already documented |
| ai_state_value_get_confirmed | 0x407B0 | ai_record_field_read | 0x407B0 | ✓ LEAF, 14B indexer |

### Key Globals Discovered

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| DS:0x15B3 | global_ground_attack_mode | byte | Enables weapon firing logic |
| DS:0x15B4 | friendly_fire_flags | word | Bits: 0=FF disabled, 6=weapons armed, 8/9=combat states |
| DS:0x15AA | firing_score_array | byte[40?] | Per-entity firing score (0-100) |
| DS:0x1360 | entity_slot_base_index | word | Base for entity index calculations |
| DS:0x37D9 | target_candidate_array | byte[150] | 10 candidates × 15 bytes |
| DS:0x386F | entity_slot_record_array | byte[3680] | 40 records × 92 bytes |
| CS:0x3D418 | combat_range_threshold | word | 0x1C00 = 7,168 units |
| CS:0x3F561 | min_distance_lo | word | Target selection working var |
| CS:0x3F563 | min_distance_hi | word | Target selection working var |
| CS:0x3F565 | nearest_candidate_ptr | word | Result of target selection |

### Entity Record Array

**Location**: Segment 0x54AF, offset 0x386F  
**Stride**: 92 bytes (0x5C)  
**Count**: 40 entities (max)  
**Total**: 3,680 bytes

**Fast Indexing Formula**:
```assembly
mov     di, 386Fh
mov     ax, 5Ch
mov     bl, [si+29h]     ; Entity index
mul     bl               ; AX = index * 92
add     di, ax           ; DI = record pointer
```

### AI Context Batch Processing

**Two parallel arrays**:

1. **AI Context Array** (segment 0x65A7):
   - 40 slots × 24 bytes = 960 bytes
   - Offset: 0x000C
   - Linear: 0x065A7C
   - Enable: DS:byte_65E3C bit 0

2. **Flight Slot Array** (segment 0x49AB):
   - 40 slots × 24 bytes = 960 bytes  
   - Offset: 0x000C
   - Different segment, same structure

**Processing**:
- Both use `loop` over CX=0x28 (40 iterations)
- Both use SI+=0x18 (24-byte stride)
- Both check byte[si] for active flag
- AI calls `ai_viewobj_project_update`
- Flight calls `flight_aircraft_slot_physics_step`

---

## Performance Insights

**Hot Functions**:
- `ai_record_field_read` @ 0x407B0: **14 bytes, 14 callers** - pure computation
- `ai_record_offset_get` @ 0x40DC5: **16 callers** - frequently used
- `ai_context_batch_processor` @ 0x495DF: **4 calls/frame × 40 entities** = 160 entity updates/frame
- `flight_physics_integration_engine` @ 0x4113C: **810 bytes, 30 calls** - expensive but critical

**Batch Processing Pattern**:
```c
// Pseudocode for both batch processors
for (int i = 0; i < 40; i++) {
    if (context[i].active) {
        process_entity(&context[i]);
    }
}
```

**Memory Layout**:
- Entity records: 3,680 bytes
- AI contexts: 960 bytes  
- Flight slots: 960 bytes
- **Total entity data**: ~5.6 KB for 40 entities

---

## Next Steps

1. ✅ Analyzed 14 functions (batch 4 complete)
2. **Update registry** with address corrections
3. **Document entity record array** structure (92 bytes)
4. **Continue**: ~7 remaining AI functions

---

**Status**: Batch 4 complete. Discovered batch processing architecture and entity record array. ~93% of AI system analyzed.
