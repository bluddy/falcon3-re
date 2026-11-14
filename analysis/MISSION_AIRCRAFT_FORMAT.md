# Mission File Aircraft Records

## Overview

Mission files contain a section of 6-byte aircraft records following the header. Each record represents an aircraft or flight member in the mission.

## Structure

### File Layout (SQUAD0.MIS, 824 bytes)

```
0x0000-0x0007: Header (8 bytes)
0x0008-0x00A3: Aircraft Records (26 records × 6 bytes = 156 bytes)
0x00A4-0x0250: Unknown data (429 bytes)
0x0251-0x032D: Waypoints (11 waypoints × 21 bytes = 231 bytes)
0x032E-0x0337: End padding (10 bytes)
```

## Aircraft Record Format (6 bytes)

```
Offset | Size | Type  | Description
-------|------|-------|----------------------------------
0x00   | 1    | uint8 | Flags (0x00, 0x80, or 0x81)
0x01   | 1    | uint8 | Aircraft ID (sequential, 2-27)
0x02   | 1    | uint8 | Constant (always 0x00)
0x03   | 1    | uint8 | Type code
0x04   | 1    | uint8 | Constant (always 0x00)
0x05   | 1    | uint8 | Subtype/variant/group
```

## Type Codes Observed

### Type 0x01 (1) - Fighter/Player Flight
- IDs: 2-6 (5 aircraft)
- Flags: 0x00 (first), 0x80 (rest)
- B5: Always 0x03
- **Likely**: Player's flight (F-16s)

### Type 0x34 (52) - Unknown
- IDs: 7-9 (3 aircraft)
- Flags: 0x80
- B5: Always 0x01

### Type 0x35 (53) - Unknown
- IDs: 10-12 (3 aircraft)
- Flags: 0x80
- B5: Always 0x23 (35)

### Type 0x36 (54) - Unknown
- IDs: 13-16 (4 aircraft)
- Flags: 0x80
- B5: Always 0x2D (45)

### Type 0x0B (11) - Unknown
- IDs: 17, 27 (2 aircraft)
- Flags: 0x80, 0x81
- B5: 0x0E (14), 0x0D (13)

### Type 0x09 (9) - Unknown
- IDs: 18-19 (2 aircraft)
- Flags: 0x81
- B5: Always 0x0B (11)

### Type 0x0A (10) - Unknown
- IDs: 20-22 (3 aircraft)
- Flags: 0x81
- B5: Always 0x09

### Type 0x08 (8) - Unknown
- IDs: 23-25 (3 aircraft)
- Flags: 0x81
- B5: Always 0x08

### Type 0x07 (7) - Unknown
- IDs: 26 (1 aircraft)
- Flags: 0x81
- B5: 0x05

## Flags Analysis

- **0x00**: First aircraft only (player aircraft?)
- **0x80**: Allied aircraft (entries 1-14, IDs 3-16)
- **0x81**: Enemy aircraft? (entries 15-25, IDs 17-27)

The flag byte may indicate:
- Bit 7 (0x80): Allied/Enemy
- Bit 0 (0x01): Player/AI or Additional flags

## SQUAD0.MIS Aircraft Distribution

```
Type | Count | ID Range | Flags  | Role Hypothesis
-----|-------|----------|--------|------------------------
0x01 |   5   |  2-6     | 00, 80 | Player flight (F-16)
0x34 |   3   |  7-9     | 80     | Ally type 1
0x35 |   3   | 10-12    | 80     | Ally type 2  
0x36 |   4   | 13-16    | 80     | Ally type 3
0x0B |   1   | 17       | 80     | Allied special?
0x0B |   1   | 27       | 81     | Enemy or support
0x09 |   2   | 18-19    | 81     | Enemy type 1
0x0A |   3   | 20-22    | 81     | Enemy type 2
0x08 |   3   | 23-25    | 81     | Enemy type 3
0x07 |   1   | 26       | 81     | Enemy type 4
-----|-------|----------|--------|------------------------
Total: 26 aircraft
```

## Observations

1. **Sequential IDs**: Aircraft IDs increment sequentially from 2 to 27
2. **Grouped by type**: Aircraft of the same type appear consecutively
3. **Flag grouping**: 0x80 flags (IDs 2-17), then 0x81 flags (IDs 18-27)
4. **Player flight**: First 5 aircraft (type 0x01) likely player's flight
5. **Mission structure**: 15 allied + 11 enemy aircraft (or 17 + 10 if ID 17 is allied)

## Questions

1. **Type code meaning**: Do type codes represent:
   - Aircraft types (F-16, MiG-29, Su-27)?
   - Mission roles (CAP, STRIKE, ESCORT)?
   - Flight formations?

2. **B5 (subtype) meaning**: 
   - Weapon loadout ID?
   - Skill level?
   - Flight behavior?

3. **Missing IDs**: Why start at ID 2 instead of 0 or 1?
   - ID 0/1 reserved for special purposes?
   - Header references?

4. **Header correlation**: Does header byte 0 (value 3) mean 3 flights?
   - Flight 1: IDs 2-6 (5 aircraft, player)
   - Flight 2: IDs 7-16 (10 aircraft, allied)
   - Flight 3: IDs 17-27 (11 aircraft, enemy)

## Next Steps

1. Search IDA for aircraft type loading code
2. Map type codes to aircraft names (F-16, MiG-29, etc.)
3. Decode the 429-byte section between aircraft and waypoints
4. Correlate aircraft IDs with waypoint usage
5. Compare SQUAD1.MIS aircraft records
