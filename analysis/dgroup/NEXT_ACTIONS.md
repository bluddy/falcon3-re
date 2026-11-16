# Next Actions - View Switching Investigation

## Current Status: Dispatchers Found! ✅

We've successfully traced input from keyboard → queue → dispatcher → handlers.

**Found:**
- Handler for scan 0x03 (Key 2 - Ground view - external)
- Handler for scan 0x04 (Key 3 - Front cockpit - internal)

**Need:** Examine these handlers to understand how they set/modify `r15_external_view_flag`.

---

## IMMEDIATE NEXT STEP: Examine Handler Functions

### Handler Addresses to Investigate

From `game_mode_r53_main_coordinator` dispatcher at 0x182476:

1. **Handler for 0x03 (Ground View - External)**
   - Address: 0x3E5 (relative to R53 segment)
   - Need absolute linear address

2. **Handler for 0x04 (Cockpit View - Internal)**  
   - Address: 0x408 (relative to R53 segment)
   - Need absolute linear address

### How to Find Absolute Addresses

The addresses 0x3E5 and 0x408 are relative to where the code segment in the jump table points. Need to:

1. Look at the dispatcher at 0x182476 in IDA
2. Follow the `jmp word ptr cs:[bx+8]` instruction
3. See where it actually jumps to
4. That's the absolute address of the handler

OR:

Look at the disassembly in `input_dispatch_patterns.json` around address 0x182491 (the jump table access). The addresses right after might be the handlers.

### What to Look For in Handlers

When you examine each handler function:

1. **Direct flag write**:
   ```assembly
   mov cs:r15_external_view_flag, 0   ; or 1
   ```

2. **Indirect flag write**:
   ```assembly
   mov bx, 107762h
   mov byte ptr [bx], al
   ```

3. **Function calls**:
   - Does it call a view setup function?
   - Does that function write the flag?

4. **Parameter passing**:
   - Does it push a view type parameter?
   - Does it call a generic view handler with that parameter?

### Expected Behavior

- Handler 0x3E5 (ground view) should set flag to **1** (external)
- Handler 0x408 (cockpit view) should set flag to **0** (internal)

OR they might call different view setup functions that handle the flag internally.

---

## SECONDARY TASKS

### 1. Find Remaining View Key Handlers

Only found 2 of 10 view keys. Where are the others?

**Approach A**: Check other game mode coordinators
- Search other functions that read `input_flag_pending_2`
- Look for similar dispatcher patterns
- Check overlay functions

**Approach B**: Check if handlers are nested
- Maybe sub_3E5 and sub_408 have their own dispatchers
- They might handle multiple related keys

**Approach C**: Look for dynamic tables
- Tables might be loaded/switched based on game state
- Different tables for different modes

### 2. Document Everything in IDA

Once you understand the handlers:

- Rename sub_3E5 → ground_view_handler (or similar)
- Rename sub_408 → cockpit_view_handler
- Add comments explaining the dispatch mechanism
- Mark the jump tables with structure comments
- Add flowchart comments

### 3. Create Final Report

Document:
- Complete input flow diagram
- All handler functions and what they do
- How r15_external_view_flag gets modified
- Why only 1 write was found in initial search
- All view key mappings

---

## Tools Ready to Use

### IDA Scripts Available

All in `analysis/dgroup/`:

1. **examine_input_dispatch_context.py** - Already run, found dispatchers
2. **find_table_addresses.py** - Already run, found table locations
3. **examine_jump_tables.py** - Needs fixing for handler analysis

### Create New Script

To examine the handlers, create:
```python
# examine_view_handlers.py

def analyze_handler(addr):
    """
    Examine a view handler function.
    Look for:
    - Writes to 0x107762
    - Calls to view setup functions
    - Parameter passing
    """
    # Implementation here
```

---

## Key Questions to Answer

1. **How does ground view handler (0x3E5) differ from cockpit handler (0x408)?**

2. **Do they write to r15_external_view_flag (0x107762) directly?**

3. **If not direct, what's the call chain that eventually sets it?**

4. **Where are the other 8 view key handlers?**

5. **Why did initial flag write search only find 1 write?**

---

## Success Criteria

Investigation complete when:

✅ Know exact mechanism for flag modification
✅ Found all view key handlers (or explained why some missing)
✅ Can trace complete execution: key press → handler → flag set → view change
✅ Documented in IDA with proper names and comments
✅ Created final report with flowcharts

---

## If You Get Stuck

### Can't find handler absolute addresses?
- Look at jump table disassembly around 0x182491
- Check segment base for R53_569Fs
- Try searching for the opcodes near the relative addresses

### Handlers don't write flag?
- They might call other functions
- Follow the call chain deeper
- Check if they modify a view state structure

### Can't find other handlers?
- May be in different overlays loaded for different game modes
- Some keys might share handlers
- Keys 9 might be unused

### Still confused?
- Re-read FINDINGS_SUMMARY.md for complete picture
- Check input_dispatch_patterns.json for raw disassembly
- Ask for help with specific addresses/functions

---

**BOTTOM LINE**: We found the dispatchers! Next is understanding the handlers. You're 80% done!
