# Falcon 3.0 File I/O System Analysis

**Date**: 2026-11-11  
**Source**: IDA Pro extraction (FALCONCD.EXE_extracted.json/summary.txt)

## Overview

Successfully identified the file I/O system and .IDX/.DAT loading functions by examining the IDA database extraction.

## Key Discovery: .IDX/.DAT Loader Function

### sub_1297F0 - PICFONT Loader
**Address**: 0x1297F0  
**Strings Used**:
- `0x14E771`: ".`PICFONT.IDX"  (referenced at 0x129809)
- `0x14E781`: ".`PICFONT.DAT" (referenced at 0x12985b)

**Significance**: This function loads .IDX and .DAT file pairs - the exact format we decoded!

**Pattern**:
```
sub_1297F0:
    ... (setup) ...
    Reference: PICFONT.IDX at 0x129809
    ... (load index file) ...
    Reference: PICFONT.DAT at 0x12985b
    ... (load data file using index) ...
```

This is the **template** for how ALL .IDX/.DAT files are loaded.

## DOS File I/O Wrappers

Located core file I/O functions that wrap DOS INT 21h calls:

### file_open - 0x226BD
**DOS Function**: AH=0x3D (Open File)  
**Usage**: Opens a file by name, returns handle

### file_close - 0x226E4  
**DOS Function**: AH=0x3E (Close File)  
**Usage**: Closes file handle

### file_read - 0x226F5
**DOS Function**: AH=0x3F (Read File)  
**Usage**: Reads data from file into memory buffer

### file_write - 0x2271F
**DOS Function**: AH=0x40 (Write File)  
**Usage**: Writes data from memory to file

### file_lseek - 0x2274D
**DOS Function**: AH=0x42 (Seek File)  
**Usage**: Moves file pointer to specific offset

## Complete INT 21h Call Inventory

From IDA extraction, found **139 INT 21h calls** total:

**File Operations**:
- Open File (3Dh): 7 calls
- Close File (3Eh): 8 calls  
- Read File (3Fh): 8 calls
- Write File (40h): 8 calls
- Seek File (42h): 2 calls
- Create File (3Ch): 4 calls
- Delete File (41h): 1 call
- Find First (4Eh): 2 calls
- Find Next (4Fh): 1 call

**Memory Operations**:
- Allocate (48h): 5 calls
- Free (49h): 2 calls
- Resize (4Ah): 2 calls

**Other**:
- Get/Set Interrupt Vector: 11 calls
- Get Time: 2 calls
- Print String: Many calls
- Exit: Several calls

## String References Found

### Menu-Related Files
1. **PICFONT.IDX / PICFONT.DAT**
   - Loader: sub_1297F0
   - Purpose: Picture font graphics

2. **madfont.idx / madfont.dat**  
   - Loader: sub_1397CE (called at 0x139909, 0x139953)
   - Purpose: Another font system

### Data Files
3. **SQUAD**
   - Loader: sub_6A651
   - References: 46 total! (8 in sub_6A651, 38 in overlay functions)
   - Purpose: Squadron/campaign data
   - Likely pattern: "SQUAD" + number + ".CAM"

4. **HARPOON.DAT**
   - Loader: sub_1779A6 (at 0x1779BA)
   - Purpose: Harpoon missile data

## Key Functions to Analyze

### 1. sub_1297F0 - .IDX/.DAT Loader (PICFONT)
**Priority**: CRITICAL  
**Why**: Template for all .IDX/.DAT loading  
**What to extract**: Complete disassembly showing:
- How .IDX file is opened and read
- How index entries (offset, size) are parsed
- How .DAT file is opened
- How file_lseek positions to offset
- How data chunk is read
- RLE decompression (if done here)

### 2. sub_1397CE - Alternative .IDX/.DAT Loader (madfont)
**Priority**: HIGH  
**Why**: May show variations in loading pattern  
**Cross-reference**: Check if it calls sub_1297F0 or reimplements

### 3. sub_6A651 - SQUAD File Handler
**Priority**: HIGH  
**Why**: Handles .CAM campaign files (might contain AI behavior tables!)  
**Note**: 46 references suggest this is a major data loader

### 4. sub_1779A6 - HARPOON.DAT Loader
**Priority**: MEDIUM  
**Why**: Shows how single .DAT files (no .IDX) are loaded

## Expected .IDX/.DAT Loading Pattern

Based on our format analysis and string references:

```assembly
; Pseudocode for .IDX/.DAT loading
sub_load_idx_dat:
    ; 1. Open .IDX file
    lea dx, filename_idx        ; "PICFONT.IDX"
    call file_open              ; Returns handle in AX
    mov idx_handle, ax
    
    ; 2. Read index entries
    mov cx, index_entry_count * 4  ; 4 bytes per entry
    lea dx, index_buffer
    call file_read
    
    ; 3. Close .IDX
    mov bx, idx_handle
    call file_close
    
    ; 4. Open .DAT file
    lea dx, filename_dat        ; "PICFONT.DAT"
    call file_open
    mov dat_handle, ax
    
    ; 5. For each entry needed:
    load_loop:
        mov si, index_buffer
        mov ax, [si]            ; offset (word)
        mov cx, [si+2]          ; size (word)
        
        ; Seek to offset
        mov bx, dat_handle
        mov dx, ax              ; offset
        xor cx, cx              ; high word
        mov al, 0               ; SEEK_SET
        call file_lseek
        
        ; Read data chunk
        mov cx, [si+2]          ; size
        lea dx, data_buffer
        call file_read
        
        ; Decompress if needed
        call rle_decompress
        
        ; Upload to VGA or store
        call vga_upload / store_graphics
        
    ; 6. Close .DAT
    mov bx, dat_handle
    call file_close
```

## Next Steps to Complete Analysis

1. **Extract sub_1297F0 disassembly**:
   - Use IDA directly or create targeted script
   - Document complete loading sequence
   - Identify RLE decompression call

2. **Find RLE decompression function**:
   - Trace what sub_1297F0 calls after file_read
   - Look for loops processing 6-byte headers (00 04 width height)
   - Document algorithm

3. **Map menu file loading**:
   - Find where COMMMENU.IDX/.DAT are referenced
   - Trace to menu initialization
   - Connect to sub_683C5 (menu controller)

4. **Connect to AI system**:
   - Examine sub_6A651 (SQUAD handler)
   - Check if .CAM files contain AI behavior tables
   - Look for ARMS*.DAT loading (weapons → AI loadout data)

## Hypothesis: Centralized Resource Loader

Evidence suggests Falcon 3.0 uses a **generic .IDX/.DAT loader** that:
- Takes filename base as parameter (e.g., "PICFONT")
- Appends ".IDX" and ".DAT" automatically
- Returns data structure with loaded graphics/data
- Used by ALL game systems (menus, fonts, AI, weapons)

This explains why we couldn't find menu-specific file I/O - it's all centralized!

## Files to Search for Menu Loading

Now that we know the pattern, search for these strings:
- "COMMMENU" (communication menu)
- "SYSMENU" (system menu)  
- "DIFFMENU" (difficulty menu)
- "ARMSMENU" or references to ARMSDATA directory

These should lead to menu initialization code that calls the .IDX/.DAT loader.

## Status

- ✅ File I/O wrappers identified
- ✅ .IDX/.DAT loader function found (sub_1297F0)
- ✅ String references mapped
- ⏳ Need complete disassembly of loaders
- ⏳ Need RLE decompression algorithm
- ⏳ Need menu file references

**Blocker**: IDA batch mode scripts timing out. Need to either:
1. Use IDA GUI interactively to extract functions
2. Find these functions in existing exports
3. Use alternative disassembly approach

## Related Documentation

- `MENU_DATA_FORMAT_SPEC.md` - Complete .IDX/.DAT format (100% decoded)
- `MENU_SYSTEM_CODE_STRUCTURE.md` - Menu controller architecture
- `AI_SYSTEM_STATUS.md` - AI behavior flags (90% complete)
