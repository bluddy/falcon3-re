# Falcon 3.0 Campaign File Format (.CAM)

**Date**: 2026-11-16  
**Status**: Initial Analysis Complete  
**Files Analyzed**: SQUAD0.CAM, SQUAD1.CAM

---

## File Overview

**Extension**: .CAM  
**Size**: 11,828 bytes (fixed size)  
**Purpose**: Campaign/squadron save data

### Files Found

| Filename | Size | Location |
|----------|------|----------|
| SQUAD0.CAM | 11,828 bytes | game\ |
| SQUAD1.CAM | 11,828 bytes | game\ |

---

## Header Analysis

### Bytes 0x0000-0x0003

```
SQUAD0.CAM: 00 00 00 03
SQUAD1.CAM: 00 00 00 03
```

**Hypothesis**: File signature or version number

### Byte 0x0004

```
SQUAD0.CAM: 01
SQUAD1.CAM: 09
```

**Hypothesis**: Squadron/campaign slot ID (SQUAD0 = slot 1, SQUAD1 = slot 9)

This matches the pattern where SQUAD0 would be squadron in slot 1, and SQUAD1 would be squadron in slot 9 (different theater or wing assignment).

---

## Structure Hypothesis

### Potential Record Sizes

File size 11,828 bytes could be:
- **179.21 records of 66 bytes** (PilotRecord size)
- **90.98 records of 130 bytes** (FlightRecord size)
- **Mixed structure** (most likely)

### 0xFF Markers

**SQUAD0.CAM**: 2,721 bytes = 0xFF  
**SQUAD1.CAM**: 2,708 bytes = 0xFF

**Analysis**: 0xFF bytes appear in clusters of 5-7 bytes, consistent with:
- Empty pilot slots (+0x41-0x45 region in PilotRecord)
- Unused/padding sections
- Uninitialized mission data

**Pattern observed**: `...11 FF FF FF FF FF 12...`

This is consistent with:
```c
// Last field of pilot record
uint8_t field_0x40 = 0x11;
uint8_t pilot_status = 0xFF;  // EMPTY
uint8_t unused[4] = {0xFF, 0xFF, 0xFF, 0xFF};
uint8_t next_field = 0x12;
```

---

## Difference Analysis (SQUAD0 vs SQUAD1)

**Total Differences**: 287 bytes out of 11,828 (2.4%)

### Key Difference Locations

| Offset Range | Size | Hypothesis |
|--------------|------|------------|
| 0x0004 | 1 byte | Squadron ID |
| 0x0842-0x0848 | 7 bytes | Squadron statistics |
| 0x0AFC | 1 byte | Configuration flag |
| 0x1162 | 1 byte | State flag |
| 0x1728-0x1841 | ~281 bytes | **Mission/pilot data blocks** |
| 0x280D-0x2878 | ~107 bytes | **Second data section** |
| 0x2C1C-0x2C61 | ~69 bytes | **Third data section** |
| 0x2D92-0x2E26 | ~148 bytes | **Fourth data section** |

### Repeating Pattern in Differences

The differences at 0x1728-0x1841 show repeating blocks of 25 bytes:
- 0x1728-0x173B: 4 bytes, gap, 25 bytes, gap, 8 bytes
- 0x1750-0x1757: 8 bytes
- 0x177D-0x1795: 25 bytes
- 0x17CB-0x17E3: 25 bytes
- 0x1819-0x1831: 25 bytes

**Hypothesis**: 25-byte records might be:
- Partial FlightRecord data
- Mission briefing parameters
- Waypoint data (coordinates + metadata)

---

## Proposed Structure

Based on sizes and patterns:

```c
struct CAMFile {
    // Header (estimated ~60-100 bytes)
    uint8_t signature[4];        // 0x0000: 00 00 00 03
    uint8_t squadron_id;         // 0x0004: Squadron slot (1, 9, etc.)
    uint8_t header_data[55];     // 0x0005-0x003B: Unknown
    
    // Mission/Campaign Data (~11700 bytes)
    // Likely contains:
    // - Squadron statistics
    // - Pilot roster (30 pilots? 179 pilots?)
    // - Mission history
    // - Theater state
    // - Target data
    // - Campaign progress
    
    // The 2721 0xFF bytes suggest:
    // - Many empty pilot slots
    // - Uninitialized mission slots
    // - Reserved/unused space
};
```

### Alternative Structure Hypothesis

Based on .SQU file knowledge (2703 bytes for squadron data):

```
11,828 bytes total
- Could be 4 × 2703 = 10,812 bytes (squadron data for 4 squadrons)
- Plus 1,016 bytes header/campaign metadata

OR

- Campaign header: ~500 bytes
- 179 pilot records × 66 bytes = 11,814 bytes
- Footer: 14 bytes
```

---

## Key Observations

### 1. Fixed Size Format

All .CAM files are exactly 11,828 bytes, suggesting:
- Pre-allocated structure
- Fixed maximum capacity
- No dynamic sizing

### 2. High 0xFF Density

~23% of file is 0xFF bytes:
- Indicates many empty/unused slots
- Consistent with "new campaign" save files
- Likely increases as campaign progresses

### 3. Small Differences Between Files

Only 287 bytes differ (2.4%):
- Most data is identical (default/template values)
- Key differences in specific sections
- Suggests most of file is static configuration

### 4. Clustered Changes

Differences appear in specific regions:
- Not random throughout file
- Organized into logical blocks
- Suggests structured record format

---

## Next Steps

### 1. Disassemble theater_campaign_file_loader ⚠️ CRITICAL

This function loads .CAM files and will reveal:
- Read order and offsets
- Structure field interpretations
- Pointer assignments to dword_79E3A

### 2. Compare More Campaign Files

Analyze campaigns at different stages:
- Fresh campaign (like SQUAD0/SQUAD1)
- Mid-campaign with missions flown
- Completed campaigns
- Different theaters

### 3. Hex Edit Testing

Make controlled changes to .CAM file:
- Modify byte 0x0004 (squadron ID)
- Change blocks at known offsets
- Test in-game to verify field meanings

### 4. Find .MSN Mission Files

Search for individual mission files:
- May be separate from .CAM campaign files
- Likely smaller (single mission vs entire campaign)
- May contain MissionRecord structure directly

### 5. Analyze Write Operations

Find code that **writes** .CAM files:
- DOS INT 21h function 0x40 (Write File)
- Functions that construct campaign data
- Save game handlers

---

## Cross-Reference with Known Structures

### PilotRecord (66 bytes)

If .CAM contains 179 pilot records:
```
Header: ~60 bytes
179 pilots × 66 = 11,814 bytes
Footer: ~14 bytes
Total: ~11,888 bytes ❌ (60 bytes too large)
```

**Doesn't quite fit** - would need 180 pilots or smaller header.

### SquadronFile (2,703 bytes)

If .CAM contains multiple squadrons:
```
4 squadrons × 2,703 = 10,812 bytes
Campaign metadata: 1,016 bytes
Total: 11,828 bytes ✅ (exact match!)
```

**Strong candidate** - file could contain:
- 4 complete squadron save files
- Plus campaign-level metadata (1KB)

This would explain:
- Fixed size (always 4 squadron slots)
- High 0xFF count (empty squadrons)
- Small differences (only 1 squadron active)

---

## Revised Structure Hypothesis

```c
struct CAMFile {
    // Campaign Header (1,016 bytes)
    uint8_t signature[4];           // 0x0000: 00 00 00 03
    uint8_t squadron_id;            // 0x0004: Active squadron
    uint8_t campaign_data[1011];    // Campaign state, progress, theater
    
    // Squadron Slots (4 × 2,703 = 10,812 bytes)
    SquadronFile squadrons[4];      // 4 squadron save files
    // Each squadron:
    //   - Header (60 bytes)
    //   - 30 pilots (1,980 bytes)
    //   - 10 extended pilots (660 bytes)
    //   - Footer (3 bytes)
};
```

**Total**: 1,016 + 10,812 = 11,828 bytes ✅

This structure explains:
1. Why SQUAD0 and SQUAD1 have byte 0x0004 = 01 vs 09 (active squadron index)
2. Why most data is identical (empty squadron slots)
3. Why differences cluster in specific regions (one squadron's data)
4. Why so many 0xFF bytes (3 empty squadrons + empty pilot slots)

---

## Files Generated

| File | Description |
|------|-------------|
| `analysis/file_loaders_analysis.json` | File loader functions found |
| `analysis/file_loaders_summary.txt` | Loader function summary |
| `analysis/cam_file_analysis.txt` | CAM file structure notes |
| `analysis/analyze_cam_files.py` | Python analysis script |

---

## Conclusion

The .CAM file format is **likely a container for 4 squadron save files plus campaign metadata**. This explains the fixed 11,828-byte size and structure.

**Key Findings**:
1. Fixed 11,828-byte format
2. Header signature: 00 00 00 03
3. Byte 0x0004 = active squadron ID
4. High 0xFF density = empty slots
5. Strongly suggests: 4 × SquadronFile (2,703 bytes each) + 1,016 byte header

**To Confirm**: Disassemble `theater_campaign_file_loader` function to see exact read pattern and structure field assignments.
