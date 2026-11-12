# IDA Verification Checklist - Math Helpers & Segment 0x7772

**Purpose:** Verify bytecode analysis and investigate data segment  
**Priority:** HIGH - Critical for understanding view_projection  
**Time estimate:** 1-2 hours

## Setup

1. Open IDA with FALCONCD.EXE.i64
2. Have this checklist and math_helpers_identified.md open
3. Prepare to take notes on actual operations vs predictions

## Part 1: Verify Math Helper Functions (10 functions)

### seg015:0C65 - Predicted: Segment Setup

**Navigate:** Press `G`, enter `seg015:0C65`, press Enter

**Check:**
- [ ] First instructions match: `push ss; pop cx; mov ax, 0x7772`?
- [ ] Sets up ES segment register?
- [ ] Multiple ES: overrides follow?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg015:0C7A - Predicted: Complex Dispatcher

**Navigate:** `G` → `seg015:0C7A`

**Check:**
- [ ] Large function (~97 bytes)?
- [ ] Multiple conditional jumps?
- [ ] ES: segment overrides?
- [ ] Jumps to seg015:0E06 (far offset)?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg015:0CDB - Predicted: 32-bit Left Shift

**Navigate:** `G` → `seg015:0CDB`

**Check:**
- [ ] `mov bh, 0; push ax; mov ax, bx`?
- [ ] `cwd` instruction (sign extend)?
- [ ] `add cx, cx; adc dx, dx` (32-bit shift)?
- [ ] Stores to `[bp-2]` and `[bp-4]`?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg015:0CF0 - Predicted: Far Call Wrapper

**Navigate:** `G` → `seg015:0CF0`

**Check:**
- [ ] `push [bp-4]` or similar parameter push?
- [ ] `call far` instruction to 0x1994:0D94?
- [ ] `pop cx; pop cx` for cleanup?
- [ ] What segment is 0x1994?

**Actual operation:**
```
[Record findings here]
```

**Far call target 0x1994:0D94:**
- Segment type: ROM / RAM / Overlay?
- Function purpose: _______________

**Rename to:** _______________

---

### seg015:0D51 - Predicted: Wrapper with Cleanup

**Navigate:** `G` → `seg015:0D51`

**Check:**
- [ ] `call` to relative address?
- [ ] Target address: 0x1CBA7 (or close)?
- [ ] `add sp, 6` (cleanup 3 words)?
- [ ] Jump to common epilogue?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg015:0D66 - Predicted: Conditional Math

**Navigate:** `G` → `seg015:0D66`

**Check:**
- [ ] Conditional jumps based on flags?
- [ ] Different code paths for different conditions?
- [ ] ES: segment overrides?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg017:01FE - Predicted: Table Lookup (4-byte entries)

**Navigate:** `G` → `seg017:01FE`

**Check:**
- [ ] `push es`?
- [ ] `shl bx, 2` (multiply by 4)?
- [ ] `mov ax, 0x7772; mov es, ax`?
- [ ] `mov ax, [es:bx+0x0F36]`?
- [ ] `mov dx, [es:bx+0x0F34]`?

**If YES - this is a TABLE LOOKUP!**
- Table location: Segment 0x7772, offsets 0x0F34 and 0x0F36
- Entry size: 4 bytes (2 words)
- Index register: BX
- Result: DX:AX (32-bit value)

**Actual operation:**
```
[Record findings here]
```

**Rename to:** table_lookup_32bit OR trig_table_lookup

---

### seg017:021C - Predicted: Multiply-Accumulate Loop

**Navigate:** `G` → `seg017:021C`

**Check:**
- [ ] `xor` instructions to zero accumulator?
- [ ] `imul` instruction?
- [ ] `loop` instruction?
- [ ] Accesses array/table in loop?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg017:01E3 - Predicted: Epilogue/Return

**Navigate:** `G` → `seg017:01E3`

**Check:**
- [ ] Comparison and conditional jump backwards?
- [ ] `popf; pop di; pop si`?
- [ ] `leave; retf`?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

### seg020:1A2F - Predicted: Absolute Value

**Navigate:** `G` → `seg020:1A2F`

**Check:**
- [ ] `cmp dx, cx; jae; xchg`?
- [ ] Test for negative (`jns`)?
- [ ] `neg dx; neg ax; sbb dx, 0` pattern?

**Actual operation:**
```
[Record findings here]
```

**Rename to:** _______________

---

## Part 2: Investigate Segment 0x7772 (Data Segment)

### Navigate to Segment

**Option A - Direct:**
1. Press `G`
2. Enter `0x7772:0` (might not work)

**Option B - Via Reference:**
1. Go to seg015:0C65 (uses segment 0x7772)
2. Find instruction `mov ax, 0x7772`
3. Double-click on the next instruction that uses ES
4. Should navigate to the data

**Option C - Segments Window:**
1. View → Open subviews → Segments
2. Look for segment at base 0x7772
3. Double-click to navigate

### Check Table at Offset 0x0F34

**Navigate:** `G` → `seg_with_base_0x7772:0F34` (adjust segment name)

**Questions:**
- [ ] What type of data is here? (bytes, words, dwords?)
- [ ] Is it a table/array? How many entries?
- [ ] Are values recognizable? (e.g., 0x0000, 0x8000, 0x7FFF suggest fixed-point)
- [ ] Pattern recognition:
  - [ ] Incrementing/decrementing values? (linear table)
  - [ ] Oscillating values? (sin/cos table)
  - [ ] Random-looking? (precomputed results)

**Sample first 16 entries (32-bit each):**
```
Offset  | DWord Value      | As Fixed-Point | Possible Meaning
--------|------------------|----------------|------------------
0x0F34  | 0x________       | _____          | 
0x0F38  | 0x________       | _____          |
0x0F3C  | 0x________       | _____          |
0x0F40  | 0x________       | _____          |
0x0F44  | 0x________       | _____          |
0x0F48  | 0x________       | _____          |
0x0F4C  | 0x________       | _____          |
0x0F50  | 0x________       | _____          |
0x0F54  | 0x________       | _____          |
0x0F58  | 0x________       | _____          |
0x0F5C  | 0x________       | _____          |
0x0F60  | 0x________       | _____          |
0x0F64  | 0x________       | _____          |
0x0F68  | 0x________       | _____          |
0x0F6C  | 0x________       | _____          |
0x0F70  | 0x________       | _____          |
```

**Table identification:**
- [ ] **Sin/Cos table** - Values oscillate between -1.0 and 1.0 (in fixed-point)
- [ ] **Atan2 table** - Values represent angles
- [ ] **Square root table** - Values increase non-linearly
- [ ] **Reciprocal table** - 1/x values for fast division
- [ ] **Perspective division table** - Screen coordinate scaling
- [ ] **Other:** _____________________

### Check for Other Data in Segment 0x7772

**Scan through segment:**
1. Start at segment base
2. Look for defined data structures
3. Check for cross-references (Ctrl+X on data)

**Notable data found:**
```
Offset | Type | Size | XRefs | Description
-------|------|------|-------|-------------
       |      |      |       |
       |      |      |       |
       |      |      |       |
```

---

## Part 3: Check Far Call Target (0x1994:0D94)

### Navigate to Target

**Navigate:** `G` → `0x1994:0D94` or calculate linear address

**Questions:**
- [ ] Does the address exist in IDB?
- [ ] Is it code or data?
- [ ] If code, what does it do?
- [ ] Segment 0x1994 properties:
  - [ ] ROM BIOS?
  - [ ] Overlay segment?
  - [ ] External library?
  - [ ] Math coprocessor emulation?

**Findings:**
```
[Record findings here]
```

---

## Part 4: Check Parent Function Names

### stream_command_interpret (sub_1CC2D at seg015:0C3B)

**Navigate:** `G` → `seg015:0C3B`

**Check main entry point (offset 0x00):**
- [ ] What are the first instructions?
- [ ] Check xrefs (Ctrl+X) - who calls the MAIN entry?
- [ ] Do xrefs come from stream/command code?
- [ ] Or from graphics/projection code?

**Xrefs to main entry:**
```
Caller Address | Caller Function | Context
---------------|-----------------|----------
               |                 |
               |                 |
```

**Assessment:**
- [ ] **Correctly named** - Actually does stream command interpretation
- [ ] **Misnamed** - Rename to: _____________________

---

### group_children_release (sub_1D88C at seg017:01F6)

**Navigate:** `G` → `seg017:01F6`

**Check main entry and xrefs:**

**Xrefs to main entry:**
```
Caller Address | Caller Function | Context
---------------|-----------------|----------
               |                 |
               |                 |
```

**Assessment:**
- [ ] **Correctly named** - Actually releases group children
- [ ] **Misnamed** - Rename to: _____________________

---

### channel_list_register_batch (sub_1D7DA at seg017:0144)

**Navigate:** `G` → `seg017:0144`

**Check main entry and xrefs:**

**Xrefs to main entry:**
```
Caller Address | Caller Function | Context
---------------|-----------------|----------
               |                 |
               |                 |
```

**Assessment:**
- [ ] **Correctly named** - Actually registers channel lists
- [ ] **Misnamed** - Rename to: _____________________

---

## Part 5: Update Naming

Based on verification, update IDA names:

### Functions to Rename

```
Current Name                    | New Name                    | Location
--------------------------------|-----------------------------|--------------
sub_1CC2D (if misnamed)         | ____________                | seg015:0C3B
sub_1D88C (if misnamed)         | ____________                | seg017:01F6
sub_1D7DA (if misnamed)         | ____________                | seg017:0144
```

### Multi-Entry Points to Create

If IDA doesn't recognize these as functions, create them:

```
Address         | New Function Name           | Parent Function
----------------|-----------------------------|-----------------
seg015:0C65     | ___________                 | sub_1CC2D
seg015:0C7A     | ___________                 | sub_1CC2D
seg015:0CDB     | ___________                 | sub_1CC2D
seg015:0CF0     | ___________                 | sub_1CC2D
seg015:0D51     | ___________                 | sub_1CC2D
seg015:0D66     | ___________                 | sub_1CC2D
seg017:01FE     | ___________                 | sub_1D88C
seg017:021C     | ___________                 | sub_1D88C
seg017:01E3     | ___________                 | sub_1D7DA
seg020:1A2F     | ___________                 | sub_2100F
```

**Note:** IDA may not allow creating functions at these addresses if they're mid-function. In that case, add comments instead.

---

## Summary Findings

### Confirmed Predictions

List which of our 10 predictions were correct:
- [ ] seg015:0C65 - 
- [ ] seg015:0C7A - 
- [ ] seg015:0CDB - 
- [ ] seg015:0CF0 - 
- [ ] seg015:0D51 - 
- [ ] seg015:0D66 - 
- [ ] seg017:01FE - 
- [ ] seg017:021C - 
- [ ] seg017:01E3 - 
- [ ] seg020:1A2F - 

### Accuracy Score

Predictions correct: _____ / 10 = _____%

### Key Discoveries

1. **Segment 0x7772 contains:**
   ```
   [Your findings]
   ```

2. **Far call target 0x1994:0D94 is:**
   ```
   [Your findings]
   ```

3. **Parent function names:**
   - stream_command_interpret: [Correct / Misnamed as ___________]
   - group_children_release: [Correct / Misnamed as ___________]
   - channel_list_register_batch: [Correct / Misnamed as ___________]

4. **Most surprising finding:**
   ```
   [Your note]
   ```

---

## Files to Update

After verification, update these files:

1. **math_helpers_identified.md** - Correct any wrong predictions
2. **Naming registry** - Add verified names
3. **view_projection_analysis.md** - Update with accurate math pipeline
4. **Create new:** segment_0x7772_data_layout.md

---

## Time Tracking

- [ ] Part 1 (Functions): _____ minutes
- [ ] Part 2 (Segment 0x7772): _____ minutes
- [ ] Part 3 (Far call): _____ minutes
- [ ] Part 4 (Parent names): _____ minutes
- [ ] Part 5 (Renaming): _____ minutes

**Total:** _____ minutes

---

**Checklist complete! Document findings and commit results.**
