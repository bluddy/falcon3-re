# Finding 205 Analysis - P2 not_head Misdecodes (Deferred)

**Date:** 2026-11-11  
**Status:** Analyzed but not applied - deferred to P6 (orphan registration)

## Summary

Investigated 6 "not_head" targets from `survey_mid.json` that appeared to be misdecode cases where calls land 1 byte into a function. Discovered these are actually **orphan bytes with no registered functions**, making this P6 work (orphan ADD) rather than P2 work (misdecode REBASE).

## The 6 Targets

All in segment R05_2B83, currently unexplored:

| Address (called) | Address (proposed) | Size | Status |
|------------------|-------------------|------|---------|
| 0x407BF | 0x407BE | 133B | No function, starts with 0x00 0x00 |
| 0x40DDB | 0x40DDA | 91B  | No function, starts with 0x00 0x00 |
| 0x40C69 | 0x40C68 | 11B  | No function, starts with 0x00 |
| 0x40045 | 0x40044 | 24B  | No function, starts with 0x00 |
| 0x3FD66 | 0x3FD65 | 36B  | No function, starts with 0x00 |
| 0x404F1 | 0x404F0 | 6B   | No function, starts with 0x00 |

## Analysis

### Initial Hypothesis (Incorrect)
- survey_mid.json showed these as "not_head" (calls landing mid-instruction)
- Appeared to be REBASE candidates (move function start 1 byte earlier)
- Expected existing functions at old addresses that needed rebasing

### Actual Situation (Discovered)
- **No functions exist** at old OR new addresses
- The bytes are **unexplored/unanalyzed** in IDA
- All start with null bytes (0x00) which are orphan data
- Xrefs exist to these addresses from other code
- This is **orphan code that was never registered as functions**

### Why This Happened
The survey_mid.json reports "not_head" because:
1. There ARE code xrefs calling these addresses
2. But NO function is registered at the target
3. The target byte happens to be 1 byte before some code
4. The null bytes at the start confused the analysis

## Correct Classification

**This is P6 work (orphan registration), not P2 work (misdecode fixes)**

- **P2 (misdecodes):** Fix existing functions that start at wrong byte
- **P6 (orphans):** Register new functions from unowned code with callers

## Workflow Complexity Discovered

Attempted to apply via manifest system (`registry/orphan_funcs_expected.json`):
- Discovered REBASE manifest requires 3 SHA256 values: `sha256`, `old_sha256`, `prefix_sha256`
- Plan mode conflicts with already-applied TRIM/REBASE entries
- Direct IDA scripting approach simpler for small batches

## Artifacts Created

- `analysis/s1/probe_not_head.py` - Analysis of not_head targets
- `analysis/s1/rebase_candidates.json` - Detailed investigation results
- `analysis/s1/apply_6_rebases_direct.py` - Direct IDA script (unused)
- `analysis/s1/check_functions_status.py` - Status verification
- `analysis/s1/check_bytes.py` - Raw byte inspection

## Recommendation

**Defer to P6 orphan batch:**
- These 6 targets should be registered as NEW functions (ADD operation)
- Need to determine correct start addresses (skip null byte prefix?)
- Batch with other orphan functions for efficiency
- Use ADD manifest mode, not REBASE

## Related Targets

Survey_mid.json shows 19 total "not_head" targets. The remaining 13 need similar analysis:
- Check if functions exist at old addresses
- Determine if REBASE (existing function) or ADD (orphan code)
- Classify appropriately

## Time Investment

- Analysis: ~2 hours
- Result: Correct classification, tooling understanding
- Value: Prevents applying wrong fix type, improves workflow knowledge

## Next Steps

1. Reclassify these 6 from P2 to P6 queue
2. Continue with other boundary fixes (P4 "other" targets more straightforward)
3. Return to these as part of larger orphan registration batch
