# Mission Session 4: Mission File Analysis

**Date:** November 11, 2026  
**Focus:** .MIS mission file structure  
**Status:** IN PROGRESS - Initial patterns identified

---

## Summary

Started analysis of .MIS mission files which contain flight definitions, waypoints, and loadouts. Files are variable size (451-824 bytes). Identified key patterns but structure more complex than expected.

## File Characteristics

**Files examined:**
- SQUAD0.MIS: 824 bytes
- SQUAD1.MIS: 451 bytes

**Variable size** indicates different mission complexity (number of flights, waypoints).

## Key Findings

### 1. File Structure (Preliminary)

```
Section          | Approx Offset | Content
-----------------|---------------|----------------------------------
Header           | 0x0000-0x0007 | Mission metadata, counts
Flight Records   | 0x0008-0x00A?  | Flight definitions
Waypoint Header  | 0x00A?-0x00C? | Waypoint metadata
Waypoint Data    | 0x00C?-End    | Coordinate and action data
```

### 2. Header (First 8 bytes)

```
0x0000: 03 00 01 14 1E 0B 00 1A
```

**Fields:**
- Byte 0: `03` - Likely count (3 flights? 3 flight groups?)
- Bytes 1-2: `00 01` - uint16 = 256 (flag or version?)
- Bytes 3-7: `14 1E 0B 00 1A` - Unknown (mission params?)

### 3. Flight Record Section (0x0008+)

Pattern observed starting at 0x0008:

```
00 02 00 01 00 03 80
03 00 01 00 03 80  
04 00 01 00 03 80
05 00 01 00 03 80
...
```

**Possible structure:** Variable-length records with embedded IDs and values.

**Challenge:** No clear fixed-size pattern. Records might be:
- 3 bytes: `XX 00 YY`
- 4 bytes: `XX 00 YY 00`
- 6 bytes: `XX 00 YY 00 ZZ FLAG`

Or the data might be interpreted differently (bit-packed?).

### 4. Waypoint Section (End of File)

Last ~300 bytes show clear coordinate-like patterns:

```
0x025C: 00 C6 F8 FF 90 C6 F4 FF 10 00 01 2C C7 F8 FF BC
0x026C: C7 F4 FF 10 00 2C C7 F8 FF BC C7 F4 FF 10 00 01
0x027C: 58 C8 F8 FF E8 C8 F4 FF 10 00 58 C8 F8 FF E8 C8
```

**Pattern:** Repeating structure with values 0xC6, 0xC7, 0xC8, 0xC9 etc.

**Interpretation:**
- Values like 0xC6, 0xC7 are 1-byte coordinates (198, 199)
- `F8 FF` = -8 (int16) - altitude offset?
- `10 00` = 16 - possible field separator or count
- Pattern repeats consistently

**Structure hypothesis:**
```
uint8  x_coord       // 0xC6, 0xC7, etc.
int16  altitude?     // 0xF8FF = -8
uint8  y_coord       // 0x90, etc.
int16  speed?        // 0xF4FF = -12
uint16 flags         // 0x1000 = 16
uint8  action?       // 0x01
```

### 5. Data Distribution

**Byte analysis:**
- 37.6% zeros (0x00) - lots of padding/alignment
- 6.1% 0xFF - markers or -1 values
- 56.3% actual data

**Pattern detection:**
- Stride 12: 40 potential structures (strong signal!)
- Stride 48: 10 structures
- Stride 24: 21 structures

This suggests **12-byte repeating units** in some section.

---

## Strategic Falcon Documentation

From modding tools, mission files contain:

**Flight data:**
- Allied flights (player squadron)
- Enemy flights
- Support flights (AWACS, tankers)

**Waypoint data:**
- Position: 1 byte per coordinate (0-255)
- Granularity: 1/256 of theater width (~1.25 nm precision)
- Speed setting
- Altitude
- Action type (CAP, CAS, STRIKE, etc.)
- Loiter time

**ILS data:**
- Which airbases have ILS enabled
- Starting positions

**Waypoint actions:**
- CAP (Combat Air Patrol)
- CAS (Close Air Support)
- INTERCEPT
- STRIKE
- SEARCH & DESTROY
- LOITER
- LANDING
- SWEEP
- Escort
- SAM suppression

---

## Challenges

### 1. No Clear Record Boundaries

Unlike .SQU and .CAM files with obvious 0xFF padding, .MIS files are more tightly packed.

### 2. Variable-Length Encoding?

The flight section might use variable-length records depending on:
- Number of waypoints per flight
- Weapon loadout complexity
- Optional fields

### 3. Bit-Packed Data?

Some values might be bit-packed flags rather than byte-aligned fields.

### 4. Documentation Gaps

Strategic Falcon docs describe *what* is stored, but not the exact byte layout.

---

## Next Steps

### Immediate

1. **Compare two mission files side-by-side**
   - SQUAD0.MIS (824b) vs SQUAD1.MIS (451b)
   - Find differences to understand variable sections

2. **Locate waypoint count**
   - Count actual waypoint-like structures in data
   - Find header field that matches this count

3. **Decode 12-byte structures**
   - Strong signal at stride 12
   - Likely waypoint records

4. **Parse end section carefully**
   - Last ~300 bytes clearly contain coordinates
   - Decode the repeating pattern

### Follow-up

5. **Search for .MIS loading code**
   - Find file I/O routines in IDA
   - Locate structure definitions

6. **Create test mission**
   - Modify .MIS file manually
   - See what changes in-game
   - Validate field interpretations

7. **Cross-reference with .CAM targets**
   - Mission waypoints reference target IDs
   - Should match campaign target array

---

## Tools Created

### analyze_mission_file.py (99 lines)

Initial mission file analyzer:
- Shows hex dump
- Counts byte distribution
- Finds text strings
- Detects repeating patterns (stride analysis)

### parse_mission_file.py (125 lines)

Mission file parser (work in progress):
- Header extraction
- Flight record detection (needs refinement)
- Waypoint section identification

**Current status:** Patterns identified but exact structure not yet decoded.

---

## Estimated Completion

**Mission files:** 10% decoded  
**Time invested:** 1 hour  
**Estimated to 60%:** 3-4 more hours (side-by-side comparison, code analysis)

---

## Session Statistics

- **Files analyzed:** 2 (.MIS files)
- **Bytes examined:** 1,275 (824 + 451)
- **Tools created:** 2 (224 lines)
- **Patterns identified:** 3 (header, flights, waypoints)
- **Structure decoded:** Partial (header + waypoint patterns)

The mission file format is more complex than squadron/campaign files. The tight packing and variable-length encoding require more careful analysis. Next session should compare multiple files and search for loading code to confirm structure.
