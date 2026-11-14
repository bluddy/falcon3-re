# Mission File Waypoint Format

## Overview

Mission files (.MIS) store waypoints in a unique dual-copy format where each waypoint appears twice:
1. An 11-byte version with `0x01` prefix
2. A 10-byte duplicate without the prefix

## Waypoint Structure

### 11-Byte Format (with prefix)
```
Offset | Size | Type   | Description
-------|------|--------|--------------------------------
0x00   | 1    | uint8  | Marker (always 0x01)
0x01   | 1    | uint8  | X coordinate (0-255)
0x02   | 1    | uint8  | ? (varies)
0x03   | 2    | int16  | Marker 1 (constant: -8 or -2)
0x05   | 1    | uint8  | Y coordinate (0-255)
0x06   | 1    | uint8  | ? (varies)
0x07   | 2    | int16  | Marker 2 (constant: -12 or -9)
0x09   | 2    | uint16 | Constant (always 16 / 0x0010)
```

### 10-Byte Format (duplicate, no prefix)
Same as above but without the leading `0x01` byte.

## Coordinate System

Coordinates use single bytes (0-255) representing position as 1/256 of theater size:
- `X = 200` → 200/256 ≈ 78.1% across theater width
- `Y = 144` → 144/256 ≈ 56.3% down theater height

## Marker Variations

Two marker patterns have been observed:

### Pattern A (SQUAD0.MIS)
- Marker 1: `-8` (0xF8 0xFF)
- Marker 2: `-12` (0xF4 0xFF)

### Pattern B (SQUAD1.MIS)  
- Marker 1: `-2` (0xFE 0xFF)
- Marker 2: `-9` (0xF7 0xFF)

The meaning of these marker variations is unknown. Possible interpretations:
- Different waypoint types (nav, target, threat, etc.)
- Different flight patterns or behaviors
- Altitude/speed encoding offsets
- Mission type indicators

## Storage Pattern

Waypoints are stored in sequence as: [11-byte] [10-byte] [11-byte] [10-byte] ...

Example from SQUAD0.MIS (waypoint 0 at offset 0x0251):
```
0x0250: 00 | 01 00 C6 F8 FF 90 C6 F4 FF 10 00 | 00 C6 F8 FF ...
             ^-- 11-byte with prefix --^   ^-- 10-byte duplicate -->
```

Total storage per waypoint: 21 bytes

## Examples

### SQUAD0.MIS (11 waypoints, 231 bytes total)
```
WP  0 @ 0x0251: X=  0, Y=144  (markers: -8, -12)
WP  1 @ 0x0266: X= 44, Y=188  (markers: -8, -12)
WP  2 @ 0x027B: X= 88, Y=232  (markers: -8, -12)
WP  3 @ 0x0290: X=132, Y= 20  (markers: -8, -12)
WP  4 @ 0x02A5: X=176, Y= 64  (markers: -8, -12)
WP  5 @ 0x02BA: X=220, Y=108  (markers: -8, -12)
WP  6 @ 0x02CF: X=  8, Y=152  (markers: -8, -12)
WP  7 @ 0x02E4: X= 52, Y=196  (markers: -8, -12)
WP  8 @ 0x02F9: X= 96, Y=240  (markers: -8, -12)
WP  9 @ 0x030E: X=140, Y= 28  (markers: -8, -12)
WP 10 @ 0x0323: X=184, Y= 72  (markers: -8, -12)
```

### SQUAD1.MIS (1 waypoint, 21 bytes total)
```
WP  0 @ 0x01AE: X=184, Y=216  (markers: -2, -9)
```

## Questions Remaining

1. **Unknown bytes**: What do bytes at offsets +0x02 and +0x06 represent?
   - Altitude component?
   - Speed setting?
   - Formation spacing?
   - Threat level?

2. **Marker significance**: Why do the int16 markers vary between files?
   - Are they waypoint action types?
   - Do they encode altitude/speed offsets?
   - Mission type dependent?

3. **Duplication purpose**: Why store each waypoint twice?
   - Performance optimization (pre-computed format)?
   - Different game phases use different formats?
   - Historical artifact from development?

4. **Constant value**: Why is the uint16 at +0x09 always 16?
   - Waypoint structure version?
   - Default radius/tolerance?
   - Bitfield with standard settings?

## Next Steps

1. Search IDA disassembly for waypoint loading code
2. Find references to the marker values (-8, -12, -2, -9)
3. Locate code that interprets the unknown bytes
4. Compare more mission files to find pattern correlations
5. Test hypothesis: load mission, modify waypoint, observe behavior
