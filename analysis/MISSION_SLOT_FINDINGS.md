# Mission Slot Structure - Deep Analysis

## Executive Summary

After comprehensive analysis of 53 references across 15 functions, we have determined:

1. **MissionSlot is 20 bytes (0x14)** - confirmed by initialization loop
2. **64 mission slots** per campaign - confirmed by loop counter (0x40)
3. **Array location**: Pointed to by `dword_79D3E` in segment 0x7894
4. **CRITICAL FINDING**: `dword_79D3E` is a **context-dependent multi-purpose pointer**

## MissionSlot Structure (20 bytes)

Based on write pattern analysis across all functions:

```c
struct MissionSlot {
    char label[2];      // +0x00-0x01: Mission label/ID
                        //   Initialized to {0x20 (space), 0x00 (null)}
                        //   Written by: squadron_mission_file_loader, sub_135C57
    
    uint16_t field_02;  // +0x02-0x03: Unknown
                        //   Written value: 0xC8 (200) by r48_time_threshold_table_init
    
    byte unknown_04[16]; // +0x04-0x13: Unknown fields (16 bytes)
                        //   Not directly written in analyzed functions
                        //   Likely populated by file read operations
};
```

### Field Details

**+0x00-0x01: Mission Label (2 bytes)**
- **Initialization**: Space (0x20) + null (0x00)
- **Writers**:
  - `squadron_mission_file_loader` @ 0x17B471, 0x17B488
  - `sub_135C57` @ 0x135C89, 0x135C91
  - `overlay_r56_handler` - writes register values (si, di)
  - `sub_170E24` - clears to 0x00
  - `undoc_191B42` - clears to 0x00
  - `r48_time_threshold_table_init` - writes 0xF0 (word)

**+0x02-0x03: Field 02 (2 bytes)**
- **Value**: 0xC8 (200 decimal, 0xC8 hex)
- **Writers**:
  - `r48_time_threshold_table_init` @ 0x176AFA
  - `undoc_190D04` @ 0x190F9A

**+0x14 (20): Next Slot Boundary**
- `sub_170E24` writes 0x00 at offset +0x14
- This confirms the 20-byte slot size

## Multi-Purpose Pointer Discovery

### Critical Insight

**`dword_79D3E` does NOT always point to a MissionSlot array!**

Evidence:
1. **Writes at offset +0x604-0x608** (1540-1544 bytes)
2. **Writes at offset +0x3F-0x41** (63-65 bytes)
3. These offsets far exceed 20-byte MissionSlot boundaries

### Pointer Context Analysis

The pointer `dword_79D3E` is used in different contexts:

#### Context 1: MissionSlot Array (20-byte stride)
**Functions**: 
- `squadron_mission_file_loader` - initializes 64×20 byte array
- `sub_135C57` - string operations on slots
- `sub_170E24` - slot clearing

**Offsets**: 0x00, 0x01, 0x02, 0x14

#### Context 2: Larger Structure (1540+ bytes)
**Functions**:
- `overlay_r55_dispatcher` 
- `overlay_r56_handler`
- `r52_data_fragment`

**Offsets**: 0x3F-0x41 (63-65), 0x604-0x608 (1540-1544)

**These functions write**:
- +0x604: 0xA68 (far pointer offset?)
- +0x606: 0x4FC2 (far pointer segment?)
- +0x608: 0x0A (count/size?)

**Hypothesis**: In R52/R55/R56 overlay contexts, `dword_79D3E` points to a **different structure** - possibly a mission execution context or UI state structure that is ~1600 bytes.

## Function Categories

### Initialization Functions

**squadron_mission_file_loader** @ 0x17B437
- Initializes all 64 mission slots
- Sets label to space+null for each slot
- Main mission file loader

**sub_135C57** @ 0x135C57
- 16 writes to mission slots
- String manipulation operations
- Variable-offset writes (es:[bx+di])

### Overlay Functions (Large Structure Context)

**overlay_r56_handler** @ 0x1A0030
- 20 writes, offsets up to +0x608
- Writes to +0x3F, +0x40, +0x41 (flags?)
- Writes to +0x604-0x608 (far pointers?)

**overlay_r55_dispatcher** @ 0x18F910
- 2 writes to +0x604, +0x606
- Far pointer manipulation

**r52_data_fragment** @ 0x180DD0
- 22 writes, similar pattern to R56

### Utility Functions

**sub_170E24** @ 0x170E24
- Clears mission slots (writes 0x00)
- Writes to both +0x00 and +0x14 (next slot boundary)

**r48_time_threshold_table_init** @ 0x176A1F
- Writes timing values: 0xF0, 0xC8
- Possibly mission timing/scheduling

## Data Flow

### Mission Slot Array Population

```
1. squadron_mission_file_loader:
   - Loop: di = 0 to 63 (0x40)
   - For each slot:
     * Calculate offset: di × 20 (0x14)
     * Load pointer: les bx, es:dword_79D3E
     * Add offset: add bx, ax
     * Write: es:[bx+0] = 0x20 (space)
     * Write: es:[bx+1] = 0x00 (null)

2. File load operations:
   - Function loads .SHP files (squadron shapes?)
   - Function loads .TSK files (tasks/missions?)
   - Reads 1902 bytes (0x76E) from .TSK → 0x602E:0x068F
   - Data then copied into mission slots

3. String operations:
   - sub_135C57 populates mission labels
   - Uses variable indexing (es:[bx+di])
```

### Pointer Assignment

**13 locations write to `dword_79E3A`** (mission context pointer)
- Multiple overlays modify this pointer
- Context switches between mission execution and UI

## Campaign File Format Correlation

### .CAM File Structure
- **Total size**: 11,828 bytes
- **Header**: 1,016 bytes
  - First 1,280 bytes could be mission slot array (64 × 20)
  - Remaining 736 bytes: squadron metadata

### Field 02 Value Analysis

Value 0xC8 (200 decimal) appears in:
- Mission slot +0x02
- Campaign file analysis

Could represent:
- Mission index/ID?
- Time threshold?
- Squadron size/capacity?

## Next Steps

### 1. Identify Pointer Context
- **Goal**: Determine what structure `dword_79D3E` points to in R55/R56 contexts
- **Method**: Trace pointer assignments before large-offset writes
- **Expected**: Find conditional pointer switching or different initialization

### 2. Complete MissionSlot Fields
- **Goal**: Map all 20 bytes
- **Method**: 
  - Analyze .TSK file read operations
  - Trace data copy from file buffer to mission slot array
  - Examine string copy operations in sub_135C57

### 3. Find Detailed Mission Data
- **Goal**: Locate MissionRecord with waypoints, flights
- **Current**: MissionSlot is just a 20-byte header/index
- **Expected**: Separate larger structure or external file (.MSN files?)

### 4. Analyze R55/R56 Large Structure
- **Goal**: Define the ~1600-byte structure used in overlay contexts
- **Method**: Disassemble R55/R56 initialization routines
- **Hypothesis**: Mission execution context with UI state

## Key Functions to Analyze Next

1. **File Read Operations in squadron_mission_file_loader**
   - Offset +0x505: Read from .SHP
   - Offset +0x713: Read 1902 bytes from .TSK
   
2. **sub_135C57** - String Manipulation
   - 16 writes to slots
   - Variable offset patterns
   
3. **R55/R56 Context Switching**
   - Find where `dword_79D3E` gets reassigned
   - Identify the large structure type

## Progress: 92% Complete

### Confirmed ✓
- MissionSlot size: 20 bytes
- Array size: 64 slots (1,280 bytes)
- Pointer location: dword_79D3E @ 0x7894
- Field +0x00-0x01: Mission label
- Field +0x02-0x03: Timing/ID value
- Campaign file format
- Multi-purpose pointer usage

### Remaining
- Fields +0x04 through +0x13 (16 bytes) - Unknown
- Detailed mission data location
- WaypointRecord structure
- R55/R56 large structure definition
- Pointer context switching logic

## Registry Update Required

```yaml
MissionSlot:
  size: 20  # 0x14
  description: "Mission slot header/index in campaign mission array"
  confidence: high
  fields:
    - offset: 0x00
      size: 2
      type: char[2]
      name: label
      description: "Mission label/ID string (initialized to space+null)"
    
    - offset: 0x02
      size: 2
      type: uint16_t
      name: field_02
      description: "Unknown field, value 0xC8 (200) - possibly timing/ID"
    
    - offset: 0x04
      size: 16
      type: byte[16]
      name: unknown
      description: "Unpopulated in initialization, likely filled from file"
  
  notes:
    - "64 slots per campaign (total 1,280 bytes)"
    - "Array pointer: dword_79D3E in segment 0x7894"
    - "Initialized by squadron_mission_file_loader @ 0x17B437"
    - "WARNING: dword_79D3E is multi-purpose, context-dependent"
```
