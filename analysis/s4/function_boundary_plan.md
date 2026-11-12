# Function Boundary Fixes - Implementation Plan

## Problem Summary

**25% of direct call sites (4,020 calls + 256 jumps) land inside function bodies** instead of at their starts.

From runtime trace analysis (`boundary_report.json`):
- **96 MID targets** across **40 parent functions** (186,233 total calls from trace)
- Categories: merged functions, secondary entries, misdecodes

From status.md broader analysis:
- 402 targets sit right after ret/jmp → **merged functions** (need split)
- 222 targets not on instruction head → **misdecode** or wrong caller
- ~120 fall-in secondary entries
- 52 runtime far-call targets mid-body (287K events)

## Top 10 High-Impact Fixes (by runtime call frequency)

### 1. segment_clip_test (+0x106): 32,576 calls
- Parent: 0x25F93, 262B
- MID target: 0x26099
- Pattern: likely secondary entry after conditional early-return

### 2. fixed_vec3_read (+0x027): 29,328 calls  
- Parent: 0x22C62, 15B (ALREADY TINY!)
- MID target: 0x22C89
- Pattern: data table or constants merged with code
- **Note:** Findings 137 already TRIM'd this from 41B to 15B, but 0x22C89 wasn't registered

### 3. control_axes_read (+0x0D3/0x0EB/0x0F0): 21,903 calls (3 entries)
- Parent: 0x2234B, 211B
- MID targets: 0x2241E, 0x22436, 0x2243B
- Pattern: **3 tiny accessor functions merged** (possibly register getters)

### 4. state_word_2223e_set (+0x00A/0x005/0x00F): 19,811 calls (3 entries)
- Parent: 0x22841, 5B (ALREADY TINY!)
- MID targets: 0x2284B, 0x22846, 0x22850
- Pattern: **3 word-setter functions merged** (these were NAMED in Level-0 batch 1!)
- **CRITICAL:** cs_word_2b80_set (0x22846), cs_word_2b82_set (0x2284B), cs_word_2b84_set (0x22850)
  are already in naming.yaml but not split from parent!

### 5. dispatch_220d4_stub (+0x006): 14,099 calls
- Parent: 0x263F0, 6B
- MID target: 0x263F6
- Pattern: stub+target merged
- **CRITICAL:** 0x263F6 = farobj_dispatch_table (Level-0 batch 1, 18K dyn calls!)
  Already named but not split!

### 6. farptr_state_set (+0x0A2/0x0FE/0x025): 13,967 calls (10 MID targets!)
- Parent: 0x23036, 16B
- Pattern: **highly split function** or dispatch table with many entries

### 7. r17_event_main_loop (+0x274): 8,765 calls
- Parent: 0x6E8F0, 330B (R17 overlay)
- Pattern: loop body or secondary entry

### 8. int32_to_ascii (+0x09D): 8,597 calls
- Parent: 0x228BF, 157B
- Pattern: secondary entry (possibly skip-leading-zeros variant)

### 9. view_block4287_entry (+0x01C/0x00C/0x005): 8,323 calls (3 entries)
- Parent: 0x25687, 5B (TINY!)
- Pattern: 3 functions merged

### 10. r06_mode_step_dispatch (+0x052/0x006): 7,209 calls (2 entries)
- Parent: 0x6CDA8, 82B (R06 overlay)
- Pattern: dispatch table or secondary entry

## Discovery: Level-0 Batch 1 Collisions!

**4 of the 10 functions named in Level-0 batch 1 are MID targets** that need to be split from their parents:

1. **cs_word_2b80_set** (0x22846) - inside state_word_2223e_set (+0x005), 6,547 calls
2. **cs_word_2b82_set** (0x2284B) - inside state_word_2223e_set (+0x00A), 7,288 calls
3. **cs_word_2b84_set** (0x22850) - inside state_word_2223e_set (+0x00F), 5,976 calls
4. **farobj_dispatch_table** (0x263F6) - inside dispatch_220d4_stub (+0x006), 14,099 calls

These were correctly *named* but their boundaries are wrong in IDA.

## Fix Strategy

### Phase 1: Fix Level-0 Batch 1 Collisions (4 splits)
**Priority:** CRITICAL - we already named these, they're hot (34K-14K calls)

Tools needed:
- IDA split script (like findings 148-160 used)
- Manifest with SPLIT mode
- Verify boundaries after split

Targets:
1. Split state_word_2223e_set (0x22841, 5B) → extract 3 setters at +0x005/+0x00A/+0x00F
2. Split dispatch_220d4_stub (0x263F0, 6B) → extract farobj_dispatch_table at +0x006

### Phase 2: Fix Top 10 Remaining MID Targets (batch 2-10)
**Priority:** HIGH - 152K calls (86% of MID call traffic)

Use same SPLIT tooling to fix:
- segment_clip_test (+0x106)
- fixed_vec3_read (+0x027) - extract 0x22C89 constants/table
- control_axes_read (+0x0D3/0x0EB/0x0F0) - extract 3 tiny accessors at 0x2241E/0x22436/0x2243B
  - **NOTE:** 0x22436 and 0x2243B are ALSO Level-0 batch 1 names (cs_word_2b76_get, cs_word_2b78_get)!
- farptr_state_set (10 MID targets)
- r17_event_main_loop (+0x274)
- int32_to_ascii (+0x09D)
- view_block4287_entry (+0x01C/0x00C/0x005) - extract 3 tiny functions
- r06_mode_step_dispatch (+0x052/0x006)

### Phase 3: Remaining 30 Parent Functions
**Priority:** MEDIUM - 34K calls (remaining 14% of MID traffic)

Apply same split approach to remaining 30 parent functions with lower call counts.

### Phase 4: Static Call Site Analysis
**Priority:** MEDIUM - broader than runtime trace

Use static xref analysis (not just traced calls) to find:
- The 402 post-terminator merge targets
- The 222 misdecode targets
- The ~120 fall-in secondary entries

Status.md says 4,020 static calls + 256 jumps land mid-body (vs 96 in runtime trace).

## Tools Required

1. **IDA split script** (adapt from findings 148-160 P1 split work)
2. **Manifest format** with SPLIT mode
3. **Boundary verification** - check xrefs resolve to function starts after split
4. **Naming preservation** - don't lose the Level-0 batch 1 names during split

## Gate Conditions

- All splits must pass `verify_rebuild` SPLIT gate
- Names from naming.yaml must be preserved
- Xrefs to MID targets must resolve to new function starts
- No byte changes (splits are metadata-only)

## Next Steps

1. Read findings 148-160 to understand SPLIT tooling
2. Create manifest for Level-0 batch 1 collision fixes (4 targets)
3. Run IDA split + verify
4. Commit Phase 1 fixes
5. Continue with Phase 2 (top 10 remaining)
