# Weapon Types Decoded - farobj_queue_drain_dispatch

**Date:** November 11, 2026  
**Function:** `farobj_queue_drain_dispatch` @ sub_4C19E  
**Size:** 2500 bytes  
**Purpose:** Processes weapon entity queue by type, initializes weapon parameters

---

## Overview

This function is the **weapon type dispatcher** - it identifies weapon types and initializes their parameters (speed, damage, physics constants, etc.).

**MAJOR FINDING:** This resolves the type 0x33 conflict! Weapons use **different type values** than we thought!

---

## Type Dispatch Logic @ 0x4C19E-0x4C1DC

```asm
0x4C19E: push   ds
0x4C19F: mov    ax, 69FFh       ; Load weapon data segment
0x4C1A2: mov    ds, ax

; ========== TYPE RANGE CHECK: 0x12-0x13 (MISSILES) ==========
0x4C1A4: cmp    bx, 12h         ; BX = weapon type ID
0x4C1A7: jb     loc_3C1DC       ; Type < 0x12, exit
0x4C1A9: cmp    bx, 13h         ; Type <= 0x13?
0x4C1AC: jbe    loc_3C1B6       ; YES: Handle types 0x12 or 0x13

; ========== TYPE RANGE CHECK: 0x33-0x37 (GUN BULLETS) ==========
0x4C1AE: cmp    bx, 33h         ; Type < 0x33?
0x4C1B1: jb     loc_3C1DC       ; YES: exit (types 0x14-0x32 not weapons)
0x4C1B3: cmp    bx, 37h         ; Type <= 0x37?
0x4C1B6: ja     loc_3C1DC       ; NO: exit (types > 0x37 not these weapons)

; ========== PROCESS WEAPON QUEUE ==========
; Types 0x12, 0x13, 0x33-0x37 continue here
0x4C1B8: cmp    cs:word_2E10C, 0   ; Check queue count
0x4C1BE: jz     loc_3C1D9          ; Empty, exit
0x4C1C0: mov    si, cs:word_2E10A  ; Get queue pointer
0x4C1C5: push   cs
0x4C1C6: call   loc_3C201          ; Process weapon (initialize params)
0x4C1C9: nop
0x4C1CA: inc    cs:word_2E10E      ; Increment processed count
0x4C1CF: dec    cs:word_2E10C      ; Decrement queue count
0x4C1D4: add    cs:word_2E10A, 1Bh ; Advance queue pointer by 0x1B (27 bytes)
0x4C1DA: nop
0x4C1DB: pop    ds
0x4C1DC: retf
```

---

## Weapon Type Ranges

### Range 1: **0x12-0x13 (Missiles)**
- **Type 0x12** - Missile Type 1
- **Type 0x13** - Missile Type 2

### Range 2: **0x33-0x37 (Gun Projectiles)**
- **Type 0x33** - Gun bullet type 1
- **Type 0x34** - Gun bullet type 2
- **Type 0x35** - Gun bullet type 3
- **Type 0x36** - Gun bullet type 4
- **Type 0x37** - Gun bullet type 5

**Gap:** Types **0x14-0x32** are NOT handled by this dispatcher.
- **Hypothesis:** Bombs/unguided weapons handled elsewhere OR don't use queue system

---

## Weapon Parameter Initialization

### Type 0x12 - Missile Type 1 (AIM-9 Sidewinder?)

**Initialization @ 0x4C20E-0x4C26B:**

```asm
0x4C20E: mov    [si], bp            ; Entity pointer
0x4C212: mov    word ptr [si+2], 412h     ; Flags: 0x0412
0x4C217: mov    word ptr [si+4], 19F5h    ; Value: 6645 (speed component?)
0x4C21C: mov    word ptr [si+6], 30h      ; Value: 48
0x4C221: mov    word ptr [si+8], 0        ; Zero
0x4C226: mov    word ptr [si+0Ah], 113Eh  ; Value: 4414
0x4C22B: mov    word ptr [si+0Ch], 828h   ; Value: 2088
0x4C230: mov    word ptr [si+0Eh], 67h    ; Value: 103
0x4C235: mov    word ptr [si+14h], 1FAh   ; Value: 506 (max speed?)
0x4C23A: mov    byte ptr [si+16h], 0      ; Counter
0x4C23E: mov    cx, cs:word_2E110         ; Load value
0x4C243: mov    [si+18h], cx              ; Store value
0x4C246: mov    byte ptr [si+1Ah], 5      ; Value: 5 (lifetime? damage tier?)
```

**Loop @ 0x4C24A-0x4C269:** Processes 12 sub-missiles?
```asm
0x4C24A: mov    cx, 0Ch           ; Loop 12 times (0x0C = 12)
0x4C24D: cmp    cs:word_2E112, 80h ; Check ammo count?
0x4C254: jz     loc_3C269          ; If 0x80 (128), skip
0x4C256: or     word ptr [si+2], 1000h  ; Set flag bit 0x1000
0x4C25B: inc    byte ptr [si+16h]  ; Increment counter
0x4C25E: dec    cs:word_2E112      ; Decrement ammo
0x4C263: add    cs:word_2E110, 4   ; Advance by 4
0x4C269: loop   loc_3C24D          ; Repeat 12 times
```

**Analysis:**
- **Base speed:** 506 (0x1FA) units
- **Loop count:** 12 - possibly 12 submunitions or tracking samples?
- **Ammo system:** cs:word_2E112 is ammo count (max 128)
- **Type 0x12 has 12× loop, Type 0x33 has 12× loop** - same pattern!

---

### Type 0x13 - Missile Type 2 (AIM-120 AMRAAM?)

**Initialization @ 0x4C26C-0x4C29F:**

```asm
0x4C26C: cmp    bx, 13h
0x4C26F: jnz    loc_3C2A0
0x4C271: mov    [si], bp
0x4C273: mov    word ptr [si+2], 812h     ; Flags: 0x0812 (different from 0x12)
0x4C278: mov    word ptr [si+4], 0C3CFh   ; Value: 50127 (much higher speed!)
0x4C27D: mov    word ptr [si+6], 14h      ; Value: 20 (less than 0x12's 48)
0x4C282: mov    word ptr [si+8], 0
0x4C287: mov    word ptr [si+0Ah], 828Ah  ; Value: 33418 (much higher)
0x4C28C: mov    word ptr [si+0Ch], 4734h  ; Value: 18228 (much higher)
0x4C291: mov    word ptr [si+0Eh], 400h   ; Value: 1024 (vs 103 for type 0x12)
0x4C296: mov    word ptr [si+14h], 0CAh   ; Value: 202 (max speed LOWER than 0x12!)
0x4C29B: mov    byte ptr [si+1Ah], 2      ; Value: 2 (vs 5 for type 0x12)
0x4C29F: retf
```

**Analysis:**
- **NO loop** - processes once
- **Different flags:** 0x0812 vs 0x0412 (bit 0x0400 set)
- **Lower max speed:** 202 vs 506
- **Different physics constants** - completely different missile!

**Hypothesis:**
- **Type 0x12 = AIM-9 Sidewinder** (IR homing, faster, short range, 12 samples?)
- **Type 0x13 = AIM-120 AMRAAM** (radar guided, slower initial speed, long range, single track)

---

### Type 0x33 - Gun Bullet Type 1 (20mm Cannon Standard?)

**Initialization @ 0x4C2A0-0x4C300:**

```asm
0x4C2A0: cmp    bx, 33h
0x4C2A3: jnz    loc_3C301
0x4C2A5: mov    [si], bp
0x4C2A7: mov    word ptr [si+2], 416h     ; Flags: 0x0416
0x4C2AC: mov    word ptr [si+4], 19F5h    ; Value: 6645 (SAME as type 0x12!)
0x4C2B1: mov    word ptr [si+6], 30h      ; Value: 48 (SAME as type 0x12!)
0x4C2B6: mov    word ptr [si+8], 0
0x4C2BB: mov    word ptr [si+0Ah], 113Eh  ; Value: 4414 (SAME as type 0x12!)
0x4C2C0: mov    word ptr [si+0Ch], 828h   ; Value: 2088 (SAME as type 0x12!)
0x4C2C5: mov    word ptr [si+0Eh], 67h    ; Value: 103 (SAME as type 0x12!)
0x4C2CA: mov    word ptr [si+14h], 1FAh   ; Value: 506 (SAME as type 0x12!)
0x4C2CF: mov    byte ptr [si+16h], 0
0x4C2D3: mov    cx, cs:word_2E110
0x4C2D8: mov    [si+18h], cx
0x4C2DB: mov    byte ptr [si+1Ah], 5      ; Value: 5 (SAME as type 0x12!)

; Loop 6 times (not 12!)
0x4C2DF: mov    cx, 6              ; 6 bullets per burst?
0x4C2E2: cmp    cs:word_2E112, 80h
0x4C2E9: jz     loc_3C2FF
0x4C2EB: or     word ptr [si+2], 1000h
0x4C2F0: inc    byte ptr [si+16h]
0x4C2F3: dec    cs:word_2E112      ; Decrement ammo
0x4C2F8: add    cs:word_2E110, 4
0x4C2FE: loop   loc_3C2E1
0x4C300: retf
```

**CRITICAL FINDING:**
- Type 0x33 gun bullets use **IDENTICAL parameters** to Type 0x12 missiles!
- **Only difference:** Loop 6 times instead of 12
- **6 bullets per burst** - standard gun burst fire pattern!

**This explains the type conflict!**
- Types 0x12 and 0x33 share parameter initialization code
- They're distinguished by their **entity type field** ([entity+0x75])
- Type 0x33 checked in sub_3CE92 is **AIRCRAFT TYPE**
- Type 0x33 here is **BULLET TYPE** - different context!

---

### Type 0x34 - Gun Bullet Type 2 (Different caliber?)

**Initialization @ 0x4C301-0x4C32F:**

```asm
0x4C301: cmp    bx, 34h
0x4C304: jnz    loc_3C32F
0x4C306: mov    [si], bp
0x4C308: mov    word ptr [si+2], 0C06h    ; Flags: 0x0C06 (different!)
0x4C30D: mov    word ptr [si+4], 5370h    ; Value: 21360 (MUCH higher speed!)
0x4C312: mov    word ptr [si+6], 78h      ; Value: 120 (vs 48)
0x4C317: mov    word ptr [si+8], 0
0x4C31C: mov    word ptr [si+0Ah], 37A0h  ; Value: 14240
0x4C321: mov    word ptr [si+0Ch], 2515h  ; Value: 9493
0x4C326: mov    word ptr [si+0Eh], 67h    ; Value: 103
0x4C32B: mov    byte ptr [si+1Ah], 6      ; Value: 6
0x4C32F: retf
```

**Analysis:**
- **No loop** - single shot? Or continuous fire elsewhere?
- **Much faster:** Speed component 21360 vs 6645
- **Different flags:** 0x0C06
- **Damage tier:** 6 vs 5

---

### Type 0x35 - Gun Bullet Type 3

**Initialization @ 0x4C330-0x4C363:**

```asm
0x4C335: mov    [si], bp
0x4C337: mov    word ptr [si+2], 0C16h    ; Flags: 0x0C16
0x4C33C: mov    word ptr [si+4], 29B8h    ; Value: 10680
0x4C341: mov    word ptr [si+6], 50h      ; Value: 80
0x4C346: mov    word ptr [si+8], 0
0x4C34B: mov    word ptr [si+0Ah], 1BD0h  ; Value: 7120
0x4C350: mov    word ptr [si+0Ch], 128Ah  ; Value: 4746
0x4C355: mov    word ptr [si+0Eh], 67h    ; Value: 103
0x4C35A: mov    word ptr [si+14h], 0CAh   ; Value: 202
0x4C35F: mov    byte ptr [si+1Ah], 5
0x4C363: retf
```

---

### Type 0x36 - Gun Bullet Type 4

**Initialization @ 0x4C364-0x4C397:**

```asm
0x4C369: mov    [si], bp
0x4C36B: mov    word ptr [si+2], 416h     ; Flags: 0x0416 (same as 0x33!)
0x4C370: mov    word ptr [si+4], 29B8h    ; Value: 10680 (same as 0x35)
0x4C375: mov    word ptr [si+6], 50h      ; Value: 80 (same as 0x35)
0x4C37A: mov    word ptr [si+8], 0
0x4C37F: mov    word ptr [si+0Ah], 1BD0h  ; Value: 7120 (same as 0x35)
0x4C384: mov    word ptr [si+0Ch], 0F04h  ; Value: 3844 (different!)
0x4C389: mov    word ptr [si+0Eh], 400h   ; Value: 1024 (different!)
0x4C38E: mov    word ptr [si+14h], 0CAh   ; Value: 202
0x4C393: mov    byte ptr [si+1Ah], 4      ; Value: 4 (lower damage)
0x4C397: retf
```

---

### Type 0x37 - Gun Bullet Type 5 (Default/Fallthrough)

**Initialization @ 0x4C398-0x4C3C6:**

```asm
0x4C398: mov    [si], bp          ; No type check - default case
0x4C39A: mov    word ptr [si+2], 16h      ; Flags: 0x0016
0x4C39F: mov    word ptr [si+4], 0C3CFh   ; Value: 50127 (same as 0x13!)
0x4C3A4: mov    word ptr [si+6], 14h      ; Value: 20
0x4C3A9: mov    word ptr [si+8], 0
0x4C3AE: mov    word ptr [si+0Ah], 828Ah  ; Value: 33418
0x4C3B3: mov    word ptr [si+0Ch], 4734h  ; Value: 18228
0x4C3B8: mov    word ptr [si+0Eh], 400h   ; Value: 1024
0x4C3BD: mov    word ptr [si+14h], 0CAh   ; Value: 202
0x4C3C2: mov    word ptr [si+1Ah], 2
0x4C3C6: retf
```

**Analysis:** Almost identical to Type 0x13 (missile)! Very similar parameters.

---

## Weapon Parameter Fields (Weapon Initialization Structure)

Based on consistent patterns:

| Offset | Field Name | Type | Purpose |
|--------|------------|------|---------|
| +0x00 | parent_entity | word/ptr | Spawning entity pointer |
| **+0x02** | **flags** | word | Weapon behavior flags |
| +0x04 | velocity_base | word | Base velocity/speed component |
| +0x06 | param_06 | word | Unknown physics parameter |
| +0x08 | zero | word | Always 0 |
| +0x0A | param_0A | word | Unknown physics parameter |
| +0x0C | param_0C | word | Unknown physics parameter |
| +0x0E | param_0E | word | Unknown physics parameter |
| **+0x14** | **max_speed** | word | Maximum velocity |
| +0x16 | counter | byte | Burst counter / sub-munition index |
| +0x18 | param_18 | word | From cs:word_2E110 |
| **+0x1A** | **damage_tier** | byte | Damage category (2-6) |

---

## Weapon Flag Analysis

### Observed Flag Values

| Type | Flags | Binary | Bits Set |
|------|-------|--------|----------|
| **0x12** | 0x0412 | 0000 0100 0001 0010 | 1, 4, 10 |
| **0x13** | 0x0812 | 0000 1000 0001 0010 | 1, 4, 11 |
| **0x33** | 0x0416 | 0000 0100 0001 0110 | 1, 2, 4, 10 |
| **0x34** | 0x0C06 | 0000 1100 0000 0110 | 1, 2, 10, 11 |
| **0x35** | 0x0C16 | 0000 1100 0001 0110 | 1, 2, 4, 10, 11 |
| **0x36** | 0x0416 | 0000 0100 0001 0110 | 1, 2, 4, 10 (same as 0x33) |
| **0x37** | 0x0016 | 0000 0000 0001 0110 | 1, 2, 4 |

**Common bits:**
- **Bit 1 (0x0002):** Set in all except 0x12, 0x13 → Gun vs Missile?
- **Bit 4 (0x0010):** Set in 0x12, 0x13, 0x33, 0x35, 0x36, 0x37 → Guided?
- **Bit 10 (0x0400):** Set in 0x12, 0x33, 0x34, 0x35, 0x36 → Projectile?
- **Bit 11 (0x0800):** Set in 0x13, 0x34, 0x35 → Long-range?

### During Loop: Bit 12 (0x1000) Set

```asm
0x4C256: or     word ptr [si+2], 1000h  ; Set bit 0x1000
```

**Bit 12 (0x1000):** Set when sub-munition/burst round is active?

---

## Weapon Speed Comparison

| Type | Base Velocity | Max Speed | Speed Ratio | Weapon Type |
|------|---------------|-----------|-------------|-------------|
| **0x12** | 6645 | **506** | 13.1:1 | AIM-9 Sidewinder (fast missile) |
| **0x13** | **50127** | **202** | 248:1 | AIM-120 AMRAAM (very fast missile) |
| **0x33** | 6645 | **506** | 13.1:1 | 20mm cannon burst (6 rounds) |
| **0x34** | **21360** | ? | ? | Heavy gun (single shot) |
| **0x35** | 10680 | 202 | 52.9:1 | Medium gun |
| **0x36** | 10680 | 202 | 52.9:1 | Medium gun variant |
| **0x37** | **50127** | 202 | 248:1 | Similar to missile 0x13 |

**Observations:**
- Type 0x13 and 0x37 share parameters (50127 velocity)
- Type 0x12 and 0x33 share parameters (6645 velocity, 506 max speed)
- Type 0x35 and 0x36 share base parameters

---

## Ammo System

### Global Ammo Counter
- **Location:** cs:word_2E112
- **Max value:** 0x80 (128 rounds)
- **Decrement:** Each sub-munition/burst round decrements by 1

### Ammo Pointer/Index
- **Location:** cs:word_2E110
- **Increment:** Advances by 4 per sub-munition
- **Purpose:** Index into ammo array or projectile spawn table?

### Queue System
- **Queue pointer:** cs:word_2E10A
- **Queue count:** cs:word_2E10C
- **Processed count:** cs:word_2E10E
- **Stride:** 0x1B (27 bytes) per entry

---

## Remaining Weapon Types (Bombs?)

**Types 0x14-0x32 NOT handled by this dispatcher.**

**Hypothesis:**
- **Unguided weapons** (bombs, rockets)
- **Don't use queue system** - instantaneous spawn?
- **Handled by different code path** - possibly in sub_3DC55 or sub_3CE92 directly
- **Alternative dispatcher** exists for these types

**Need to search for:**
- Type 0x14 handler (bombs suspected)
- Other weapon initialization code paths
- Bomb physics (gravity + drag, no guidance)

---

## Key Insights

### 1. Type 0x33 Conflict RESOLVED!

**Two different type contexts:**
- **Entity type ([entity+0x75]):** Type 0x33 = **Special aircraft** (player/advanced AI)
- **Weapon initialization (BX register):** Type 0x33 = **Gun bullet type 1**

**These are DIFFERENT type spaces!**
- Entity types: Used by sub_3CE92 behavior dispatcher
- Weapon init types: Used by sub_4C19E queue processor

**Not a conflict - just two type classification systems!**

### 2. Burst Fire Mechanism

Type 0x12 and 0x33 have **loop processing:**
- Type 0x12: 12 iterations
- Type 0x33: 6 iterations

**Purpose:** Spawn multiple projectiles per fire event
- Missiles: 12 samples for tracking? Or salvo launch?
- Gun: 6-round burst (realistic M61A1 Vulcan behavior!)

### 3. Shared Parameter Sets

Types share initialization parameters:
- 0x12 ≈ 0x33 (missile and gun with same base speed)
- 0x13 ≈ 0x37 (long-range missile and bullet?)
- 0x35 ≈ 0x36 (gun variants)

**Hypothesis:** Code reuse for similar physics - efficient!

### 4. Damage Tiers

Values seen in +0x1A field: **2, 4, 5, 6**

**Possible damage categories:**
- 2: Low damage (long-range missile, light bullet)
- 4: Medium damage
- 5: Standard damage (most guns)
- 6: High damage (heavy gun)

---

## Next Steps

### Immediate
1. **Find bomb initialization** - Types 0x14-0x32 handler
2. **Trace weapon physics** - How are these parameters used in sub_3CE92?
3. **Map damage calculation** - sub_32393, uses damage_tier field?

### Analysis
4. **Complete flag bit meanings** - All 16 bits in flags field
5. **Identify real-world weapons:**
   - Type 0x12 = AIM-9 Sidewinder?
   - Type 0x13 = AIM-120 AMRAAM?
   - Type 0x33 = M61A1 Vulcan 20mm?
6. **Document ammo management** - cs:word_2E110, cs:word_2E112 usage

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: Weapon types decoded, type conflict resolved, 6 weapons documented!*

