# View Key Dispatch - FOUND!

## Discovery

Found input dispatchers that process view key scan codes!

### Dispatcher 1: r29_tactical_screen_coordinator at 0x12DFD6

**Pattern**: Loop-based table lookup with indirect jump
```assembly
mov ax, es:input_flag_pending_2   ; Read scan code from input queue
mov [bp+var_26], ax                ; Save it
mov cx, 4                          ; Loop counter = 4 entries
mov bx, 1E99h                      ; Table offset
loop_start:
  mov ax, cs:[bx]                  ; Read table entry (scan code)
  cmp ax, [bp+var_26]              ; Compare with input
  jz match_found                   ; Jump if match
  inc bx                           
  inc bx                           ; Move to next word
  loop loop_start
  jmp no_match
match_found:
  jmp word ptr cs:[bx+8]           ; Jump to handler (8 bytes after scan code)
```

**Table Address**: cs:0x1E99 (linear 0x12F9FC)

### Dispatcher 2: game_mode_r53_main_coordinator at 0x182476

**Pattern**: Same loop-based table lookup
```assembly
mov ax, es:input_flag_pending_2
mov cx, 4
mov bx, 3225h                      ; Different table
...same pattern...
jmp word ptr cs:[bx+8]
```

**Table Address**: cs:0x3225 (linear 0x1852D5)

**Table Entries Found**:
- Scan code **0x01** → handler at 0x3F3
- Scan code **0x03** → handler at 0x3E5 (Key 2 - Ground view)
- Scan code **0x04** → handler at 0x408 (Key 3 - Front cockpit)
- Scan code **0xFF** → handler at 0x54A (Special code)

## Scan Code Mapping

From manual and keyboard capture analysis:

| Key | Scan Code | View Type | Internal/External |
|-----|-----------|-----------|-------------------|
| 1 | 0x02 | Satellite | External |
| **2** | **0x03** | **Ground** | **External** ✓ Found |
| **3** | **0x04** | **Front cockpit** | **Internal** ✓ Found |
| 4 | 0x05 | Left cockpit | Internal |
| 5 | 0x06 | Rear cockpit | Internal |
| 6 | 0x07 | Right cockpit | Internal |
| 7 | 0x08 | Wingman | External |
| 8 | 0x09 | Padlock | External |
| 9 | 0x0A | ? | ? |
| 0 | 0x0B | Chase plane | External |

## Key Finding

**We found handlers for scan codes 0x03 and 0x04!**

These are:
- **0x03 = Key 2 = Ground view (EXTERNAL)**
- **0x04 = Key 3 = Front cockpit (INTERNAL)**

This is EXACTLY what we need! One external view key and one internal view key.

## Next Steps

### 1. Examine Handler Functions

Need to examine what these handlers do:
- **sub_3E5** (handler for 0x03 - ground view)
- **sub_408** (handler for 0x04 - cockpit view)

Questions:
- Do they write to `r15_external_view_flag` (0x107762)?
- Do they call view setup functions?
- How do they differ?

### 2. Find Remaining View Keys

The table only has 4 entries but we need handlers for all view keys (0x02-0x0B).

Possibilities:
- Multiple tables in different game modes
- Some keys handled elsewhere
- Dynamic table loading
- Nested dispatchers

### 3. Verify Flag Modification

Need to trace execution through the handlers to see if/when `r15_external_view_flag` gets modified.

## Table Structure (Hypothesis)

Based on the dispatch code `jmp word ptr cs:[bx+8]`:

```
[Scan Code Word] [unused/padding 6 bytes] [Handler Address Word]
```

Or possibly:
```
[Entry 0 Scan Code]
[Entry 1 Scan Code]  
[Entry 2 Scan Code]
[Entry 3 Scan Code]
[padding/other data]
[Entry 0 Handler]
[Entry 1 Handler]
[Entry 2 Handler]
[Entry 3 Handler]
```

Need to dump actual table bytes to confirm structure.

## Success Markers

✅ Found input capture (0x130749)
✅ Found input queue (input_flag_pending_2)
✅ Found dispatchers (2 locations)
✅ Found view key handlers (0x03 and 0x04)
❓ Flag modification mechanism (next to investigate)

## Files with Details

- `input_dispatch_patterns.json` - Full dispatcher disassembly
- `jump_table_addresses.json` - Table addresses and entries
- `examine_input_dispatch_context.py` - Script that found the dispatchers
- `find_table_addresses.py` - Script that located the tables
