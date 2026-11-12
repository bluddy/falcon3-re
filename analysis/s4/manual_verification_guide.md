# Manual IDA Verification Guide

Since automated batch mode verification had issues, use this manual checklist in IDA Pro.

## Quick Start
1. Open IDA Pro with FALCONCD.EXE.i64
2. Use "G" (Jump to Address) to navigate to each address below
3. Use "X" (Xrefs) to check callers
4. Record findings in verification_findings.txt

---

## Phase 1: Core Address Verification (15 min)

### seg020 Base Address
```
Action: File → Segments → seg020 properties
Expected: base = 0x1F6C0
Actual: _________
```

### view_projection Location
```
Press G, enter: 20BDB
Expected: Function "view_projection" at seg020:151B
Actual name: _________
Actual segoff: _________
```

### sub_256A3 Location
```
Press G, enter: 256A3
Expected: Function at seg020:5FE3
Actual name: _________
Actual segoff: _________
```

### DGROUP Data Structures
```
Press G, enter: DGROUP:4287
Expected: 3D coordinate structure
Actual type: _________
Actual name: _________

Press G, enter: DGROUP:7C054
Expected: near object queue
Actual name: _________

Press G, enter: DGROUP:7D0C6
Expected: far object queue
Actual name: _________
Queue separation: 7D0C6 - 7C054 = _________ bytes (expect 4,210)
```

---

## Phase 2: Math Helper Entry Points (30 min)

For each address below:
1. Press G, enter the linear address
2. Note if code exists at that exact address
3. Press X to see xrefs (who calls this address)
4. Check if ONLY view_projection calls it

### Helper 1: seg015:0C65 (segment setup)
```
Linear address: (seg015 base + 0xC65) = _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 2: seg015:0C7A (complex dispatcher)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 3: seg015:0CDB (32-bit left shift)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 4: seg015:0CF0 (far call wrapper)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 5: seg015:0D51 (wrapper with cleanup)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 6: seg015:0D66 (conditional math)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 7: seg017:01FE (table lookup)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO

Table address: 0x7772:0x0F34
Press G, enter that segoff, verify table exists: YES / NO
```

### Helper 8: seg017:021C (multiply-accumulate)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 9: seg017:01E3 (conditional epilogue)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

### Helper 10: seg020:1A2F (32-bit absolute value)
```
Linear address: _________
Function name: _________
Called by: _________
Exclusive to view_projection? YES / NO
```

---

## Phase 3: Graphics Functions (20 min)

### fixed_vec3_transform_es
```
Press Shift+F12 (Functions), search for: fixed_vec3_transform_es
Address: _________
Press X to see xrefs
Caller count: _________ (expect 10)
Callers:
1. _________
2. _________
3. _________
4. _________
5. _________
6. _________
7. _________
8. _________
9. _________
10. _________
```

### vec2_normalize_seq
```
Address: _________
Caller count: _________ (expect 2)
Callers: _________, _________
```

### farobj_record_step
```
Address: _________
Function size: _________ bytes (expect 393)
Called by: _________
```

### farobj_record_push_7c054
```
Address: _________
Function size: _________ bytes (expect 72)
References DGROUP:7C054? YES / NO
```

### farobj_record_lookup_step
```
Address: _________
Function size: _________ bytes (expect 72)
```

### farobj_record_push_7d0c6
```
Address: _________
Function size: _________ bytes (expect 70)
References DGROUP:7D0C6? YES / NO
```

---

## Phase 4: vec3_transform Callers (20 min)

Navigate to fixed_vec3_transform_es, press X to see all xrefs.
For each caller, count how many times they call vec3_transform:

```
Caller                          | Expected Calls | Actual Calls
-------------------------------|----------------|-------------
view_projection                |       1        | _____
record_xform_apply             |       4        | _____
object_proj_draw_dispatch      |       1        | _____
object_quad_proj_draw          |       4        | _____
view_proj_setup_1f73d          |       3        | _____
view_scroll_rotate_apply       |       1        | _____
view_proj_setup_1f73d_rot      |       3        | _____
view_basis_build_3850          |       2        | _____
stub_to_248d1                  |       1        | _____
sub_21657                      |       1        | _____
```

### sub_21657 Special Check
```
Press G, search for: sub_21657
Press X (xrefs to)
Direct callers found: _________ (expect 0 - should be indirect call)
```

---

## Phase 5: View Projection Call Graph (20 min)

Navigate to view_projection (0x20BDB), examine the function body.

Count all CALL instructions:
```
Total CALLs in view_projection: _________ (expect 16)

List of called functions:
1. _________
2. _________
3. _________
4. _________
5. _________
6. _________
7. _________
8. _________
9. _________
10. _________
11. _________
12. _________
13. _________
14. _________
15. _________
16. _________
```

Compare with expected:
- 10 math helpers (seg015:0C65, 0C7A, 0CDB, 0CF0, 0D51, 0D66, seg017:01FE, 021C, 01E3, seg020:1A2F)
- 6 graphics functions (vec3_transform, vec2_normalize, 4x farobj functions)

---

## Phase 6: Multi-Entry Verification (15 min)

### seg020:051B Check (Finding 207 Address)
```
Press G, enter: 1FBDB (calculated as seg020 base + 051B)
Is this INSIDE another function? YES / NO
Parent function name: _________ (expect: record_xform_apply)
Is 1FBDB listed as a separate function? YES / NO
```

### Random Multi-Entry Spot Check
Pick 5 random addresses from segment_map.json multi-entry list and verify they exist:
```
1. Address _________ → Function: _________ | Exists: YES/NO
2. Address _________ → Function: _________ | Exists: YES/NO
3. Address _________ → Function: _________ | Exists: YES/NO
4. Address _________ → Function: _________ | Exists: YES/NO
5. Address _________ → Function: _________ | Exists: YES/NO
```

---

## Phase 7: Data Table Verification (15 min)

### Segment 0x7772 Table
```
Press G, enter: 7772:0F34
Is there data at this location? YES / NO
Data type: _________
Entry size: _________ bytes (expect 4)
Number of entries visible: _________
```

### DGROUP:0x4287 Structure
```
Press G, enter: DGROUP:4287
Current type: _________
Size: _________ bytes
Used by: _________ (expect: sub_256A3)

Try to identify structure (look at how sub_256A3 uses it):
+0x00: _________
+0x04: _________
+0x08: _________
Looks like: 3D coordinate (x,y,z)? YES / NO
```

---

## Summary

Total verification time: ~2-3 hours
Critical findings: Record any discrepancies here
New discoveries: Record unexpected findings here

Save this file as: verification_findings_[date].txt
