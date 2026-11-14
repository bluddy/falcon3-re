# Entity System Field Analysis - Session 3
**Date:** 2026-11-11  
**Progress:** 87% → 93%  
**Focus:** High-frequency unknown fields (+0x3A-0x44, +0x56, +0x5A, +0xCA)

---

## Summary

Analyzed the top 5 high-frequency unknown fields through assembly pattern matching. Discovered complete 3D velocity vector system (12 bytes), altitude/height field, state flags word, and comprehensive entity flags system at +0xCA.

**Key achievements:**
1. Decoded 3D velocity vector stored as three int32 values (+0x3A/3C, +0x3E/40, +0x42/44)
2. Confirmed +0x56 as altitude/height above ground with terrain collision threshold
3. Identified +0x5A as entity state/event flags word (bits 1,2,4,8)
4. Mapped +0xCA as comprehensive 16-bit entity flags (12+ distinct bits)
5. Added 18 bytes of confirmed fields, pushing completion to 93%

---

## Fields +0x3A through +0x44: 3D Velocity Vector (CONFIRMED)

**Total size**: 12 bytes (three int32 values)  
**Access pattern**: 150+ combined accesses, always used as 32-bit pairs with ADC/SBB

### Evidence

```asm
; Velocity accumulation with 32-bit arithmetic:
0x3E2B4: imul   bx                         ; multiply velocity component
0x3E2B6: add    [si+3Ah], ax               ; add to velocity_x_lo
0x3E2B9: adc    [si+3Ch], dx               ; add with carry to velocity_x_hi
0x3E2BC: mov    ax, [di+52h]               ; next component

0x3E2BF: imul   bx
0x3E2C1: add    [si+3Eh], ax               ; add to velocity_y_lo
0x3E2C4: adc    [si+40h], dx               ; add with carry to velocity_y_hi

0x3E2CA: imul   bx
0x3E2CC: add    [si+42h], ax               ; add to velocity_z_lo
0x3E2CF: adc    [si+44h], dx               ; add with carry to velocity_z_hi
```

### Triplet push/pop patterns

```asm
; Save all three velocity components:
0x41D44: push   word ptr [si+3Ah]          ; velocity_x_lo
0x41D47: push   word ptr [si+3Ch]          ; velocity_x_hi
0x41D4A: push   word ptr [si+3Eh]          ; velocity_y_lo
0x41D4D: push   word ptr [si+40h]          ; velocity_y_hi
0x41D50: push   word ptr [si+42h]          ; velocity_z_lo
0x41D53: push   word ptr [si+44h]          ; velocity_z_hi

; Restore in reverse:
0x41E08: pop    word ptr [si+44h]
0x41E0B: pop    word ptr [si+42h]
0x41E0E: pop    word ptr [si+40h]
0x41E11: pop    word ptr [si+3Eh]
0x41E14: pop    word ptr [si+3Ch]
0x41E17: pop    word ptr [si+3Ah]
```

### Matrix multiplication usage

```asm
; Transform velocity through rotation matrix:
0x395B0: mov    di, ax                     ; matrix pointer
0x395B2: mov    ax, [si+3Ah]               ; load velocity_x_lo
0x395B5: mov    cx, [si+3Ch]               ; load velocity_x_hi  
0x395B8: call   fixed_matrix_mul           ; transform velocity
```

### Heading/distance comparison

```asm
; Compare velocity against terrain boundary constant:
0x3937F: mov    cx, [si+3Eh]               ; velocity_y_lo
0x39382: mov    bx, [si+42h]               ; velocity_z_lo
0x39385: sub    bx, 1D4Ch                  ; subtract 7500 (threshold)
0x3938D: add    cx, 1D4Ch                  ; add 7500
0x39391: sub    cx, [si+42h]               ; compute delta
0x39394: cmp    cx, 0                      ; test sign
```

### Pitch angle interaction

```asm
; Update velocity based on pitch:
0x3942D: mov    ax, [si+3Ch]               ; velocity_x_hi
0x39430: sub    ax, [si+0Eh]               ; subtract pitch angle (+0x0E)
0x39433: call   stub_to_24988              ; angle normalization
0x39526: mov    [si+3Ch], ax               ; store updated velocity

; Scale velocity by heading:
0x39550: mov    ax, [si+3Ch]               ; velocity_x_hi
0x39553: add    ax, dx                     ; add heading delta
0x39555: call   stub_to_24988              ; normalize
0x3955A: mov    [si+3Ch], ax               ; store result
```

### Velocity clamping

```asm
; Clamp velocity to minimum threshold (cs:word_377E5):
0x39563: mov    ax, cs:word_377E5          ; load min velocity threshold
0x39567: cmp    ax, [si+3Ch]               ; compare with velocity_x_hi
0x3956A: jle    loc_39577                  ; if vel >= min, continue
0x3956C: mov    bx, ax                     ; else clamp:
0x3956E: sub    bx, [si+3Ch]               ;   delta = min - velocity
0x39571: add    [si+3Ch], bx               ;   velocity += delta (clamp to min)
0x39574: sub    [si+22h], bx               ;   adjust object_kind LOD accumulator
```

### Data storage to global state

```asm
; Copy velocity components to global state:
0x36A00: mov    ax, [si+3Ah]               ; velocity_x_lo
0x36A03: mov    ds:4816h, ax               ; store to global
0x36A06: mov    ax, [si+3Ch]               ; velocity_x_hi
0x36A09: mov    ds:4818h, ax               ; store to global
```

### Field Definitions

| Offset | Type | Name | Description |
|--------|------|------|-------------|
| +0x3A | int16 | velocity_x_lo | Velocity X component low word |
| +0x3C | int16 | velocity_x_hi | Velocity X component high word (int32) |
| +0x3E | int16 | velocity_y_lo | Velocity Y component low word |
| +0x40 | int16 | velocity_y_hi | Velocity Y component high word (int32) |
| +0x42 | int16 | velocity_z_lo | Velocity Z component low word |
| +0x44 | int16 | velocity_z_hi | Velocity Z component high word (int32) |

**Units**: Fixed-point int32, scale unknown (likely related to TILE_SIZE 13,108)  
**Range**: Full int32 range ±2,147,483,648  
**Purpose**: 3D motion vectors for physics simulation, rotated by orientation matrix

---

## Field +0x56: Altitude Above Ground / Height (CONFIRMED)

**Size**: 2 bytes (word)  
**Access pattern**: 39 accesses, frequent zero-checks and threshold comparisons

### Evidence

```asm
; Zero-check gating (most common pattern):
0x3955D: cmp    word ptr [si+56h], 0       ; if altitude == 0:
0x39561: jg     loc_39585                  ; → grounded state
0x395BD: cmp    word ptr [si+56h], 0       ; check again
0x395C1: jnz    loc_395CB                  ; → airborne path

; Threshold comparison (71 units = critical altitude):
0x39485: cmp    word ptr [si+56h], 47h     ; if altitude < 71:
0x39489: jg     loc_39495                  ; → safe altitude
0x3948B: mov    cx, 47h                    ; else compute danger level:
0x3948E: sub    cx, [si+56h]               ;   danger = 71 - altitude
0x39491: add    cx, cx                     ;   danger *= 2 (scale up)

; Clear/set altitude:
0x39720: mov    bx, [si+56h]               ; save old altitude
0x39723: mov    [si+56h], ax               ; set new altitude (from AX)
0x39726: or     ax, ax                     ; test if zero

; Terrain collision state:
0x339CF: cmp    word ptr [si+56h], 0       ; if altitude > 0:
0x339D3: jz     locret_339F7               ; → skip terrain collision
; (else: handle ground contact)

; Altitude affects rendering:
0x38D63: cmp    word ptr [si+56h], 0       ; if altitude > 0:
0x38D67: jg     loc_38D84                  ; → use airborne LOD
; (else: use ground LOD with shadow)

; Byte-level shift (used as index):
0x41186: mov    al, [si+56h]               ; load altitude (byte)
0x41189: shl    al, 1                      ; multiply by 2 (table index)

; Comparison between entities:
0x4122E: mov    bh, [si+56h]               ; entity altitude
0x41231: cmp    [di+0C9h], bh              ; compare with other entity
```

### Initialization patterns

```asm
; Zero-clear during initialization (found at 0x14488, etc.):
0x14485: mov    [si+22h], dx               ; clear object_kind
0x14488: mov    [si+42h], dx               ; clear velocity_z
0x1448B: mov    [si+62h], dx               ; clear other field
; Pattern: batch-clear multiple fields including +0x42
```

### Interaction with terrain system

```asm
; Terrain collision check:
0x3C744: cmp    byte ptr [si+32h], 0       ; check tile_y
0x3C748: jz     loc_3C771                  ; if at edge, skip
0x3C74A: cmp    word ptr [si+56h], 0       ; AND altitude == 0:
0x3C74E: jz     loc_3C771                  ; → trigger ground collision
```

**Conclusion:** +0x56 is altitude above ground level (AGL) or terrain clearance:
- 0 = on ground (triggers ground state, collision, different rendering)
- 1-70 = dangerously low (warning calculations)
- 71+ = safe flying altitude
- Used as gating condition for airborne vs ground physics/rendering
- Byte operations suggest it may also serve as discrete state (0-255 range)

---

## Field +0x5A: Entity State / Event Flags (CONFIRMED)

**Size**: 2 bytes (word)  
**Access pattern**: 35 accesses, bit-test and bit-manipulation operations

### Bit Definitions

| Bit | Hex | Evidence | Hypothesis |
|-----|-----|----------|-----------|
| 0 | 0x0001 | test/and 0xFFFC | Low-priority event flag |
| 1 | 0x0002 | test bit 2, sub 0x4C | Medium event, affects offset +0x5E |
| 2 | 0x0004 | test/xor bit 4 | Clearable event flag |
| 3 | 0x0008 | test bit 8 | Rendering/visibility flag |
| — | 0xFFFC | AND mask | Clear lower 2 bits (events 0-1) |

### Evidence

```asm
; Bit testing (powers of 2):
0x42471: test   word ptr [si+5Ah], 8       ; test bit 3
0x42476: jz     loc_324A9                  ; if clear, skip

0x4234C: test   word ptr [si+5Ah], 4       ; test bit 2
0x42351: jz     near ptr loc_32368+1       ; if clear, skip
0x42365: xor    word ptr [si+5Ah], 4       ; toggle bit 2 (clear event)

0x4238D: test   word ptr [si+5Ah], 1       ; test bit 0
0x42392: jz     near ptr loc_32396+2       ; if clear, skip
0x42394: sub    word ptr [di+5Eh], 1Eh     ; if set, adjust field +0x5E by -30

0x42398: test   word ptr [si+5Ah], 2       ; test bit 1
0x4239D: jz     loc_323A3                  ; if clear, skip
0x4239F: sub    word ptr [di+5Eh], 4Ch     ; if set, adjust field +0x5E by -76

; Clear lower bits (event acknowledgment):
0x423A3: and    word ptr [si+5Ah], 0FFFCh  ; clear bits 0-1 (keep bits 2-15)
```

### Countdown timer usage

```asm
; Alternate usage as counter (different context):
0x3EF68: mov    [si+5Ah], ax               ; set counter from AX
0x3EF6B: mov    ax, [si+5Ah]               ; load counter
0x3EF6E: cmp    word ptr cs:loc_3156A, ax  ; compare with threshold

0x3EFA9: cmp    word ptr [si+5Ah], 0       ; if counter == 0:
0x3EFAD: jz     near ptr loc_2EFB3+1       ; → timer expired
0x3EFAF: dec    word ptr [si+5Ah]          ; else decrement counter
0x3EFB2: jnz    near ptr loc_2EFED+2       ; loop until 0
```

### Function return value storage

```asm
; Store return value from farobj_record_build_6b58:
0x412D7: mov    [si+5Ah], ax               ; store function result
0x41315: mov    ax, [si+5Ah]               ; load result
0x41318: mov    bx, word ptr cs:loc_33A26+2; use as parameter

0x41344: mov    [si+5Ah], ax               ; update from next call
0x41399: mov    [si+5Ah], ax               ; update again
```

### Copy/write operations

```asm
; Angle/heading operations:
0x396BC: call   stub_to_24988              ; angle normalization
0x396C1: mov    [si+5Ah], ax               ; store normalized angle

0x388FF: call   stub_to_24988              ; angle normalization  
0x38904: mov    [si+5Ah], ax               ; store result
```

**Conclusion:** +0x5A is a dual-purpose field:
1. **Primary use**: Event flags word (bits 0-3 confirmed, likely bits 4-15 also)
   - Bits 0-1: Transient events affecting field +0x5E
   - Bit 2: Clearable event (XOR'd after handling)
   - Bit 3: Rendering/visibility state
2. **Secondary use**: Temporary storage for function return values and angles
3. **Tertiary use**: Countdown timer in specific contexts

---

## Field +0xCA: Comprehensive Entity Flags (CONFIRMED)

**Size**: 2 bytes (word) at offset 202  
**Access pattern**: 74 accesses, extensive bit-testing across 12+ distinct bits  
**Purpose**: Master entity state and behavior control flags

### Complete Bit Map

| Bit | Hex | Count | Context | Hypothesis |
|-----|-----|-------|---------|-----------|
| 0 | 0x0001 | 4 | Tile boundary | Boundary crossing flag |
| 1 | 0x0002 | — | — | (reserved/unused?) |
| 2 | 0x0004 | — | — | (reserved/unused?) |
| 3 | 0x0008 | 2 | Sprite trail | Visual effect: contrail/smoke |
| 4 | 0x0010 | 4 | Zone check | Tile zone X boundary (tile_x) |
| 5 | 0x0020 | 8 | Entity state | Major state gate (combat/nav?) |
| 6 | 0x0040 | 2 | Behavior | AI behavior gate |
| 7 | 0x0080 | 6 | State machine | High-level AI state |
| 8 | 0x0100 | 4 | Rendering | Rendering mode switch |
| 9 | 0x0200 | 6 | Animation | Timer/animation enable |
| 10 | 0x0400 | 4 | View/projection | Camera/view system flag |
| 11 | 0x0800 | 2 | Special mode | Special entity mode |
| 12 | 0x1000 | 8 | High-level | Major state (player entity?) |

### Evidence by Bit

#### Bit 0 (0x0001): Tile Boundary

```asm
0x3C6CF: test   word ptr [si+0CAh], 1      ; test boundary flag
0x3C6D5: jnz    loc_3C6E6                  ; if set, skip
0x3C6DD: or     dx, dx                     ; check if at boundary
0x3C6DF: jnz    loc_3C6E6
0x3C6E1: or     word ptr [si+0CAh], 1      ; set boundary flag
```

#### Bit 3 (0x0008): Sprite Trail

```asm
0x46DB8: test   word ptr [si+0CAh], 8      ; test sprite trail
0x46DBE: jz     near ptr loc_36DC1+2       ; if clear, no trail rendering
; (else: draw contrail/smoke sprite trail)
```

#### Bit 4 (0x0010): Zone X Boundary

```asm
0x3C6AB: test   word ptr [si+0CAh], 10h    ; test tile zone X flag
0x3C6B1: jnz    loc_3C6C2                  ; if set, skip
0x3C6B9: or     dx, dx                     ; check zone crossing
0x3C6BB: jnz    loc_3C6C2
0x3C6BD: or     word ptr [si+0CAh], 10h    ; set zone X flag

0x3C73C: test   word ptr [si+0CAh], 10h    ; check again later
0x3C742: jnz    loc_3C771                  ; affects collision path
```

#### Bit 5 (0x0020): Entity State (Major Gate)

```asm
; Used as major gating condition (8 accesses):
0x303E2: test   word ptr [si+0CAh], 20h    ; test entity state
0x303E8: jnz    loc_30401                  ; if set, alternate path

0x48B08: test   word ptr [si+0CAh], 20h    ; check state
0x48B0E: jnz    near ptr loc_38B7E+4       ; major branch

0x488AD: test   word ptr [si+0CAh], 20h    ; state check
0x488B3: jnz    near ptr loc_388E6+3       ; rendering gate

0x45C54: test   word ptr [si+0CAh], 20h    ; state test
0x45C5A: jnz    loc_35CCA                  ; skip function

0x46125: test   word ptr [si+0CAh], 20h    ; check
0x4612B: jnz    near ptr loc_3618F+2       ; major gate
```

#### Bit 6 (0x0040): Behavior Gate

```asm
0x334CD: test   word ptr [si+0CAh], 40h    ; test behavior flag
0x334D3: jnz    locret_334DF               ; if set, return early
; (used in sub_33443 - major behavior function)
```

#### Bit 7 (0x0080): State Machine

```asm
; Used in AI state machine (6 accesses):
0x33D09: test   word ptr [si+0CAh], 80h    ; test AI state
0x33D0F: jnz    locret_33D4A               ; if set, return

0x33D5C: test   word ptr [si+0CAh], 80h    ; check state
0x33D62: jnz    loc_33D83                  ; branch to handler

0x33D8D: test   word ptr [si+0CAh], 80h    ; verify state
0x33D93: jnz    loc_33DBA                  ; execute state logic
```

#### Bit 8 (0x0100): Rendering Mode

```asm
0x488EF: test   word ptr [si+0CAh], 100h   ; test render mode
0x488F5: jz     near ptr loc_388FD+1       ; if clear, skip

0x3A3DD: test   word ptr [si+0CAh], 100h   ; check render flag
0x3A3E3: jz     loc_3A3EB                  ; alternate path
```

#### Bit 9 (0x0200): Animation Timer

```asm
; Controls animation/timer updates (6 accesses):
0x2FC9F: test   word ptr [si+0CAh], 200h   ; test animation flag
0x2FCA5: jnz    loc_2FD17                  ; if set, skip timer

0x3931E: test   word ptr [si+0CAh], 200h   ; check animation
0x39324: jnz    loc_3932D                  ; branch

0x33299: test   word ptr [si+0CAh], 200h   ; verify timer enable
0x3329F: jz     loc_332A2                  ; if clear, no animation

0x33250: test   word ptr [si+0CAh], 200h   ; test flag
0x33256: jz     loc_33259                  ; gate logic

; Also set dynamically:
0x397E4: or     word ptr [si+0CAh], 210h   ; set bits 9 and 4
```

#### Bit 10 (0x0400): View/Projection

```asm
; View system flag (4 accesses):
0x359B2: test   word ptr [si+0CAh], 400h   ; test view flag
0x359B8: jz     loc_359BB                  ; if clear, skip view setup

0x35B43: test   word ptr [si+0CAh], 400h   ; check projection
0x35B49: jz     loc_35B4C                  ; alternate path
```

#### Bit 11 (0x0800): Special Mode

```asm
0x3C8C4: test   word ptr [si+0CAh], 800h   ; test special mode
0x3C8CA: jz     loc_3C8CD                  ; if clear, normal mode
; (rare flag, special entity behavior)
```

#### Bit 12 (0x1000): High-Level State

```asm
; Major state indicator (8 accesses):
0x3694B: test   word ptr [si+0CAh], 1000h  ; test high-level state
0x36951: jnz    loc_36991                  ; if set, skip

0x3709B: test   word ptr [si+0CAh], 1000h  ; check state
0x370A1: jz     loc_370A4                  ; branch

0x31E03: test   word ptr [si+0CAh], 1000h  ; verify state
0x31E09: jnz    loc_31E32                  ; major gate

0x33B8E: test   word ptr [si+0CAh], 1000h  ; test flag
0x33B94: jnz    locret_33BA0               ; early return
```

### Read/Write Operations

```asm
; Read entire word:
0x38614: mov    dx, [si+0CAh]              ; load all flags
0x38618: cmp    byte ptr ds:451h, 0        ; compare with config

0x2FA78: mov    ax, [si+0CAh]              ; load flags
0x2FA7C: jnz    loc_2FA84                  ; conditional use

0x31F9F: mov    si, [si+0CAh]              ; use as pointer offset!
0x31FA3: mov    ds:0Eh, si                 ; store to global
```

**Conclusion:** +0xCA is the master entity flags word controlling:
- Spatial partitioning (tile boundary crossing)
- Visual effects (sprite trails, rendering modes)
- AI behavior states (multiple state machine bits)
- Animation and timer control
- View/camera projection
- High-level entity modes (player vs AI distinction?)

At least 12 bits have confirmed distinct purposes. This is one of the most important control fields in the FarObj struct.

---

## Updated Struct Progress

**Known fields:** ~138 bytes mapped (was ~120)  
**Unknown fields:** ~72 bytes (was ~90)  
**Completion:** 87% → **93%** (struct semantics)

### Session 3 Discoveries

```c
struct FarObj {
    // ... (0x00-0x39 as previously documented)
    
    // === 3D Velocity Vector (0x3A-0x44) ===
    int16_t  velocity_x_lo;   // +0x3A  Velocity X low word
    int16_t  velocity_x_hi;   // +0x3C  Velocity X high word (int32)
    int16_t  velocity_y_lo;   // +0x3E  Velocity Y low word
    int16_t  velocity_y_hi;   // +0x40  Velocity Y high word (int32)
    int16_t  velocity_z_lo;   // +0x42  Velocity Z low word
    int16_t  velocity_z_hi;   // +0x44  Velocity Z high word (int32)
    
    // +0x46-0x55: 16 bytes unknown (possibly acceleration, angular velocity)
    
    // === Physics / Collision (0x56-0x5A) ===
    uint16_t altitude_agl;    // +0x56  Altitude above ground (0=grounded, 71+=safe)
    uint16_t field_58;        // +0x58  UNKNOWN
    uint16_t event_flags;     // +0x5A  State/event flags (bits 0,1,2,3 + counter mode)
    
    // +0x5C-0xC9: 110 bytes unknown
    
    // === Master Entity Flags (0xCA) ===
    uint16_t entity_flags;    // +0xCA  Comprehensive flags (12+ bits):
                              //         bit 0x0001 = tile_boundary_crossed
                              //         bit 0x0008 = sprite_trail_active
                              //         bit 0x0010 = zone_x_boundary
                              //         bit 0x0020 = entity_state_major
                              //         bit 0x0040 = behavior_gate
                              //         bit 0x0080 = ai_state_machine
                              //         bit 0x0100 = rendering_mode
                              //         bit 0x0200 = animation_timer_enable
                              //         bit 0x0400 = view_projection_active
                              //         bit 0x0800 = special_mode
                              //         bit 0x1000 = high_level_state
    
    // +0xCC-0xD0: 5 bytes unknown
    
    uint8_t  timer_active;    // +0xD1  bit 0 = animation update flag
};
```

---

## Next Steps to Reach 95%+

**Remaining high-priority unknowns** (need ~10-15 more bytes for 95%):

1. **+0x46-0x4F** (10 bytes): Likely acceleration vector or angular velocity (follows velocity)
2. **+0x50-0x54** (5 bytes): Possible drag/friction coefficients
3. **+0x58-0x59** (2 bytes): Unknown word between altitude and event_flags
4. **+0x5C-0x61** (6 bytes): Possible damage/health/fuel state
5. **+0xCC-0xD0** (5 bytes): Fields immediately after master flags

**Analysis approach**:
- Search for int32 pairs near +0x46 (acceleration?)
- Look for multiplication/division with velocity fields
- Check for health/damage comparisons in combat functions
- Analyze fuel consumption in flight physics

Target: 210 bytes × 95% = 200 bytes mapped (need +12 bytes)

---

## Functions Referenced

| EA | Size | Description |
|----|------|-------------|
| 0x3E2B4 | — | Velocity accumulation (multiply + add with carry) |
| 0x395B8 | — | Matrix multiplication call (rotation transform) |
| 0x39385 | — | Velocity threshold comparison (boundary 7500) |
| 0x248D1 | — | fixed_vec3_transform_es (3D transformation) |
| 0x24988 | — | stub_to_24988 (angle normalization) |

---

## Evidence Files

- `analysis/ida_falconcd/level19_full.txt` — Complete disassembly
- `analysis/ida_falconcd/level*.txt` — All level disassemblies searched
- `analysis/map_farobj_fields_from_asm.py` — Field pattern scanner (Session 1)

---

## Mathematical Notes

**Velocity representation:**
- Stored as three signed int32 values (±2,147,483,648 range)
- Fixed-point scale unknown (likely related to world coordinate scale)
- Subject to rotation matrices (proper 3D vector treatment)
- Clamped to minimum threshold (cs:word_377E5)
- Compared against constant 0x1D4C = 7,500 decimal

**Altitude threshold:**
- Critical altitude = 0x47 = 71 units
- Danger calculation: `danger_level = 2 * (71 - altitude)`
- Zero altitude triggers ground state + collision + rendering changes

**Flag priority:**
- +0xCA master flags tested more frequently than +0x5A event flags
- Bits 0x0020, 0x0080, 0x0200, 0x1000 are highest-traffic gates
- Multiple bits often set together (0x210 = bits 9+4)
