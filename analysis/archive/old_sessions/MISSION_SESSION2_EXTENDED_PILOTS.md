# Mission System Session 2: Extended Pilot Records

**Date:** November 11, 2026  
**Focus:** Decode "supply data" block at end of squadron files  
**Status:** COMPLETE - Extended pilot record structure fully decoded

---

## Summary

Successfully decoded the final 663 bytes (0x7F8-0xA8E) of squadron files, previously labeled as "supply data" in Strategic Falcon documentation. This block actually contains **extended data for the last 10 pilots** (indices 20-29), not supply/inventory information.

## Key Findings

### 1. File Structure Corrected

**Previous understanding (from Strategic Falcon docs):**
- Header: 60 bytes
- Pilots: 30 × 66 bytes = 1,980 bytes
- Supply data: 663 bytes (weapons, fuel, aircraft count)

**Actual structure:**
- Header: 60 bytes (0x00-0x3B)
- Main pilot records: 30 × 66 bytes (0x3C-0x7F7)
- **Extended pilot records: 10 × 66 bytes (0x7F8-0xA8B)**
- Footer: 3 bytes (0xA8C-0xA8E)

### 2. Extended Pilot Record Format

Each extended record is 66 bytes:

```
Offset | Size | Description
-------|------|--------------------------------------------------
+0x00  |  1   | Marker (always 0xFF)
+0x01  |  1   | Pilot index (0x1D=29 down to 0x14=20, counts down)
+0x02  |  1   | Status flags (0x00 or 0x01)
+0x03  | 15   | Callsign (null-terminated, duplicates main record)
+0x12  |  1   | Padding (0x00)
+0x13  | 15   | Nickname (null-terminated, duplicates main record)
+0x22  |  1   | Padding (0x00)
+0x23  |  4   | Pilot ID (4 chars, duplicates main record)
+0x27  | 14   | Extended state (mission-specific data)
+0x35  | 13   | Separator (all zeros)
```

### 3. Extended State Field (+0x27, 14 bytes)

In fresh squadron files, the extended_state field is mostly zeros except for an FF FF marker at the end:
- Bytes 0-11: 0x00
- Bytes 12-13: 0xFF 0xFF

**Purpose (inferred):** Runtime mission state that gets populated during gameplay:
- Current aircraft assignment (which of 18 F-16s is this pilot flying?)
- Mission status (available, flying, returning, KIA, MIA, POW)
- Current kills/score for this mission
- Combat damage/status
- Fuel remaining
- Weapons remaining

### 4. Why Only 10 Pilots?

Falcon 3.0 supports up to **10 simultaneous flights** in a single mission (player + 9 AI flights). The extended records track the 10 pilots currently assigned to active flight slots.

The pilot_index field (byte +0x01) shows these are the **last 10 pilots** in the squadron roster:
- Record 0: Pilot 29 (0x1D)
- Record 1: Pilot 28 (0x1C)
- Record 2: Pilot 27 (0x1B)
- ...
- Record 9: Pilot 20 (0x14)

This suggests the game assigns pilots from the end of the roster first, or these slots represent specific roles (wingmen, other flights).

### 5. File Footer

3 bytes at the very end (0xA8C-0xA8E): **FF 1E 00**

The 0x1E (30 decimal) likely represents the total pilot count, serving as a file integrity marker.

---

## Evidence

**File analyzed:** game/SQUAD0.SQU (2,703 bytes)

**All 10 extended records successfully parsed:**

```
Record 0 @ 0x07F8: Pilot 29 (0x1D), GATTERA/DAFFY, ID:52515064
Record 1 @ 0x083A: Pilot 28 (0x1C), EISENBERG/DRACULA, ID:52595664
Record 2 @ 0x087C: Pilot 27 (0x1B), OLIVEIRA/MOTOWN, ID:4D4F5864
Record 3 @ 0x08BE: Pilot 26 (0x1A), JONES/SCAVENGER, ID:58504C64
Record 4 @ 0x0900: Pilot 25 (0x19), SAUNDERS/GROMMET, ID:584F5564
Record 5 @ 0x0942: Pilot 24 (0x18), LEWIS/ROCKY, ID:45595364
Record 6 @ 0x0984: Pilot 23 (0x17), YETZER/SUZUKI, ID:41525564
Record 7 @ 0x09C6: Pilot 22 (0x16), ELMORE/BUZZ, ID:46445964
Record 8 @ 0x0A08: Pilot 21 (0x15), TRAUGER/FATMAN, ID:50485064, status=0x01
Record 9 @ 0x0A4A: Pilot 20 (0x14), VITALE/EXCALIBUR, ID:48435164, status=0x01
```

**Pattern confirmation:**
- 10 records × 66 bytes = 660 bytes
- Footer: 3 bytes
- Total: 663 bytes ✓

---

## Implications for Supply Data

The Strategic Falcon documentation mentions "supply data" (ammunition, fuel, aircraft count) should be in .SQU files. Our analysis proves this section contains **pilot data**, not supply data.

**Where is the supply data?**

Most likely in the **.CAM (campaign) file** (11,828 bytes):
- Aircraft inventory (which of 18 F-16s are operational?)
- Weapons stockpile (AIM-9s, AIM-120s, bombs, etc.)
- Fuel reserves
- Campaign day counter
- Strategic target status

This makes architectural sense: campaign-wide resources belong in the campaign file, while pilot-specific data belongs in the squadron file.

---

## Tools Created

### parse_extended_pilots.py (189 lines)

Parses all 10 extended pilot records from a squadron file and displays:
- Header bytes (marker, pilot index, status)
- Callsign and nickname (duplicated from main record)
- Pilot ID (duplicated from main record)
- Extended state bytes (hex dump)
- Separator bytes

**Usage:**
```bash
python parse_extended_pilots.py ../game/SQUAD0.SQU
```

### analyze_supply2.py (87 lines)

Hex pattern analysis tool that helped identify:
- FF FF marker patterns (record boundaries)
- Actual record spacing (66 bytes)
- Text string locations
- Structure alignment

---

## Next Steps

1. **Verify extended state usage:**
   - Load a saved game mid-campaign
   - Parse extended pilot records
   - Check if extended_state field has non-zero data
   - Correlate with pilot missions/status

2. **Decode .CAM file structure:**
   - Parse 11,828 byte campaign file
   - Locate aircraft inventory section
   - Locate weapons stockpile section
   - Find strategic target array

3. **Cross-reference with game code:**
   - Search for "SQUAD" string references (file loading)
   - Find squadron file read routines
   - Locate extended pilot record usage
   - Identify which functions update extended_state during missions

4. **Compare all 6 squadron files:**
   - SQUAD0.SQU through SQUAD5.SQU
   - Check if extended records differ between saves
   - Look for active vs. inactive squadron patterns

---

## Session Statistics

- **Time:** ~1.5 hours
- **Files analyzed:** 1 (SQUAD0.SQU)
- **Bytes decoded:** 663 (extended pilot block)
- **Tools created:** 3 (analyze_supply.py, analyze_supply2.py, parse_extended_pilots.py)
- **Structure confirmed:** Extended pilot record (66 bytes × 10)
- **Documentation updated:** docs/architecture/mission_campaign.md

**Completion estimate:**
- Squadron file format: **95% complete** (only extended_state field details remaining)
- Overall mission system: **35% complete** (need .CAM, .MIS, and code analysis)
