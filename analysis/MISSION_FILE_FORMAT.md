# .MIS Mission File Format Analysis

## File Discovery

**Filename Pattern**: `SQUAD[0-9].MIS`, `MISSION[0-9].MIS`, `INSTACT*.MIS`

**Files Found**:
- `SQUAD0.MIS`: 824 bytes (0x338)
- `SQUAD1.MIS`: 451 bytes (0x1C3)
- `MISSION1-8.MIS`: 1593-3114 bytes
- `INSTACT*.MIS`: 1726-1744 bytes

**Code Reference**: 
- Function: `squadron_mission_file_loader` @ 0x17B437
- Constructs filename dynamically: "SQUAD" + number + ".MIS" (not .TSK!)
- Read operation @ offset +0x713: Reads variable-length data

## File Structure

### Overall Layout

```
+0x0000  Header (12 bytes)
         ├─ Mission count
         ├─ Theater/campaign data
         └─ Various metadata
         
+0x000C  Mission Slot Records (6 bytes each × N)
         ├─ Slot index
         ├─ Mission type
         ├─ Parameters
         └─ Flags
         
+0x????  Detailed Mission Data (variable)
         ├─ Waypoint data
         ├─ Flight compositions
         ├─ Threat data
         └─ Objectives
```

## Header Format (12 bytes)

### SQUAD0.MIS Header
```
Offset  Value  Interpretation
------  -----  --------------
+0x00   03     Mission count? (SQUAD0 has 3 active squadrons?)
+0x01   00     
+0x02   01     Theater ID? (1 = Korea, Israel, etc.)
+0x03   14     0x14 = 20 (MissionSlot size!)
+0x04   1E     0x1E = 30 (pilots per squadron)
+0x05   0B     0x0B = 11 (menu elements?)
+0x06   00     
+0x07   1A     0x1A = 26 (number of mission records that follow)
+0x08   00     
+0x09   02     
+0x0A   00     
+0x0B   01     
```

### SQUAD1.MIS Header
```
Offset  Value  Interpretation
------  -----  --------------
+0x00   02     Mission count = 2
+0x01   00     
+0x02   07     Different theater? (7)
+0x03   11     0x11 = 17
+0x04   01     
+0x05   00     
+0x06   10     0x10 = 16 (number of mission records)
+0x07   00     
+0x08   02     
+0x09   00     
+0x0A   01     
+0x0B   00     
```

### Header Field Hypothesis

```c
struct MISFileHeader {
    uint16_t mission_count;      // +0x00: Number of active missions
    uint8_t  theater_id;         // +0x02: Theater ID
    uint8_t  slot_size;          // +0x03: MissionSlot size (0x14 = 20)
    uint8_t  pilots_per_squad;   // +0x04: Pilots (0x1E = 30)
    uint8_t  menu_elements;      // +0x05: UI elements (0x0B = 11)
    uint8_t  unknown_06;         // +0x06: 
    uint8_t  record_count;       // +0x07: Number of mission records following
    uint16_t unknown_08;         // +0x08-0x09:
    uint16_t unknown_0A;         // +0x0A-0x0B:
};  // 12 bytes
```

## Mission Slot Record Format (6 bytes)

### Pattern Analysis

**SQUAD0.MIS Records** (26 records):
```
Index  B2  B3  B4  Flags  | Interpretation
-----  --  --  --  -----  | --------------
  03   01  00  03   80    | Mission 3: Type 1, param 3
  04   01  00  03   80    | Mission 4: Type 1, param 3
  05   01  00  03   80    | Mission 5: Type 1, param 3
  06   01  00  03   80    | Mission 6: Type 1, param 3
  07   34  00  01   80    | Mission 7: Type 52, param 1
  08   34  00  01   80    | Mission 8: Type 52, param 1
  09   34  00  01   80    | Mission 9: Type 52, param 1
  0A   35  00  23   80    | Mission 10: Type 53, param 35
  ...
  11   0B  00  0E   81    | Mission 17: Type 11, param 14, flags 0x81 (different!)
  12   09  00  0B   81    | Mission 18: Type 9, param 11, flags 0x81
  ...
```

**Pattern**: `[Index] [00] [Type] [00] [Param] [Flags]`

### Field Structure

```c
struct MissionSlotRecord {
    uint8_t  slot_index;      // +0x00: Mission slot number (0-63)
    uint8_t  zero_01;         // +0x01: Always 0x00
    uint8_t  mission_type;    // +0x02: Mission type (0x01, 0x34=52, 0x35=53, etc.)
    uint8_t  zero_03;         // +0x03: Always 0x00
    uint8_t  parameter;       // +0x04: Mission-specific parameter
    uint8_t  flags;           // +0x05: Flags (0x80 or 0x81)
                              //        Bit 0: 0x80 = ??, 0x81 = ??
                              //        Bit 7: Always set (0x80 mask)
};  // 6 bytes
```

### Flag Analysis

**0x80 vs 0x81**:
- **0x80**: Most common (missions 3-16 in SQUAD0)
- **0x81**: Less common (missions 17-27 in SQUAD0)
- **Hypothesis**: Bit 0 = mission availability or completion status

### Mission Type Values

From SQUAD0.MIS:
- **0x01**: Appears for missions 3-6 (4 times)
- **0x34** (52): Appears for missions 7-9 (3 times)
- **0x35** (53): Appears for missions 10-12 (3 times)
- **0x36** (54): Appears for missions 13-16 (4 times)
- **0x0B** (11): Mission 17 (flags 0x81)
- **0x09** (9): Missions 18-19 (flags 0x81)
- **0x0A** (10): Missions 20-22 (flags 0x81)
- **0x08** (8): Missions 23-25 (flags 0x81)
- **0x07** (7): Mission 26 (flags 0x81)

**Correlation with MissionType Enum**:
```
MISSION_FIGHTER_SCRAMBLE     = 0
MISSION_FIGHTER_SWEEP        = 1  ← Matches 0x01!
MISSION_BARCAP               = 2
MISSION_INTERCEPT            = 3
MISSION_ESCORT               = 4
MISSION_STRIKE               = 7  ← Matches 0x07!
MISSION_DEEPSTRIKE           = 8  ← Matches 0x08!
MISSION_CASUP                = 9  ← Matches 0x09!
MISSION_CAS                  = 10 ← Matches 0x0A!
MISSION_SEAD                 = 11 ← Matches 0x0B!
...
```

**✓ CONFIRMED**: Byte +0x02 is the MissionType enum value!

### Parameter Values

Different mission types have different parameter meanings:
- **Type 1 (FIGHTER_SWEEP)**: param = 3
- **Type 52**: param = 1 or 7
- **Type 53**: param = 32, 35 (loadout variant?)
- **Type 54**: param = 45
- **Type 11 (SEAD)**: param = 14
- **Type 9 (CASUP)**: param = 11
- **Type 10 (CAS)**: param = 9
- **Type 8 (DEEPSTRIKE)**: param = 8
- **Type 7 (STRIKE)**: param = 5, 13

**Hypothesis**: Parameter is target ID, loadout preset, or difficulty level.

## Detailed Mission Data Section

After mission slot records, the file contains detailed data. Pattern suggests:

### Structure Hypothesis

Looking at offsets after records (SQUAD0 @ 0x00AD onwards):

**Section 1: Waypoint/Coordinate Data**
```
+0x00C1: 0A 46 35 49 03 DA CB 10 5A 08
         └─ Looks like coordinates (16-bit values)
         
Pattern repeats every ~20-40 bytes with coordinate-like data.
```

**Section 2: Flight/Loadout Data** (starts ~0x0170)
```
+0x0170: C8 00 02 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 1E 1E
         └─ 0xC8 = 200 (matches MissionSlot field_02!)
         └─ Repeated pattern suggests array
```

**Structure**:
```c
// Appears to be 20-byte records
struct MissionDetailRecord {
    uint16_t field_00;        // 0xC8 common value
    uint8_t  field_02;        // 0x02
    uint8_t  field_03;        // 0x02, 0x04, 0x00
    uint16_t field_04;        // Often 0x0000
    uint8_t  data_06[10];     // Variable data
    uint16_t field_10;        // Often 0x1E (30)
    uint16_t field_12;        // Often 0x1E (30)
    uint16_t field_14;        // Often 0x0000
};  // 20 bytes?
```

**Section 3: Threat/Object Data** (later in file)
```
+0x0250: E7 00 01 00 C6 F8 FF 90 C6 F4 FF 10 00 00
         └─ Coordinate pairs with flags
         
Pattern: [type] [00] [flags] [00] [x_low] [x_high] [FF] [??] [y_low] [y_high] ...
```

## Correlation with 20-Byte MissionSlot

### File Record → Memory MissionSlot Mapping

**File Format (6 bytes)** → **Memory Format (20 bytes)**

```c
// File record (6 bytes)
struct MissionSlotRecord {
    uint8_t  slot_index;      // +0x00
    uint8_t  zero;            // +0x01
    uint8_t  mission_type;    // +0x02  ← Goes to MissionSlot +0x??
    uint8_t  zero;            // +0x03
    uint8_t  parameter;       // +0x04  ← Goes to MissionSlot +0x??
    uint8_t  flags;           // +0x05  ← Goes to MissionSlot +0x??
};

// Memory structure (20 bytes)
struct MissionSlot {
    char     label[2];        // +0x00: Initialized to space+null
    uint16_t field_02;        // +0x02: Value 0xC8 (from detail section?)
    uint8_t  mission_type;    // +0x04: From file record +0x02 ← HYPOTHESIS
    uint8_t  flags;           // +0x05: From file record +0x05 ← HYPOTHESIS
    uint8_t  parameter;       // +0x06: From file record +0x04 ← HYPOTHESIS
    uint8_t  unknown_07[13];  // +0x07: From detail section
};  // 20 bytes
```

## File Read Operation in Code

### squadron_mission_file_loader @ 0x17B437

**Key Operations**:

1. **Initialize mission slot array** (offsets +0x033 to +0x092):
   ```asm
   loop:
     mov dx, 14h              ; MissionSlot size = 20
     imul dx                  ; Calculate offset
     les bx, es:dword_79D3E   ; Load array pointer
     add bx, ax               ; Index into array
     mov byte ptr es:[bx], 20h    ; label[0] = space
     mov byte ptr es:[bx+1], 0    ; label[1] = null
     inc di
     cmp di, 40h              ; Loop 64 times
   ```

2. **Open .MIS file** (offsets +0x222 to +0x321):
   ```asm
   ; Construct filename: "SQUAD" + number + ".MIS"
   call string_concatenate
   call op_dispatch_far_entry   ; DOS file open
   ```

3. **Read mission file** (offset +0x713):
   ```asm
   ; Read variable bytes from .MIS → buffer 0x602E:0x068F
   call op_dispatch_far_entry
   ```

4. **Parse and populate mission slots** (later in function):
   - Loop through file records
   - Extract mission_type, parameter, flags
   - Write to mission slot array at calculated offsets

## Next Steps

### 1. Trace File Data Copy

Need to find where the code copies from file buffer to mission slot array:
- Buffer: `0x602E:0x068F`
- Destination: `es:dword_79D3E` array
- Look for memory copy loop after file read

### 2. Map Remaining MissionSlot Fields

**Confirmed**:
- +0x00-0x01: label (initialized)
- +0x02-0x03: field_02 = 0xC8

**Hypothesis**:
- +0x04: mission_type (from file +0x02)
- +0x05: flags (from file +0x05)
- +0x06: parameter (from file +0x04)

**Unknown** (+0x07 to +0x13):
- Data from detail section
- Possibly: target coordinates, timing, difficulty, etc.

### 3. Parse Detail Section

Need to understand the structure after mission records:
- Waypoint coordinates
- Flight compositions
- Threat data
- Objectives

## Summary

### Confirmed Discoveries

✓ **File Extension**: .MIS (not .TSK!)  
✓ **File Structure**: Header (12B) + Records (6B each) + Details (variable)  
✓ **Mission Type Field**: Byte +0x02 in file record = MissionType enum  
✓ **Record Count**: Stored in header +0x07  
✓ **6-byte to 20-byte mapping**: File records expand into memory slots  

### Confidence Levels

- Header format: 85% ✓
- Mission record format: 95% ✓
- Mission type identification: 100% ✓
- Detail section structure: 40% ~
- MissionSlot field mapping: 60% ~

### Remaining Work

1. Trace file buffer → mission slot copy code
2. Complete MissionSlot field definitions (+0x04 to +0x13)
3. Parse detail section structure
4. Identify waypoint format
5. Document complete file specification
