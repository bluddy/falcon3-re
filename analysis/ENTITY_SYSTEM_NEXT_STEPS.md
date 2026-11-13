# Entity System - Analysis Next Steps

**Current Status**: 75% Complete  
**Goal**: Push to 90%+ by filling key gaps

---

## What We Know (75%)

### ✅ Core Architecture
- 4-layer system (FarObj, EntitySlotRecord, timers, spawn queue)
- Main accessor: `farptr_table_get` (78 callers, 210K+ calls/session)
- Update pipeline mapped (6-step per-frame process)
- Type descriptor system understood

### ✅ FarObj Struct (Partial - ~80 bytes mapped of 210+)
**Well-understood fields**:
- World position (0x00-0x0B): int32 X, Y, Z
- Orientation (0x0C-0x11): heading, pitch, roll (14-bit angles)
- Type/category (0x12-0x1D): render_flags, entity_class, attributes
- Per-frame state (0x1E-0x27): timers, object_kind, slot_id
- Active flag (0x74): bit 0 = occupied
- Self reference (0x7A): slot index

**GAPS** (need work):
- Extended fields (0x2E-0x73): 70 bytes with varying access patterns
- Unknown region (0x7C-0xD0): 85 bytes
- Field purposes beyond basic access patterns

### ✅ Functions Mapped
- Creation: `entity_slot_create` (loads from disk!)
- Lifecycle: spawn queue, slot management
- Rendering: `farobj_sort_and_step` (called 3x per frame)
- Visibility: near/far queue system

---

## Key Gaps (25% Missing)

### 1. FarObj Field Semantics (Priority: HIGH)

**Problem**: We know WHICH fields are accessed, but not WHAT they mean.

**Example unknowns**:
- What is field +0x2E? (56 accesses in 41 functions - IMPORTANT!)
- What is field +0x30? (31 accesses in 25 functions)
- What are fields +0x7C through +0xD0? (85 bytes)

**Data exists** but needs interpretation:
- `farobj_si_fields.json` has access patterns
- `farobj_fields_probe.py` collected the data
- Need to correlate with function purposes

**Next step**: 
1. Parse `farobj_si_fields.json` properly
2. Group fields by access pattern type (read/write/alu)
3. Correlate with function names (e.g., flight_physics functions → motion fields)
4. Map to known systems (rendering, AI, physics)

### 2. EntitySlotRecord Structure (Priority: MEDIUM)

**Problem**: Only 3 bytes known of 92-byte struct

**Known**:
- +0x06: farobj_slot (index into main table)
- +0x0A: flags (bit 0 = active)
- Rest: UNKNOWN

**Why it matters**: 
- Updated 3x per frame per entity
- Core to entity processing pipeline
- 16 active slots = key performance structure

**Next step**:
1. Find `farobj_slot_update_driver` disassembly
2. Trace what fields are accessed
3. Map to per-frame update operations

### 3. AI / Behavior State Machines (Priority: HIGH)

**Problem**: Entity behavior logic not understood

**Clues**:
- `farobj_behavior_dispatch_step` @ 0x3CE92 (2,580 bytes!)
- References to "entity class" codes (0x12, 0x14, 0x33, 0x38)
- Flight physics integration exists but not mapped

**Why it matters**:
- Core gameplay: how enemies attack, evade, navigate
- Mission scripting likely ties into this
- AI difficulty/skill levels

**Next step**:
1. Disassemble `farobj_behavior_dispatch_step`
2. Find state machine dispatch tables
3. Map entity_class codes to behavior types
4. Trace decision-making logic

### 4. Inter-Entity Communication (Priority: MEDIUM)

**Problem**: How entities interact not documented

**Questions**:
- How does missile lock onto target?
- How do wingmen follow player?
- How do enemies coordinate?
- Collision detection between entities?

**Clues**:
- `farobj_record_ops_exec` @ 0x3BB8F (1,365 bytes)
- References to "op_dispatch" and "op-stream"
- Entity accum table (40 × 14B motion records)

**Next step**:
1. Analyze entity accum table usage
2. Find target acquisition functions
3. Map communication channels

---

## Recommended Approach

### Quick Win Option: Field Semantics (2-3 hours)

**Goal**: Map 20-30 most-accessed FarObj fields

**Method**:
1. Parse `farobj_si_fields.json` to extract field offsets
2. Count access frequency per field
3. For top 20 fields:
   - List all accessing functions
   - Categorize by function type (physics, rendering, AI, etc.)
   - Infer purpose from context
4. Update `farobj.md` with findings

**Expected outcome**: 75% → 85% complete

### Deep Dive Option: AI Behavior (4-6 hours)

**Goal**: Understand enemy AI state machines

**Method**:
1. Extract complete disassembly of `farobj_behavior_dispatch_step`
2. Find dispatch tables (jump tables, function pointer arrays)
3. Map entity_class to behavior handlers
4. Trace one complete behavior (e.g., "attack player")
5. Document state transitions

**Expected outcome**: 75% → 90% complete, major gameplay insight

### Comprehensive Option: Both (6-8 hours)

Do field semantics first (foundation), then AI behavior (builds on it).

**Expected outcome**: 75% → 95% complete

---

## Tools/Data Available

### Existing Analysis
- `analysis/s4/farobj_verified_findings.md` - Core functions verified
- `analysis/s4/farobj_si_fields.json` - Field access patterns (needs parsing)
- `analysis/s4/farobj_callers.json` - Complete caller information
- `docs/architecture/farobj.md` - Current documentation
- `docs/architecture/entity.md` - Lifecycle documentation

### IDA Disassembly
- `analysis/ida_falconcd/level19_*.txt` - Contains farobj functions
- Function names in `*_names.json` files
- Cross-references available

### Scripts
- `analysis/s4/farobj_fields_probe.py` - Field access scanner
- `analysis/s4/verify_farobj_system.py` - API verification
- `analysis/s4/analyze_farobj_system.py` - System analysis

---

## Success Criteria

**85% Complete** (Field Semantics):
- Top 20 FarObj fields documented with purpose
- Field groups identified (position, motion, AI state, rendering)
- Clear examples of usage per field

**90% Complete** (+ Partial AI):
- Main AI dispatch mechanism understood
- Entity class → behavior type mapping
- Example state machine traced (attack or patrol)

**95% Complete** (+ Full AI):
- Complete AI state machine documentation
- All entity classes mapped
- Inter-entity communication understood
- Collision detection system mapped

---

## Next Action

**Recommendation**: Start with **Quick Win** (Field Semantics)

**Rationale**:
1. Foundation for understanding other systems
2. Concrete, measurable progress
3. 2-3 hour time investment
4. High value (fills major documentation gap)

**First step**: Create tool to parse `farobj_si_fields.json` and generate field access report.

---

**Status**: Ready to proceed  
**Time estimate**: 2-3 hours to 85%, 6-8 hours to 95%  
**Blocker**: None - all data available
