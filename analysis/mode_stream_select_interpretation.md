# mode_stream_select_step Function Analysis (0x39E62 / 0x39E13)

**Function:** F6 key handler - likely ACM (Air Combat Maneuvering) mode step/cycle
**Size:** 266 bytes (0x39E13 - 0x39F1D)

## High-Level Logic Flow

This function appears to handle target selection cycling for radar modes, particularly when switching or stepping through targets in ACM or similar modes.

## Mode State Machine

### byte_595B2 - Primary Mode/State Variable

The function starts by checking `byte_595B2` against several values:

```asm
0x39E13: mov     al, byte_595B2
0x39E16: cmp     al, 4          ; If mode == 4, return (exit early)
0x39E18: jnz     short loc_39E1B
0x39E1A: retn

0x39E1B: cmp     al, 5          ; If mode == 5, call sub_2C12B and return
0x39E1D: jnz     short loc_39E25
0x39E1F: call    sub_2C12B
0x39E24: retn
```

**Mode Values:**
- **Mode 4:** Inactive/disabled - immediate return
- **Mode 5:** Special handler - calls `sub_2C12B` (needs investigation)
- **Mode 0 or 1:** Target scanning mode (continues to main logic)
- **Other values:** Return (invalid/unsupported)

### byte_59573 - Secondary Mode Gate

```asm
0x39E25: cmp     byte_59573, 1
0x39E2A: jg      short loc_39E2F
0x39E2C: jmp     near ptr steerpoint_scan_update
```

If `byte_59573 <= 1`, jumps to `steerpoint_scan_update` - this suggests:
- `byte_59573` might be radar type selector (SAD/SAM/HFR?)
- Value > 1 might indicate HFR mode (where target selection is active)
- Value <= 1 might be SAM or SAD (where steerpoints are used instead of target tracking)

### Mode 0 or 1 Check

```asm
0x39E2F: cmp     al, 1          ; Check if mode == 1
0x39E31: jz      short loc_39E3E
0x39E33: cmp     al, 0          ; Check if mode == 0
0x39E35: jz      short loc_39E3E
0x39E37: retn
```

Only modes 0 or 1 proceed to target scanning logic.

## Target Scanning Logic

### Setup

```asm
0x39E3E: push    es
0x39E3F: mov     ax, word_593A8        ; Load some base value
0x39E42: mov     byte_595B9, 0         ; Clear flag
0x39E47: shl     ax, 1                 ; Multiply by 4 (ax <<= 2)
0x39E49: shl     ax, 1
0x39E4B: mov     word ptr cs:loc_39E69+2, ax  ; Self-modifying code!
0x39E4F: mov     word ptr cs:loc_39E9C+2, ax  ; Patch comparison values
0x39E53: mov     cx, 10h               ; Loop counter = 16 entities
```

**Self-Modifying Code:**
The function patches the immediate values at 0x39E69 and 0x39E9C (both `cmp bx, 4444h` instructions). This dynamically sets the entity array boundary based on `word_593A8`.

### Two Scanning Modes

The function has two entity scanning loops:

#### Mode A: Continue from Last Target (word_5959B != 0xFFFF)

```asm
0x39E56: mov     bx, word_5959B        ; Load last target index
0x39E5A: cmp     bx, 0FFFFh            ; Check if invalid (-1)
0x39E5D: jz      short loc_39E98       ; If no previous target, use Mode B
0x39E5F: add     bx, 4                 ; Next entity (stride = 4 bytes)
0x39E62: cmp     bx, 40h               ; Check if beyond 64 (16 entities)
0x39E65: jl      short loc_39E69
0x39E67: sub     bx, bx                ; Wrap to 0
```

Cycles through entities starting from the last selected target + 1, wrapping around.

#### Mode B: Scan from Start (word_5959B == 0xFFFF)

```asm
0x39E98: sub     bx, bx                ; Start at index 0
0x39E9A: xor     si, si
```

Scans from the first entity.

### Entity Filter Criteria

Both loops use identical filter logic:

```asm
0x39E6F: les     di, [bx+1734h]        ; Load entity pointer from array at 0x1734
0x39E73: mov     al, es:[di+74h]       ; Entity flags +0x74
0x39E77: test    al, 1                 ; Must have bit 0 set
0x39E79: jz      short loc_39E93       ; Skip if not set
0x39E7B: test    al, 40h               ; Must have bit 6 set (0x40)
0x39E7D: jz      short loc_39E93       ; Skip if not set
0x39E7F: test    byte ptr es:[di+79h], 1  ; Entity flags +0x79, bit 0
0x39E84: jz      short loc_39E93       ; Skip if not set
```

**Entity Field at +0x74:**
- Bit 0 (0x01): Entity active/alive?
- Bit 6 (0x40): Entity is aircraft/target type?

**Entity Field at +0x79:**
- Bit 0 (0x01): Unknown criteria (friendly/enemy? visible?)

### Target Position Extraction

When a valid target is found:

```asm
0x39E86: mov     ax, es:[di+96h]       ; X coordinate (word)
0x39E8B: dec     ax                    ; X - 1
0x39E8C: mov     dx, es:[di+98h]       ; Y coordinate (word)
0x39E91: jmp     short loc_39EE8       ; Process target
```

**Entity Fields:**
- **+0x96h:** X position (16-bit)
- **+0x98h:** Y position (16-bit)
- **+0x9Ah:** Z position / altitude (used later at 0x39EF1)

### Loop Control

```asm
0x39E93: loop    loc_39E5F             ; CX = 16, check next entity
0x39E95: pop     es
0x39E96: jmp     short loc_39ECC       ; No valid target found
```

Checks up to 16 entities.

## No Target Found Handler

```asm
0x39ECC: mov     ax, 9Fh               ; Default X = 159
0x39ECF: mov     dx, 96h               ; Default Y = 150
0x39ED2: mov     bx, 0FFFFh            ; Mark no target selected
0x39ED5: mov     word_5959B, bx        ; Store -1 in target index
0x39ED9: mov     word_59597, ax        ; Store default position
0x39EDC: mov     word_59595, ax
0x39EDF: mov     word_59599, dx
0x39EE3: push    cs
0x39EE4: call    near ptr undoc_39D02  ; Update display?
0x39EE7: retn
```

Sets display to center screen position (159, 150) when no target is available.

## Target Found Handler

```asm
0x39EE8: mov     word_59595, ax        ; Store target X
0x39EEB: mov     bp, ax
0x39EED: mov     word_59599, dx        ; Store target Y
0x39EF1: mov     ax, es:[di+9Ah]       ; Get target altitude
0x39EF6: pop     es
0x39EF7: mov     si, word_593AA        ; Load reference pointer
0x39EFB: sub     ax, [si+0Ch]          ; Altitude difference
0x39EFE: mov     dx, 630h              ; Scale factor = 1584
0x39F01: imul    dx                    ; (target_alt - ref_alt) * 1584
0x39F03: add     dx, bp                ; Add X position to result
0x39F05: mov     ax, dx
0x39F07: cmp     ax, 60h               ; Check if < 96
0x39F0A: jl      short loc_39ECC       ; Out of bounds (too far left/below)
0x39F0C: cmp     ax, 0E2h              ; Check if > 226
0x39F0F: jg      short loc_39ECC       ; Out of bounds (too far right/above)
0x39F11: mov     word_59597, ax        ; Store computed display X
0x39F14: mov     word_5959B, bx        ; Store target index
0x39F18: push    cs
0x39F19: call    near ptr undoc_39D02  ; Update display
0x39F1C: retn
```

### Altitude Perspective Calculation

The function computes a display X coordinate based on altitude difference:

```
display_x = ((target_alt - reference_alt) * 1584) + target_x
```

**Bounds Check:** Display X must be in range [96, 226] (130 pixel width)

This suggests a 3D perspective projection for the radar display, where altitude affects horizontal position (pseudo-3D or vertical separation indicator).

## Key Variables Summary

| Address | Name | Purpose |
|---------|------|---------|
| 0x595B2 | byte_595B2 | Primary mode state (0/1=scan, 4=off, 5=special) |
| 0x59573 | byte_59573 | Radar type? (>1 for target tracking modes) |
| 0x595B4 | byte_595B4 | Mode flag (cleared at 0x39E38) |
| 0x595B9 | byte_595B9 | Temporary flag |
| 0x593A8 | word_593A8 | Entity array scaling factor |
| 0x5959B | word_5959B | Selected target index (-1 if none) |
| 0x59595 | word_59595 | Target/display X coordinate |
| 0x59597 | word_59597 | Computed display X (with altitude offset) |
| 0x59599 | word_59599 | Target/display Y coordinate |
| 0x593AA | word_593AA | Reference altitude pointer |

## Entity Structure Offsets (Partial)

| Offset | Size | Purpose |
|--------|------|---------|
| +0x74 | byte | Status flags (bit 0: active, bit 6: aircraft type?) |
| +0x79 | byte | Visibility/tracking flags (bit 0: trackable?) |
| +0x96 | word | X position |
| +0x98 | word | Y position |
| +0x9A | word | Z position / altitude |

## Function Called

- **sub_2C12B (0x2C12B):** Called when mode == 5, needs analysis
- **undoc_39D02 (0x39D02):** Called at end to update display, likely refreshes radar scope

## Hypothesis

This function implements the **F6 ACM mode step function**, which cycles through eligible air targets on the radar display. When F6 is pressed:

1. Checks if radar is in an appropriate mode (byte_595B2 == 0 or 1)
2. Verifies radar type supports target tracking (byte_59573 > 1, likely HFR mode)
3. Scans through entity list for valid air targets (active, aircraft type, trackable)
4. Computes 3D perspective display position based on target coordinates and altitude
5. Updates display to highlight the next target

Mode 4 likely means "ACM not available" (e.g., ground mapping mode active).
Mode 5 might be "target locked" (STT - Single Target Track), where sub_2C12B handles the locked target behavior.

## Next Steps

1. Analyze `sub_2C12B` (mode 5 handler) - likely the STT locked target handler
2. Analyze `undoc_39D02` (display update) - renders the target reticle/marker
3. Find where `byte_595B2` is set - trace mode transitions
4. Find where `byte_59573` is set - confirm it's the radar type (SAD/SAM/HFR)
5. Look for F5 (NAM mode) and F7 (GM mode) handlers with similar structure
6. Find the Z key handler that locks targets (sets mode to 5?)
