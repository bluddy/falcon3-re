# Complete Waypoint Specification

## Overview

Waypoints in Falcon 3.0 control both the flight path and aircraft behavior at each point. This document combines reverse-engineered binary format with manual documentation.

## Binary Format (Proven by Analysis)

### 11-Byte Format (with 0x01 prefix marker)
```
Offset | Size | Type   | Field          | Description
-------|------|--------|----------------|--------------------------------
0x00   | 1    | uint8  | marker         | Always 0x01
0x01   | 1    | uint8  | x_low          | X coordinate LOW byte
0x02   | 1    | uint8  | x_high         | X coordinate HIGH byte
0x03   | 2    | int16  | marker_1       | Constant (-8 or -2)
0x05   | 1    | uint8  | y_low          | Y coordinate LOW byte
0x06   | 1    | uint8  | y_high         | Y coordinate HIGH byte
0x07   | 2    | int16  | marker_2       | Constant (-12 or -9)
0x09   | 2    | uint16 | constant       | Always 16 (0x0010)
```

### 10-Byte Duplicate
Immediately follows 11-byte version, same structure minus leading 0x01 marker.

Total: **21 bytes per waypoint** (11 + 10)

### Coordinates (16-bit, proven)

**X coordinate** = (x_high << 8) | x_low → uint16 (0-65,535)  
**Y coordinate** = (y_high << 8) | y_low → uint16 (0-65,535)

Full 16-bit range represents entire theater map.

**Example (SQUAD0.MIS waypoint 0):**
- x_low=0x00, x_high=0xC6 → X = 50,688
- y_low=0x90, y_high=0xC6 → Y = 50,832

## Waypoint Parameters (from Manual)

### Altitude
- **Unit**: Feet (above ground level - AGL, or mean sea level - MSL)
- **Typical values:**
  - Cruise: 8,000 - 15,000 ft
  - CAP: 20,000 - 30,000 ft
  - Strike ingress: 200 - 1,000 ft (low-level)
  - Attack: 5,000 - 10,000 ft (medium altitude)
- **Storage**: Not yet found in 11-byte structure (may be in flight plan section)

### Speed
- **Unit**: Knots (True Airspeed - TAS)
- **Typical values:**
  - Optimal F-16 maneuvering: 450 kts
  - Fast transit: 500-600 kts
  - Attack approach: 400-450 kts
  - Low-level penetration: 500-600 kts
- **Storage**: Not yet found in 11-byte structure (may be in flight plan section)

### Action Codes (from Manual)

| Action | Code? | Description |
|--------|-------|-------------|
| **TAKEOFF** | ? | Start on runway (player only, first waypoint at home base) |
| **NOTHING** | ? | Transit waypoint, no special action |
| **CAP** | ? | Combat Air Patrol - engage nearby threats |
| **INTERCEPT** | ? | Aggressively pursue all enemy aircraft |
| **ESCORT** | ? | Protect corridor along flight route |
| **BOMB** | ? | Attack assigned target (needs 15nm approach) |
| **CAS** | ? | Close Air Support - ground attack |
| **SEAD** | ? | Suppress Enemy Air Defenses |
| **LOITER** | ? | Repeat previous CAP waypoints until fuel low |
| **LAND** | ? | Land at airfield (auto-set for final waypoint) |

**Action behavior notes:**
- BOMB: AI makes only one pass, needs 15nm for target acquisition
- INTERCEPT: Aircraft may wander far from route
- CAP: Stays near route, engages only nearby threats
- LOITER: Repeats only consecutive CAP waypoints, calculates fuel
- ESCORT: Speed/route should match escorted flight

## Marker Value Patterns

Two patterns observed (purpose unknown):

**Pattern A** (SQUAD0.MIS - 11 waypoints):
- marker_1 = -8 (0xF8FF)
- marker_2 = -12 (0xF4FF)

**Pattern B** (SQUAD1.MIS - 1 waypoint):
- marker_1 = -2 (0xFEFF)
- marker_2 = -9 (0xF7FF)

**Hypotheses:**
1. Different waypoint action types
2. Different mission types (training vs combat)
3. Different theaters
4. Encoding for altitude/speed offsets

## SQUAD0.MIS Waypoints (11 total, 231 bytes)

Perfect diagonal line with 300-unit spacing:

```
WP  | X_16bit | Y_16bit | Spacing | Notes
----|---------|---------|---------|---------------------------
 0  |  50,688 |  50,832 |    -    | Start position
 1  |  50,988 |  51,132 |   300   | +300 X, +300 Y
 2  |  51,288 |  51,432 |   300   | Perfect diagonal
 3  |  51,588 |  51,732 |   300   | continues...
 4  |  51,888 |  52,032 |   300   | 
 5  |  52,188 |  52,332 |   300   | 
 6  |  52,488 |  52,632 |   300   | 
 7  |  52,788 |  52,932 |   300   | 
 8  |  53,088 |  53,232 |   300   | 
 9  |  53,388 |  53,532 |   300   | 
10  |  53,688 |  53,832 |   300   | End position
```

Diagonal distance: 424.3 units between waypoints (√(300² + 300²))

## Missing Fields

Based on manual, these fields should exist but haven't been located in the 11-byte structure:

1. **Altitude** (feet) - Essential flight parameter
2. **Speed** (knots) - Essential flight parameter  
3. **Action code** - Determines aircraft behavior
4. **Target reference** - For BOMB actions

**Hypothesis:** These fields are stored in the **flight plan section** (429 bytes between aircraft records and waypoints) rather than with each individual waypoint. This would allow:
- Multiple flights to share the same waypoint coordinates
- Each flight to have different speeds/altitudes at same waypoint
- Efficient storage (coordinates once, parameters per flight)

## Relationship to Flight Plans

The 7-byte pattern found in flight plan section may link aircraft to waypoints:

```
Pattern: XX YY ZZ FF ID 40 11
- Bytes 0-2: Possibly waypoint reference or target coords
- Byte 4: Aircraft ID (6, 9, 12, 14 observed)
- Could assign waypoints + actions to specific flights
```

## Questions Remaining

1. **Where are altitude/speed stored?** 
   - In flight plan section?
   - Separate lookup table?
   - Default values per action type?

2. **Where are action codes?**
   - In flight plan section per flight?
   - Encoded in marker values?
   - Separate action table?

3. **What do marker values mean?**
   - Action type indicators?
   - Theater/mission type?
   - Default altitude/speed encodings?

4. **What is the constant 16?**
   - Version number?
   - Default radius/tolerance?
   - Bitfield flags?

5. **Why dual storage?**
   - Performance (different access patterns)?
   - Different game phases?
   - Historical artifact?

## Next Steps

1. Correlate flight plan 7-byte patterns with waypoint indices
2. Search IDA for waypoint action code comparisons
3. Find altitude/speed loading code
4. Decode flight plan section structure
5. Test hypothesis: modify mission file and observe in-game behavior
