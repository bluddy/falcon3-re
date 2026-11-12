# Entity System — Lifecycle & Architecture

*See also: `farobj.md` for FarObj struct, `flight_physics.md` for aircraft slots.*

---

## Four-Layer Entity Architecture

The entity system uses four distinct data structures, each serving a different purpose:

| Layer | Location | Size | Description | Update function |
|---|---|---|---|---|
| FarObj instances | `R05_400C:0x34` (N×4B ptrs) | ≥210B per obj | World state: position, orientation, type, LOD | `farptr_table_accum_fields`, `farptr_table_offset_apply` |
| Entity slot records | `0x54AF:0x386F` (16×92B) | 92B per slot | Per-frame update flags + processing state | `farobj_slot_update_driver` |
| Event/timer state | `0x7772:0x506+N` (1B per entity) | 1B per entity | Countdown timers (weapons, damage, etc.) | `entity_counters_update` |
| Spawn queue | `0x6B58:0x33` (10×6B) | 6B per entry | Pending entity creation | `farobj_slot_step_spawn` |

### Per-Frame Update Order (from `main_frame_update_loop`)

1. `farobj_slot_update_driver` — 3-pass update of 16 entity slot records
2. `farobj_move_accumulate_step` — apply EntityAccumEntry motion (up to 82 entities)
3. `aircraft_slot_cycle_step` — cycle 40 aircraft/AI slots
4. `farobj_slot_step_spawn` — process spawn queue (up to 10 pending spawns)
5. `farobj_sweep_all` — slot sweep + cmd sweep + entity accum sweep
6. Within `game_frame_pipeline_step`: `farobj_sort_and_step` → depth sort + per-entity step

---

## Entity Slot Records (0x54AF:0x386F, 16×92B)

16 active entity slot records at `DS:0x54AF:0x386F` with stride 92 (0x5C).

**Partial layout** (from `farobj_slot_update_driver` and `farobj_record_ops_exec`):

```c
struct EntitySlotRecord {        // stride 0x5C = 92 bytes
    // +0x00..+0x05  unknown
    uint16_t farobj_slot;        // +0x06  farobj main table slot index
                                 //         (accessed as [si+6] in farobj_record_ops_exec)
    // +0x08..+0x09  unknown
    uint8_t  flags;              // +0x0A  bit 0 = active (checked by farobj_slot_update_driver)
    // +0x0B..+0x5B  unknown
    // Note: farobj_record_ops_exec accesses DI+0xC0, DI+0xC1
    //       where DI = [si+6] → these are offsets into the entity STATE BUFFER
    //       pointed to by slot[6], NOT offsets in this struct!
};
```

`farobj_slot_update_driver` runs 3 passes over all 16 slots each frame:
- Pass 1: If active: `sub_40BC5+1`, `sub_3C62C`, `sub_4355B` (main update)
- Pass 2: If active: `sub_428A1` (secondary step)
- Pass 3: Different per-slot operations

---

## Entity Class Codes (FarObj.entity_class [+0x14])

Set by `farobj_entity_attr_setup` (0x44352) from type table B at DS:0x16F4 (R05_33AE).
Used by `farobj_type_gate_test` (0x4BF8B) for entity-type filtering.

| Code | Hypothesis | Callers that check it |
|---|---|---|
| 0x12 (18) | Player / allied aircraft | farobj_type_gate_test |
| 0x14 (20) | Enemy aircraft | farobj_type_gate_test |
| 0x33 (51) | Ground target / vehicle | farobj_type_gate_test |
| 0x38 (56) | Naval / other entity | farobj_type_gate_test |

The type table is indexed by a type_index (pre-shifted): `bx = type_index × 2; word = [bx+16F4h]`.
The low byte of this word becomes `entity_class`. Type table location: R05_33AE overlay at
DS:0x16F4 relative to the segment's paragraph base.

---

## Entity Step State Machine (farobj_record_lookup_step, 0x213E6)

Called per projected entity by `farobj_sort_and_step` and `view_projection`.
Looks up and executes the type-specific step record.

```
SI = FarObj.object_kind [+0x22]      ; LOD accumulator
AX = FarObj.state_flags [+0x24]

IF NOT (AX & 0x10):                  ; bit 4 = has type record
    scan for 0xFFFF at [SI+8-byte intervals]
    jump to loc_214B9 when found
    return
ELSE:
    ES = 0x7B0E
    SI = SI × 4 + 0x3052             ; index into type descriptor table
    LES SI, ES:[SI]                  ; load far ptr to type desc stream
    IF SI == 0xFFFF: return
    AL = ES:[SI]                     ; skip distance
    SI += AL                         ; skip to record
    LOOP: IF ES:[SI] == 0xFFFF: found (cs:byte_1F742 = 0, goto loc_214B9)
          ELSE: SI += 8              ; next 8-byte record
```

The type descriptor stream format (8-byte records):
```c
struct TypeStepRecord {
    uint16_t sentinel_or_type;   // +0x00  0xFFFF = end of stream; else = type code
    // +0x02..+0x07  record data
};
```

---

## Entity Creation: entity_slot_create (0x2EBCD, 463B)

**Entities are loaded from disk at creation time** (STRONG). Called by `entity_slot_pair_create`.

```
1. file_open (op BX=6, AX=0=read, DS:DX=filename at DS:0x4E)
2. Store handle to cs:word_2EA26
3. dos_mem_alloc (op BX=0, AX=N paras) → segment
4. file_read (op BX=0xA, CX=4B, DX=0) → header
5. file_lseek (op BX=0xE) → seek to record
6. file_read → load entity record
7. file_close (op BX=8)
8. Initialize FarObj fields from loaded data
```

The filename is at DS:0x4E (offset 78 in the data segment). Likely a 2-character entity
type name (e.g. "F4" for F-4, "SA" for SA-2 SAM, etc.).

### entity_slot_pair_create (0x2EA78, 47B)

Creates a pair of linked entity slots from two type IDs:
```
lodsw → type_id_A (CS:word_2EA18)
lodsw → type_id_B (CS:word_2EA1A)
IF type_id_A != 0xFFFF: entity_slot_create(BX=0)
IF type_id_B != 0xFFFF: entity_slot_create(BX=1)
```

Used for: wingman pairs, weapon-platform pairs, etc.

---

## Entity Spawning: farobj_slot_step_spawn (0x4D8A7, 284B)

Processes a spawn queue of up to 10 entries at `DS:0x6B58:[0x33]` (stride 6).

**Active check**: `DS:0x6B58:byte_6B58A & 1` = spawn system active.

**Spawn position computation** (with jitter):
```
for each active spawn entry at DS:[0x33 + N×6]:
    call fixed_vec3_accumulate_b   ; accumulate base position
    jitter_x = (CX & 7) - 3       ; ±3 tile jitter (from fractional accumulation)
    jitter_y = (CX & 7) - 3
    pos_x = ds:word_6B586 + jitter_x × cs:word_4D8A5
    pos_y = ds:word_6B588 + jitter_y × cs:word_4D8A5
```

Each spawn entry (6B):
- [+0]: entity type/flags
- [+1..+5]: spawn parameters

---

## Entity Counters (entity_counters_update, 0x1CEA3)

Per-entity countdown timers at `ES:0x7772:0x506+N` (one byte per entity).
Updated each frame via `sub_17537` (called through function pointer, 10K dyn calls).

```
for N = 0..count-1:
    counter = ES:0x7772:[0x506+N]
    if counter == 0: skip
    if counter > threshold: counter--
    else:
        counter--
        set event flag ES:0x7894:0xD1Ah = 1  ; entity event triggered
```

Also uses shift register `ES:0x7772:word_7E94C+0x17Bh` (shr by cl) for threshold
computation where cl = `ES:0x7772:byte_7E94C+0x179h`.

---

## Map Tile Position (map_tile_pos_get, 0x128A1)

Returns current map tile coordinates (corrected from misnamed `state_farptr_get`):
```
AX = cs:map_pos_y    ; Y tile index
BX = cs:map_pos_x    ; X tile index
```

Called by `tile_object_interpreter`, `farobj_tile_key_cache`, R12 state entry records.
Used as the base tile for terrain rendering/sampling.

---

## Three-Phase Sweep: farobj_sweep_all (0x2E2D0, 16B)

```
call farobj_slot_sweep         ; sweeps entity slot states (phase 1)
call farobj_cmd_sweep          ; sweeps command queues (phase 2)
call farobj_entity_accum_sweep ; applies EntityAccumEntry motion (phase 3)
retf
```

Called by both `game_frame_update_chain` and `main_frame_update_loop` each flight frame.
Applies accumulated motion (EntityAccumEntry) to FarObj world positions and orientations.
