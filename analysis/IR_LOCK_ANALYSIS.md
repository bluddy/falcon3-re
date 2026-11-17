# IR Lock System Analysis

**Date:** 2026-11-17  
**Function:** `weapon_aim9_seeker_lock_check` (entity_slot_cycle_select) @ 0x32B7F  
**Size:** ~200 bytes  
**Purpose:** Manages IR missile seeker lock state and audio tone

---

## Key Globals Identified

### Lock State Variables

**`ds:0x44AA` (word) - IR Lock State/Index**
- Read and written multiple times throughout function
- Stores current lock target index or lock state value
- Values: 0-3 in one mode, 4-16 in another mode
- **Name:** `ir_lock_target_index`

**`ds:0x44DB` (byte) - IR Lock Cycle Counter (Mode 0)**
- Used when `cs:loc_35929` == 0
- Values 0-3, cycles through potential targets
- Incremented with `(ax+1) & 3` pattern
- **Name:** `ir_lock_cycle_index_mode0`

**`ds:0x44DC` (byte) - IR Lock Cycle Counter (Mode 1)**
- Used when `cs:loc_35929` == 1
- Values 4-16 (0x4-0x10), wider search range
- Wraps around: if > 16, reset to 4
- **Name:** `ir_lock_cycle_index_mode1`

### Status/Control Variables

**`ds:0x4AC2` (byte) - Detection Mode State**
- **Already in registry as `detection_mode_state`**
- Compared to 5 at 0x32BCC and 0x32C23
- When == 5, triggers audio tone (call `mode_audio_state_step` with al=3)
- Links IR lock system to radar detection state

**`ds:0x4890` (byte) - Unknown Status**
- Compared to AH (high byte of lock index)
- Used as gate condition before checking entity field
- **Name:** `ir_lock_status_byte`

**`ds:0x48BA` (word) - Entity Base Pointer**
- Loaded into SI, used as base for entity field access
- Entity checked: `[bx+si+0xAE]` (heat signature field?)
- **Name:** `ir_lock_entity_base`

**`ds:0x487E` (array) - Entity Slot Index Mapping**
- Indexed by lock cycle value to get entity slot
- Used as: `mov bl, [bx+487Eh]`
- Translates lock index → actual entity slot ID
- **Name:** `ir_lock_slot_mapping`

### Cleared at Entry (Temporary State)

**`ds:0x1075` (byte)**
- Cleared to 0 at function entry (0x32B81)
- Not used elsewhere in visible code
- Likely temporary/working variable

**`ds:0x44D4` (byte)**
- Cleared to 0 at function entry (0x32B84)
- Not used elsewhere in visible code

**`ds:0x499E` (byte)**
- Cleared to 0 at function entry (0x32B87)
- Not used elsewhere in visible code

---

## Lock Algorithm

### Mode 0 (Simple Cycle, cs:loc_35929 == 0)

**Targets:** 4 potential targets (indices 0-3)

```asm
; Load and advance cycle counter
mov  al, ds:44DBh           ; Get cycle counter (0-3)
cbw
cmp  ax, ds:44AAh           ; Compare to current lock
mov  ds:44AAh, ax           ; Store as lock state
mov  ds:44DBh, al           ; Store back to counter
jnz  skip_increment         ; If changed, don't increment

; Increment if no change
inc  ax
and  ax, 3                  ; Wrap 0-3

; Check if target slot is valid (has heat signature?)
cmp  ds:4890h, ah           ; Status check
jz   accept_target
mov  cx, 4                  ; Try 4 times
mov  bx, ax
mov  bl, [bx+487Eh]         ; Get entity slot from mapping
cmp  byte ptr [bx+si+0AEh], 0  ; Check entity+0xAE (heat signature?)
jnz  accept_target
inc  ax
and  ax, 3
loop check_loop
retn                        ; No valid target found

accept_target:
mov  ds:44AAh, ax           ; Store locked target
mov  ds:44DBh, al           ; Store cycle counter
cmp  byte ptr ds:4AC2h, 5   ; Check detection_mode_state == 5
jnz  done
mov  al, 3                  ; Audio tone code
jmp  mode_audio_state_step  ; Trigger lock tone

done:
retn
```

### Mode 1 (Extended Cycle, cs:loc_35929 == 1)

**Targets:** 13 potential targets (indices 4-16, 0x4-0x10)

Similar algorithm but:
- Cycle range 4-16 instead of 0-3
- Loop count 13 (0x0D) instead of 4
- Wraps at 16: `if (ax > 0x10) ax = 4`
- Additional check: `if (al >= 6 && al <= 10)` triggers visual/audio updates

---

## Entity Field

**Offset 0xAE: Heat Signature (Hypothetical)**

```c
struct Entity {
    // ... offsets 0x00-0xAD ...
    uint8_t heat_signature;  // +0xAE: IR visibility (0=cold, non-zero=hot)
    // ...
};
```

Checked as: `cmp byte ptr [bx+si+0AEh], 0`
- If 0: Target is cold, no IR lock possible
- If non-zero: Target emits heat, can be locked

**Heat sources:**
- Jet engines (afterburner = high heat)
- Exhaust plume
- Hot airframe from friction
- May be angle-dependent (rear aspect = hotter)

---

## Audio Integration

**Lock Tone Trigger:**

When `detection_mode_state` (ds:4AC2h) == 5 AND lock acquired:
```asm
cmp  byte ptr ds:4AC2h, 5   ; Check detection mode
jnz  skip_tone
mov  al, 3                  ; Audio code 3 = IR lock tone
call mode_audio_state_step  ; Trigger tone
```

**Tone codes:**
- 3 = IR lock tone (constant/growling tone when locked)

**Sustained tone = locked, no tone = searching**

---

## Integration with Radar

**Detection Mode State (ds:4AC2h):**
- Shared with radar system
- Value 5 = active detection/lock mode
- Gates IR lock tone output
- Links IR missiles to radar detection state machine

**Hypothesis:** Both IR and radar missiles use same detection framework, just different sensors (heat vs radar returns).

---

## Code Segment Variable

**`cs:loc_35929` - IR Lock Mode Selector**
- 0 = Mode 0 (4 targets, simple cycle)
- 1 = Mode 1 (13 targets, extended cycle)
- Determines search pattern complexity
- **Name:** `ir_lock_search_mode`

---

## Next Steps

1. **Add 8 IR lock globals to registry:**
   - ir_lock_target_index (0x44AA)
   - ir_lock_cycle_index_mode0 (0x44DB)
   - ir_lock_cycle_index_mode1 (0x44DC)
   - ir_lock_status_byte (0x4890)
   - ir_lock_entity_base (0x48BA)
   - ir_lock_slot_mapping (0x487E)
   - ir_lock_search_mode (cs:loc_35929)

2. **Add entity field to EntitySlotRecord:**
   - heat_signature @ +0xAE (byte)

3. **Find radar lock equivalent:**
   - Search for radar_mode_state (0x595B2) == 5 (STT) integration
   - Find radar lock target index variable
   - Find AMRAAM (type 0x13) lock check function

4. **Find HARM lock code:**
   - Search for radar_emitter_active entity field
   - Find anti-radiation homing logic
   - Link to type 0x14-0x32 (A-G weapons)

---

## Summary

✅ **IR lock system decoded:**
- 2 search modes (4-target simple, 13-target extended)
- Entity heat signature field @ +0xAE
- Lock state stored in ds:0x44AA
- Audio tone triggered when detection_mode == 5
- Cycles through potential targets each frame

**Progress:** IR lock system ~85% understood, globals identified, ready for registry integration.
