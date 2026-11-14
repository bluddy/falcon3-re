# Mission System Session 3: Campaign File Structure

**Date:** November 11, 2026  
**Focus:** Decode .CAM campaign file structure  
**Status:** IN PROGRESS - Target array decoded, supply data not yet located

---

## Summary

Continuing mission system analysis by decoding the 11,828-byte .CAM campaign files. Successfully identified and partially decoded the strategic target array. Discovered two types of target records: full targets (70-73 bytes) and simplified targets (16-20 bytes).

## Key Findings

### 1. Campaign File Structure

**Total size:** 11,828 bytes (0x2E34)

**Organization:**
- Data blocks separated by 4+ consecutive 0xFF bytes (heavy padding)
- 208 total data blocks
- Block size distribution:
  - Small (1-10 bytes): 127 blocks (counters, flags, individual values)
  - Medium (11-30 bytes): 47 blocks (mini-structures, simplified targets)
  - Large (31-69 bytes): 10 blocks (unknown structures)
  - XLarge (70+ bytes): 26 blocks (24 full targets + 2 unknown)

### 2. Strategic Target Records (Full) - 24 targets

**Size:** 70-73 bytes each  
**Identifier:** Target ID at bytes 0-1, 0x3C marker at byte +6

**Structure:**

```
Offset | Size | Description
-------|------|--------------------------------------------------
+0x00  |  2   | Target ID (uint16, range 0-799)
+0x02  |  1   | Byte 2 (unknown, usually 0x00 or 0x01)
+0x03  |  1   | Byte 3 (varies 0-16, might be ownership or type)
+0x04  |  1   | Byte 4 (unknown, usually 0x00)
+0x05  |  1   | Byte 5 (varies 0-3, might be subtype)
+0x06  |  1   | Separator (always 0x3C except one 0x19 case)
+0x07  |  1   | Field 7 (varies 6-60, purpose unclear)
+0x08  |  8   | Array 1: 8 values, range 0-10 (strength/count data?)
+0x10  |  8   | Array 2: 8 values, 0x00-0xFF (usually repeated)
+0x18  |  8   | Array 3: 8 values, 190-218 range (coordinates?)
+0x20  |  8   | Data array 4: varies
+0x28  | ...  | More data fields
+0x30+ | var  | Multiple uint16 values (cross-references to other targets)
```

**Example:** Target ID 0 (first target in file)
```
00 00 00 03 01 02 3C 28 | 05 05 05 05 05 05 05 05
DD DD DD DD DD DE DC DD | C5 C5 C5 C5 C5 C5 C4 C4
00 06 07 08 09 00 00 00 | 01 00 00 00 00 06 04 0F
06 01 30 00 31 00 33 00 | 62 00 77 00 0F 00 91 01
61 F1 8E 08 39 1C 21 15 | 11
```

### 3. Strategic Target Records (Simplified) - 20+ targets

**Size:** 16-20 bytes  
**Identifier:** Target ID at bytes 0-1, 0x3C marker at byte +6 (same as full targets)

**Structure:** Similar to full targets but truncated
```
+0x00  |  2   | Target ID (uint16)
+0x02  |  4   | Header fields
+0x06  |  1   | Separator (0x3C)
+0x07  |  1   | Field 7
+0x08  | 8-10 | Abbreviated data arrays
```

**Examples:**
- ID 67 @ 0x00EA (16 bytes): `43 00 01 04 00 01 3C 17 03 01 06 08 03 01 01 00`
- ID 103 @ 0x0186 (18 bytes): `67 00 00 10 00 00 3C 07 01 01 01 01 01 01 01 00 09 0A`
- ID 248 @ 0x0444 (17 bytes): `F8 00 00 10 00 00 3C 05 02 00 01 02 00 00 00 00 CD`

**Purpose:** Likely secondary/minor targets:
- SAM sites
- Small airbases
- Supply depots
- Radar installations
- Bridge/infrastructure targets

### 4. Target Cross-References

The uint16 values in the latter portion of full target records contain **references to other target IDs**.

**Example:** Target ID 571 references targets 121 and 0

**Purpose:** Defines target relationships:
- Connected airbases
- Supply routes  
- Defensive networks (SAM coverage)
- Strategic dependencies

### 5. Key Data Patterns

**Array 1 (bytes +8 to +15):**
- Values: 0-10
- Most targets have repeated values (e.g., all 5s)
- Likely: Squadron/aircraft counts per target OR strength levels (0-10 scale)

**Array 2 (bytes +16 to +23):**
- Values: 0x00-0xFF
- Highly consistent within each target (mostly repeated bytes)
- Possible: X-coordinates or region IDs

**Array 3 (bytes +24 to +31):**
- Values: 190-218 range
- Also consistent within targets
- Possible: Y-coordinates or altitude data

**Hypothesis:** Arrays 2 and 3 might encode location data (map coordinates) rather than status/strength.

### 6. Small Blocks (Potential Supply Data)

**127 small blocks** of 1-10 bytes scattered throughout file.

**Sample blocks:**
```
0x012A (8b):  24 F0 99 FD 02 05 08 30
0x0150 (4b):  E6 E7 E7 E6  (u32=3873957862)
0x0158 (4b):  00 00 01 01  (u32=16842752)
0x0160 (4b):  0C 0C 0C 0C  (u32=202116108)
0x0168 (8b):  BE 00 BF 00 C0 00 C1 00
```

**Status:** Not yet decoded. These could be:
- Campaign day counter
- Aircraft inventory (18 F-16s initially)
- Weapon stockpiles (AIM-9, AIM-120, bombs)
- Fuel reserves
- Victory/defeat condition tracking
- Political state variables

---

## Total Targets

**Full targets:** 24 (70-73 bytes each)  
**Simplified targets:** 20+ (16-20 bytes each)  
**Total strategic objectives:** 44+

**Target ID range:** 0 to 863 (IDs are not sequential, sparse)

---

## Tools Created

### parse_campaign_targets.py (159 lines)

Initial campaign target parser. Identifies 70-73 byte blocks, extracts target IDs, shows hex dumps, and attempts field interpretation.

**Usage:**
```bash
python parse_campaign_targets.py [camfile]
```

### decode_target_structure.py (214 lines)

Detailed target structure decoder. Parses all targets, extracts arrays, analyzes patterns, and identifies small data blocks that might contain supply/inventory data.

**Features:**
- Parses full target structure with all arrays
- Cross-references between targets
- Pattern analysis (repeated values, value ranges)
- Small block identification and categorization
- Statistical analysis of field distributions

**Usage:**
```bash
python decode_target_structure.py
```

**Output:**
- Detailed hex dumps of first 5 targets
- Pattern analysis of arrays
- Distribution of field values
- List of small blocks (supply data candidates)

---

## Remaining Questions

### 1. What do the 8-element arrays represent?

**Array 1 (+8-15):** Values 0-10
- Could be: Aircraft counts, squadron strength, damage levels
- Pattern: Often repeated (all 5s)
- Needs: Comparison with mid-campaign saves to see changes

**Array 2 (+16-23):** Values 0x00-0xFF
- Could be: X-coordinates, region IDs, unit types
- Pattern: Highly consistent per target
- Needs: Correlation with map data or theater .STR files

**Array 3 (+24-31):** Values 190-218
- Could be: Y-coordinates, altitude, zone IDs
- Pattern: Consistent per target
- Needs: Map coordinate validation

### 2. What is byte +7 (varies 6-60)?

**Not a simple type code** (only 13 unique values across 24 targets).

**Hypotheses:**
- Combined field (bits for multiple flags)
- Calculated value (e.g., strategic value score)
- Index into another table

**To resolve:** Need to find code that loads targets and see how byte +7 is used.

### 3. Where is the supply/inventory data?

**Expected data not yet found:**
- Aircraft count (initial 18 F-16s)
- Weapon stockpile (AIM-9, AIM-120, bombs, rockets)
- Fuel reserves
- Campaign day counter

**Candidates:**
- The 127 small blocks (1-10 bytes)
- The 10 large blocks (31-69 bytes, not yet analyzed)
- A dedicated header block at file start

**Next step:** Systematically decode small blocks and large blocks.

### 4. What are the two extra XLarge blocks?

24 full targets identified, but 26 XLarge (70+ byte) blocks found.

**Possibilities:**
- Campaign header/footer
- Player squadron data
- Victory/defeat condition blocks

### 5. What is the first 73-byte block (0x0000-0x0049)?

**Currently treated as Target ID 0**, but might actually be:
- Campaign file header
- Theater configuration
- Player squadron summary

**Key characteristic:** ID = 0, which could mean "header" rather than "target 0"

---

## Next Steps

### Immediate (this session)

1. **Decode first block (0x0000-0x0049):**
   - Determine if it's a header or Target ID 0
   - Look for campaign day, theater ID, player squadron ID

2. **Analyze the 10 large blocks (31-69 bytes):**
   - Could be supply data structures
   - Might be squadron/flight summaries

3. **Decode representative small blocks:**
   - Find patterns in 1-10 byte blocks
   - Look for aircraft counts (expect value ~18)
   - Look for counters (campaign day, missions flown)

### Follow-up (next session)

4. **Compare multiple campaign files:**
   - SQUAD0.CAM vs SQUAD1.CAM etc.
   - Look for differences (campaign day, target status)
   - Validate field interpretations

5. **Cross-reference with .STR theater files:**
   - ISRAEL.STR contains theater-specific target layout
   - Validate coordinates/regions
   - Understand target types

6. **Find campaign loading code:**
   - Search for "CAM" string references in IDA
   - Locate file I/O routines
   - Identify structure definitions in code

---

## Progress Metrics

| Component | Completion | Status |
|-----------|-----------|--------|
| Squadron format (.SQU) | 95% | Extended state internals remaining |
| Campaign format (.CAM) | 25% | Target array decoded, supply data missing |
| Mission format (.MIS) | 0% | Not started |
| Code analysis | 0% | Not started |
| **Overall Mission System** | **45%** | Progressing on campaign files |

**Time invested this session:** ~1.5 hours  
**Total time (3 sessions):** ~5.5 hours

---

## Architecture Implications

### Target Array is Sparse

Target IDs range from 0 to 863, but only 44 targets exist. This suggests:
- Targets are indexed into a much larger global table
- Theater files (.STR) define the full 800+ target universe
- Campaign files only store active/relevant targets for the current theater

### Two-Tier Target System

Full targets vs. simplified targets suggests:
- **Primary targets** (airbases, command centers): Full complexity, 70-73 bytes
- **Secondary targets** (SAM sites, minor installations): Simplified, 16-20 bytes
- This optimizes storage while maintaining strategic detail

### Cross-Reference Network

Targets reference each other (via uint16 IDs), creating a:
- Strategic dependency graph
- Supply chain network
- Defense coordination system (SAM coverage, fighter cover)

This enables sophisticated campaign AI where:
- Destroying a supply depot weakens connected airbases
- Eliminating C3 centers degrades enemy coordination
- Taking out SAM sites opens attack corridors

---

## Session 3 Status

**Completed:**
- Identified 24 full strategic targets (70-73 bytes)
- Identified 20+ simplified targets (16-20 bytes)
- Decoded target header structure (ID, separator, field 7)
- Discovered 3 internal arrays per target (8 bytes each)
- Found target cross-reference system
- Categorized remaining blocks (127 small, 10 large)
- Created 2 parsing tools (214 + 159 = 373 lines)

**Remaining:**
- Decode array meanings (strength, coordinates, types)
- Locate supply/inventory data (127 small blocks)
- Analyze 10 large blocks (31-69 bytes)
- Determine first block purpose (header vs Target 0)
- Validate with multiple campaign files

**Estimated completion for campaign files:** 60-70% (2-3 more hours)
