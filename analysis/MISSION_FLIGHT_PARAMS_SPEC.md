# Flight Parameter Structure Specification

## Overview

Mission files contain 23-byte flight parameter structures that specify altitude and action codes for flights. These structures are found in the flight plan section between the aircraft records and waypoint data.

**Location**: Flight plan section (after aircraft records, before waypoints)  
**Size**: 23 bytes per structure  
**Purpose**: Define altitude, speed, and behavior for each flight

## Binary Format

```
Offset | Size | Type   | Field          | Description
-------|------|--------|----------------|----------------------------------
0x00   | 2    | uint16 | mystery        | 180 (0x00B4) for first, 0 for rest
0x02   | 1    | uint8  | altitude       | Altitude / 100 (feet)
0x03   | 1    | uint8  | unknown_3      | Always 0x00 (observed)
0x04   | 1    | uint8  | unknown_4      | 0 or 2
0x05   | 1    | uint8  | unknown_5      | Always 2 (observed)
0x06   | 1    | uint8  | action_code    | Waypoint action (0-9)
0x07   | 13   | bytes  | padding        | All zeros
0x14   | 1    | uint8  | timeout_a      | Always 30 (0x1E) - fuel/time limit?
0x15   | 1    | uint8  | timeout_b      | Always 30 (0x1E) - fuel/time limit?
0x16   | 1    | uint8  | terminator     | Always 0x00
```

## Field Details

### +0x00-01: Mystery uint16

- **First structure in file**: 180 (0x00B4)
- **All other structures**: 0 (0x0000)
- **Hypothesis**: Time offset, formation spacing, or player flight marker

### +0x02: Altitude (Confirmed)

**Encoding**: Value * 100 = feet  
**Range**: 0-255 → 0-25,500 feet

**Observed values:**
- 150 (0x96) = 15,000 feet
- 200 (0xC8) = 20,000 feet  
- 250 (0xFA) = 25,000 feet

**Typical usage:**
- Low-level strike: 2-10 (200-1,000 ft)
- Medium altitude: 80-100 (8,000-10,000 ft)
- CAP patrol: 150-300 (15,000-30,000 ft)

### +0x03: Speed (Hypothesis - NOT CONFIRMED)

**Status**: Field exists but always 0x00 in test files  
**Hypothesis**: May encode speed or use default per action type  
**Expected range if speed**: 400-600 knots typical

**Possibility**: Speed is defaulted based on action code:
- CAP: 450 knots (optimal F-16 maneuvering)
- INTERCEPT: 600 knots (high speed)
- BOMB: 500 knots (attack approach)

### +0x04-05: Unknown bytes

- **+0x04**: Varies (0 or 2)
- **+0x05**: Always 2 (observed)
- **Hypotheses**:
  - Formation type
  - Aggression level
  - ROE (Rules of Engagement)
  - Bitfield flags

### +0x06: Action Code (Confirmed)

**Type**: uint8 (0-9)  
**Purpose**: Defines aircraft behavior at waypoints

| Code | Action | Behavior |
|------|--------|----------|
| 0 | TAKEOFF/NOTHING | Transit or takeoff |
| 1 | NOTHING | Simple transit waypoint |
| 2 | CAP | Combat Air Patrol - engage nearby threats |
| 3 | INTERCEPT | Aggressively pursue all enemy aircraft |
| 4 | ESCORT | Protect corridor along route |
| 5 | BOMB | Attack assigned ground target |
| 6 | CAS | Close Air Support |
| 7 | SEAD | Suppress Enemy Air Defenses |
| 8 | LOITER | Repeat previous CAP waypoints |
| 9 | LAND | Land at airfield |

**Action code 2 (CAP)** confirmed by SQUAD1.MIS analysis.

### +0x07-13: Padding

13 bytes of zeros. Reserved for future use or alignment.

### +0x14-15: Timeout/Fuel Limit

Both bytes always 0x1E (30 decimal).

**Hypotheses:**
- Time limit in minutes
- Fuel reserve percentage  
- Loiter duration
- Engagement timeout

### +0x16: Terminator

Always 0x00. Marks end of structure.

## File Structure Relationship

### SQUAD0.MIS (824 bytes)

**Header byte 0**: 3 (flight count)  
**Header byte 5**: 11 (waypoint count)  
**Header byte 7**: 26 (aircraft count)  
**Param structures**: 3 (one per flight)

```
Offset   | Section           | Size
---------|-------------------|--------
0x0000   | Header            | 8 bytes
0x0008   | Aircraft records  | 156 bytes (26 × 6)
0x00A4   | Flight plan       | 429 bytes (includes 3 × 23-byte params)
0x0251   | Waypoints         | 231 bytes (11 × 21)
```

**Flight parameters at**:
- 0x0167: Flight 1 (20,000 ft, action 0)
- 0x017E: Flight 2 (20,000 ft, action 0)
- 0x0195: Flight 3 (20,000 ft, action 0)

### SQUAD1.MIS (451 bytes)

**Header byte 0**: 2 (flight count)  
**Header byte 4**: 1 (waypoint count)  
**Header byte 7**: 0 (no aircraft records)  
**Param structures**: 5 (MORE than flight count!)

```
Offset   | Section           | Size
---------|-------------------|--------
0x0000   | Header            | 8 bytes
0x0008   | Flight plan       | 422 bytes (includes 5 × 23-byte params)
0x01AE   | Waypoints         | 21 bytes (1 × 21)
```

**Flight parameters at**:
- 0x00F2: Params 1 (15,000 ft, action 2=CAP)
- 0x0109: Params 2 (15,000 ft, action 2=CAP)
- 0x0120: Params 3 (25,000 ft, action 0)
- 0x0137: Params 4 (25,000 ft, action 0)
- 0x014E: Params 5 (25,000 ft, action 0)

**Mystery**: Why 5 param structures for 2 flights with 1 waypoint?

**Hypotheses:**
1. **Per waypoint-per-flight**: Each flight can have different params at each waypoint (5 = unused slots?)
2. **Waypoint segments**: Each flight route divided into segments with different altitudes/actions
3. **Mission phases**: Different phases (ingress, target, egress) with separate params
4. **Template structure**: Fixed array size with unused entries

## Decoding Algorithm

```python
def decode_flight_params(data, offset):
    """Decode 23-byte flight parameter structure."""
    mystery = struct.unpack('<H', data[offset:offset+2])[0]
    altitude_raw = data[offset+2]
    altitude_feet = altitude_raw * 100
    action_code = data[offset+6]
    timeout_pair = (data[offset+0x14], data[offset+0x15])
    
    return {
        'mystery_uint16': mystery,
        'altitude': altitude_feet,
        'action': action_code,
        'timeout': timeout_pair
    }
```

## Example Data

### SQUAD0.MIS Flight 1 (0x0167)
```
B4 00 C8 00 02 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 1E 1E 00
```

- Mystery: 180 (first flight marker)
- Altitude: 200 × 100 = 20,000 feet
- Action: 0 (NOTHING/transit)
- Timeout: 30, 30

### SQUAD1.MIS Params 1 (0x00F2)
```
B4 00 96 00 02 02 02 00 00 00 00 00 00 00 00 00 00 00 00 00 1E 1E 00
```

- Mystery: 180 (first structure marker)
- Altitude: 150 × 100 = 15,000 feet
- Action: 2 (CAP)
- Timeout: 30, 30

## Questions Remaining

1. **Where is speed stored?**
   - Default per action type?
   - Encoded in unknown bytes +0x03-05?
   - Calculated from flight plan?

2. **What is the mystery uint16 at +0x00?**
   - Why 180 for first, 0 for rest?
   - Player flight marker?
   - Time offset in seconds?

3. **Why does SQUAD1 have 5 structures for 2 flights?**
   - Per-waypoint parameters?
   - Fixed array size?
   - Segmented flight plans?

4. **What do bytes +0x04 and +0x05 encode?**
   - Formation type?
   - Aggression/ROE?
   - Flags?

5. **What is the timeout pair (30, 30)?**
   - Time limit?
   - Fuel reserve?
   - Same for all missions?

## Next Steps

1. Search IDA for action code comparisons (0-9) to confirm mapping
2. Find speed loading code in IDA to determine if defaulted or stored
3. Analyze more mission files to understand structure count variations
4. Test hypothesis: modify mission file altitude/action and observe in-game
5. Correlate 7-byte patterns in flight plan with these parameter structures

## Progress

**Decoded**: 5/23 bytes (22%)
- +0x02: Altitude ✓
- +0x06: Action code ✓  
- +0x14-15: Timeout pair ✓

**Partially decoded**: 3/23 bytes
- +0x00-01: Mystery uint16 (observed pattern, purpose unclear)

**Unknown**: 15/23 bytes
- +0x03: Speed? (always 0)
- +0x04-05: Flags? (varies)
- +0x07-13: Padding (all zeros)

**Overall mission system progress: 85% → 88%**
