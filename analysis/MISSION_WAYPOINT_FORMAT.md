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

## Waypoint Structure

### 11-Byte Format (with prefix)
```
Offset | Size | Type   | Description
-------|------|--------|--------------------------------
0x00   | 1    | uint8  | Marker (always 0x01)
0x01   | 1    | uint8  | X coordinate LOW byte
0x02   | 1    | uint8  | X coordinate HIGH byte
0x03   | 2    | int16  | Marker 1 (constant: -8 or -2)
0x05   | 1    | uint8  | Y coordinate LOW byte
0x06   | 1    | uint8  | Y coordinate HIGH byte
0x07   | 2    | int16  | Marker 2 (constant: -12 or -9)
0x09   | 2    | uint16 | Constant (always 16 / 0x0010)
```

### 10-Byte Format (duplicate, no prefix)
Same as above but without the leading `0x01` byte.

## Coordinate System

**PROVEN: Waypoints use 16-bit coordinates (0-65535)**

The bytes previously labeled "unknown" are actually the HIGH bytes of 16-bit little-endian coordinates. The coordinate bytes are split non-contiguously in the structure:

- **X coordinate** = (byte[2] << 8) | byte[1]  = uint16 (0-65535)
- **Y coordinate** = (byte[6] << 8) | byte[5]  = uint16 (0-65535)

This provides much higher precision than the 8-bit coordinates (0-255) mentioned in Strategic Falcon documentation.

### Coordinate Range Examples

**SQUAD0.MIS** (11 waypoints forming diagonal line):
- X range: 50,688 - 53,688 (span: 3,000 units)
- Y range: 50,832 - 53,832 (span: 3,000 units)  
- Spacing: Exactly 300 units between consecutive waypoints
- Pattern: Perfect diagonal with equal X and Y increments

**SQUAD1.MIS** (1 waypoint):
- X: 38,072
- Y: 56,024
- Different coordinate range suggests different theater or mission area

### Coordinate Scale

The full 16-bit range (0-65535) likely represents the entire theater map or game world. Assuming a typical theater size of ~200-400 nautical miles:

- 65535 units ≈ 250-400nm → ~120-240 feet per unit
- 300 unit spacing (SQUAD0) ≈ 6.7-13.5nm between waypoints

This matches realistic tactical flight planning distances.

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
WP  | X_16bit | Y_16bit | Spacing | Markers
----|---------|---------|---------|----------
 0  |  50,688 |  50,832 |    -    | -8, -12
 1  |  50,988 |  51,132 |   300   | -8, -12
 2  |  51,288 |  51,432 |   300   | -8, -12
 3  |  51,588 |  51,732 |   300   | -8, -12
 4  |  51,888 |  52,032 |   300   | -8, -12
 5  |  52,188 |  52,332 |   300   | -8, -12
 6  |  52,488 |  52,632 |   300   | -8, -12
 7  |  52,788 |  52,932 |   300   | -8, -12
 8  |  53,088 |  53,232 |   300   | -8, -12
 9  |  53,388 |  53,532 |   300   | -8, -12
10  |  53,688 |  53,832 |   300   | -8, -12
```

Perfect diagonal line: Each waypoint is exactly 300 units in X and 300 in Y from the previous (424.3 unit diagonal distance).

### SQUAD1.MIS (1 waypoint, 21 bytes total)
```
WP  | X_16bit | Y_16bit | Markers
----|---------|---------|----------
 0  |  38,072 |  56,024 | -2, -9
```

## Questions Remaining

1. **Marker significance**: Why do the int16 markers vary between files?
   - Pattern A (-8, -12): SQUAD0.MIS
   - Pattern B (-2, -9): SQUAD1.MIS
   - Could indicate: waypoint action types, mission types, or theater-specific encoding

2. **Duplication purpose**: Why store each waypoint twice?
   - Performance optimization (different access patterns)?
   - Different game phases use different formats?
   - Historical artifact from development?

3. **Constant value**: Why is the uint16 at +0x09 always 16?
   - Waypoint structure version identifier?
   - Default radius/tolerance value?
   - Bitfield with standard settings?

4. **Coordinate origin**: Where is (0, 0) in the game world?
   - Southwest corner of map?
   - Center of theater?
   - Absolute world coordinates?

## Next Steps

1. Search IDA disassembly for waypoint loading code
2. Find references to the marker values (-8, -12, -2, -9)
3. Locate code that interprets the unknown bytes
4. Compare more mission files to find pattern correlations
5. Test hypothesis: load mission, modify waypoint, observe behavior
