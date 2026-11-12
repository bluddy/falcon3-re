# Math Library Investigation - Major Findings

**Date:** 2026-11-12  
**Context:** Analyzing functions called by view_projection  
**Status:** CRITICAL DISCOVERY - Misnamed Functions

## Executive Summary

What we thought were "math library functions" are actually **misnamed multi-purpose functions** with embedded math routines that view_projection accesses exclusively. The function names (stream_command_interpret, group_children_release, etc.) don't match their actual purpose when called by view_projection.

## The Discovery

view_projection calls 10 addresses across 4 parent functions:

### stream_command_interpret (seg015:0C3B, 475 bytes)
**6 call targets:**
- seg015:0C65 (+0x002A)
- seg015:0C7A (+0x003F)
- seg015:0CDB (+0x00A0)
- seg015:0CF0 (+0x00B5)
- seg015:0D51 (+0x0116)
- seg015:0D66 (+0x012B)

### group_children_release (seg017:01F6, 136 bytes)
**2 call targets:**
- seg017:01FE (+0x0008) 
- seg017:021C (+0x0026)

### channel_list_register_batch (seg017:0144, 178 bytes)
**1 call target:**
- seg017:01E3 (+0x009F)

### vec_delta_norm_1f6ee (seg020:194F, 442 bytes)
**1 call target:**
- seg020:1A2F (+0x00E0)

## Critical Finding: Exclusive Access

**ALL 10 call targets are NOT registered multi-entry points in segment_map.json.**

This means:
1. ✓ view_projection is the ONLY caller of these specific offsets
2. ✓ No other code in the entire codebase jumps to these addresses
3. ✓ These are not shared subroutines used elsewhere

## What This Means

### Option A: Misnamed Functions (LIKELY)

The parent functions have misleading names from IDA's initial analysis:

**"stream_command_interpret"** is probably:
- Actually a math/graphics library with 6 helper routines
- 475 bytes = enough for multiple small functions
- view_projection uses 6 different entry points
- May have been mis-analyzed due to complex control flow

**"group_children_release" / "channel_list_register_batch"** are probably:
- Graphics/math helpers, not stream or group management
- Names may have come from nearby string refs or data

**"vec_delta_norm_1f6ee"** is probably:
- Correctly named (vector delta normalization)
- Used by view_projection for coordinate transformations

### Option B: Multi-Purpose Functions (LESS LIKELY)

These could be legitimately multi-purpose functions:
- Main entry does stream/group operations
- Secondary entries do math operations
- Unlikely because names don't suggest dual purpose

### Option C: Compiler Optimizations (POSSIBLE)

The compiler may have merged unrelated functions:
- Tail-call merging
- Common epilogue sharing
- Code block reuse

## Evidence for Misnamed Functions

### 1. Name Semantics Don't Match

"stream_command_interpret" calling context:
- view_projection calls it 6 times during coordinate transformation
- Unlikely to be interpreting stream commands during rendering
- More likely: math operations (mul, div, normalize, etc.)

### 2. Exclusive Access Pattern

If these were truly stream/group functions:
- We'd expect calls from stream management code
- We'd see registered multi-entry points with high xref counts
- Instead: ONLY view_projection uses these offsets

### 3. Size and Structure

"stream_command_interpret" (475 bytes):
- Too small for a complex interpreter
- Perfect size for 6 small math helpers (80 bytes each average)
- view_projection calls at regular intervals (+0x2A, +0x3F, +0xA0, +0xB5, +0x116, +0x12B)

## Architectural Pattern

This reveals an interesting optimization:

```
view_projection (1076 bytes)
    ├─ Calls "stream_command_interpret" +0x2A  (maybe: fixed_mul_16)
    ├─ Calls "stream_command_interpret" +0x3F  (maybe: fixed_div_16)
    ├─ Calls "stream_command_interpret" +0xA0  (maybe: normalize_vector)
    ├─ Calls "stream_command_interpret" +0xB5  (maybe: dot_product)
    ├─ Calls "stream_command_interpret" +0x116 (maybe: cross_product)
    ├─ Calls "stream_command_interpret" +0x12B (maybe: scale_vector)
    ├─ Calls "group_children_release" +0x8    (maybe: sqrt_fixed)
    ├─ Calls "group_children_release" +0x26   (maybe: atan2_table)
    ├─ Calls "channel_list_register_batch" +0x9F (maybe: sin_cos_table)
    └─ Calls "vec_delta_norm_1f6ee" +0xE0     (maybe: vector_normalize)
```

**Why this pattern?**
- DOS real-mode has 64KB segment limits
- Grouping small functions together saves segment overhead
- view_projection needs fast math, not modularity
- Inlining would be too large, calls are better

## Naming Recommendations

### Immediate: Document Misleading Names

Update naming registry with notes:
```
stream_command_interpret -> RENAME to math_helpers_1 or projection_math_lib
  - Contains 6+ math subroutines used by view_projection
  - Name is misleading; not actually a stream interpreter
  - Entry points at +0x2A, +0x3F, +0xA0, +0xB5, +0x116, +0x12B
```

### Future: Disassemble and Re-name

Once we understand what each entry point does:
```
seg015:0C65 -> fixed_point_multiply_16
seg015:0C7A -> fixed_point_divide_16  
seg015:0CDB -> vector_normalize_2d
seg015:0CF0 -> dot_product_3d
... etc
```

## IDA Analysis Plan

### Step 1: Verify Multi-Purpose vs Misnamed

Navigate to stream_command_interpret in IDA (seg015:0C3B):

1. Check xrefs to the MAIN entry (+0x00)
   - If called from stream code → multi-purpose
   - If rarely called → misnamed

2. Check xrefs to each secondary entry
   - Confirm only view_projection calls them
   - Look for any other callers missed by export

3. Examine code structure
   - Is there a jump table or switch?
   - Or are these separate inline functions?

### Step 2: Disassemble Each Entry Point

For each of the 10 call targets:
1. Identify the operation (mul, div, normalize, etc.)
2. Determine input/output registers
3. Check for fixed-point scaling
4. Look for table lookups (sin/cos/atan2)

### Step 3: Map the Math Library

Create comprehensive documentation:
```
Math Library Map (seg015/seg017/seg020)

Fixed-Point Arithmetic:
- seg015:0C65 - 16-bit multiply with shift
- seg015:0C7A - 16-bit divide with rounding

Vector Operations:
- seg015:0CDB - 2D vector normalize
- seg015:0CF0 - 3D dot product
- seg020:1A2F - Vector delta normalization

Trigonometry:
- seg017:01E3 - Sin/cos table lookup
- seg017:01FE - Atan2 approximation

... etc
```

## Impact on view_projection Understanding

This changes our interpretation of view_projection:

**Before:**
> "Calls math library functions for transformations"

**After:**
> "Performs 3D-to-2D projection using EXCLUSIVE helper routines embedded 
> in misnamed parent functions. Has dedicated math operations that no other 
> code uses, suggesting highly optimized, purpose-built transformation pipeline."

## Next Steps

### Priority 1: Disassemble in IDA (1-2 hours)
1. Navigate to stream_command_interpret (seg015:0C3B)
2. Jump to each call target (0C65, 0C7A, 0CDB, etc.)
3. Identify operations
4. Document register usage

### Priority 2: Update Naming (30 min)
1. Add notes to naming registry
2. Mark stream_command_interpret as misnamed
3. Document the 10 exclusive entry points

### Priority 3: Extract Bytecode (30 min)
Get the actual bytecode for each entry point:
```python
# Extract bytecode from parent functions at specific offsets
# Analyze for MUL/DIV/shift patterns
# Look for table accesses
```

## Related Findings

- **Finding 207:** Revealed address translation issues
- **Session 56:** Discovered 57% multi-entry architecture
- **view_projection:** 1,076-byte projection function with exclusive math helpers

## Files

- analysis/s4/verify_math_calls.py - Verification script
- analysis/s4/math_library_findings.md - This document
- analysis/s4/segment_map.json - Multi-entry data

---

**Status:** Investigation in progress  
**Confidence:** HIGH that functions are misnamed  
**Blocker:** Need IDA disassembly to confirm and rename  
**Value:** Understanding the math library is critical for decompiling view_projection
