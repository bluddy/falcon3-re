# Mission Editing UI to File Format Connection

## Objective

Connect the mission editing UI code (where users modify waypoints, altitudes, tasks, aircraft counts) to the mission file format (.MIS files) and in-memory structures.

## What We Know

### 1. Mission File Format (.MIS) - Confirmed

**File Structure**:
```
+0x0000  Header (12 bytes)
+0x000C  Mission Records (6 bytes × N)
         [index][00][type][00][param][flags]
+0x????  Detail Section (variable)
         - Waypoint coordinates (21 bytes each)
         - Flight data
         - Extended parameters
```

### 2. Waypoint Format - Confirmed

**21-Byte Waypoint Record**:
```c
struct Waypoint {
    uint8_t  marker;          // +0x00: Always 0x01
    uint16_t x_coord;         // +0x01-0x02: X coordinate (16-bit)
    int16_t  marker_1;        // +0x03-0x04: Constant (-8 or -2)
    uint16_t y_coord;         // +0x05-0x06: Y coordinate (16-bit)
    int16_t  marker_2;        // +0x07-0x08: Constant (-12 or -9)
    uint16_t constant;        // +0x09-0x0A: Always 16 (0x0010)
    // Followed by 10-byte duplicate minus marker
};  // 11 + 10 = 21 bytes total
```

**Missing from waypoint record**:
- Altitude
- Speed
- Action code (TAKEOFF, CAP, BOMB, etc.)
- Target reference

**Hypothesis**: These are stored separately, possibly per-flight in the detail section.

### 3. Memory Structures - Confirmed

**MissionSlot (20 bytes)** @ `dword_79D3E`:
```c
struct MissionSlot {
    char     label[2];        // +0x00
    uint16_t field_02;        // +0x02: Value 0xC8
    uint8_t  mission_type;    // +0x04: MissionType enum
    uint8_t  flags;           // +0x05: 0x80/0x81
    uint8_t  parameter;       // +0x06
    uint8_t  extended[13];    // +0x07-0x13: Unknown
};
```

**FlightRecord (130 bytes)** @ `dword_79BEC`:
```c
struct FlightRecord {
    // Size confirmed from R57 weapons loadout analysis
    // 130 bytes (0x82)
    uint8_t  aircraft_count;  // Number of aircraft (1-4)
    // ... other fields unknown
    LoadoutRecord loadouts[4]; // 4 × 23 bytes = 92 bytes
    // ... remaining fields
};
```

**LoadoutRecord (23 bytes)**:
```c
struct LoadoutRecord {
    uint8_t  hardpoint_config[11]; // Weapon configuration
    uint16_t pilot_id;             // Assigned pilot
    // ... remaining fields
};
```

## Known Overlays

### R53: Mission Briefing (Confirmed)
- **Address**: 0x1820B0
- **Size**: 32KB
- **Purpose**: Display mission briefing, view mission data
- **Main Function**: `game_mode_r53_main_coordinator`
- **References**: Mission slots (read-only display)

### R55: Mission Management (Likely Editor)
- **Address**: 0x18F910 (`overlay_r55_dispatcher`)
- **Size**: Unknown
- **References**: `dword_79D3E` with large offsets (+0x604-0x608)
- **Hypothesis**: Mission editing and campaign management

### R56: Mission Execution (Likely Editor Helper)
- **Address**: 0x1A0030 (`overlay_r56_handler`)
- **References**: `dword_79D3E` with large offsets (+0x3F-0x41)
- **20 writes** to mission data structures
- **Hypothesis**: Mission parameter modification

### R54: Campaign Manager (Likely Related)
- **References**: 12 calls to cursor functions
- **Hypothesis**: Top-level campaign/mission management UI

## Connection Strategy

### Step 1: Identify Mission Editing Entry Points

**Expected UI Flow**:
```
Campaign Menu (R54?)
    ↓
Mission List/Selection
    ↓
Mission Editor (R55/R56)
    ↓ [User edits]
├─ Waypoint Editor
│   ├─ Add/Delete waypoint
│   ├─ Modify coordinates
│   ├─ Set altitude/speed
│   └─ Set action (CAP, BOMB, etc.)
├─ Flight Configuration
│   ├─ Number of aircraft (1-4)
│   ├─ Pilot assignment
│   └─ Loadout selection (R57)
└─ Mission Parameters
    ├─ Mission type
    ├─ Time of day
    └─ Weather
    ↓
Save to .MIS file
```

### Step 2: Trace Data Modifications

**Key Functions to Find**:

1. **Waypoint Add/Delete**:
   - Should manipulate array of 21-byte waypoint records
   - Update waypoint count
   - Recalculate file size

2. **Coordinate Modification**:
   - Read current X/Y from waypoint record
   - Allow user input (map click or numeric entry)
   - Write back to waypoint (+0x01-0x02, +0x05-0x06)

3. **Altitude/Speed Setting**:
   - Find where these are stored (not in waypoint record!)
   - Likely in flight plan section or separate array
   - Per-flight or per-waypoint?

4. **Action Code Assignment**:
   - Dropdown/menu selection
   - Write action code to unknown location
   - Link to waypoint or flight?

5. **Aircraft Count**:
   - Write to FlightRecord (+0x00)
   - Update loadout array size
   - Recalculate mission data

### Step 3: Find the Data Structures

**Search Patterns**:

1. **Look for 21-byte stride** in R55/R56:
   ```asm
   mov dx, 15h          ; 21 bytes
   imul dx              ; Waypoint index × 21
   ```

2. **Look for 130-byte stride** (FlightRecord):
   ```asm
   mov dx, 82h          ; 130 bytes
   imul dx              ; Flight index × 130
   ```

3. **Look for waypoint coordinate access**:
   ```asm
   ; Reading X coordinate
   mov al, es:[bx+1]    ; x_low
   mov ah, es:[bx+2]    ; x_high
   
   ; Reading Y coordinate  
   mov al, es:[bx+5]    ; y_low
   mov ah, es:[bx+6]    ; y_high
   ```

4. **Look for file save operations**:
   - DOS INT 21h, AH=40h (write file)
   - Buffer address with .MIS data
   - File handle from earlier open

## Known Code Locations

### File I/O
- **File Loader**: `squadron_mission_file_loader` @ 0x17B437
- **Read Operation**: Offset +0x713 (reads to buffer 0x602E:0x068F)
- **File Open**: Constructs "SQUAD" + number + ".MIS"

### Data Structures
- **Mission Slots**: `dword_79D3E` @ segment 0x7894 (64 × 20 bytes)
- **Mission Context**: `dword_79E3A` (60B header + 30 pilots × 66B)
- **Flight Array**: `dword_79BEC` (N × 130 bytes)

### UI Overlays
- **R55 Dispatcher**: 0x18F910 (writes to +0x604-0x608)
- **R56 Handler**: 0x1A0030 (writes to +0x3F-0x41)
- **R53 Briefing**: 0x1820B0 (read-only display)

## Hypotheses

### Hypothesis 1: R55 is Mission Editor

**Evidence**:
- Writes to large offsets in `dword_79D3E` (+0x604-0x608)
- Suggests large editing buffer (not just 20-byte slots)
- Name "dispatcher" implies mode manager

**Test**: Find string references like "EDIT", "MODIFY", "WAYPOINT" in R55

### Hypothesis 2: Flight Plan Section Structure

**Based on file analysis**, the detail section likely contains:

```c
struct FlightPlan {
    // Per-flight waypoint parameters
    struct FlightWaypointParams {
        uint16_t altitude;      // Feet (AGL or MSL)
        uint16_t speed;         // Knots (TAS)
        uint8_t  action_code;   // TAKEOFF, CAP, BOMB, etc.
        uint8_t  target_ref;    // Target ID for BOMB missions
        uint8_t  padding[2];    // Alignment
    } waypoint_params[MAX_WAYPOINTS];
    
    // Shared waypoint coordinates (21 bytes each)
    Waypoint waypoints[MAX_WAYPOINTS];
    
    // Flight composition
    FlightRecord flights[MAX_FLIGHTS];
};
```

**This would explain**:
- Why waypoints don't have altitude/speed
- Why multiple flights can share routes
- Why file has large detail section

### Hypothesis 3: Extended Data in MissionSlot

The 13 unknown bytes (+0x07 to +0x13) in MissionSlot might contain:

```c
// +0x07-0x13: Extended mission data (13 bytes)
uint8_t  waypoint_count;     // +0x07: Number of waypoints
uint8_t  flight_count;       // +0x08: Number of flights
uint16_t detail_offset;      // +0x09-0x0A: Offset to detail section
uint8_t  time_of_day;        // +0x0B: 0=0600, 1=1200, 2=1800, 3=2300
uint8_t  weather;            // +0x0C: Weather condition
uint8_t  difficulty;         // +0x0D: Mission difficulty
uint8_t  reserved[6];        // +0x0E-0x13: Reserved/padding
```

## Next Steps

### Immediate Actions

1. **Disassemble R55 Dispatcher** (0x18F910):
   - Find function entry point
   - Identify menu handlers
   - Look for waypoint/flight data access

2. **Search for 21-byte patterns** in R55/R56:
   - Waypoint array access
   - Coordinate read/write operations

3. **Find file save function**:
   - Reverse of `squadron_mission_file_loader`
   - Should write .MIS file format
   - Trace buffer construction

4. **Trace FlightRecord usage** in R56:
   - 130-byte stride patterns
   - Aircraft count modification
   - Pilot assignment

### Analysis Tools Needed

1. **String search in R55/R56**:
   ```python
   # Search for: WAYPOINT, ALTITUDE, SPEED, FLIGHT, etc.
   # In segments: R55_*, R56_*
   ```

2. **Pattern scanner**:
   ```python
   # Look for: mov dx, 15h; imul dx (waypoint stride)
   # Look for: mov dx, 82h; imul dx (flight stride)
   ```

3. **Cross-reference tracker**:
   ```python
   # Find all writes to dword_79D3E with offsets > 20
   # Find all writes to dword_79BEC (flight array)
   ```

4. **File I/O tracker**:
   ```python
   # Find DOS INT 21h, AH=40h (write)
   # Trace buffer addresses
   # Identify .MIS file handles
   ```

## Expected Findings

When analysis complete, we should be able to:

1. **Map complete .MIS file format**:
   - Header (12 bytes) ✓
   - Mission records (6 bytes each) ✓
   - Flight plan section structure
   - Waypoint coordinates (21 bytes each) ✓
   - Per-flight waypoint parameters (altitude, speed, action)
   - Flight compositions (130 bytes each)

2. **Document mission editing workflow**:
   - UI navigation
   - Data structure updates
   - File save process
   - Validation/constraints

3. **Create mission editor tools**:
   - Read/write .MIS files
   - Modify waypoints graphically
   - Edit flight parameters
   - Validate mission consistency

## Questions to Answer

1. **Where is altitude/speed stored**?
   - In detail section? Per-flight or per-waypoint?
   
2. **How are waypoints assigned to flights**?
   - All flights share same waypoints?
   - Or separate waypoint lists per flight?
   
3. **What are the action codes**?
   - Numeric values for TAKEOFF, CAP, BOMB, etc.?
   
4. **How does target assignment work**?
   - For BOMB missions, how is target referenced?
   
5. **What are the file size limits**?
   - Maximum waypoints per mission?
   - Maximum flights per mission?
   - Maximum file size?

## Progress Tracker

| Component | Status | Confidence |
|-----------|--------|------------|
| .MIS header | ✓ Complete | 100% |
| Mission records | ✓ Complete | 100% |
| Waypoint coordinates | ✓ Complete | 100% |
| Mission slot structure | ✓ Mostly complete | 95% |
| Flight record structure | ⚠ Partial | 60% |
| Detail section layout | ⚠ Hypothesis | 40% |
| Altitude/speed storage | ⚠ Unknown | 0% |
| Action codes | ⚠ Unknown | 0% |
| R55/R56 functionality | ⚠ Unknown | 20% |
| File save mechanism | ⚠ Unknown | 0% |

**Overall Mission Editing Analysis**: 40% Complete

## Conclusion

We have strong foundations:
- ✓ File format partially decoded
- ✓ Memory structures identified
- ✓ Waypoint coordinates confirmed
- ✓ Overlay candidates located

Next phase requires:
- Disassembly of R55/R56 overlays
- Tracing data modification code
- Finding altitude/speed/action storage
- Mapping detail section structure

This will complete our understanding of how mission editing works and enable creation of external mission editor tools.
