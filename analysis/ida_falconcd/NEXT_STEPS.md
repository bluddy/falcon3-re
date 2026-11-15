# View Mode Switching - Next Steps

## What We Found

### 1. Correct Keys Identified
- Number keys 0-9 (scan codes 0x02-0x0B) control views
- NOT F2/F3/F4 (those are zoom/rotation)
- Keys: 1=satellite, 2=ground, 3-6=cockpit directions, 0=chase, 7=wingman, 8=padlock

### 2. Key Storage Mechanism Found
- Location: `input_poll_handler` @ 0x12FAC3
- Number keys handled at 0x130709-0x130749
- Loop compares scan code (var_6) against range 1-0xD (includes 0-9 keys)
- Match found → stores scan code in `input_flag_pending_2` @ 0x130749

### 3. Flag Usage Pattern
`input_flag_pending_2` is a **message queue** variable used across 170+ locations in multiple overlays

## The Missing Link

**We still need to find WHERE the number key codes are processed to actually change `r15_external_view_flag`.**

The flow is:
1. User presses number key (e.g., "1" for satellite view)
2. `input_poll_handler` stores scan code in `input_flag_pending_2`
3. **UNKNOWN CODE** reads `input_flag_pending_2` and:
   - Determines if it's a cockpit view (3-6) or external view (0,1,2,7,8)
   - Sets `r15_external_view_flag` to 0 (cockpit) or 1 (external)
   - Sets additional camera state variables for specific view

## Search Strategy

###  Option 1: Find R15 Reader of input_flag_pending_2
Search the R15 overlay (R29_3174s segment and R15_5E0Bs segment) for code that:
- Reads `input_flag_pending_2`
- Has switch/conditional logic on values 0x02-0x0B
- Writes to `r15_external_view_flag` based on the value

### Option 2: Trace from input_poll_handler Exit
Follow execution flow AFTER `input_poll_handler` returns:
- Who calls `input_poll_handler`?
- What do they do with the result?
- Is there a dispatch loop that processes the stored key?

### Option 3: Search for Switch on Values 0-9
Look for switch statements or lookup tables that dispatch on values 0-9:
```asm
cmp ax, 2      ; satellite view
jz  set_external
cmp ax, 3      ; front cockpit
jz  set_cockpit
...
```

## Recommended Next Script

```python
# find_view_dispatch.py
#
# Search R15 segments for:
# 1. Reads of input_flag_pending_2
# 2. Comparisons with 0x02-0x0B (number key scan codes)
# 3. Writes to r15_external_view_flag in same function
# 4. Switch/dispatch patterns on small values
```

## Why This is Hard

The code that processes `input_flag_pending_2` might:
1. Be in a different function/overlay
2. Use a lookup table we haven't found
3. Be part of a larger state machine
4. Transform the scan code before comparison (e.g., subtract offset)

## Alternative Theory

Maybe `r15_external_view_flag` ISN'T set by number key handlers at all!

Instead:
- Each number key might call a DIFFERENT function directly
- Functions 0-2,7,8 might set flag=1 and configure external camera
- Functions 3-6 might set flag=0 and configure cockpit view
- The flag is set AS A SIDE EFFECT of view initialization, not explicitly

## Files Created This Session

- `find_number_key_handlers.py` - Found key storage code
- `extract_pre_switch_code.py` - Analyzed input_poll_handler flow
- `check_jump_target.py` - Found loop that stores scan codes
- `find_input_flag_processor.py` - Mapped 170+ uses of input_flag_pending_2
- `input_flag_refs.json` - Complete reference list

## Bottom Line

**We're ONE STEP AWAY from the answer!**

We know:
- ✅ Which keys control views (0-9)  
- ✅ Where keys are captured (`input_poll_handler`)
- ✅ Where scan codes are stored (`input_flag_pending_2`)
- ❌ Where scan codes are processed to set view flag

**Next**: Find the code that reads `input_flag_pending_2` in R15 and dispatches to view handlers.
