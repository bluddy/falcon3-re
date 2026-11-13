# CORRECTION: word_2E139 is NOT Control Input!

**Date:** November 11, 2026  
**Session 3 Discovery**

## ERROR IN SESSION 2

**Previous Assumption (WRONG):**
- `cs:word_2E139` = scaled control input (0..127)
- Set by `tick_rate_compute`

**Reality:**
- `cs:word_2E139` = frame period/time delta
- Set by BOTH `tick_rate_compute` AND from entity data structures

## Evidence

### 1. tick_rate_compute Description

From function names analysis:
```
"tick_rate_compute"
"void far; CX=cs:22220 (tick count); if 0 -> AX=4,BX=40h; 
 else AX=0x123/CX clamped >=4, BX=0x40; retf. Returns rate+period"
"50B, 12K calls, 2 callers. Computes a rate divisor from tick counter cs:22220 
 (0x123/ticks, min 4), BX=0x40 period."
```

**Returns:**
- AX = rate divisor (0x123/ticks, minimum 4)
- BX = 0x40 (constant 64 = frame period)

So `word_2E139` = 0x40 (64) when set by tick_rate!

### 2. Alternative Source @ 0x30DD4-0x30DD7

In `sub_30CB8`:
```asm
0x30DCD: mov    ax, [si+0Fh]              ; load from offset +0Fh
0x30DD0: mov    cs:word_2E137, ax         ; store to word_2E137
0x30DD4: mov    ax, [si+11h]              ; load from offset +0x11h
0x30DD7: mov    cs:word_2E139, ax         ; ← STORE TO word_2E139
0x30DDB: mov    ax, [si+13h]              ; load from offset +0x13h
0x30DDE: call   control_axes_read         ; THEN call control read
```

**Key Observation:** `word_2E139` is set from `[si+11h]` BEFORE calling `control_axes_read`

This means `word_2E139` is NOT the control input - it's loaded from a data structure!

### 3. Usage in Aerodynamics @ 0x38DE9

```asm
0x38DE7: idiv   bx                        ; divide by some value
0x38DE9: mov    bx, cs:word_2E139         ; load word_2E139
0x38DEE: cmp    bx, 80h                   ; compare to 128
0x38DF2: jl     loc_38DF7
0x38DF4: mov    bx, 7Fh                   ; clamp to 127
0x38DF7: imul   bx                        ; multiply
```

**Interpretation:**
- If word_2E139 = 0x40 (64), comparison to 0x80 (128) is always less
- No clamping occurs (64 < 128)
- Force is multiplied by 64

**This is NOT a control input - it's a scaling factor or time multiplier!**

## What word_2E139 Actually Is

### Theory 1: Frame Time Delta
- tick_rate_compute returns 0x40 (64) as frame period
- Used to scale physics calculations by time
- Ensures consistent physics at different frame rates

### Theory 2: Physics Update Rate
- Loaded from entity data at [si+11h]
- Different entities may have different update rates
- 64 = standard update rate

### Theory 3: Combined Time/Rate Factor
- Sometimes from tick_rate (global time)
- Sometimes from entity data (per-entity rate)
- Multiplied into physics for scaling

## Where is the REAL Control Input?

**Need to find:**
1. Where control_axes_read stores its output (AX, BX, CX, DX from the clamping function)
2. How those 4 axes (±2048) are stored
3. Where they're used in aerodynamics

**Search Strategy:**
```
1. Find control_axes_read function (sub_11450 @ 0x11450)
2. See what it returns (returns values in AX, BX, CX, DX after clamping)
3. Find where those registers are stored after the call
4. Look for usage of those storage locations in sub_38CF3
```

## Next Steps

1. **Disassemble control_axes_read completely**
   - Find what it returns
   - Where return values go

2. **Find actual control storage**
   - Trace registers after control_axes_read call
   - Find DS or CS storage locations

3. **Re-examine aerodynamics**
   - Find where REAL control values are used
   - Distinguish control from time scaling

---

**Status:** Session 2 conclusions about control→force were PARTIALLY WRONG

**What WAS Correct:**
- ✅ Physics coefficient fields (+0x60-0x70)
- ✅ Force calculation algorithm structure
- ✅ Speed-dependent control authority
- ✅ Rate limiting mechanism

**What WAS WRONG:**
- ❌ cs:word_2E139 = control input (it's time/rate factor)
- ❌ Scaling from ±2048 → 0..127 (need to find real path)

---

*Discovery: 2026-11-11, Session 3*  
*Analyst: Kiro*
