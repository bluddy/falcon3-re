# Falcon 3.0 Graphics Pipeline Analysis

**Status**: ✅ Analysis Complete | ⏳ Ready for IDA Verification  
**Session**: Extended graphics pipeline deep-dive  
**Date**: Resumed from compacted context

---

## 🎯 Quick Start

**New to this analysis?** Start here:

1. **Read**: [`GRAPHICS_PIPELINE_MAP.txt`](GRAPHICS_PIPELINE_MAP.txt) - Visual architecture overview
2. **Verify**: [`verification_quickstart.md`](verification_quickstart.md) - 5-minute IDA check
3. **Deep Dive**: [`session_extended_summary.md`](session_extended_summary.md) - Complete findings

**Ready to verify in IDA?** → [`verification_quickstart.md`](verification_quickstart.md)

---

## 📊 What Was Accomplished

### Major Discoveries

✅ **Complete graphics pipeline mapped** (view_projection + 16 calls)  
✅ **10 math helpers identified** (exclusive to view_projection)  
✅ **6 core graphics functions** analyzed  
✅ **10 vec3_transform callers** documented (9 named, 1 pending)  
✅ **farobj visibility system** reverse-engineered (Finding 208)  
✅ **Multi-entry architecture** discovered (57% of codebase)  
✅ **Finding 207 resolved** (address typo, false alarm)

### Statistics

- **28 files** created (~3,500 lines of code)
- **9 MB** of analysis data
- **~50 functions** analyzed and documented
- **9 commits** this session
- **2 findings** (1 closed, 1 documented)

---

## 📁 File Organization

### 🔍 Start Here
- **[`verification_quickstart.md`](verification_quickstart.md)** ⭐ - 5-min quick check + deep verification guide
- **[`GRAPHICS_PIPELINE_MAP.txt`](GRAPHICS_PIPELINE_MAP.txt)** - Visual architecture diagram
- **[`session_extended_summary.md`](session_extended_summary.md)** - Complete session report

### 📖 Documentation
- [`manual_verification_guide.md`](manual_verification_guide.md) - Phase-by-phase IDA checklist
- [`ida_verification_plan.md`](ida_verification_plan.md) - 7-phase verification strategy
- [`ADDRESS_TRANSLATION_GUIDE.md`](ADDRESS_TRANSLATION_GUIDE.md) - Segment:offset math
- [`view_projection_analysis.md`](view_projection_analysis.md) - Pipeline details
- [`math_helpers_identified.md`](math_helpers_identified.md) - Math library findings
- [`finding_207_sub_10bdb.md`](finding_207_sub_10bdb.md) - Finding 207 resolution

### 🔧 Analysis Tools
- [`analyze_view_projection.py`](analyze_view_projection.py) - Pipeline mapper
- [`analyze_graphics_functions.py`](analyze_graphics_functions.py) - Graphics function analyzer
- [`analyze_vec3_transform_callers.py`](analyze_vec3_transform_callers.py) - Caller mapper
- [`analyze_farobj_system.py`](analyze_farobj_system.py) - farobj system analyzer
- [`disassemble_math_helpers.py`](disassemble_math_helpers.py) - Custom x86 disassembler
- [`address_translator.py`](address_translator.py) - Address conversion tool

### ✔️ Verification Tools
- [`verify_graphics_pipeline.py`](verify_graphics_pipeline.py) - IDA batch verification
- [`run_verification.bat`](run_verification.bat) - Batch runner
- [`prepare_verification_data.py`](prepare_verification_data.py) - Data summary
- [`find_seg020.py`](find_seg020.py) - Segment calculator

### 📊 Data Files (JSON)
- [`segment_map.json`](segment_map.json) - 3.4 MB, complete segment/function map
- [`projection_pipeline_map.json`](projection_pipeline_map.json) - Call graph
- [`math_library_analysis.json`](math_library_analysis.json) - Math helpers
- [`graphics_functions_analysis.json`](graphics_functions_analysis.json) - 6 core functions
- [`vec3_transform_callers.json`](vec3_transform_callers.json) - Caller details
- [`farobj_system_analysis.json`](farobj_system_analysis.json) - farobj architecture
- [`sub_21657_analysis.json`](sub_21657_analysis.json) - Unnamed function
- [`math_helper_bytecode.json`](math_helper_bytecode.json) - Extracted bytecode

---

## 🏗️ Architecture Summary

### view_projection Pipeline (0x20BDB)
Main 3D-to-2D transformation pipeline, 1,076 bytes, calls 16 functions:

**Stage 1: Math Setup** (10 exclusive helpers)
- Segment configuration, dispatchers, shifts, lookups
- All in seg015, seg017, seg020
- Called ONLY by view_projection

**Stage 2: Transform** (vec3/vec2 operations)
- `fixed_vec3_transform_es` - 3D vector transform (10 callers)
- `vec2_normalize_seq` - 2D normalize (2 callers)

**Stage 3: Visibility Culling** (farobj system)
- 4 functions, 2 queues (near/far)
- Level-of-detail management
- 250+ related functions

### Data Structures
- **DGROUP:0x4287** - 3D coordinate structure
- **DGROUP:0x7C054** - Near object queue
- **DGROUP:0x7D0C6** - Far object queue (+ 4,210 bytes)
- **0x7772:0x0F34** - Math lookup table

### seg020 Details
- **Base**: 0x1F6C0
- **Size**: 45,936 bytes
- **Type**: Resident (not overlaid)
- **Contents**: All critical graphics code

---

## ✅ Verification Plan

### Quick Check (5 minutes)
Use [`verification_quickstart.md`](verification_quickstart.md):
1. Verify seg020 base address (0x1F6C0)
2. Check view_projection exists (0x20BDB)
3. Check fixed_vec3_transform_es (0x248D1, 10 callers)
4. Verify farobj queues (0x7C054, 0x7D0C6)

### Deep Verification (2-3 hours)
Use [`manual_verification_guide.md`](manual_verification_guide.md):
1. **Phase 1**: Address translation (30 min)
2. **Phase 2**: Math helper entry points (45 min)
3. **Phase 3**: Graphics functions (30 min)
4. **Phase 4**: vec3_transform callers (30 min)
5. **Phase 5**: Data structures (30 min)
6. **Phase 6**: Pipeline flow (30 min)
7. **Phase 7**: Multi-entry audit (30 min)

---

## 🔍 Key Findings

### Finding 207: Address Typo ✓ CLOSED
**Issue**: sub_256A3 appeared to call non-existent 0x10BDB  
**Resolution**: Typo - actual call is to 0x20BDB (view_projection)  
**Status**: False alarm, no code issue

### Finding 208: farobj System ✓ DOCUMENTED
**Discovery**: Complete visibility culling and LOD engine
- 4 core functions
- 2 queues (near/far)
- 250+ related functions
- Critical for Falcon 3.0 performance

### Multi-Entry Architecture
**Discovery**: 2,385 of 4,170 functions (57%) have multiple entry points  
**Impact**: Deliberate DOS-era optimization pattern throughout codebase

---

## 📝 Pending Items

### Needs Investigation
- [ ] Name `sub_21657` (no direct callers, indirect call)
- [ ] Name `sub_256A3` (uses DGROUP:0x4287)
- [ ] Document DGROUP:0x4287 structure layout
- [ ] Analyze 0x7772:0x0F34 table contents
- [ ] Detail farobj culling algorithm
- [ ] Map complete scene graph

### Verification Tasks
- [ ] Run 5-minute quick check (verification_quickstart.md)
- [ ] Complete deep verification (manual_verification_guide.md)
- [ ] Document discrepancies in verification_findings.txt
- [ ] Update JSON files based on IDA ground truth

---

## 🎓 Key Insights

1. **Multi-Entry is Deliberate** - 57% of functions use this optimization
2. **Math Helpers are Specialized** - 10 functions exclusive to view_projection
3. **Graphics Code is Resident** - seg020 never swapped, ensures performance
4. **farobj is Sophisticated** - 250+ functions for culling/LOD
5. **Pipeline is Well-Structured** - Clear stages: setup → transform → project

---

## 📈 Next Steps

### This Session
1. Run 5-minute IDA verification
2. Document any discrepancies
3. Update analysis files

### Next Session
1. Complete deep verification (2-3 hours)
2. Name pending functions (sub_21657, sub_256A3)
3. Document data structures
4. Map complete scene graph

### Future
1. Verify multi-entry functions (sample of 2,385)
2. Complete overlay architecture docs
3. Map entity-rendering integration
4. Create rendering pipeline flowchart

---

## 🛠️ How to Use This Analysis

### For Understanding Falcon 3.0 Graphics
1. Read [`GRAPHICS_PIPELINE_MAP.txt`](GRAPHICS_PIPELINE_MAP.txt)
2. Review [`view_projection_analysis.md`](view_projection_analysis.md)
3. Check data files: `projection_pipeline_map.json`, etc.

### For Verification
1. Start: [`verification_quickstart.md`](verification_quickstart.md)
2. Tools: `verify_graphics_pipeline.py`, `find_seg020.py`
3. Manual: [`manual_verification_guide.md`](manual_verification_guide.md)

### For Further Analysis
1. Tools: All `analyze_*.py` scripts
2. Data: All `*.json` files (9 MB of structured data)
3. Reference: [`ADDRESS_TRANSLATION_GUIDE.md`](ADDRESS_TRANSLATION_GUIDE.md)

---

## 📞 Quick Reference

### Key Addresses
```
view_projection            0x20BDB  (seg020:151B)  1,076 bytes
fixed_vec3_transform_es    0x248D1  (seg020:5211)    146 bytes
sub_256A3                  0x256A3  (seg020:5FE3)      ? bytes
abs_helper                 0x210EF  (seg020:1A2F)      ? bytes

DGROUP:0x4287   - 3D coordinate structure
DGROUP:0x7C054  - Near object queue
DGROUP:0x7D0C6  - Far object queue (+ 4,210 bytes)
0x7772:0x0F34   - Math lookup table
```

### Key Statistics
```
Total segments:        137
Total functions:       4,170
Multi-entry:           2,385 (57%)
seg020 base:           0x1F6C0
seg020 size:           45,936 bytes
```

### Git Commits
```
979c453  Finding 207 resolution
75f0a5c  Segment export tooling
b47e856  view_projection analysis
b2d6ed1  Math helper identification
98e2e2c  Math helper bytecode
da9d068  Graphics functions
71a3905  vec3_transform callers
91b27d2  farobj + sub_21657
19d2acf  Verification tools
7440994  Session summary
```

---

## 📄 License & Attribution

Part of the Falcon 3.0 reverse engineering project.

---

**Status**: ✅ Ready for IDA verification  
**Next**: Open [`verification_quickstart.md`](verification_quickstart.md) and begin!
