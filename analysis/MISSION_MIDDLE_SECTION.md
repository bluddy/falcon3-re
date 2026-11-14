# Mission File Middle Section

## Overview

The middle section (0x00A4 - 0x0250 in SQUAD0.MIS, 429 bytes) contains flight plans, target assignments, and AI parameters between aircraft records and waypoints.

## Structure

Highly variable structure with data blocks separated by zero-padding:
- **53.8% zeros** - sparse data format
- **24 data blocks** of varying sizes
- **6 instances** of 7-byte target/assignment pattern

## 7-Byte Pattern (Target Assignment?)

**Format:** `XX YY ZZ FF ID 40 11`

Found at 6 locations:
```
Offset | B0  B1  B2  | FF | ID  | Notes
-------|-------------|----|----|--------------------------------
0x00DA |  55  66  72 | FF |  6 | Aircraft ID 6 (player flight)
0x00E5 |  66  51  60 | FF |  6 | Aircraft ID 6 (repeated)
0x0117 |  60  57  58 | FF |  9 | Aircraft ID 9 (Type 0x34)
0x0122 |  67  70  54 | FF |  9 | Aircraft ID 9 (repeated)
0x0145 |  69  61  55 | FF | 12 | Aircraft ID 12 (Type 0x35)
0x015E |  69  61  55 | FF | 14 | Aircraft ID 14 (Type 0x36)
```

**Interpretation:**
- Bytes 0-2: Coordinates (8-bit format?) or target IDs
- Byte 3: 0xFF marker
- Byte 4: Aircraft ID or flight leader ID
- Bytes 5-6: 0x40 0x11 (constant, possibly flags)

**Hypothesis:** Target assignments for flights
- Each flight gets assigned coordinates/targets
- ID field references aircraft record (flight leader?)
- Duplicate entries might indicate waypoint sequence

## Data Block Types

### Short Records (2-10 bytes)
- **Count:** 14 blocks
- **Purpose:** Headers, flags, counters
- **Examples:**
  - `81 91 02 A7 00 DB C6` (7 bytes at 0x00A4)
  - `B4 00 42 33 3C FF 06 40 11` (9 bytes at 0x00E3)

### Flight Plans (20-35 bytes)
- **Count:** 3 blocks
- **Purpose:** Flight waypoint routes?
- **Example:** 32 bytes at 0x00C1
  - Starts with 0x0A (10 - count?)
  - Contains multiple uint16 values in coordinate range
  - Includes 7-byte target pattern

### Extended Flight Plans (40-50 bytes)
- **Count:** 1 block (48 bytes at 0x00EE)
- **Purpose:** Detailed flight parameters
- **Contains:** Multiple coordinate-like values

## Block 1 Analysis (0x00C1, 32 bytes)

```
0A 46 35 49 03 DA CB 10 5A 08 D8 C6 10 5A 08 DD
C3 10 5A 08 DF C9 10 5A 0A 37 42 48 FF 06 40 11
```

**Interpretation:**
- Byte 0: 0x0A (10) - possibly waypoint count or structure version
- Contains multiple patterns:
  - `10 5A` appears 4 times (could be altitude/speed markers)
  - Coordinate-like uint16 values: 55811, 50904, 56584, 51679
  - Ends with 7-byte target pattern (aircraft ID 6)

## Trailing Section Pattern

Starting around 0x0167, the data becomes very sparse with small 2-4 byte blocks:
- Repeating pattern: `C8 00 02 02` followed by zeros
- `1E 1E` (30, 30) appears periodically
- Might be: state flags, timers, or formation spacing parameters

## Size Correlation

**SQUAD0.MIS:** 429 bytes in middle section
**SQUAD1.MIS:** ~410 bytes (smaller file, 1 waypoint vs 11)

Size difference (19 bytes) doesn't correlate directly with waypoint difference (210 bytes), suggesting this section encodes more than just waypoint references.

## Questions

1. **7-byte pattern:**
   - Are bytes 0-2 really coordinates (8-bit) or target/waypoint IDs?
   - Why does aircraft ID 6 appear twice?
   - What do 0x40 0x11 flags mean?

2. **Block 1 structure:**
   - Is 0x0A a waypoint count? (We have 11 waypoints, close to 10)
   - What do the `10 5A` repeated patterns represent?
   - Are the coordinate-like values actual coordinates or scaled/encoded?

3. **Sparse trailing data:**
   - What do the small 2-4 byte blocks encode?
   - Why is there so much zero-padding?
   - Could this be a fixed-size array with many unused slots?

4. **Flight correlation:**
   - How do these blocks map to the 3 flights indicated by header byte 0?
   - Are there exactly 3 flight plan blocks (one per flight)?

## Next Steps

1. Correlate data blocks with flight structure (3 flights in header)
2. Map 7-byte pattern coordinates to game world locations
3. Search IDA for middle section loading code
4. Compare multiple mission files to understand variations
5. Decode the `10 5A`, `40 11` constant patterns
6. Understand the sparse trailing section purpose
