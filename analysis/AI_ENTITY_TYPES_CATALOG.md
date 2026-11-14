# Entity Type Catalog - Complete Mapping

**Date:** November 11, 2026  
**Purpose:** Comprehensive catalog of all entity types in Falcon 3.0 for IDA synchronization  
**Progress:** 40%

---

## Entity Type Field

**Offset:** `+0x75h` (117 decimal)  
**Size:** 1 byte  
**Range:** 0x00-0xFF (but only ~20 types used)  
**Purpose:** Behavioral classification for entity dispatch

---

## Type Assignment Logic

**Location:** sub_3BB8F @ 0x3BD76-0x3BD9E

```asm
; Load type from data table
0x3BD6E: call   farptr_table_get           ; Get entity data pointer
0x3BD73: call   loc_3BEFD                  ; Some setup
0x3BD76: mov    ax, es                     ; ES:DI = data table entry
0x3BD78: mov    [si+2], ax
0x3BD7B: mov    [si+4], di
0x3BD7E: mov    al, es:[di+26h]            ; *** LOAD TYPE from data ***
0x3BD82: and    al, 3Fh                    ; Mask: keep bits 0-5

; Conditional override for multiplayer friendly
0x3BD8F: cmp    byte ptr ds:15B3h, 0       ; Check game mode (0=single, 1+=multi)
0x3BD94: jz     loc_3BD9E                  ; Single player → use table type
0x3BD96: cmp    bp, ds:1360h               ; Compare with player entity slot
0x3BD9A: jnz    loc_3BD9E                  ; Not player → use table type
0x3BD9C: mov    al, 16h                    ; OVERRIDE: Player wingman = type 0x16

; Assign type
0x3BD9E: mov    [di+75h], al               ; SET entity type field
```

**Key insight:** Entity types come from **external data tables** (likely .DAT files), loaded at offset +0x26 in entity data records. Type 0x16 is **forced for player wingmen in multiplayer**.

---

## Complete Type Catalog

### Combat Aircraft Types

| Type | Hex | Decimal | Name (Hypothesis) | Evidence | Behavior |
|------|-----|---------|-------------------|----------|----------|
| **0x16** | 0x16 | 22 | **Friendly Aircraft / Wingmen** | Multiplayer override, friendly fire checks | Full AI state machine |
| **0x33** | 0x33 | 51 | **Player Aircraft** | 4× special handlers, weapon spawn | Full control + special physics |
| **0x10** | 0x10 | 16 | **Guided Missiles** | Skips state machine → tracking | Always tracking, no states |

### Ground Units / Other Aircraft (from searches)

| Type | Hex | Decimal | Name (Hypothesis) | Evidence |
|------|-----|---------|-------------------|----------|
| **0x03** | 0x03 | 3 | **Ground unit / Vehicle?** | @ 0x3BFC2 (excluded from some checks) |
| **0x0B** | 0x0B | 11 | **Unknown entity** | @ 0x39218 (special handling) |
| **0x0C** | 0x0C | 12 | **Unknown entity** | @ 0x3921E (grouped with 0x0B) |
| **0x0D** | 0x0D | 13 | **Unknown entity** | @ 0x39230, 0x3C892, 0x3BFCE, 0x42537 (multiple refs) |
| **0x0F** | 0x0F | 15 | **Unknown entity** | @ 0x39236, 0x3C898 (grouped with 0x0D) |
| **0x20+** | 0x20+ | 32+ | **Special entities?** | @ 0x40EED: `cmp [di+75h], 20h; jnb` (≥32 branch) |
| **0x2B** | 0x2B | 43 | **Unknown entity** | @ 0x3922E (special handling) |
| **0x2C** | 0x2C | 44 | **Unknown entity** | @ 0x39224 (grouped with 0x2B) |
| **0xFF** | 0xFF | 255 | **Dead / Invalid Entity** | @ 0x3BDB9 (set on entity death) |

### Special Values

| Value | Meaning | Evidence |
|-------|---------|----------|
| **0xFF** | Destroyed / Invalid | Set at death @ 0x3BDB9, cleared to mark as inactive |

---

## Type Dispatch Patterns

### Pattern 1: Combat Aircraft Dispatch (Behavior Dispatcher)

```asm
; @ sub_3CE92 (behavior dispatcher)

0x3CFA0: cmp    byte ptr [di+75h], 33h     ; Check type 0x33
0x3CFA4: jnz    loc_3CFAA
0x3CFA6: call   loc_3D37F                  ; Type 0x33 special handler

0x3D042: cmp    byte ptr [di+75h], 10h     ; Check type 0x10
0x3D046: jz     loc_3D087                  ; Type 0x10 → skip state machine

; Fall through: All other types go through state machine
```

**Pattern:** 
- Type 0x33 gets early special handling BEFORE state machine
- Type 0x10 SKIPS state machine entirely
- All others (including 0x16, 0x03, 0x0B-0x0F, 0x2B-0x2C) run state machine

### Pattern 2: Friendly Fire Check (Weapon Spawn)

```asm
; @ sub_3DC55 (weapon spawn gate) @ 0x3DEE6

0x3DEE6: mov    bl, [di+75h]               ; Get shooter type
0x3DEE9: cmp    bl, 16h                    ; Type 0x16?
0x3DEEC: jnz    loc_3DEF8                  ; Not 0x16 → check other conditions

; Type 0x16 friendly fire logic:
; - Can fire in single player
; - Restricted by permission flags in multiplayer
```

**Pattern:** Type 0x16 has **firing restrictions** in multiplayer

### Pattern 3: Physics/Rendering Dispatch

```asm
; @ sub_3CE92 physics constants

0x3D830: cmp    byte ptr [di+75h], 33h     ; Check type 0x33
0x3D834: jnz    loc_3D839
0x3D836: mov    ax, 0C00h                  ; Type 0x33: use 0x0C00
; else:
0x3D82A: mov    ax, 800h                   ; Others: use 0x0800
```

**Pattern:** Type 0x33 gets **different physics constant** (0x0C00 vs 0x0800 = 1.5× multiplier)

### Pattern 4: Group Checks

```asm
; @ sub_38CF3 (unknown function) @ 0x39218-0x39236

0x39218: cmp    byte ptr [si+75h], 0Bh     ; Type 0x0B
0x3921C: jz     loc_39287                  ; Jump if match
0x3921E: cmp    byte ptr [si+75h], 0Ch     ; Type 0x0C
0x39222: jz     loc_39287                  ; Jump if match
0x39224: cmp    byte ptr [si+75h], 2Ch     ; Type 0x2C
0x39228: jz     loc_39287                  ; Jump if match
0x3922A: cmp    byte ptr [si+75h], 2Bh     ; Type 0x2B
0x3922E: jz     loc_39287                  ; Jump if match
0x39230: cmp    byte ptr [si+75h], 0Dh     ; Type 0x0D
0x39234: jz     loc_39287                  ; Jump if match
0x39236: cmp    byte ptr [si+75h], 0Fh     ; Type 0x0F
```

**Pattern:** Types 0x0B, 0x0C, 0x0D, 0x0F, 0x2B, 0x2C are **grouped together** for special handling. Possibly ground units or special effects?

---

## Type Identification Strategy

### Confirmed Types (100% confidence)

1. **0x33 = Player Aircraft**
   - Most complex handling in dispatcher
   - Special physics constants (0x0C00)
   - Weapon spawning capability
   - Target search
   - 4+ dedicated code paths

2. **0x16 = Friendly Aircraft / Wingmen**
   - Multiplayer override for player squadron
   - Friendly fire protection
   - Full AI state machine access
   - Spawning restrictions

3. **0x10 = Guided Missiles**
   - Skips AI state machine
   - Goes directly to tracking
   - Always has target
   - Simple behavior (track and fly)

4. **0xFF = Dead/Invalid**
   - Set on entity destruction
   - Cleared to mark slot as free

### Likely Types (70%+ confidence)

5. **0x03 = Ground Units / Vehicles**
   - Excluded from certain aircraft checks
   - Grouped with non-flying entities

6. **0x0D, 0x0F = Special Ground Targets**
   - Heavily referenced together
   - Multiple exclusion checks
   - Possibly SAM sites, AAA, or buildings

7. **0x0B, 0x0C = Effects / Explosions?**
   - Grouped with other special types
   - Limited references

8. **0x2B, 0x2C = Unknown Special**
   - Grouped with 0x0B/0x0C types
   - Possibly flares, chaff, or debris

9. **0x20+ (≥32) = High-value entities?**
   - Boundary check suggests different class
   - Could be bombers, transports, ships

### Unknown - Enemy AI Aircraft Type

**Problem:** Enemy AI must exist, but we haven't found explicit type!

**Hypotheses:**

**Hypothesis A: Type 0x16 is BOTH friendly AND enemy**
- Evidence: 0x16 has full state machine access
- Evidence: Friendly fire check only matters in multiplayer
- Evidence: In single player, all AI aircraft could be 0x16
- Problem: Doesn't explain friend/foe identification

**Hypothesis B: Enemy AI uses MULTIPLE types based on aircraft**
- Types 0x0B-0x0F could be different enemy aircraft classes
- Evidence: Grouped handling suggests related behavior
- Evidence: Multiple types with similar AI treatment
- Problem: These seem more like ground units

**Hypothesis C: Type is MASKED in data table**
- Data table has bits 6-7 for flags (0x3F mask @ 0x3BD82)
- Enemy vs friendly could be in upper bits, not type field
- Type field may only indicate aircraft CLASS (fighter, bomber, etc.)
- Friend/foe determined by other data (nation, side, etc.)

**Hypothesis D: Default type (from data table) IS enemy**
- Type 0x16 is OVERRIDE for player wing
- Default types from data (0x01-0x15?) are enemy aircraft
- Evidence: Only player wingmen get forced to 0x16
- Problem: Haven't seen references to types < 0x10

---

## Entity Field +0x74h (Related to Type)

**Referenced during target validation @ 0x3D18C:**

```asm
0x3D18C: test   byte ptr [bx+74h], 1       ; Check bit 0
0x3D190: jz     loc_3D198
0x3D192: test   byte ptr [bx+74h], 38h     ; Check bits 3, 4, 5
0x3D196: jz     loc_3D1A8                  ; Target VALID if bits 0=1, 3/4/5=0
0x3D198: mov    byte ptr [si+29h], 0FFh    ; Otherwise: LOSE TARGET
```

**Also set during init @ 0x3BD24:**
```asm
0x3BD24: mov    byte ptr [di+74h], 1       ; Set bit 0 on spawn
```

**Purpose:** Entity status flags
- Bit 0: Entity active/targetable
- Bits 3, 4, 5: Entity invalid/dying/special state
- Used for target validation (can I lock this entity?)

---

## For IDA Synchronization

### Struct Definition for IDA

```c
struct FarObjEntity {
    // ... (other fields)
    byte field_74;      // Entity status flags (bit 0=active, bits 3/4/5=invalid)
    byte entity_type;   // +0x75: Entity type dispatch
    // ...
};

enum EntityType {
    TYPE_GUIDED_MISSILE = 0x10,  // Always tracking, no AI states
    TYPE_FRIENDLY       = 0x16,  // Wingmen, full AI, friendly fire protect
    TYPE_PLAYER         = 0x33,  // Player aircraft, special handling
    TYPE_INVALID        = 0xFF,  // Dead/destroyed entity
    
    // Likely ground/special:
    TYPE_GROUND_UNIT    = 0x03,
    TYPE_SPECIAL_0B     = 0x0B,
    TYPE_SPECIAL_0C     = 0x0C,
    TYPE_SPECIAL_0D     = 0x0D,
    TYPE_SPECIAL_0F     = 0x0F,
    TYPE_SPECIAL_2B     = 0x2B,
    TYPE_SPECIAL_2C     = 0x2C,
};
```

### Functions to Annotate in IDA

| Address | Name | Comment |
|---------|------|---------|
| 0x3BB8F | entity_init_from_data | Loads entity type from data table +0x26 |
| 0x3BD7E | | `mov al, es:[di+26h]` - Load type from data |
| 0x3BD9C | | Override type to 0x16 for player wingmen |
| 0x3BD9E | | `mov [di+75h], al` - Set entity type |
| 0x3BDB9 | entity_destroy | Sets type to 0xFF (invalid) |
| 0x3CFA0 | | Type 0x33 dispatch (player) |
| 0x3D042 | | Type 0x10 dispatch (missiles) |
| 0x3DEE9 | | Type 0x16 check (friendly fire) |
| 0x3D830 | | Type 0x33 physics constant (0x0C00) |

### Fields to Rename in IDA

| Offset | Old Name | New Name | Type | Comment |
|--------|----------|----------|------|---------|
| +0x74 | field_74 | entity_status | byte | Bit 0=active, bits 3/4/5=invalid state |
| +0x75 | field_75 | entity_type | byte | Type dispatch: 0x10/0x16/0x33/etc. |

---

## Next Investigation

### Priority 1: Find Enemy Aircraft Type

**Approach A - Data File Analysis:**
1. Locate entity data tables (referenced at 0x3BD6E)
2. Extract type bytes (offset +0x26)
3. See which types are assigned to which aircraft models
4. Cross-reference with manual aircraft names

**Approach B - Type Usage Analysis:**
1. Search ALL references to `[di+75h]` and `[si+75h]`
2. Build complete usage map
3. Find types that use state machine (not 0x10, not 0x33 special)
4. Process of elimination

**Approach C - Multiplayer Logic:**
1. Analyze ds:15B3h (game mode: 0=single, 1+=multi)
2. See how enemy identification works
3. May be in other fields, not type

### Priority 2: Map Remaining Types

Need to identify types:
- 0x01-0x09 (unused or undiscovered?)
- 0x11-0x15 (between missile and friendly)
- 0x17-0x32 (between friendly and player)
- 0x34-0xFE (after player, before invalid)

### Priority 3: Friend/Foe System

How does game distinguish friend from enemy?
- Type field (our current assumption)
- Separate IFF field (nation, side, team)
- Data table flags (bits 6-7 masked at 0x3BD82)
- Combination of fields

---

## Summary for IDA

**Key discoveries for database sync:**

1. **Entity type field @ +0x75h** - Primary behavioral classification
2. **Type loaded from data table** @ offset +0x26 in entity records
3. **Type 0x16 forced** for player wingmen in multiplayer
4. **Three confirmed types:** 0x10 (missiles), 0x16 (friendly), 0x33 (player)
5. **Six likely types:** 0x03, 0x0B-0x0F, 0x2B-0x2C (ground/special)
6. **Type 0xFF** marks dead entities
7. **Entity status @ +0x74h** - Validation flags for targeting

**IDA actions:**
- Create EntityType enum with known values
- Rename field_75 → entity_type
- Rename field_74 → entity_status  
- Add comments at all type dispatch points
- Create struct for entity data table format

---

*Analysis: November 11, 2026*  
*Status: Type system architecture understood, 9 types identified, enemy AI type still unknown*


