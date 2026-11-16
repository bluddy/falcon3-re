# ACMI Investigation - Current Status

## What We've Confirmed

### ✅ ACMI System Exists
- ACMI menu option: "K4.`ACMI" (case 8 at 0x190A8B)
- ACMI files: acmi.dat, acmi.idx
- ACMI handler: sub_11CC39 at 0x11CC39

### ✅ Flag Has Only 1 Write
- **Confirmed**: Only 1 write to `view_pipeline_mode` (0x107762)
- **Location**: view_mode_set at 0x1087B2
- **Instruction**: `mov cs:view_pipeline_mode, al`

### ✅ Initialization Sets Mode to 0
At 0x1086EE: `mov al, 0`
At 0x1087B2: `mov cs:view_pipeline_mode, al`  ; AL = 0

The function clears MANY flags, all set to 0.

## The Core Mystery

**Question**: If the only write sets AL=0, how does ACMI mode set it to 1?

## Possible Explanations

### Theory A: Parameter-Based (MOST LIKELY)
The function `view_mode_set` might:
1. Check a parameter or global flag
2. Conditionally set AL to 0 or 1 based on context
3. The initialization at 0x1086EE might be overridden later in the function

**Evidence**:
- The function is 600 bytes - lots of code we haven't analyzed
- There are many conditional branches
- At 0x10871B: `cmp cs:byte_107A90, 0` - checking a flag!

**Action**: Analyze the FULL function flow, not just the write

### Theory B: AL Set Before Function Call
The caller might:
1. Set AL to desired mode (0 or 1)  
2. Call view_mode_set
3. Function uses AL parameter instead of hardcoding 0

**Evidence**: Need to check calling convention

**Action**: Find all callers and check what they do before calling

### Theory C: Wrong Hypothesis
Maybe `view_pipeline_mode` doesn't control ACMI at all!

**Evidence**: 
- We inferred ACMI from the name and user hint
- Never actually confirmed the flag controls it

**Action**: Re-examine what the flag ACTUALLY controls

## What To Do Next

### Priority 1: Analyze Full view_mode_set Function ⭐
Look at the function flow more carefully:
- Check the conditional at 0x10871B (byte_107A90)
- See if there's a path that sets AL=1 instead of 0
- The function is complex with multiple paths

### Priority 2: Find view_mode_set Callers
Who calls this function and in what context?
- Normal mission start
- ACMI playback start  
- Game mode switches

### Priority 3: Check What the Flag Controls
Look at the 4 places that READ the flag:
- 0x108A05 (in sub_108A05)
- 0x108BAC (in r15_simulation_loop) 
- 0x108FC2 (in sub_108FC2)

What do they actually DO based on the flag value?

## Most Promising Lead

**The conditional at 0x10871B**:
```assembly
0x10871B: cmp cs:byte_107A90, 0
0x108721: jz  short loc_10872E  ; Jump if 0
0x108723: ; Path 1 (byte_107A90 != 0)
0x10872E: ; Path 2 (byte_107A90 == 0)
```

This happens BEFORE the AL=0 initialization!

Maybe:
- byte_107A90 is an "ACMI mode" flag
- If set, the function takes a different path
- That path might set AL=1 instead of AL=0

## Files Created

- `ACMI_FINDINGS.md` - Initial findings
- `ACMI_INVESTIGATION_STATUS.md` (this file) - Current status
- `acmi_analysis.json` - Handler analysis
- `analyze_acmi.py` - Analysis script
- `find_all_flag_writes.py` - Exhaustive write search

## Recommendation

**Manually analyze view_mode_set in IDA**:
1. Open FALCONCD.EXE.i64
2. Navigate to 0x1086EC (view_mode_set)
3. Follow the function flow carefully
4. Check what byte_107A90 does
5. See if there's a path that sets view_pipeline_mode = 1

The answer is probably IN this function, we just need to trace it properly!

## Alternative: Ask User

Since you have experience with the game, you could confirm:
1. Does the game have an ACMI playback feature?
2. Is it a separate mode or just replay viewing?
3. Can you switch views in ACMI mode?

This might help us understand what the flag actually controls!
