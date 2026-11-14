# ISLDAT Binary Format Analysis

## File Information

**Filename**: ISLDAT.ISR (Israel theater)  
**Size**: 6,787 bytes  
**Purpose**: Theater coastline/terrain vector data

## Binary Format Header (First 256 bytes)

### Hex Dump
```
Offset  Hex Data
------  --------
0x0000: 7A 1A 00 00 00 05 4E 07 00 00 00 00 00 00 00 00
0x0010: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0x0020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0x0030: 00 00 00 00 00 00 00 00 00 00 00 00 01 01 00 05
0x0040: 06 0A 0B 00 00 00 00 00 00 00 00 00 01 02 03 05
0x0050: 07 09 0C 00 31 31 31 00 00 00 00 00 00 02 04 00
0x0060: 08 08 08 00 31 31 31 00 00 00 00 00 00 00 00 00
0x0070: 0D 0D 0D 00 00 00 00 00 00 00 00 00 00 00 00 00
0x0080: 0E 0E 0E 00 00 00 00 00 00 00 00 00 00 00 00 00
0x0090: 11 0F 0F 10 00 00 00 00 00 00 00 00 00 00 00 00
0x00A0: 12 13 13 00 00 00 00 00 00 00 00 00 00 00 00 00
0x00B0: 14 15 16 17 00 00 00 00 00 00 00 00 00 21 20 1F
0x00C0: 1D 1B 1A 18 00 00 00 00 00 00 00 00 00 21 20 1F
0x00D0: 1E 1C 19 18 00 00 00 00 00 00 00 00 00 00 00 00
```

## Header Structure Analysis

### Bytes 0x00-0x01: Magic Number
```
0x7A 0x1A = 31,258 decimal
```
**Purpose**: File format identifier ("ISLDAT" magic)

**Verification**: This should be checked by loader to validate file format

### Bytes 0x02-0x05: Header Fields
```
0x00 0x00 = Version? (0)
0x00 0x05 = Count/Index? (5)
```

### Bytes 0x06-0x07: Data Size?
```
0x4E 0x07 = 0x074E = 1,870 decimal
```
**Possible**: Size of vector data section in bytes

### Bytes 0x08-0x3F: Reserved/Padding
All zeros - likely reserved for future use or alignment

### Bytes 0x40-0xFF: Index/Offset Table
```
Pattern observed:
0x3A-0x3F: 01 01 00 05 06 0A 0B
0x4A-0x4F: 01 02 03 05 07 09 0C
0x50-0x52: 31 31 31 (ASCII '111')
0x5A-0x5C: 02 04 00
0x60-0x62: 08 08 08
0x64-0x66: 31 31 31 (ASCII '111')
...
```

**Hypothesis**: This is an **index table** or **offset array** pointing to vector segments

**Pattern Analysis**:
- Appears to be grouped in 16-byte blocks
- Some blocks contain indices (01, 02, 03...)
- Some blocks contain ASCII '111' (0x31 = '1')
- Some blocks have triplets (08 08 08, 0D 0D 0D, 0E 0E 0E)

**Possible Interpretation**:
- Each block = one coastline segment descriptor
- Format: [start_index] [end_index] [flags] [padding]

### Bytes 0xB0-0xCF: Large Index Values
```
0xB0: 14 15 16 17 = Indices 20-23
0xBF: 21 20 1F 1D 1B 1A 18 = Indices 33, 32, 31, 29, 27, 26, 24
0xCF: 21 20 1F 1E 1C 19 18 = Indices 33, 32, 31, 30, 28, 25, 24
```

**Note**: Indices up to 0x21 (33) observed

**Hypothesis**: This section defines **polyline chains** - sequences of point indices that form coastlines

## Data Section (After Header)

**Location**: Starts at offset 0x100 (256 bytes)?

**Expected Contents**:
1. **Point Array**: X,Y coordinate pairs for all vector points
2. **Polyline Definitions**: Lists of point indices forming lines
3. **Segment Types**: Coastline vs road vs river flags

## Comparison with JSON Analysis Files

### From ISR.json (Modern Analysis Format):
```json
{
  "coastlines": [
    {
      "type": "closed",
      "points": [[x1,y1], [x2,y2], ...]
    }
  ]
}
```

**Mapping to Binary**:
- JSON "points" array → Binary point array @ offset 0x100+
- JSON "type" field → Binary flags in index table
- JSON structure → Binary index table entries

## File Size Analysis

**Total File Size**: 6,787 bytes  
**Header Size**: ~256 bytes  
**Data Size**: ~6,531 bytes

**Point Count Estimate**:
- If 33 points (0x21 max index seen)
- Each point = 4 bytes (2 WORDs: X, Y)
- 33 × 4 = 132 bytes for points

**Remaining**: 6,531 - 132 = 6,399 bytes

**Interpretation**: Most of file is polyline definitions and segment data, not just points

## Proposed Binary Structure

```c
struct ISLDAT_Header {
    WORD magic;              // 0x00: 0x1A7A ("ISLDAT" identifier)
    WORD version;            // 0x02: 0x0000 (version 0)
    WORD segment_count;      // 0x04: Number of coastline segments
    WORD data_size;          // 0x06: Size of data section
    BYTE reserved[56];       // 0x08-0x3F: Reserved/padding
    BYTE index_table[192];   // 0x40-0xFF: Segment index table
};

struct ISLDAT_Point {
    SWORD x;                 // X coordinate (signed)
    SWORD y;                 // Y coordinate (signed)
};

struct ISLDAT_Segment {
    BYTE point_count;        // Number of points in this segment
    BYTE flags;              // Type: 0=coast, 1=road, 2=river?
    WORD first_point;        // Index of first point
    WORD reserved;
};

struct ISLDAT_File {
    ISLDAT_Header header;
    ISLDAT_Segment segments[segment_count];
    ISLDAT_Point points[total_point_count];
};
```

## Verification Needed

To confirm this structure, we need to:

1. **Find the loader code** in FALCONCD.EXE
   - Look for:
     - File open with "ISLDAT" string
     - Magic number check (0x1A7A or 0x7A1A)
     - Reading into segment 0x62D4 (vector data segment)

2. **Analyze more theater files**
   - Compare ISLDAT.ISR with ISLDAT.KOR, etc.
   - Check if header format is consistent
   - Verify point count and data size fields

3. **Trace rendering**
   - Confirm how segment index table is used
   - Verify point array access patterns
   - Check flag interpretation

## Connection to Rendering Code

**From Previous Analysis**:
- Vector data loaded into **segment 0x62D4**
- Vector count at **0x62D6A**
- Vector array starts at **0x6266**

**Loader Must**:
1. Read ISLDAT.ISR file
2. Parse header
3. Allocate memory in segment 0x62D4
4. Copy points to vector array (16 bytes each, includes projection space)
5. Build polyline structures from index table
6. Store count at 0x62D6A

## Next Steps

1. Find ISLDAT loader in FALCONCD.EXE (search in progress)
2. Disassemble loader to understand exact format
3. Create structure definitions for IDA
4. Document complete file format
5. Write parser/converter tool

---

*Analysis Status*: Format partially understood, loader not yet found  
*Confidence*: 60% on header structure, 40% on data layout  
*Blocker*: Need to find loader code to confirm
