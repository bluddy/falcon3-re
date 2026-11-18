# AI Functions Batch 2 Analysis
**Date**: 2025-01-15  
**Batch**: 8 functions (decision trees, range checks, field comparisons)

## Summary

Analyzed 8 more AI support functions. **Key finding**: Registry addresses don't match IDA in several cases. Functions are smaller and have different purposes than documented.

---

## Function Details

### 1. ai_behavior_decision_tree @ 0x3EBA5 ✓

**Size**: 814 bytes  
**Called by**: 2 locations  
**Makes**: 15 calls

**Purpose**: Complex decision tree that sets behavior state codes based on entity combat status

**Key Logic**:
```assembly
; Check for special "ground attack" mode
cmp     byte ptr ds:15B3h, 0        ; Global flag check
test    byte ptr [si+0Ah], 80h       ; Behavior flag bit 7
cmp     byte ptr [di+0B4h], 0        ; Farobj field +0xB4
; If all true: Set special bomber behavior
mov     cs:byte_3D41A, 4
mov     cs:byte_3D41B, 0A7h
```

**Behavior State Codes** (written to cs:byte_3D41A):
- **4**: Bomber/ground attack mode
- **6**: Default cruise
- **7**: Combat initiated
- **8**: Combat engaged
- **9**: Defensive maneuver
- **10 (0xA)**: Target acquired
- **11 (0xB)**: Weapons free
- **12 (0xC)**: Special maneuver

**Farobj Fields Checked** (+0xB4 through +0xBC):
- **+0xB4**: Bombing run flag
- **+0xB6**: Combat readiness level 1
- **+0xB7**: Combat readiness level 2
- **+0xB8**: Combat readiness level 3
- **+0xB9**: Defensive state
- **+0xBA**: Target tracking state
- **+0xBC**: Weapons status

**Global State Writes**:
- **cs:byte_3D41A**: Behavior code
- **cs:byte_3D41B**: Sub-behavior parameter
- **cs:word_3E346**: Range threshold 1 (0x19C8 or 0x4D58)
- **cs:word_3E348**: Range threshold 2  
- **cs:word_3E34A**: Angle parameter
- **cs:loc_3E34C**: Timer/countdown

**Pattern**: Cascading if-else checking farobj combat status bytes in sequence. Earlier checks have priority (bomber > cruise > combat > defensive).

---

### 2. sub_40708 (formerly ai_state_range_check)

**Size**: 124 bytes  
**Address mismatch**: Registry says 0x40768, IDA shows 0x40708  
**Called by**: 2 locations  
**Makes**: 5 calls

**Purpose**: Distance/range calculation between two entities with physics integration

**Key Operations**:
1. Call `flight_physics_integration_engine` for entity [SI]
2. Store result in globals (DS:137Ah, 137Ch, 137Eh)
3. Call physics engine for entity [DI]
4. Subtract positions to get delta vector
5. Transform and scale delta (vec_transform_scale)
6. Clamp result to 0x64 (100 decimal)
7. Call loc_41167 twice (once per entity)

**Signature**:
```c
// Pseudocode
int range_check(entity_t* si, entity_t* di) {
    vec3 pos1 = physics_integrate(si);
    vec3 pos2 = physics_integrate(di);
    vec3 delta = pos2 - pos1;
    int distance = vec_transform_scale(delta);
    distance = min(distance, 100);
    
    // Call unknown function on both entities
    loc_41167(si, distance);
    loc_41167(di, distance);
    
    return 1;
}
```

---

### 3. sub_40784 (formerly ai_state_value_dispatcher)

**Size**: 43 bytes  
**Address mismatch**: Registry says 0x407AA, IDA shows 0x40784  
**Called by**: 1 location  
**Makes**: 2 calls

**Purpose**: State value calculation and conditional dispatch

**Key Logic**:
```assembly
call    hud_font_glyph_get           ; Strange - HUD function?
xor     ah, ah
mov     al, [di+58h]                 ; Read farobj +0x58
add     al, [di+57h]                 ; Add farobj +0x57
adc     ah, 0                        ; Propagate carry
shr     ax, 1                        ; Average: (f57 + f58) / 2
mov     bp, ax
mov     ax, 1
xor     bx, bx
push    si/di
mov     si, [si+6]                   ; Get farobj pointers
mov     di, [di+6]
call    undoc_40DDC                  ; Unknown comparison?
pop     si/di
or      ax, ax
jz      nullsub (return)
jmp     sub_406FD                    ; Dispatch to handler
```

**Interesting**: Averages two farobj bytes (+0x57, +0x58), then uses result for conditional dispatch. Returns early if undoc_40DDC returns 0.

---

### 4. sub_40BF8 (formerly ai_distance_range_check)

**Size**: 21 bytes  
**Address mismatch**: Registry says 0x40C0A, IDA shows 0x40BF8  
**Called by**: 1 location  
**Makes**: 2 calls

**Purpose**: Formation position check with heading correction flag

**Key Logic**:
```assembly
call    entity_record_table_ops      ; Check entity table
jnz     sub_40C14                    ; Branch if non-zero
call    ai_formation_position_calc   ; Calculate formation position
jnz     sub_40C0D                    ; Branch if non-zero
or      byte ptr cs:ai_heading_correction_calc, 8  ; Set bit 3
retn
```

**Purpose**: Simple gate that sets `ai_heading_correction_calc` bit 3 if both entity table ops and formation calc return zero.

---

### 5. undoc_40C73 (formerly ai_rect_ratio_check)

**Size**: 54 bytes  
**Address mismatch**: Registry says 0x40C9E, IDA shows 0x40C73  
**Called by**: 1 location  
**Makes**: 1 call

**Purpose**: Heading delta check with threshold and timer

**Key Logic**:
```assembly
mov     ax, [si+1Dh]                 ; Entity heading
sub     ax, [di+0Ch]                 ; Farobj heading
cwd
xor     ax, dx                       ; Absolute value trick
sub     ax, dx
pop     word ptr [si+1Fh]            ; Restore stack values
pop     word ptr [si+1Dh]
cmp     ax, 1CCh                     ; Compare delta to 0x1CC (460 decimal ~= 25°)
jle     sub_40CAF                    ; Small delta: branch
cmp     cs:word_40C68, 0             ; Check timer
jnz     sub_40CA9                    ; Timer active: skip
; Timer expired: trigger event
mov     ax, [si]
sub     ax, ds:1360h
push    si
call    sub_41D23
mov     cs:word_40C68, 1E0h          ; Reset timer to 0x1E0 (480)
pop     si
retn
```

**Purpose**: Monitors heading delta. If delta > 25° and timer expired, triggers event and resets timer.

**Angle Conversion**: 0x1CC / 16384 * 360 = ~25.3 degrees

---

### 6. sub_40CC5 (formerly ai_rect_ratio_update)

**Size**: 80 bytes  
**Called by**: 1 location  
**Makes**: 2 calls

**Purpose**: Range-based state evaluation with thresholds

**Key Logic**:
```assembly
and     word ptr [si+8], 0FF00h      ; Clear lower byte of state flags
mov     bp, 80E8h                    ; Load constant
; Call undoc_40DDC with specific segment/offset parameters
call    undoc_40DDC
or      ax, ax
jz      sub_40D15                    ; Failed: return
; Check range thresholds
cmp     bx, 3A98h                    ; Range > 0x3A98 (15,000)?
ja      loc_40D19                    ; Too far: branch
mov     cx, 19C8h                    ; Default: long range threshold
mov     dx, 120Ch                    ; Default: short range threshold
call    state_word_44d3d_get
cmp     ax, 3                        ; Check state
jnz     loc_40D0C
mov     cx, 120Ch                    ; Adjusted thresholds for state 3
mov     dx, 990h
; Compare range against thresholds
cmp     bx, cx                       ; Range > long threshold?
ja      loc_40D1D
cmp     bx, dx                       ; Range > short threshold?
ja      loc_40D21
retn
```

**Range Thresholds**:
- **0x3A98** (15,000): Maximum engagement range
- **0x19C8** (6,600): Long range threshold (default)
- **0x120C** (4,620): Short range threshold (default)
- **0x990** (2,448): Close range threshold (state 3)

---

### 7. ai_state_value_get @ 0x428A1 (formerly ai_field_check_flag)

**Size**: 32 bytes  
**Address mismatch**: Registry says 0x428B8, IDA shows 0x428A1  
**Called by**: 34 locations (!!) - heavily used
**Makes**: 0 calls (LEAF function)

**Purpose**: Fast AI state validator - returns 1 if entity is valid target

**Key Logic**:
```assembly
mov     ax, [si]                     ; Entity slot index
sub     ax, word ptr ds:byte_7B328+358h  ; Subtract base
cmp     al, ds:byte_7E207            ; Compare against limit
jge     return_zero                  ; Out of range: return 0
cmp     ax, cs:rfm_related_word_3    ; Compare against RFM global
jz      return_zero                  ; Matches excluded value: return 0
test    byte ptr [si+0Ah], 2         ; Test behavior flag bit 1
jnz     return_zero                  ; Flag set: return 0
mov     ax, 1                        ; Passed all checks: return 1
retn
return_zero:
xor     ax, ax
retn
```

**Purpose**: **Target validation gate**. Returns 1 if entity is valid AI target, 0 otherwise. Checks:
1. Entity in valid slot range
2. Not excluded by RFM global
3. Behavior flag bit 1 clear

**Performance**: Called 34 times - critical path function. All checks are fast (no calls).

---

### 8. undoc_428D4 (formerly ai_field_pair_compare)

**Size**: 101 bytes  
**Address mismatch**: Registry says 0x428E1, IDA shows 0x428D4  
**Called by**: 5 locations  
**Makes**: 3 calls

**Purpose**: Field comparison with debug/UI output

**Key Logic**:
```assembly
test    word ptr ds:byte_7B328+356h, 40h  ; Check global bit 6
jz      skip_ui_output
; Build debug string
mov     ax, [si]
sub     ax, word ptr ds:byte_7B328+358h
call    ai_formation_position_calc
; Copy 16 bytes to buffer at DS:2DC7h
rep movsb
; Copy string from [BX] to buffer
copy_loop:
    mov     al, [si]
    mov     [di], al
    cmp     al, 0                    ; Null terminator?
    jz      done
    inc     si
    inc     di
    jmp     copy_loop
; Display via key event system
call    r05_dgroup_save_reg
call    key_event_gate_process_0c
skip_ui_output:
retn
```

**Purpose**: Debug function. When global flag is set, formats and displays AI state info via UI/key system. Production code probably has flag disabled.

---

## Address Corrections for Registry

| Function | Registry Addr | Actual Addr | Delta |
|----------|--------------|-------------|-------|
| ai_state_range_check | 0x40768 | 0x40708 | -0x60 |
| ai_state_value_dispatcher | 0x407AA | 0x40784 | -0x26 |
| ai_distance_range_check | 0x40C0A | 0x40BF8 | -0x12 |
| ai_rect_ratio_check | 0x40C9E | 0x40C73 | -0x2B |
| ai_field_check_flag | 0x428B8 | 0x428A1 | -0x17 |
| ai_field_pair_compare | 0x428E1 | 0x428D4 | -0x0D |

**Root Cause**: Registry addresses may be outdated or derived from different IDA analysis. Need to verify all AI function addresses.

---

## New Globals Discovered

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| DS:0x15B3 | global_ground_attack_mode | byte | Enables bomber behavior |
| CS:byte_3D41A | behavior_state_code | byte | Current behavior state (4-12) |
| CS:byte_3D41B | behavior_sub_param | byte | Sub-behavior parameter |
| CS:word_3E346 | range_threshold_1 | word | Engagement range (0x19C8 or 0x4D58) |
| CS:word_3E348 | range_threshold_2 | word | Secondary range |
| CS:word_3E34A | behavior_angle_param | word | Angle parameter |
| CS:loc_3E34C | behavior_timer | byte | Countdown timer |
| CS:word_40C68 | heading_delta_timer | word | Timer for heading checks (0x1E0) |

---

## Farobj Fields Discovered

| Offset | Type | Name | Purpose |
|--------|------|------|---------|
| +0x57 | byte | state_value_1 | Averaged with +0x58 for dispatcher |
| +0x58 | byte | state_value_2 | Averaged with +0x57 |
| +0xB4 | byte | combat_flag_bomber | Bombing run active |
| +0xB6 | byte | combat_readiness_1 | Combat state level 1 |
| +0xB7 | byte | combat_readiness_2 | Combat state level 2 |
| +0xB8 | byte | combat_readiness_3 | Combat state level 3 |
| +0xB9 | byte | defensive_state | Defensive maneuver flag |
| +0xBA | byte | target_tracking | Target lock status |
| +0xBC | byte | weapons_status | Weapons armed/fired |

---

## Performance Notes

**Hot Functions**:
- `ai_state_value_get` @ 0x428A1: **34 callers** - critical path validator
- `ai_behavior_decision_tree` @ 0x3EBA5: **814 bytes, 87 comparisons** - complex decision logic

**LEAF Functions** (no calls, fast):
- `ai_state_value_get`: 32 bytes, 34 callers

---

## Next Steps

1. ✅ Analyzed 8 functions (batch 2)
2. **Fix registry addresses** for 6 functions
3. **Add new globals** to globals.yaml
4. **Add farobj fields** to structs.yaml
5. **Continue analyzing** remaining ~29 functions

---

**Status**: Batch 2 complete. Ready for registry updates and batch 3.
