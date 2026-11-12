---
inclusion: auto
name: reverse-engineering-best-practices
description: Best practices for reverse engineering and static analysis work, especially with IDA Pro
---

# Reverse Engineering Best Practices

## Critical Rule: ALWAYS Verify with IDA API

**Never trust static/bytecode analysis alone.**

### The Problem
- Bytecode pattern matching finds CODE, not CALLS
- Address with instructions ≠ function entry point
- Mid-function addresses can look like helpers
- XRef count matters: 0 xrefs = no CALL instructions (just JMP/JZ/fall-through)

### The Solution
**Use IDA Python API for all call graph analysis:**

```python
import idautils

# Find actual callers
addr = 0x12345
xrefs = list(idautils.XrefsTo(addr, 0))
for xref in xrefs:
    caller = idc.get_func_name(xref.frm)
    print(f"Called from: {caller}")

# Extract CALL instructions
ea = func.start_ea
while ea < func.end_ea:
    if idc.print_insn_mnem(ea) == "call":
        target = idc.get_operand_value(ea, 0)
        # This is a real call!
    ea = idc.next_head(ea, func.end_ea)
```

### Verification Workflow

1. **Static Analysis** (initial exploration)
   - Find patterns, identify candidates
   - Extract bytecode for inspection
   - Form hypotheses

2. **API Verification** (ground truth)
   - Run IDA Python scripts
   - Check xrefs for every claim
   - Extract actual CALL instructions
   - Verify sizes, addresses, call counts

3. **Cross-Reference** (validation)
   - Compare static findings vs API data
   - Identify discrepancies
   - Correct false positives
   - Document verified facts only

### Red Flags
- ⚠️ "Called exclusively by X" without xref check
- ⚠️ Counting functions without verifying CALL instructions
- ⚠️ Assuming address with code = function entry
- ⚠️ XRef count = 0 (no external calls - internal jump target)

### Example from Falcon 3.0

**False Finding**:
- "10 math helpers exclusive to view_projection"
- Based on bytecode patterns at specific addresses
- NO xref verification done

**Reality** (after API check):
- XRef count = 0 (no CALL instructions)
- Addresses are mid-function jump targets
- In unrelated functions (stream_command_interpret, etc.)
- **Complete false positive**

**Correction**:
- view_projection has 7 CALL instructions (verified)
- No "exclusive helpers" - just normal function calls
- Saved by automated verification

## IDA Automation Scripts

### Always Include These
```python
# Auto-wait for IDA analysis
idaapi.auto_wait()

# Auto-exit when done
idc.qexit(0)

# Save results to JSON
import json
with open("results.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Run from Command Line
```bash
idat.exe -A -S"script.py" database.i64
```

## Call Graph Analysis

### Count Call Sites vs Callers
- **Call sites**: Total number of CALL instructions
- **Callers**: Unique functions making calls

Example:
- Function has 21 xrefs
- But only 10 unique caller functions
- One function calls it 4 times
- Report: "10 callers, 21 call sites"

### Verify Function Sizes
```python
func = idaapi.get_func(addr)
size = func.end_ea - func.start_ea
print(f"Size: {size} bytes")
```

Always verify claimed sizes with IDA.

## Multi-Entry Functions

In DOS-era code, ~50%+ of functions may have multiple entry points:
- Optimization for code reuse
- Different parameter configurations
- Not a bug - deliberate design

**Don't assume**: One address = one function

## Segment Address Calculation

```python
# seg:offset to linear
seg_base = idc.get_segm_by_sel(idc.selector_by_name("seg020"))
linear = seg_base + offset

# Example: seg020:151B
# Base: 0x1F6C0
# Offset: 0x151B
# Linear: 0x1F6C0 + 0x151B = 0x20BDB
```

Always verify segment base addresses.

## Performance Analysis

### Frame Budget
For real-time games:
- Count function calls in main loop
- Measure critical path
- Identify hot spots (called 3x+)

### Visibility Culling
Look for:
- Multiple culling passes
- Queue management (near/far)
- LOD systems
- Slot-based object pools

## Documentation

### What to Document
- ✅ Verified addresses (with segment:offset)
- ✅ Verified sizes (byte count from IDA)
- ✅ Verified call counts (from xrefs)
- ✅ Call graphs (actual CALL instructions)
- ✅ Verification methodology

### What NOT to Document
- ❌ Unverified hypotheses
- ❌ Bytecode patterns without xref proof
- ❌ Assumed relationships
- ❌ "Probably" or "might be"

## Commit Messages

Good:
```
"Verify farobj system via IDA API
- Confirmed sizes: 393, 72, 72, 70 bytes
- Found 3x calls from game_frame_pipeline_step
- All addresses verified with xrefs"
```

Bad:
```
"Add farobj analysis
- Looks like it handles visibility
- Probably called a few times"
```

## When Things Go Wrong

### False Positives
- Don't hide them - document the correction
- Explain what went wrong
- Update all related docs
- Add lesson to this file

### Verification Failures
- IDA script won't run → simplify, test incrementally
- Results don't match expectations → trust IDA, not assumptions
- Can't find function → check spelling, try by address

## Tools

### Essential IDA Python Modules
```python
import idc         # Basic functions (get_name, get_func_name, etc.)
import idaapi      # Advanced (get_func, auto_wait, etc.)
import idautils    # Utilities (XrefsTo, Functions, etc.)
import json        # Save results
from pathlib import Path  # File handling
```

### Verification Scripts to Create
1. `verify_addresses.py` - Check all key addresses
2. `verify_sizes.py` - Measure function sizes
3. `verify_callers.py` - Count xrefs and callers
4. `extract_calls.py` - Get actual CALL instructions
5. `verify_data_structures.py` - Check DGROUP refs

## Summary

**The Golden Rule**: 
If you didn't verify it with the IDA API, you don't know it's true.

**The Process**:
1. Explore with static analysis
2. Verify with IDA API
3. Cross-reference findings
4. Document only verified facts
5. Correct false positives immediately

**The Result**:
Accurate, trustworthy reverse engineering that stands up to scrutiny.
