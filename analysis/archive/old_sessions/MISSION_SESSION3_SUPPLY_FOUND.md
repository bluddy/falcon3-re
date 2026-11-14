# Mission Session 3: Supply Data Discovered!

**Date:** November 11, 2026  
**Major Milestone:** Located and decoded supply/inventory data in campaign files

---

## Critical Discovery

Found the **supply and inventory data** that was misidentified in Strategic Falcon documentation! The data is located at **offset 0x2D8E** in the .CAM file (near the end, after extensive space padding).

## Supply Data Structure

**Location:** 0x2D8E to end of file  
**Format:** uint16 array (little-endian)

### Decoded Fields

```
Offset | Size | Description                    | Example Value
-------|------|--------------------------------|---------------
+0x00  |  4   | Header/unknown                 | 00 00 00 00
+0x04  |  2   | Unknown value                  | 32931 (0x80A3)
+0x06  |  2   | Campaign flags                 | 1

=== WEAPON STOCKPILES ===
+0x08  |  2   | AIM-9 Sidewinder (IR missile)  | 258
+0x0A  |  2   | AIM-120 AMRAAM (radar missile) | 188
+0x0C  |  2   | AGM-65 Maverick (AG missile)   | 175
+0x0E  |  2   | AGM-88 HARM (anti-radar)       | 150
+0x10  |  2   | Mk-82 Bomb (500 lb)            | 150
+0x14  |  2   | Mk-84 Bomb (2000 lb)           | 250
+0x16  |  2   | CBU Cluster Bomb               | 200
+0x18  |  2   | Rockets/Other                  | 175

=== ADDITIONAL STORES ===
+0x12  |  2   | Secondary slot 1               | 302
+0x1A  |  2   | Secondary slot 2               | 150
+0x1C  |  2   | Secondary slot 3               | 250
+0x1E  |  2   | Secondary slot 4               | 232
+0x20  |  2   | Secondary slot 5               | 100
+0x22  |  2   | Secondary slot 6               | 100
+0x24  |  2   | Secondary slot 7               | 100
+0x26  |  2   | Secondary slot 8               | 100

=== FUEL ===
+0x28  |  2   | Fuel reserves value 1          | 6030
+0x2A  |  2   | Fuel reserves value 2          | 6030 (duplicate)

=== CAMPAIGN STATE ===
+0x2C  |  2   | Unknown counter                | 50
+0x2E  |  2   | Unknown value                  | 52407 (0xCCB7)
+0x30  |  2   | Campaign day?                  | 5
+0x32  |  2   | Small counter                  | 10

=== AIRCRAFT INVENTORY ===
+0x34  |  2   | F-16s Available                | 18 *** PRIMARY ***
+0x36  |  2   | Aircraft damaged/maintenance?  | 1
+0x38  |  2   | Pilots available?              | 9
+0x3A  |  2   | Unknown counter                | 9
+0x3C  |  2   | Unknown counter                | 6
+0x3E  |  2   | Flag/status                    | 1

+0x42  |  2   | Additional counter             | 4
```

### Example Values (SQUAD0.CAM)

**Squadron Starting Inventory:**
- **Aircraft:** 18 F-16s
- **AA Missiles:** 258 AIM-9 + 188 AIM-120 = 446 total
- **AG Missiles:** 175 Maverick + 150 HARM = 325 total
- **Bombs:** ~400 (various types)
- **Fuel:** 6,030 units (possibly gallons or pounds)

This represents a well-stocked squadron at campaign start.

---

## Why This Was Hard to Find

1. **Incorrect documentation:** Strategic Falcon docs said supply data was in .SQU files at 0x7F8. That location actually contains extended pilot records.

2. **Heavy padding:** The .CAM file has 5,590 bytes of final data, but the first ~4KB is all space characters (0x20), obscuring the actual data location.

3. **File structure:** Unlike the target array with clear 0xFF separators, the supply section is at the absolute end of the file with minimal markers.

---

## Additional Campaign State (0x2DCE+)

After the main supply data, there are more byte arrays:

```
0x2DFA: 1D 16 0C 06 02 12 0C 0C 0D F2  (10 bytes - unknown)
0x2E06: 01 00 00 39 FF                (5 bytes - flags/counters)
0x2E14: FF FF 04 03 FF                (5 bytes - more flags)
0x2E27: FF 03 1E 00 00 00 FF 0F       (8 bytes - campaign state?)
```

**Possible interpretations:**
- Victory/defeat condition tracking
- Strategic target capture counts
- Mission success/failure statistics
- Political state variables
- Daily casualty counts

**To decode:** Need to compare multiple campaign files at different campaign days or after significant events.

---

## Architecture Implications

### File Layout Summary

**Campaign File (.CAM) - 11,828 bytes:**

```
0x0000 - 0x185D   Strategic target array (24 large + 20+ small targets)
                  Heavy 0xFF padding between blocks
                  
0x185E - 0x2D8D   Space-padded section (~4KB of 0x20)
                  Purpose: Reserved text buffer or alignment
                  
0x2D8E - 0x2E33   Supply & Inventory data (~160 bytes)
                  - Weapon stockpiles (8+ types)
                  - Fuel reserves
                  - Aircraft counts
                  - Campaign state counters
                  - Additional flags/status bytes
```

### Why This Design?

**Space padding** suggests:
- Fixed allocation for potential text messages or campaign log
- Memory alignment for DOS/real-mode loading
- Room for future expansion in patches

**Placement at end** suggests:
- Supply data is read/written frequently (append-only optimization?)
- Targets are read once at campaign load, supply updated after each mission
- File I/O pattern: Load targets → skip padding → read supply

---

## Tools Created

### parse_supply_inventory.py (160 lines)

Complete supply/inventory parser with field mapping.

**Features:**
- Decodes all 8 weapon types
- Shows aircraft count and fuel
- Displays campaign state counters
- Summary statistics

**Usage:**
```bash
python parse_supply_inventory.py [camfile]
```

**Output:**
```
=== FALCON 3.0 SUPPLY & INVENTORY ===

Weapon Stockpiles:
  AIM-9 Sidewinder         :  258
  AIM-120 AMRAAM           :  188
  ...

Aircraft Inventory:
  F-16s Available:  18 *** PRIMARY AIRCRAFT COUNT ***
  
=== SUMMARY ===
Aircraft:         18 F-16s
AA Missiles:     ~446 (AIM-9 + AIM-120)
AG Missiles:     ~325 (Maverick + HARM)
Bombs:           ~400 (Mk-82 + Mk-84 approx)
Fuel:             6030 units
```

### decode_supply_data.py (140 lines)

Utility for finding and analyzing the supply section, including padding detection.

---

## Validation Needed

To confirm field interpretations:

1. **Play a campaign** and advance several days
2. **Fly missions** that expend weapons and fuel
3. **Lose aircraft** to see damage counters
4. **Compare .CAM files** before and after
5. **Look for field changes** that match gameplay events

Example predictions:
- Fly mission with 4 Sidewinders used → AIM-9 count decreases by 4
- Aircraft damaged → +0x36 counter increases
- Advance campaign day → +0x30 increments
- Fuel consumed → 0x28/0x2A values decrease

---

## Remaining Campaign File Mysteries

### 1. What is the 4KB space buffer? (0x185E - 0x2D8D)

**Hypothesis:** Campaign log or text message buffer
- Could store mission briefings
- Could store campaign events ("Target destroyed", "Aircraft lost")
- Could be historical data (previous mission results)

**To resolve:** Search for code that writes to this area, or find non-empty examples.

### 2. What are the secondary weapon slots? (+0x12, +0x1A-0x26)

8 additional weapon slots with values. Possibilities:
- Different weapon variants (AIM-9M vs AIM-9P)
- Spare parts / replacement stocks
- Allied squadron contributions
- Theater-wide inventory (not just player squadron)

### 3. Campaign state bytes after supply data

10-20 bytes of status data:
- Bytes like 0x1D, 0x16, 0x0C, 0x06 (29, 22, 12, 6)
- Could be target capture counts per type
- Could be mission counters (flown, successful, failed)
- Need comparison with progressed campaign

---

## Mission System Progress Update

| Component | Completion | Change | Notes |
|-----------|-----------|--------|-------|
| Squadron files (.SQU) | 95% | - | Extended state field internals remaining |
| Campaign files (.CAM) | 50% | +25% | Targets + supply decoded, state bytes remain |
| Mission files (.MIS) | 0% | - | Not started |
| Code analysis | 0% | - | Not started |
| **Overall Mission System** | **55%** | **+10%** | Major supply breakthrough |

**Time this session:** 2.5 hours  
**Total time (3 sessions):** ~8 hours

---

## Next Steps

### Immediate (complete campaign file)

1. **Decode remaining state bytes** (0x2DCE+)
   - Compare multiple campaign files
   - Match byte changes to game events

2. **Analyze first block** (0x0000-0x0049)
   - Is it a campaign header or Target ID 0?
   - Look for theater ID, player squadron ID

3. **Understand space buffer** (0x185E - 0x2D8D)
   - Search for code references
   - Check if it's ever used

### Follow-up (next session)

4. **Parse .MIS mission files**
   - Flight structures
   - Waypoints (1-byte coordinate format)
   - Weapon loadouts

5. **Cross-reference with code**
   - Search for ".CAM" string in IDA
   - Find file loading routines
   - Identify structure definitions

6. **Create complete campaign parser**
   - Combine target + supply parsers
   - Export to JSON for analysis
   - Enable campaign state tracking

---

## Key Takeaway

**The supply data was hidden in plain sight** at the end of the file, obscured by 4KB of space padding. This highlights the importance of:
- Examining entire files, not just documented sections
- Looking for patterns in unexpected places
- Validating third-party documentation with actual data

The mission system is now more than halfway decoded, with both critical file formats (squadron and campaign) largely understood!
