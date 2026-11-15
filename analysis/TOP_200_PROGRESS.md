# Top 200 Functions Analysis Progress

**Current Status**: 150/200 (75%)  
**Phase**: Ranks #151-200  
**Started**: 2026-11-11  

---

## Completed: Ranks #1-100 ✓

See `TOP_100_COMPLETE.md` for comprehensive summary of ranks 1-100.

---

## In Progress: Ranks #101-200

###  Batch Strategy
Analyzing in larger batches for efficiency.

### Rank #101-150 ✓ (Disassembly Extracted)

**Rank #101-110**: ✓ Analyzed, renamed, documented  
**Rank #111-150**: ✓ Disassembly extracted (40 functions)

### Rank #101-110 ✓

| Rank | Address | Name | Calls | Size | Status |
|------|---------|------|-------|------|--------|
| 101 | 0x11C884 | utility_11c884 | 24 | 139B | ✓ Analyzed |
| 102 | 0x11C90F | utility_11c90f | 24 | 127B | ✓ Analyzed |
| 103 | 0x13536F | vector_arithmetic_complex | 24 | 1085B | ✓ Analyzed |
| 104 | 0x22EE8 | fixed_abs_div4 | 23 | 16B | ✓ Already named |
| 105 | 0x249D8 | trig_table_lookup | 23 | 173B | ✓ Already named |
| 106 | 0x13BCE5 | string_cr_null_terminate | 23 | 33B | ✓ Analyzed |
| 107 | 0x23C9B | angle_xy_far | 22 | 144B | ✓ Already named |
| 108 | 0x24CF7 | cs_word_store | 22 | 10B | ✓ Already named |
| 109 | 0x25E22 | dispatch_220f4_stub | 22 | 6B | ✓ Already named |
| 110 | 0x11C642 | utility_11c642 | 22 | 197B | ✓ Analyzed |

**Notable**:
- Rank #104: `fixed_abs_div4` - Fixed-point math utility (16 bytes, tiny!)
- Rank #105: `trig_table_lookup` - Trigonometry table lookup
- Rank #107: `angle_xy_far` - Angle calculation from X/Y coordinates
- Rank #108: `cs_word_store` - Simple CS segment word store (10 bytes)
- Rank #109: `dispatch_220f4_stub` - Dispatch stub (6 bytes, smallest!)

### Observations
- Many tiny utility functions (6-33 bytes)
- Math/trig functions prominent
- Generic `sub_XXXXXX` names need investigation

---

## Statistics

### Completed (Ranks 1-100)
- Functions analyzed: 100
- Functions renamed: 100
- Inline comments added: 500+
- Major discoveries: 1 (r15_simulation_loop)

### Remaining (Ranks 101-200)
- Functions to analyze: 100
- Estimated time: TBD
- Expected patterns: More utility functions, less game loop logic

---

## Next Steps

1. ☐ Extract disassembly for ranks 101-110
2. ☐ Analyze purpose of each function
3. ☐ Rename in IDA with descriptive names
4. ☐ Add inline comments
5. ☐ Update registry
6. ☐ Batch process 111-120

---

*Last Updated*: 2026-11-11
