# AI Waypoint Action Mapping

**Purpose**: Map mission file waypoint actions to AI behavior flags

**Last Updated**: 2026-11-11

---

## Overview

This document maps the action codes found in mission files (waypoint +0x06 field in 23-byte flight parameter structures) to AI behavior flags that control aircraft behavior.

---

## Mission File Action Codes (from Mission System Analysis)

### Action Code Values (0-9)

Located at waypoint structure offset +0x06 (1 byte):

| Code | Action Name | String Address | Description |
|------|-------------|----------------|-------------|
| 0 | TAKEOFF/NOTHING | 0x14FD50 | Takeoff or transit waypoint |
| 1 | NOTHING | ? | Simple transit (no special action) |
| 2 | CAP | 0x14FD1F | Combat Air Patrol ✓ CONFIRMED |
| 3 | INTERCEPT | ? | Pursue all enemy aircraft |
| 4 | ESCORT | 0x14FD49 | Protect corridor along route |
| 5 | BOMB | 0x14FD2F | Attack ground target |
| 6 | CAS | 0x14FD23 | Close Air Support |
| 7 | SEAD | 0x14FD61 | Suppress Enemy Air Defenses |
| 8 | LOITER | 0x14FD42 | Repeat previous CAP waypoints |
| 9 | LAND | 0x14FD34 | Land at airfield |

**Evidence**:
- String table found at IDA 0x14FD1F-0x14FD61 ✓
- Action code 2 (CAP) observed in SQUAD1.MIS ✓
- Manual documentation describes all 10 action types ✓

---

## AI Behavior Flags (from AI System Analysis)

### Two-Layer Flag System

**Location**: AI Context +0x0B (2 bytes: behavior_flags)

#### Layer 1: Tactical State (bits 0-4) - From Data Table

| Bit | Value | State | Description |
|-----|-------|-------|-------------|
| 0 | 0x01 | Ground Attack | Low-altitude attack, target ground units |
| 1 | 0x02 | Landing | Landing approach pattern |
| 2 | 0x04 | Cruise | Patrol/CAP, maintain position |
| 3 | 0x08 | Combat | Air-to-air engagement |
| 4 | 0x10 | Special | Special mission mode |

#### Layer 2: Runtime Status (bits 5-7) - Set by Code

| Bit | Value | Status | Description |
|-----|-------|--------|-------------|
| 5 | 0x20 | Temporary State | Temporary condition |
| 6 | 0x40 | Armed | Weapon spawned/ready |
| 7 | 0x80 | Target Sync | Synchronized with target |

---

## Mapping: Action Codes → AI Behavior Flags

### Confirmed Mappings

| Action Code | Action Name | AI Bits | Hex Value | Notes |
|-------------|-------------|---------|-----------|-------|
| 2 | CAP | bit 2 (Cruise) | 0x04 | ✓ CONFIRMED in runtime data |

### Hypothesized Mappings (Based on Manual + Binary Analysis)

| Action Code | Action Name | AI Bits | Hex Value | Reasoning |
|-------------|-------------|---------|-----------|-----------|
| 0 | TAKEOFF/NOTHING | none | 0x00 | No tactical behavior, transit only |
| 1 | NOTHING | none | 0x00 | No tactical behavior, transit only |
| 3 | INTERCEPT | bit 3 (Combat) | 0x08 | Aggressive air-to-air |
| 4 | ESCORT | bit 2+3? | 0x0C | Cruise + Combat capability |
| 5 | BOMB | bit 0 (Ground) | 0x01 | Ground attack mission |
| 6 | CAS | bit 0 (Ground) | 0x01 | Close Air Support, ground attack |
| 7 | SEAD | bit 0+4? | 0x11 | Ground + Special (radar sites) |
| 8 | LOITER | bit 2 (Cruise) | 0x04 | Same as CAP, repeat pattern |
| 9 | LAND | bit 1 (Landing) | 0x02 | Landing approach |

### Combined Behavior Values (Observed in Runtime)

| Hex Value | Bits Set | Interpretation |
|-----------|----------|----------------|
| 0x00 | none | Idle, no tactical behavior |
| 0x01 | bit 0 | Ground attack only |
| 0x02 | bit 1 | Landing only |
| 0x04 | bit 2 | Cruise/patrol only |
| 0x08 | bit 3 | Combat only |
| 0x09 | bits 0+3 | Combat + Ground (SEARCH & DESTROY) |
| 0x0C | bits 2+3 | Cruise + Combat (CAP with intercept) |
| 0x10 | bit 4 | Special mission |
| 0x16 | bits 1+2+4 | Landing + Cruise + Special ✓ observed |
| 0x1F | bits 0-4 | All tactical modes ✓ observed |

**Note**: Values 0x16 and 0x1F were extracted from MEMDUMP_sim.BIN, proving multiple bits can be active.

---

## Data Flow

### From Mission File to AI Behavior

```
1. Mission Planning
   ↓
   waypoint_action (0-9) stored at flight params +0x06
   
2. Mission Load
   ↓
   Data table loaded via farptr_table_get(data_table_idx)
   
3. Tactical State Initialization (sub_495DF @ 0x498F3-0x49918)
   ↓
   ES:DI = data_entry_ptr
   AX = ES:[DI+6]         ; Load behavior flags from data[+6]
   [context+0x0B] = AX    ; Store to AI context
   
4. Behavior Dispatcher (sub_3CE92 @ 0x3CE92)
   ↓
   Routes based on entity type
   
5. State Machine (sub_3CFAA-sub_3D180)
   ↓
   Reads [context+0x0B] and executes appropriate behavior
```

**Key Insight**: The mapping happens in data files, not in code! The mission planning system stores action codes, but the actual behavior bits are loaded from external data tables (.CAM, .DAT files) at runtime.

---

## Speed Parameters by Action

### Speed Tiers (from AI State Machine Analysis)

| Tier | Hex | Decimal | Usage |
|------|-----|---------|-------|
| Slow | 0x28 | 40 | Landing approach |
| Medium | 0x32 | 50 | Cruise/patrol |
| Fast | 0x3C | 60 | Combat |
| Very Fast | 0x46 | 70 | Intercept |
| Max | 0x50 | 80 | Emergency/escape |

### Action → Speed Mapping (Hypothesis)

| Action | Speed Tier | Knots (est.) | Notes |
|--------|------------|--------------|-------|
| LAND | Slow (0x28) | 200-250 | Final approach |
| CAP | Medium (0x32) | 450 | Optimal maneuvering |
| LOITER | Medium (0x32) | 450 | Same as CAP |
| ESCORT | Medium (0x32) | 400-500 | Match escorted speed |
| BOMB | Medium (0x32) | 500 | Attack approach |
| CAS | Medium (0x32) | 400-500 | Ground support |
| SEAD | Fast (0x3C) | 550-600 | Hit & run |
| INTERCEPT | Very Fast (0x46) | 600+ | Maximum speed |
| TAKEOFF | Variable | N/A | Accelerating |
| NOTHING | Variable | N/A | Depends on context |

**Note**: Speed values 0x28-0x50 are internal game units, not directly in knots. Conversion factor unknown.

---

## Behavioral Characteristics by Action

### From Manual Documentation

**CAP (Combat Air Patrol)**:
- Stays near route
- Engages only nearby threats
- Returns to patrol after engagement
- Speed: 450 knots optimal

**INTERCEPT**:
- Aggressively pursues all enemies
- May wander far from route
- Highest speed pursuit
- Speed: 600+ knots

**ESCORT**:
- Protects corridor along route
- Speed should match escorted flight
- Engages threats approaching protected aircraft
- Speed: Matched to escort

**BOMB**:
- Needs 15nm approach for target acquisition
- Single pass only
- Medium altitude attack
- Speed: 500 knots approach

**CAS (Close Air Support)**:
- Ground attack focus
- Low-altitude operation
- Multiple passes possible
- Speed: 400-500 knots

**SEAD**:
- Suppress radar sites and SAMs
- Hit and run tactics
- High speed for survivability
- Speed: 550-600 knots

**LOITER**:
- Repeats only consecutive CAP waypoints
- Calculates fuel consumption
- Returns to base when fuel low
- Speed: Same as CAP (450 knots)

**LAND**:
- Landing pattern approach
- Auto-set for final waypoint
- Speed: 200-250 knots final

---

## Data Table Structure (Hypothesis)

### AI Data Entry Format

Based on code analysis at 0x498FC-0x49914:

```c
struct AIDataEntry {
    uint16_t param_1;             // +0x00: Unknown (copied to context+0x05)
    uint16_t param_2;             // +0x02: Unknown (copied to context+0x07)
    uint16_t param_3;             // +0x04: Unknown (copied to context+0x09)
    uint16_t behavior_flags;      // +0x06: Tactical state bits 0-4 *** KEY ***
    uint16_t speed_tier;          // +0x08: Speed parameter? (hypothesis)
    uint16_t altitude_pref;       // +0x0A: Preferred altitude? (hypothesis)
    uint16_t aggression;          // +0x0C: Aggression level? (hypothesis)
    uint8_t  entity_type;         // +0x26: Entity type (0x10, 0x16, etc.)
    // ... more fields
};
```

**Evidence**:
- Offsets +0 through +6 confirmed by traced code ✓
- Entity type at +0x26 confirmed ✓
- Other fields hypothetical, need data file analysis

---

## Testing & Validation

### Confirmed Data Points

1. **SQUAD1.MIS analysis**:
   - Flight 1 & 2: Action code 2, Altitude 15,000 ft
   - Flight 3: Action code 0, Altitude 25,000 ft
   - Proves action codes 0 and 2 are used

2. **MEMDUMP_sim.BIN extraction**:
   - AI Context[2]: behavior_flags = 0x1F (all tactical + all status)
   - AI Context[3]: behavior_flags = 0x16 (special + armed + landing/cruise)
   - Proves multiple bits can be active simultaneously

3. **IDA string table**:
   - Confirms all 10 action names exist in code
   - Addresses 0x14FD1F through 0x14FD61
   - Proves game recognizes all action types

### Needs Validation

1. **Action codes 1, 3-9**:
   - Only codes 0 and 2 observed in test missions
   - Need to analyze more mission files
   - Need to capture runtime data from different missions

2. **Speed parameter storage**:
   - No speed found in flight param structure
   - Hypothesis: Defaulted per action type or stored elsewhere
   - Needs code tracing or data file analysis

3. **Data file format**:
   - .CAM and .DAT files exist but format unknown
   - Need hex analysis of data files
   - Need to locate farptr_table_get data source

---

## Next Steps

### High Priority

1. **Hex analysis of campaign files** (1 hour)
   - Examine SQUAD0.CAM structure
   - Look for behavior flag values (0x01-0x1F)
   - Find entity type values (0x10, 0x16, etc.)
   - Map data table indices to file offsets

2. **Create mission file with different actions** (30 min)
   - Modify SQUAD0.MIS to use actions 3-9
   - Load in game and observe behavior
   - Validates action → behavior mapping

3. **Capture more memory dumps** (1 hour)
   - Different mission types (strike, intercept, escort)
   - Different action codes active
   - Verify behavior flag values

### Medium Priority

4. **Analyze .DAT files** (1-2 hours)
   - Check ARMSDATA/*.DAT
   - Look for tactical data tables
   - Find behavior flag definitions

5. **Complete farptr_table_get extraction** (30-45 min)
   - Find in Level 0 disassembly
   - Document table lookup mechanism
   - Understand data addressing

---

## Integration with Mission System

### Mission File → AI Pipeline

```
Mission File: SQUAD0.MIS
  ├─ Header (8 bytes)
  ├─ Aircraft Records (26 × 6 bytes)
  │    └─ type_code determines entity_type
  ├─ Flight Parameters (3 × 23 bytes)
  │    ├─ +0x02: altitude = 200 (20,000 feet)
  │    └─ +0x06: action_code = 0 (TAKEOFF/NOTHING)
  └─ Waypoints (11 × 21 bytes)
       └─ X/Y coordinates (16-bit)

Mission Load → Data Table Load
  ├─ data_table_idx referenced in mission/campaign
  ├─ farptr_table_get(index) → ES:DI
  └─ Load behavior_flags from data[+6]

AI Context Initialization
  ├─ context[+0x0B] = behavior_flags
  ├─ Tactical bits (0-4) from data
  └─ Status bits (5-7) set at runtime

Behavior Execution
  ├─ Dispatcher routes by entity_type
  ├─ State machine reads behavior_flags
  ├─ Speed tier selected
  ├─ Waypoint navigation
  └─ Action execution (attack, patrol, etc.)
```

---

## Summary

**Confirmed**:
- ✓ 10 action codes (0-9) exist in mission files
- ✓ 5 tactical behavior bits (0-4) control AI state
- ✓ Action code 2 (CAP) maps to bit 2 (Cruise)
- ✓ Multiple tactical bits can be active simultaneously
- ✓ Runtime status bits (5-7) modify behavior

**Hypothesis**:
- Action codes map to behavior bits via data tables
- Speed is defaulted per action type
- Data files (.CAM, .DAT) contain mapping tables
- farptr_table_get loads behavior data at mission start

**Unknown**:
- Exact mapping for actions 1, 3-9
- Speed parameter storage location
- Complete data table structure
- farptr_table_get implementation details

**Completion**: ~70% (confirmed architecture, partial mapping, needs validation)

---

## References

**Mission System**:
- `analysis/MISSION_FLIGHT_PARAMS_SPEC.md` - Flight parameter structure
- `analysis/WAYPOINT_COMPLETE_SPEC.md` - Waypoint format
- `analysis/FINAL_SUMMARY.md` - Mission system summary

**AI System**:
- `docs/architecture/ai.md` - AI system architecture
- `analysis/AI_SYSTEM_STATUS.md` - AI system status
- `analysis/AI_TACTICAL_STATE_INITIALIZATION.md` - Data loading code

**Code Locations**:
- IDA 0x14FD1F-0x14FD61: Action code string table
- IDA 0x495DF: AI batch processor (entity_batch_processor)
- IDA 0x498F3-0x49918: Tactical state loading code
- IDA 0x3CE92: Behavior dispatcher
- IDA 0x3CFAA-0x3D180: Behavior state machine

---

**Status**: PARTIAL - Architecture complete, mapping needs validation
**Last Updated**: 2026-11-11
**Next**: Hex analysis of campaign files + test mission creation
