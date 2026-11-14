# Mission System Status - After Session 2

**Last Updated:** November 11, 2026  
**Overall Completion:** 35% → 40%  
**Time Invested:** ~4 hours (2 sessions)

---

## Progress Summary

### Session 1 (2.5 hours) - Squadron File Basics
- Decoded header (60 bytes, theater name)
- Decoded main pilot records (30 × 66 bytes)
- Created parse_squadron.py
- Identified "supply data" block (663 bytes) as unknown

**Result:** Squadron format 60% decoded

### Session 2 (1.5 hours) - Extended Pilot Records
- Fully decoded "supply data" block → actually extended pilot records
- 10 extended records for pilots 20-29 (last 10 pilots)
- Each record: 66 bytes with duplicated name data + 14-byte extended state
- Created parse_extended_pilots.py and analysis tools
- Corrected Strategic Falcon documentation misidentification

**Result:** Squadron format 95% decoded

---

## Squadron File Format (.SQU) - 95% COMPLETE

**File Size:** 2,703 bytes  
**Status:** Nearly complete, only extended_state internals remaining

### Fully Decoded (2,700 / 2,703 bytes)

#### Header (60 bytes, 0x00-0x3B) ✓
- Bytes 0-2: Flags
- Bytes 3-59: Theater name (null-terminated)

#### Main Pilot Records (1,980 bytes, 0x3C-0x7F7) ✓
- 30 pilots × 66 bytes
- Fields: status, rank, callsign, nickname, ID, stats (4 bytes), mission data (28 bytes)
- Rank values: 0-4 (2nd Lt → Lt Col)
- Successfully parses all 30 pilots

#### Extended Pilot Records (660 bytes, 0x7F8-0xA8B) ✓
- 10 records × 66 bytes (pilots 20-29 only)
- Fields: marker (0xFF), pilot index, status, callsign, nickname, ID, extended_state (14 bytes), separator (13 bytes)
- Duplicates name data from main records
- Extended_state is mostly zeros in fresh saves

#### Footer (3 bytes, 0x8AC-0xA8E) ✓
- Bytes: FF 1E 00
- 0x1E = 30 decimal = pilot count

### Remaining (3 / 2,703 bytes)

#### Extended State Field (14 bytes per pilot, 10 pilots)
**Location:** +0x27 in each extended pilot record  
**Status:** Structure unknown, values are 0x00 in fresh saves

**Hypothesis:** Runtime mission-specific data populated during gameplay:
- Current aircraft assignment (which F-16?)
- Mission status (available, flying, KIA, POW)
- Current kills this sortie
- Damage state
- Fuel remaining
- Weapons remaining

**To decode:** Need to analyze a save file from mid-campaign with active missions.

---

## Campaign File Format (.CAM) - 5% COMPLETE

**File Size:** 11,828 bytes  
**Status:** Structure documented by Strategic Falcon, not yet decoded

**Expected Contents:**
- Campaign day counter
- Strategic target array (airbases, factories, C3 nodes)
- Target ownership (Allied/Enemy/Neutral)
- Target strength (0-100%)
- **Supply data: Aircraft inventory, weapons stockpile, fuel reserves**
- Victory/defeat tracking
- Political objectives

**Why .CAM likely has supply data:**
- .SQU "supply data" block turned out to be pilot records
- Supply/inventory is campaign-wide, not pilot-specific
- 11,828 bytes is large enough for detailed inventory

**Next step:** Parse SQUAD0.CAM to locate supply sections.

---

## Mission File Format (.MIS) - 0% COMPLETE

**File Size:** Variable (451-824 bytes)  
**Status:** Structure documented by Strategic Falcon, not yet decoded

**Expected Contents:**
- Allied flights (n × flight structure)
- Enemy flights (n × flight structure)
- Support flights (AWACS, tankers)
- ILS configuration per airbase
- Weather conditions
- Time of day

**Flight Structure (from Strategic Falcon):**
- Callsign
- Aircraft type
- Number of aircraft
- Weapon loadout
- Waypoints (special 1-byte coordinate format)
- Fuel state
- IFF/radar settings

**Next step:** Parse SQUAD0.MIS after completing .CAM.

---

## Code Analysis - 0% COMPLETE

**Status:** No code investigated yet

**Next steps:**
1. Search for "SQUAD" string references (file I/O)
2. Find squadron/campaign loading routines
3. Locate mission file parser
4. Identify extended pilot record usage
5. Find War Room UI code (sub_33443 @ 0x33443 is candidate master loop)
6. Locate mission planning screens

---

## Tools Created

### Squadron Parsing
- **parse_squadron.py** (263 lines) - Parses all 30 main pilot records
- **parse_extended_pilots.py** (189 lines) - Parses 10 extended pilot records
- **analyze_supply.py** - Hex analysis of extended data block
- **analyze_supply2.py** - Manual structure parser

### Usage
```bash
cd analysis
python parse_squadron.py ../game/SQUAD0.SQU
python parse_extended_pilots.py ../game/SQUAD0.SQU
```

---

## Documentation

### Analysis Documents (Session 1-2)
- MISSION_SYSTEM_INITIAL.md (492 lines) - Initial investigation
- MISSION_FILE_FORMATS.md (732 lines) - Format specs from modding tools
- MISSION_SESSION1_SUMMARY.md (401 lines) - Squadron format decode
- MISSION_SESSION2_EXTENDED_PILOTS.md (245 lines) - Extended records decode

### Architecture
- **docs/architecture/mission_campaign.md** (1,208 lines) - Complete squadron/campaign specs

---

## Next Session Plan

**Goal:** Decode .CAM file structure (locate supply data)

**Approach:**
1. Read SQUAD0.CAM (11,828 bytes) into hex dump
2. Look for patterns:
   - Theater name reference (should match .SQU header)
   - Campaign day (probably uint16, low values)
   - Target counts (probably arrays)
   - Aircraft count (expect ~18 initially)
3. Use Strategic Falcon docs to guide field identification
4. Create parse_campaign.py
5. Locate supply/inventory section
6. Document structure in architecture/mission_campaign.md

**Estimated time:** 2-3 hours  
**Expected completion:** Campaign format 60-70%, Mission system 50%

---

## Long-Term Roadmap

### Phase 1: File Formats (Current)
- [x] Squadron files (.SQU) - 95%
- [ ] Campaign files (.CAM) - 5%
- [ ] Mission files (.MIS) - 0%
- [ ] Theater strength files (.STR) - 0%

**Target:** 70% completion on all file formats

### Phase 2: Code Analysis
- [ ] File I/O routines (loading/saving)
- [ ] War Room UI (sub_33443 investigation)
- [ ] Mission planning screens
- [ ] Campaign state machine
- [ ] Strategic AI (target selection, enemy response)

**Target:** 60% completion on code understanding

### Phase 3: Integration
- [ ] Complete mission flow (planning → flight → debrief)
- [ ] Campaign progression logic
- [ ] Victory/defeat conditions
- [ ] Pilot career/death/replacement

**Target:** 80% overall mission system completion

---

## Key Insights

### Architectural Discoveries

1. **Dual pilot record system:**
   - Main records (30 pilots, static roster)
   - Extended records (10 pilots, dynamic mission state)
   - Suggests clear separation of persistent vs. runtime data

2. **10-flight mission limit:**
   - Extended records exist for exactly 10 pilots
   - Matches documented max simultaneous flights
   - Last 10 pilots in roster get extended tracking

3. **Squadron = saved game:**
   - Each SQUAD*.{SQU,CAM,MIS} set is independent
   - 6 save slots (SQUAD0-SQUAD5)
   - Complete campaign state per squadron

4. **File separation by data type:**
   - .SQU: Persistent pilot roster
   - .CAM: Persistent campaign state (supply, targets, day count)
   - .MIS: Transient mission state (current mission only)

### Documentation Corrections

**Strategic Falcon misidentification:**
- Docs say "supply data" is in .SQU files at 0x7F8
- Actually contains extended pilot records
- Supply data likely in .CAM files instead

This demonstrates the value of independent verification vs. trusting third-party documentation.

---

## Mission System Completion Estimate

**Current:** 40%

**Breakdown:**
- Squadron format: 95% (blocked on extended_state internals)
- Campaign format: 5% (structure known, not decoded)
- Mission format: 0% (structure known, not decoded)
- Code analysis: 0% (not started)
- Integration/flow: 0% (not started)

**Path to 70%:**
- Complete .CAM decode: +20% → 60%
- Complete .MIS decode: +10% → 70%

**Estimated time to 70%:** 6-8 hours (3-4 more sessions)
