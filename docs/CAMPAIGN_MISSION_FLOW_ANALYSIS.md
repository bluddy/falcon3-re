# Campaign Mission Flow Analysis
## Reverse Engineering Mission-to-Mission Progression

**Date**: 2025-01-15  
**Status**: IN PROGRESS - Campaign loader decompiled  
**Goal**: Understand how Falcon 3.0 advances campaign state between missions

---

## Overview

The campaign system in Falcon 3.0 is tightly integrated with the menu system, as campaign progression only occurs between missions. The core loader function `squad_campaign_file_loader` @ 0x6A651 handles loading and saving campaign state across 6+ file types.

**Key Insight**: Campaign state is distributed across multiple files with a numbering scheme (0-N squadrons), all loaded/saved together during squadron selection.

---

## Core Campaign Files

### File Naming Convention

All campaign files use **squadron slot number** prefix:

```
Format: [slot][type_suffix]
Example: 0SQUAD.CAM, 1SQUAD.CAM, 2SQUAD.CAM, etc.
```

### File Types Discovered

From `squad_campaign_file_loader` @ 0x6A651:

1. **`.CAM`** - Campaign state file
   - Primary campaign data
   - Loaded first in sequence
   - Contains: Territory control, mission history, date/time

2. **`.SQU`** - Squadron data file
   - Squadron configuration
   - Wing assignment
   - Squadron statistics
   - Commander, insignia, name

3. **`.SHP`** - Ship/Naval data (file extension "7..`.SHP")
   - Naval task force positions?
   - Ship availability?
   - Linked to ANTISHIP/SEADSHIP missions

4. **`.TSK`** - Task data (file extension "...`.TSK")
   - Mission task definitions?
   - Available mission types?
   - Current task assignments?

5. **`.TRG`** - Target data (file extension "v..`.TRG")
   - Ground target status
   - Target priority lists
   - Damage states

6. **`.MIS`** / **`.MTV`** - Mission data (inferred from other analysis)
   - Mission templates
   - Briefing data
   - Flight configuration

---

## squad_campaign_file_loader @ 0x6A651

### Function Profile

```
Size: 2056 bytes (largest campaign function)
Calls: 88 function calls
Strings: 11 string references
Called by: 1 location (likely from squadron selection menu)
```

### Execution Flow

#### Phase 1: Initialize Campaign Load (0x6A651-0x6A66F)

```asm
0x6A651: enter   6, 0                    ; Allocate 6 bytes local vars
0x6A655: push    si                       ; Save registers
0x6A656: push    di
0x6A657: mov     di, [bp+arg_0]          ; DI = squadron slot number (0-N)
0x6A65A: call    flag2224a_clear         ; Clear campaign-in-progress flag
0x6A65F: mov     ax, 4FC2h               ; ES = segment 4FC2
0x6A662: mov     es, ax
0x6A664: push    es:word_13E016          ; Push dispatch parameter
0x6A669: call    dispatch_220f0_invoke_1arg ; Invoke operation dispatcher
```

**Analysis**:
- `arg_0` = squadron slot number (from UI selection)
- `flag2224a` = Global flag indicating campaign is being loaded
- `word_13E016` @ 4FC2 = Dispatch parameter (operation code?)
- Clears flag before load, sets it after (atomicity)

#### Phase 2: Setup Memory Buffer (0x6A66F-0x6A687)

```asm
0x6A66F: mov     ax, 7894h               ; ES = segment 7894
0x6A672: mov     es, ax
0x6A674: mov     ax, word ptr es:dword_79E60+2  ; Load base pointer (segment)
0x6A678: mov     dx, word ptr es:dword_79E60    ; Load base pointer (offset)
0x6A67D: add     dx, 7530h               ; DX += 0x7530 (30,000 bytes)
0x6A681: mov     [bp+var_4], ax          ; Store segment in var_4
0x6A684: mov     [bp+var_6], dx          ; Store offset+30000 in var_6
```

**Analysis**:
- `dword_79E60` @ 7894 = Far pointer to campaign data buffer
- Adds offset `0x7530` (30,000 bytes) to buffer address
- **30,000 bytes** = Approximate size of campaign data loaded into memory
- Buffer pointer stored in local vars for subsequent reads

#### Phase 3: Build .CAM Filename (0x6A687-0x6A6EB)

```asm
; Convert slot number to string
0x6A687: mov     ax, 602Eh               ; ES = segment 602E (menu data)
0x6A68A: mov     es, ax
0x6A68C: push    word ptr es:current_menu_slot_ptr+2  ; Load slot pointer
0x6A691: push    word ptr es:current_menu_slot_ptr
0x6A696: push    di                      ; Push squadron slot number
0x6A697: call    int_to_string_converter ; Convert slot number to string

; Build filename: [slot]+"SQUAD"+".CAM"
0x6A69F: push    7894h
0x6A6A2: push    0F32h                   ; Buffer at 7894:0F32
0x6A6A5: mov     ax, 602Eh
0x6A6A8: mov     es, ax
0x6A6AA: push    word ptr es:current_menu_slot_ptr+2
0x6A6AF: push    word ptr es:current_menu_slot_ptr
0x6A6B4: mov     ax, 602Eh
0x6A6B7: mov     es, ax
0x6A6B9: push    word ptr es:aSSquad+2   ; String "S-.`SQUAD"
0x6A6BE: push    word ptr es:aSSquad
0x6A6C3: call    string_concatenate      ; Concatenate: slot + "SQUAD"

0x6A6CB: push    7894h
0x6A6CE: push    0F32h                   ; Same buffer
0x6A6D1: mov     ax, 602Eh
0x6A6D4: mov     es, ax
0x6A6D6: push    word ptr es:aCam+1      ; String ".`.CAM"
0x6A6DB: push    word ptr es:byte_151325
0x6A6E0: push    7894h
0x6A6E3: push    0F32h
0x6A6E6: call    string_concatenate      ; Concatenate: buffer + ".CAM"
```

**Analysis**:
- `current_menu_slot_ptr` @ 602E = Pointer to selected squadron slot
- `aSSquad` = String template "SQUAD"
- `aCam` = String template ".CAM"
- Resulting filename: `"0SQUAD.CAM"`, `"1SQUAD.CAM"`, etc.
- Buffer @ 7894:0F32 holds filename string

**String Corruption Note**: "S-.`SQUAD" suggests the strings are corrupted or compressed in memory. The actual file names are standard DOS 8.3 format.

#### Phase 4: Open and Read .CAM File (0x6A6EE-0x6A732)

```asm
0x6A6EE: push    7894h
0x6A6F1: push    0F32h                   ; Filename buffer
0x6A6F4: push    0                       ; Open mode: Read
0x6A6F6: push    2                       ; Access mode: Read/Write
0x6A6F8: push    6                       ; Operation: OPEN file
0x6A6FA: call    op_dispatch_far_entry   ; DOS file open
0x6A6FF: add     sp, 0Ah
0x6A702: mov     [bp+var_2], ax          ; Store file handle in var_2
0x6A705: cmp     ax, 0FFFFh              ; Check if open failed (0xFFFF)
0x6A708: jz      short loc_6A777         ; If failed, skip to .SQU file

; Read .CAM file into memory buffer
0x6A70A: push    [bp+var_4]              ; Buffer segment
0x6A70D: push    [bp+var_6]              ; Buffer offset (+30000)
0x6A710: push    0FFFFh                  ; Read size: 65535 bytes (MAX)
0x6A712: push    [bp+var_2]              ; File handle
0x6A715: push    0Ah                     ; Operation: READ
0x6A717: call    op_dispatch_far_entry   ; DOS file read
0x6A71C: add     sp, 0Ah
0x6A71F: mov     si, ax                  ; SI = bytes actually read

; Close .CAM file
0x6A721: push    ss
0x6A722: lea     ax, [bp+var_2]
0x6A725: push    ax                      ; Address of file handle
0x6A726: push    0
0x6A728: push    [bp+var_2]              ; File handle
0x6A72B: push    8                       ; Operation: CLOSE
0x6A72D: call    op_dispatch_far_entry   ; DOS file close
```

**Analysis**:
- Operation codes: 6=OPEN, 8=CLOSE, 10=READ
- `op_dispatch_far_entry` = DOS interrupt wrapper (INT 21h)
- Reads entire .CAM file (up to 65535 bytes) into buffer+30000
- Stores actual bytes read in SI register
- Continues even if .CAM file doesn't exist

#### Phase 5: Set Campaign Active Flag (0x6A735)

```asm
0x6A735: call    flag2224a_set           ; Set flag 2224a
```

**Analysis**:
- Sets global flag indicating campaign is now loaded
- Flag checked by other systems to determine if in campaign mode
- Set AFTER .CAM read but BEFORE other files

#### Phase 6: Open Unknown Data File (0x6A73A-0x6A774)

```asm
0x6A73A: push    ds
0x6A73B: push    0A34Ah                  ; Hardcoded filename offset
0x6A73E: push    0                       ; Open mode: Read
0x6A740: push    0                       ; Access mode: Read-only
0x6A742: push    4                       ; Operation: 4 (OPEN variant?)
0x6A744: call    op_dispatch_far_entry   ; DOS file open
0x6A749: add     sp, 0Ah
0x6A74C: mov     [bp+var_2], ax          ; Store file handle

; Read data from unknown file
0x6A74F: push    [bp+var_4]              ; Buffer segment
0x6A752: push    [bp+var_6]              ; Buffer offset (+30000)
0x6A755: push    si                      ; Read size = bytes from .CAM
0x6A756: push    [bp+var_2]              ; File handle
0x6A759: push    0Ch                     ; Operation: 12 (READ variant?)
0x6A75B: call    op_dispatch_far_entry   ; DOS file read
0x6A760: add     sp, 0Ah

; Close file
0x6A763: push    ss
0x6A764: lea     ax, [bp+var_2]
0x6A767: push    ax
0x6A768: push    0
0x6A76A: push    [bp+var_2]
0x6A76D: push    8                       ; Operation: CLOSE
0x6A76F: call    op_dispatch_far_entry
```

**Analysis**:
- Opens hardcoded filename at DS:0A34Ah (need to extract this string)
- Reads same number of bytes as .CAM file (SI register)
- Uses operations 4 and 12 (variants of OPEN and READ?)
- **Hypothesis**: Secondary campaign data file (backup? history?)

#### Phase 7: Load .SQU File (0x6A777-0x6A822)

```asm
; Build filename: [slot]+"SQUAD"+".SQU"
0x6A777: mov     ax, 602Eh
0x6A77A: mov     es, ax
0x6A77C: push    word ptr es:current_menu_slot_ptr+2
0x6A781: push    word ptr es:current_menu_slot_ptr
0x6A786: push    di                      ; Squadron slot number
0x6A787: call    int_to_string_converter

0x6A78F: push    7894h
0x6A792: push    0F32h                   ; Buffer at 7894:0F32
0x6A795: mov     ax, 602Eh
0x6A798: mov     es, ax
0x6A79A: push    word ptr es:current_menu_slot_ptr+2
0x6A79F: push    word ptr es:current_menu_slot_ptr
0x6A7A4: mov     ax, 602Eh
0x6A7A7: mov     es, ax
0x6A7A9: push    word ptr es:aSSquad+2   ; "SQUAD"
0x6A7AE: push    word ptr es:aSSquad
0x6A7B3: call    string_concatenate

0x6A7BB: push    7894h
0x6A7BE: push    0F32h
0x6A7C1: mov     ax, 602Eh
0x6A7C4: mov     es, ax
0x6A7C6: push    word ptr es:aSqu+1      ; ".SQU"
0x6A7CB: push    word ptr es:byte_151393
0x6A7D0: push    7894h
0x6A7D3: push    0F32h
0x6A7D6: call    string_concatenate      ; Result: "0SQUAD.SQU"

; Open and read .SQU file
0x6A7DE: push    7894h
0x6A7E1: push    0F32h
0x6A7E4: push    0
0x6A7E6: push    2
0x6A7E8: push    6                       ; Operation: OPEN
0x6A7EA: call    op_dispatch_far_entry
0x6A7EF: add     sp, 0Ah
0x6A7F2: mov     [bp+var_2], ax          ; Store file handle
0x6A7F5: cmp     ax, 0FFFFh              ; Check if failed
0x6A7F8: jz      short loc_6A867         ; Skip to next file if failed

0x6A7FA: push    [bp+var_4]              ; Buffer segment
0x6A7FD: push    [bp+var_6]              ; Buffer offset
0x6A800: push    0FFFFh                  ; Read size: 65535 bytes
0x6A802: push    [bp+var_2]              ; File handle
0x6A805: push    0Ah                     ; Operation: READ
0x6A807: call    op_dispatch_far_entry
0x6A80C: add     sp, 0Ah
0x6A80F: mov     si, ax                  ; SI = bytes read

; Close .SQU file
0x6A811: push    ss
0x6A812: lea     ax, [bp+var_2]
0x6A815: push    ax
0x6A816: push    0
0x6A818: push    [bp+var_2]
0x6A81B: push    8                       ; Operation: CLOSE
0x6A81D: call    op_dispatch_far_entry
```

**Pattern Identified**: Same structure as .CAM file loading
- Build filename with slot number
- Open file (operation 6)
- Read entire file (operation 10, up to 65535 bytes)
- Close file (operation 8)
- Store bytes read in SI

#### Phase 8-11: Load Remaining Files

The function continues with identical patterns for:
- **0x6A8A3**: `.MIS` file (missions)
- **0x6A998**: `.TRG` file (targets) 
- **0x6AAB9**: `.TSK` file (tasks)
- **0x6AB9F**: `.SHP` file (ships/naval)

*Truncated disassembly due to 2056 byte function size*

---

## Campaign File Load Sequence

### Complete Loading Order

```
1. Clear campaign flag (flag2224a)
2. Setup memory buffer (base + 30,000 bytes)
3. Load [slot]SQUAD.CAM    (Campaign state)
4. Set campaign flag (flag2224a)
5. Load unknown file (DS:0A34Ah)
6. Load [slot]SQUAD.SQU    (Squadron data)
7. Load [slot]SQUAD.MIS    (Mission data)
8. Load [slot]SQUAD.TRG    (Target data)
9. Load [slot]SQUAD.TSK    (Task data)
10. Load [slot]SQUAD.SHP   (Ship/naval data)
```

### Error Handling

All file loads use same error pattern:
```asm
cmp     ax, 0FFFFh          ; Check if open failed
jz      next_file           ; Skip to next file (continue loading)
```

**Campaign loads successfully even if files are missing** - fault tolerant design for partial saves or corruption.

### Memory Buffer Strategy

```
Base Pointer: dword_79E60 @ segment 7894
Campaign Buffer: Base + 0x7530 (30,000 bytes)

Layout (hypothesized):
+0x0000: .CAM data (campaign state, ~10-15 KB?)
+0x????:  .SQU data (squadron data, ~2-5 KB?)
+0x????:  .MIS data (mission data, ~5-10 KB?)
+0x????:  .TRG data (target data, ~3-5 KB?)
+0x????:  .TSK data (task data, ~2-3 KB?)
+0x????:  .SHP data (ship data, ~1-2 KB?)

Total: ~25-40 KB (fits within 65535 byte limit)
```

Each file read stores bytes read in SI register, possibly used to calculate next file offset in buffer.

---

## ui_slot_list_mode_enter @ 0x6AE59

### Function Profile

```
Size: 1393 bytes
Calls: 30 function calls
Strings: 0 (operates on data structures, no direct strings)
Called by: 2 locations (likely menu navigation)
```

### Execution Flow

#### Phase 1: Initialize Slot List (0x6AE59-0x6AF13)

```asm
0x6AE59: enter   4, 0                    ; Allocate 4 bytes local vars
0x6AE5D: mov     ax, 7894h               ; ES = segment 7894
0x6AE60: mov     es, ax
0x6AE62: mov     es:byte_7A30C, 0        ; Clear slot list flag
0x6AE68: mov     [bp+var_1], 0           ; Loop counter = 0

; Loop through 6 slots
0x6AE6C: jmp     loc_6AF13

; Loop body (initialization)
0x6AE70-0x6AF0B:
    ; For each slot (0-5):
    ; - Clear slot availability flags
    ; - Initialize slot data structures
    ; - Set default values
    
0x6AF0B: mov     al, [bp+var_1]
0x6AF0E: inc     al                      ; counter++
0x6AF10: mov     [bp+var_1], al

0x6AF13: cmp     [bp+var_1], 6           ; Loop while counter < 6
0x6AF17: jnb     short loc_6AF1C
0x6AF19: jmp     near ptr unk_6AE6F      ; Continue loop
```

**Analysis**:
- Initializes **6 squadron slots** (0-5)
- Each slot has associated data structures cleared
- `byte_7A30C` @ 7894 = Slot list active flag

#### Phase 2: Graphics Mode Check (0x6AF1C-0x6AF2C)

```asm
0x6AF1C: mov     ax, 7894h
0x6AF1F: mov     es, ax
0x6AF21: cmp     es:graphics_mode_flag, 3  ; Check if graphics mode = 3
0x6AF27: jz      short loc_6AF2C           ; If yes, render UI
0x6AF29: jmp     loc_6B1E7                 ; Else, skip to non-graphics mode
```

**Analysis**:
- `graphics_mode_flag` @ 7894 = Display mode (VGA/SVGA?)
- Mode 3 = Full graphics mode with UI rendering
- Other modes may use text-based UI or skip rendering

#### Phase 3: Render Slot List UI (0x6AF2C-0x6AFA5)

```asm
0x6AF2C: mov     ax, 602Eh
0x6AF2F: mov     es, ax
0x6AF31: mov     al, es:byte_14E5A0      ; Load current UI state
0x6AF35: mov     dx, 602Eh
0x6AF38: mov     es, dx
0x6AF3A: mov     es:byte_14E5A1, al      ; Store previous UI state
0x6AF3E: mov     ax, 602Eh
0x6AF41: mov     es, ax
0x6AF43: mov     es:byte_14E5A2, 1       ; Set UI active flag

; Loop through slots and render
0x6AF49: mov     [bp+var_1], 1           ; Start at slot 1
0x6AF4D: jmp     short loc_6AF6D

0x6AF4F: push    709Fh                   ; UI segment
0x6AF52: push    11E7h                   ; UI offset
0x6AF55: push    6                       ; Render operation 6
0x6AF57: mov     al, [bp+var_1]          ; Slot number
0x6AF5A: push    ax
0x6AF5B: push    14h                     ; Parameter 20
0x6AF5D: call    ui_text_render_engine   ; Render slot text
0x6AF62: add     sp, 0Ah

0x6AF65: mov     al, [bp+var_1]
0x6AF68: inc     al
0x6AF6A: mov     [bp+var_1], al

0x6AF6D: mov     al, [bp+var_1]
0x6AF70: mov     ah, 0
0x6AF72: mov     dx, 709Fh
0x6AF75: mov     es, dx
0x6AF77: cmp     ax, es:word_70A2A+1     ; Compare to max slot count
0x6AF7C: jle     short loc_6AF4F          ; Continue loop
```

**Analysis**:
- Renders squadron slot list in UI
- `ui_text_render_engine` = Text rendering function for menu
- Renders slots 1-N (N determined by `word_70A2A+1` @ 709F)
- Each slot displayed at different UI position

#### Phase 4: Squadron Slot Validation (0x6AFBC-0x6AFFB)

```asm
; Loop through all 6 slots
0x6AFBC: jmp     short loc_6AFF7

0x6AFBE: mov     al, [bp+var_1]          ; Slot number
0x6AFC1: mov     ah, 0
0x6AFC3: shl     ax, 2                   ; Slot * 4 (4-byte slot records)
0x6AFC6: mov     dx, 602Eh
0x6AFC9: mov     bx, ax
0x6AFCB: mov     es, dx
0x6AFCD: cmp     byte ptr es:[bx+1], 0   ; Check if slot has data
0x6AFD3: jz      short loc_6AFEF         ; Skip if empty

; Slot has data - tally it
0x6AFD5: mov     al, [bp+var_1]
0x6AFD8: push    ax                      ; Slot number
0x6AFD9: mov     ah, 0
0x6AFDB: shl     ax, 2
0x6AFDE: mov     bx, ax
0x6AFE0: mov     es, dx
0x6AFE2: mov     al, es:[bx+1]           ; Load slot type
0x6AFE7: push    ax
0x6AFE8: call    ui_slot_count_tally     ; Count available slots
0x6AFED: pop     cx
0x6AFEE: pop     cx

0x6AFEF: mov     al, [bp+var_1]
0x6AFF2: inc     al
0x6AFF4: mov     [bp+var_1], al

0x6AFF7: cmp     [bp+var_1], 6           ; Loop while < 6
0x6AFFB: jb      short loc_6AFBE
```

**Analysis**:
- Checks each of 6 slots for saved campaign data
- Slot record size = 4 bytes
- `es:[bx+1]` = Slot occupied flag (0=empty, non-zero=has data)
- `ui_slot_count_tally` = Updates UI with available squadrons

#### Phase 5: Slot Selection Logic (0x6AFFD-0x6B0A5)

```asm
0x6AFFD: mov     ax, 7894h
0x6B000: mov     es, ax
0x6B002: cmp     es:byte_7A302, 0        ; Check if any slots available
0x6B008: jnz     short loc_6B00D         ; If yes, enable selection
0x6B00A: jmp     loc_6B0A5               ; Else, skip selection phase

; Find first available slot
0x6B00D: mov     [bp+var_2], 0FFh        ; var_2 = first slot index (init -1)
0x6B011: mov     [bp+var_1], 0           ; counter = 0

0x6B015: jmp     short loc_6B07F

; Loop to find first occupied slot
0x6B017: mov     al, [bp+var_1]
0x6B01A: mov     ah, 0
0x6B01C: shl     ax, 2                   ; Slot * 4
0x6B01F: mov     dx, 602Eh
0x6B022: mov     bx, ax
0x6B024: mov     es, dx
0x6B026: cmp     byte ptr es:[bx+1], 0   ; Check if slot has data
0x6B02C: jz      short loc_6B079         ; Skip if empty

; Found first slot
0x6B02E: cmp     [bp+var_2], 0FFh        ; Is this first iteration?
0x6B032: jnz     short loc_6B03C         ; No, skip default selection
0x6B034: mov     al, [bp+var_1]
0x6B037: mov     [bp+var_2], al          ; Store first slot index

; Additional slot validation logic continues...
```

**Analysis**:
- Finds first non-empty squadron slot
- Sets default selection to first available slot
- Stores selected slot index in `var_2`

---

## Campaign State Memory Layout

### Global Segments Involved

```
Segment 4FC2: System dispatcher parameters
Segment 602E: Menu state and UI data
Segment 7894: Campaign data buffers
Segment 709F: UI rendering data
```

### Key Global Variables

```c
// Segment 7894 (Campaign Data)
far byte byte_7A30C;           // Slot list initialized flag
far byte byte_7A302;           // Available slot count
far byte graphics_mode_flag;   // Display mode (3 = full graphics)
far dword dword_79E60;         // Base pointer to campaign buffer

// Segment 602E (Menu State)
far dword current_menu_slot_ptr;   // Pointer to selected slot
far byte byte_14E5A0;              // Current UI state
far byte byte_14E5A1;              // Previous UI state
far byte byte_14E5A2;              // UI active flag
far byte byte_14E5C8;              // Slot flag 0
far byte byte_14E5C9;              // Slot flag 1
far byte byte_14E5CA;              // Slot flag 2

// Segment 709F (UI Rendering)
far word word_70A2A;               // Max slot count
far byte byte_71BD6;               // UI mode flag
far byte byte_71BD7;               // UI state flag
```

---

## Campaign File Format (Inferred)

### .CAM File (Campaign State)

```c
struct CampaignFile {
    // Header
    uint16_t version;               // File format version
    uint16_t file_size;             // Total file size
    
    // Date/Time
    uint16_t campaign_day;          // Day counter (1-N)
    uint16_t campaign_time;         // Time of day (0-2359?)
    
    // Territory Control
    uint8_t allied_territory_pct;   // Allied territory percentage
    uint8_t enemy_territory_pct;    // Enemy territory percentage
    
    // Mission History
    uint16_t missions_flown;
    uint16_t missions_accomplished;
    uint16_t sorties_flown;
    
    // Air Combat Statistics
    uint16_t allied_aircraft_lost;
    uint16_t enemy_aircraft_destroyed;
    uint16_t enemy_class_a_fighters;    // MiG-29, Su-27, etc.
    uint16_t enemy_class_b_fighters;    // MiG-21, F-5, etc.
    uint16_t enemy_bombers;
    uint16_t enemy_attack;
    uint16_t enemy_helicopters;
    uint16_t enemy_transports;
    
    // Ground Target Statistics
    uint16_t targets_destroyed;
    uint16_t class_a_targets;       // Nuclear plants, command centers
    uint16_t class_b_targets;       // Airbases, bridges, SAM sites
    uint16_t class_c_targets;       // Army bases, bunkers
    uint16_t class_d_targets;       // Buildings, hangars, tanks
    
    // Campaign Rating
    uint16_t ordnance_efficiency;   // Ordnance/target ratio
    uint16_t overall_rating;        // Combined campaign score
    
    // Theater Data
    uint8_t theater_id;             // 0=Kuwait, 1=Israel, etc.
    uint8_t weather_state;          // Current weather
    uint8_t ceiling_height;         // Cloud ceiling
    
    // Variable-length data follows...
    // - Available mission list
    // - Ground unit positions
    // - Front line data
};
```

### .SQU File (Squadron Data)

```c
struct SquadronFile {
    // Squadron Identity
    char squadron_name[32];         // Squadron name
    uint8_t insignia_id;            // Selected insignia graphic
    uint8_t wing_assignment;        // 0=1st Wing, 1=2nd Wing, etc.
    
    // Squadron Commander
    char commander_name[32];        // Pilot name
    char commander_callsign[16];    // Pilot callsign
    uint8_t commander_rank;         // Rank (LT, CAPT, MAJ, etc.)
    
    // Squadron Statistics
    uint16_t squadron_missions;
    uint16_t pilots_active;
    uint16_t pilots_killed;
    uint16_t pilots_mia;
    
    // Pilot Roster (variable-length)
    uint8_t pilot_count;            // Number of pilots
    Pilot pilots[pilot_count];      // Pilot records
};

struct Pilot {
    char name[32];
    char callsign[16];
    uint8_t rank;                   // 0=LT, 1=CAPT, 2=MAJ, etc.
    uint8_t status;                 // 0=ACTIVE, 1=FATIGUED, 2=INJURED, 3=COURT_MARTIALED
    
    uint16_t missions_flown;
    uint16_t awards;
    uint16_t flight_hours;
    uint16_t plane_kills;
    uint16_t merits;
    
    // Skill Ratings (0-100?)
    uint8_t dogfighting_skill;
    uint8_t bombing_skill;
    uint8_t navigation_skill;
    uint8_t guns_skill;
    uint8_t rear_aspect_ir_skill;
    uint8_t all_aspect_ir_skill;
    uint8_t radar_missile_skill;
    uint8_t cas_ordnance_skill;
    uint8_t heavy_ordnance_skill;
};
```

### .MIS File (Mission Data)

```c
struct MissionFile {
    uint8_t mission_count;          // Number of available missions
    Mission missions[mission_count];
};

struct Mission {
    uint8_t mission_type;           // 0=CAP, 1=CAS, 2=STRIKE, etc.
    uint8_t time_of_day;            // 0=0600, 1=1200, 2=1800, 3=2300
    uint8_t weather;                // Weather condition
    uint8_t ceiling;                // Cloud ceiling
    
    // Target Information
    uint8_t target_count;           // Number of targets (1-8)
    Target targets[8];
    
    // Flight Configuration
    uint8_t flight_count;           // Number of flights (1-N)
    Flight flights[flight_count];
};

struct Target {
    uint8_t target_type;            // 0=AIRBASE, 1=SAM, 2=BRIDGE, etc.
    uint16_t position_x;            // Grid X coordinate
    uint16_t position_y;            // Grid Y coordinate
    uint8_t priority;               // Target priority (1-8)
    uint8_t damage_state;           // 0=intact, 100=destroyed
};

struct Flight {
    uint8_t aircraft_count;         // 1-4 aircraft
    uint8_t formation;              // 0=WEDGE, 1=ECHELON, etc.
    
    // Loadout per aircraft
    Loadout loadouts[4];
    
    // Pilot assignments
    uint8_t pilot_indices[4];       // Index into squadron pilot roster
    
    // AI Settings
    uint8_t ai_aggressiveness;      // 0=DUMB, 1=PASSIVE, 2=AGGRESSIVE
    uint8_t engagement_rules;       // Bit flags: AIR ON/OFF, GRND ON/OFF
};
```

### .TRG File (Target Data)

```c
struct TargetFile {
    uint16_t target_count;          // Total targets in theater
    TargetState targets[target_count];
};

struct TargetState {
    uint8_t target_type;            // Building type
    uint16_t position_x;
    uint16_t position_y;
    uint8_t damage_percent;         // 0-100
    uint8_t priority;               // Strategic value
    uint8_t defending_force;        // SAM/AAA coverage
};
```

### .TSK File (Task Data)

```c
struct TaskFile {
    uint8_t active_task_count;
    Task active_tasks[active_task_count];
};

struct Task {
    uint8_t task_type;              // Mission type
    uint8_t assigned_squadron;      // Squadron assigned to task
    uint8_t completion_percent;     // 0-100
    uint16_t time_remaining;        // Minutes until deadline
};
```

### .SHP File (Ship/Naval Data)

```c
struct ShipFile {
    uint8_t ship_count;             // Number of ships in theater
    Ship ships[ship_count];
};

struct Ship {
    uint8_t ship_type;              // 0=KUZNETSOV, 1=KIROV, etc.
    uint16_t position_x;
    uint16_t position_y;
    uint8_t damage_state;           // 0-100
    uint8_t allegiance;             // 0=ALLIED, 1=ENEMY
    uint8_t task_force_id;          // Group assignment
};
```

---

## Mission-to-Mission Flow

### Campaign Progression Sequence

```
[Mission End]
     ↓
Mission Result Calculation
     ↓
Update Campaign State (.CAM)
     ├─→ Advance time
     ├─→ Update territory percentages
     ├─→ Update statistics
     └─→ Calculate new available missions
     ↓
Update Squadron Data (.SQU)
     ├─→ Update pilot statistics
     ├─→ Update pilot status (fatigue, injury)
     ├─→ Update squadron statistics
     └─→ Check for promotions/awards
     ↓
Update Target States (.TRG)
     └─→ Mark targets as destroyed/damaged
     ↓
Update Task States (.TSK)
     └─→ Update mission objectives completion
     ↓
Update Naval Positions (.SHP)
     └─→ Move ship task forces
     ↓
Save All Files to Disk
     ↓
[Return to Squadron Menu]
     ↓
Load Updated Campaign
     ↓
[Select Next Mission]
```

### Campaign Advancement Triggers

**Time Advancement**:
- After each mission, time advances (6 hours? 12 hours?)
- Missions available at specific times: 0600, 1200, 1800, 2300
- Day counter increments after 2300 mission

**Territory Changes**:
- Mission success: Allied territory +X%, Enemy territory -X%
- Mission failure: Enemy territory +X%, Allied territory -X%
- Percentage based on mission objective importance

**Dynamic Mission Generation**:
- Available missions depend on front line position
- Target priorities change based on campaign state
- Mission types vary based on strategic needs

**Pilot Status Changes**:
- After mission: Pilot marked as FATIGUED (needs rest)
- If ejected: Pilot marked as INJURED (unavailable for N days)
- If friendly fire: Pilot marked as COURT_MARTIALED (removed)
- After N missions: Pilot gains skill improvements
- After M kills: Pilot promoted (LT → CAPT → MAJ → LT COL → COL)

**Supply System**:
- Aircraft lost in mission: Subtracted from available pool
- Weapons expended: Replenished over time
- Ground units: Advance/retreat based on campaign state

---

## Campaign Save System - DISCOVERED!

### campaign_save_temp_file_write @ 0x136133

**Function Profile**:
```
Size: 368 bytes
Called by: 6 locations:
  - overlay_r49_processor @ 0x172031
  - sub_173EA0 @ 0x1740F2
  - game_mode_r48_main_coordinator @ 0x175BF5
  - game_mode_r53_main_coordinator @ 0x185177
  - r53_head_garbage_fragment @ 0x1863D0
  - overlay_r55_dispatcher @ 0x190518
```

This is **NOT** the main campaign saver, but rather a **temporary save writer** that creates intermediate state files during menu operations.

### Campaign Save Flow

#### Temporary Save File Format

Filename: `[N]TEMP.DAT` (where N is a slot number)

Example: `0TEMP.DAT`, `1TEMP.DAT`

**Saved Data Blocks**:
```asm
; Block 1: Campaign data (14,000 bytes)
0x1361BE: dword_79E60+0xBB84 → Size 0x36B0 (14,000 bytes)

; Block 2: Extended data (20,000 bytes)  
0x1361E4: dword_79E5C → Size 0x4E20 (20,000 bytes)

; Block 3: System state 1 (2 bytes)
0x1361F8: 4FC2:0x132 → Size 0x2 (2 bytes)

; Block 4: System state 2 (2 bytes)
0x13620B: 4FC2:0x12E → Size 0x2 (2 bytes)

; Block 5: System state 3 (2 bytes)
0x13621E: 4FC2:0x130 → Size 0x2 (2 bytes)

; Block 6: Mission state (2 bytes)
0x136231: 7894:0x121E → Size 0x2 (2 bytes)

; Block 7: Extended state (16 bytes)
0x136244: 4FC2:0x158 → Size 0x10 (16 bytes)

; Block 8: UI state (8 bytes)
0x136257: 7894:0x1588 → Size 0x8 (8 bytes)

; Block 9: Variable-length menu state
0x13626A: 602E:0x3D2 → Size word_151C94 (variable)
```

**Total: ~34KB of temporary state**

#### Analysis: Why Temporary Save?

The temp file is written **during menu operations**, not after mission completion. This allows:
1. **Crash recovery**: If game crashes in menus, state is preserved
2. **Menu rollback**: Undo changes if user cancels
3. **Multiplayer sync**: Send state to other players without committing to campaign

### Main Campaign Writer - STILL SEARCHING

The temp file writer suggests the main campaign writer has a similar structure but:
- Writes to `.CAM`, `.SQU`, `.MIS`, `.TRG`, `.TSK`, `.SHP` files
- Called after mission completion, not during menus
- Much larger (similar to 2056B `squad_campaign_file_loader`)

**Search Strategy**:
- Look for functions that **write** operation 0x0A (instead of read)
- Called from mission debriefing or end-of-mission handler
- References same campaign file strings as loader

### Mission Selection Functions

- **Mission generator**: Creates available mission list based on campaign state
- **Mission briefing loader**: Loads mission details from .MIS file
- **Flight configurator**: Sets up flights and loadouts
- **Mission launcher**: Transitions from menu to in-game

### UI Functions

- **ui_text_render_engine** @ unknown: Renders menu text
- **ui_slot_count_tally** @ unknown: Counts available squadrons
- **ui_slot_list_mode_enter** @ 0x6AE59: Enters slot selection mode

### Dispatcher Functions

- **op_dispatch_far_entry** @ unknown: DOS interrupt wrapper
  - Operation 4: OPEN file (variant)
  - Operation 6: OPEN file (standard)
  - Operation 8: CLOSE file
  - Operation 10: READ file (standard)
  - Operation 12: READ file (variant)

---

---

## Squadron Mission File Loader @ 0x17B437

### Function Profile

```
Size: 4516 bytes (larger than squad_campaign_file_loader!)
Called by: overlay_r4F_handler @ 0x17AC3E
Makes: 104 function calls
Strings: 9 references
```

### Purpose

This function loads **mission-specific data** when entering mission planning:

**Files Loaded**:
1. `.MTV` - Mission Text/Descriptions (`"...`.MTV"`)
2. `.SQU` - Squadron data (reloaded)
3. `.SHP` - Shape/3D model references (`"7..`.SHP"`)
4. `.TSK` - Task definitions (`"...`.TSK"`)
5. `misstext.bin` - Mission text database (`"86.`misstext.bin"`)

### Key Data Structures

**Mission Slot Array**:
```c
// Located at mission_slot_array_ptr @ segment 7894
struct MissionSlot {
    char name[20];          // Mission display name
};

MissionSlot mission_slots[64];  // 64 missions × 20 bytes = 1,280 bytes
```

**Initialization Loop** (0x17B45E-0x17B491):
```asm
; Initialize 64 mission slots with space + null
for (int i = 0; i < 64; i++) {
    mission_slots[i].name[0] = 0x20;  // ' ' space character
    mission_slots[i].name[1] = 0x00;  // null terminator
}
```

### Mission Data Flow

```
Mission Selection
     ↓
squadron_mission_file_loader @ 0x17B437
     ↓
Load .MTV file (mission descriptions)
     ↓
Load .SQU file (squadron roster for this mission)
     ↓  
Load .SHP file (aircraft 3D models available)
     ↓
Load .TSK file (mission objectives/tasks)
     ↓
Load misstext.bin (mission briefing text database)
     ↓
Populate mission_slots[64] array
     ↓
Display Mission Selection Menu
```

**Branch at 0x17B4EB**: Tests `word_14F8BE` bit 0
- If **0**: Load files from disk (first time)
- If **1**: Update state from memory (already loaded)

This is an optimization - mission data is cached in memory and only reloaded if changed.

---

## Overlay R4F Handler @ 0x1793C0

### Function Profile

```
Size: 7661 bytes (MASSIVE - largest campaign function)
Called by: sub_2C7B1 @ 0x2C7B4
Makes: 262 function calls (!!!)
Strings: 23 references (16 campaign files)
```

### Purpose

This is the **main squadron/campaign menu coordinator** that handles:
- Squadron selection
- Campaign loading
- Mission planning
- File I/O operations
- UI rendering
- Multiplayer synchronization

### Campaign File References (All 6 Types!)

**Referenced Files**:
- `.SQU` - 8 references (squadron data)
- `.TSK` - 4 references (task data)
- `.SHP` - 3 references (ship/shape data)
- `.TRG` - 2 references (target data)
- `DAY` - 3 references (`"P0.`DAY "` - daily state?)

### Temporary Debug Files

The function creates **debug dump files** during campaign operations:
- `cdumpr.tmp` - Read debug dump
- `cdumpf.tmp` - Flight debug dump
- `cdumpw.tmp` - Write debug dump

These suggest **development/debugging features** left in the release build.

### Flight Array Structure

**Flight Data Pointer** @ 0x1795E9:
```c
// Located at flight_array_ptr @ segment 7894
struct Flight {
    byte data[130];         // Flight configuration data
};

Flight flights[N];          // Variable count based on mission
```

**Size**: 0x410 (1,040 bytes) read per flight array operation.

### Theater Names

Found **theater string** "India" @ 0x17A2B3, confirming the India theater is hardcoded into this function.

### Key Operations

1. **Graphics Mode Check** (0x179422):
   - Mode 3 = Full graphics UI
   - Mode 0 = Text-only UI
   - Different rendering paths for each

2. **Squadron Validation** (0x179475):
   - Checks `byte_7A302` (available squadron count)
   - Sets `word_14F8BE` bit 0 if squadrons exist

3. **State Initialization** (0x1794EA):
   - Calls `sub_13AA6A` (initialization routine)
   - Clears mission arrays
   - Resets UI state

4. **Campaign Load Trigger** (0x179528):
   - Calls `tail_bridge_to_r30_state_init_all_k`
   - This likely triggers the main campaign load sequence

### Relationship to Campaign Writer

This function is **NOT** the writer, but it:
- Orchestrates when saves happen
- Manages state that will be written
- Calls other functions that perform actual writes

The actual campaign writer is likely called from within this massive coordinator.

---

## Next Steps

1. **Extract hardcoded filename at DS:0A34Ah**
   - Identify mystery file loaded between .CAM and .SQU

2. **Locate mission result handler**
   - Find function called after mission end
   - Trace how statistics are updated

3. **Find campaign file writer**
   - Reverse of `squad_campaign_file_loader`
   - Saves updated campaign state to disk

4. **Analyze mission generator**
   - How does game determine available missions?
   - What algorithm creates mission parameters?

5. **Map pilot management functions**
   - Pilot status change logic
   - Fatigue recovery system
   - Promotion/award system

6. **Decode target priority system**
   - How are targets selected for missions?
   - What determines target value?

7. **Understand territory calculation**
   - How does mission success affect percentages?
   - What is the victory condition?

8. **Extract campaign file structures**
   - Run campaign, hex dump .CAM/.SQU files
   - Verify hypothesized structures

---

## Tools Needed

### File Analysis
```bash
# Extract campaign files from running game
# Compare before/after mission completion
# Identify changing bytes → field locations
```

### IDA Scripts
```python
# extract_campaign_strings.py - Find all campaign-related strings
# trace_campaign_save.py - Find campaign write functions
# analyze_mission_generator.py - Analyze mission creation
# map_pilot_system.py - Map pilot management functions
```

### Runtime Analysis
- DOSBox debugger to capture file I/O
- Monitor file writes after mission
- Trace execution from mission end to menu

---

## Summary

The campaign system is **file-based with 6+ file types** per squadron slot:
- `.CAM` = Campaign state (territory, statistics, date)
- `.SQU` = Squadron data (pilots, commander, history)
- `.MIS` = Mission data (available missions, configurations)
- `.TRG` = Target data (positions, damage states)
- `.TSK` = Task data (objectives, assignments)
- `.SHP` = Ship data (naval positions, task forces)

**Campaign progression occurs between missions**, with all files loaded into a 30KB memory buffer, modified during gameplay, and saved back to disk after mission completion.

The system is **fault-tolerant**, continuing to load even if files are missing, suggesting graceful degradation for corrupted saves.

**Next critical function**: The campaign save/write function (reverse of `squad_campaign_file_loader`), which updates all 6 files after mission completion.
