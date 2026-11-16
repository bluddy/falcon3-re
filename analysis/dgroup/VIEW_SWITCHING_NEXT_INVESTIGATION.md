# View Switching Investigation - Next Steps

## Summary of Findings

### Input Capture (FOUND ✓)
- **Location**: `input_poll_handler` at `0x12FAC3` (R29_3174s segment)
- **Number key capture loop**: `0x130709` - `0x130749`
- **Storage**: Scan code written to `input_flag_pending_2` at `0x130749`
- **Scan codes**:
  - Keys 1-9: scan codes 0x02-0x0A
  - Key 0: scan code 0x0B

### View Key Mapping (from Manual)
**Internal/Cockpit Views** (should use Path A, flag=0):
- Key 3 (0x04): Front view
- Key 4 (0x05): Left view
- Key 5 (0x06): Rear view
- Key 6 (0x07): Right view

**External Views** (should use Path B, flag=1):
- Key 1 (0x02): Satellite view
- Key 2 (0x03): Ground view
- Key 7 (0x08): Wingman view
- Key 8 (0x09): Padlock view
- Key 0 (0x0B): Chase plane view

### View Flag Status (INCOMPLETE ❓)
- **Flag**: `r15_external_view_flag` at `cs:0x107762` (R15_5E0Bs segment)
- **Writes Found**: Only 1 - initialization in `view_mode_set` at `0x1087B2`
- **Reads Found**: 4 - in simulation loop and related functions
- **Problem**: No runtime writes found despite user confirming views can switch during flight!

### Input Dispatch (MISSING ❓)
- **Queue**: `input_flag_pending_2` at `es:0x79B66`
- **Reads**: 37 functions across multiple overlays read this flag
- **Problem**: Haven't found the dispatcher that processes scan codes 0x02-0x0B

## Top Priority Investigation Targets

### Primary Candidates - Game Mode Coordinators

These functions read `input_flag_pending_2` multiple times, suggesting they handle input dispatch:

1. **r29_tactical_screen_coordinator** (R29_2F8As segment)
   - Read at `0x12DFD6`
   - Read at `0x12EEDC`
   - Read at `0x12F512`
   - **Action**: Manually examine each read location in IDA for next 30-50 instructions
   - **Look for**: cmp/jz chains, jump tables, calls based on scan code value

2. **game_mode_r53_main_coordinator** (R53_569Fs segment)
   - Read at `0x182476`
   - Read at `0x183834`
   - Read at `0x183FA6`
   - Read at `0x184B10`
   - Read at `0x185068`
   - **Action**: Same as above

### What to Look For in IDA

When examining code after each `mov ax, es:input_flag_pending_2`:

1. **Normalization**: `sub ax, 2` (converts 0x02-0x0B to 0x00-0x09)
2. **Bounds check**: `cmp ax, 10` or similar
3. **Switch table**: `jmp [table + ax*2]` or `shl ax, 1 ; add ax, offset ; jmp ax`
4. **If/else chain**: Multiple `cmp ax, <value>` followed by `jz`
5. **Parameterized call**: `push ax ; call <function>`
6. **Comparisons with our scan codes**: Look for cmp with 2,3,4,5,6,7,8,9,10,11 (0x02-0x0B)

### Alternative Hypotheses

If dispatch not found in coordinators:

1. **Indirect writes**: The flag might be written via pointer/indirect addressing
   - Search for: `mov [bx], al` where bx might contain 0x107762
   - Search for: segment register tricks

2. **View functions set flag**: Each view setup function might set the flag
   - The dispatcher calls different view functions
   - Each function sets flag appropriately as side effect

3. **Flag is session-static**: The flag is set once per mission/mode
   - View keys just change camera position within that mode
   - Both internal and external views work in same mode

4. **Different mechanism**: View switching uses a different variable
   - `r15_external_view_flag` might control something else
   - Actual view state stored elsewhere

## Manual Investigation Steps

1. **Open IDA**: `FALCONCD.EXE.i64`

2. **Navigate to first target**: Press 'G' and go to `0x12DFD6`

3. **Examine context**:
   - This should be `mov ax, es:input_flag_pending_2`
   - Look at next 30-50 instructions
   - Look for patterns listed above

4. **Document findings** for each of the 8 target addresses

5. **If dispatcher found**:
   - Document the dispatch mechanism
   - Find which functions are called for scan codes 0x02-0x0B
   - Trace those functions to see if they modify `r15_external_view_flag`

6. **If no dispatcher found**:
   - Re-evaluate hypothesis
   - Consider that view switching might work differently than expected

## Questions to Answer

1. Is there a dispatcher that processes `input_flag_pending_2`?
2. If yes, how does it map scan codes to handlers?
3. Do the handlers modify `r15_external_view_flag`?
4. If not, how do external vs internal views actually differ in code execution?

## Files Created

- `find_view_key_dispatch.py` - Analyzed input_flag reads by function
- `find_input_dispatcher.py` - Listed all 37 functions that read the flag
- `examine_input_dispatch_context.py` - IDA script to analyze dispatch patterns (needs to be run)
- `hypothesis_view_switching.md` - Initial hypothesis about view switching
- This file - Next investigation steps

## Current Status

**BLOCKED**: Need to manually examine IDA database at the 8 target addresses to find the dispatcher logic. Automated scripts cannot run without proper IDA automation setup.

**NEXT**: Manual IDA inspection required.
