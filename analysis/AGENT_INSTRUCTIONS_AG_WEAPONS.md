# Agent Instructions: A-G Weapons Continuation

**Date Created:** 2026-11-17  
**Purpose:** Instructions for future agents/context after compaction  
**Current Progress:** 90% weapons system, A-G weapons 60%

---

## IDA AUTOMATION - CRITICAL PATTERN

**ALWAYS read `docs/IDA_AUTOMATION_GUIDE.md` before running IDA scripts!**

### Working Pattern

```python
"""Script description."""
import idc
import idaapi
import json
from pathlib import Path

print("Starting analysis...")

# Wait for auto-analysis
idaapi.auto_wait()

# Your code here (NO main() function, just module-level code)

results = {"data": "value"}

# Save results
output_file = Path(__file__).parent / "output.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Saved to {output_file}")

# CRITICAL: Exit explicitly
idc.qexit(0)
```

### Run Command

```batch
"C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"script.py" "C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### Key Points

- NO `if __name__ == "__main__"` wrapper
- NO `main()` function - write code at module level
- MUST call `idaapi.auto_wait()` first
- MUST call `idc.qexit(0)` at end
- Use Python (.py), not IDC (.idc)
- Save results to JSON files
- See `analysis/s4/test_ida_minimal.py` for working example

---

## Current Status Summary

### Completed (90%)

✅ **IR Lock System (AIM-9 Sidewinder) - 100%**
- 9 globals documented (ir_lock_target_index, ir_lock_cycle_index_mode0/1, etc.)
- 2-mode search algorithm (simple 0-3, extended 4-16)
- Entity field: heat_signature @ +0xAE
- Lock tone integration
- Full analysis: `analysis/IR_LOCK_ANALYSIS.md`

✅ **Radar Lock System (AIM-120 AMRAAM) - 95%**
- Reuses existing radar globals (radar_selected_target_index, radar_mode_state)
- STT mode (radar_mode_state == 5) is lock state
- No new globals needed (leverages radar system)
- Full analysis: `analysis/RADAR_LOCK_ANALYSIS.md`

✅ **Weapon Queue System - 100%**
- 5 globals: weapon_queue_head, weapon_queue_count, weapon_processed_count, weapon_spawn_value, weapon_ammo_count
- 27-byte stride for A-A missiles and guns
- Full registry integration

✅ **A-G Weapon Queue - 100%**
- 2 new globals: ag_weapon_queue_head @ cs:0x4C0D6, ag_weapon_queue_count @ cs:0x4C0D8
- 41-byte stride (14 bytes more than A-A weapons)
- Separate dispatcher: farobj_utility_1819 @ 0x4C3C7
- Registry updated

✅ **A-G Weapon Types - 60%**
- Type 0x15: velocity 4860, damage 200 (Maverick?)
- Type 0x19: AGM-88 HARM (confirmed)
- Type 0x28: velocity 3280, damage 2 (bomb/rocket?)
- Type 0x2B: velocity 3690, damage 20
- Type 0x30: velocity 3526, damage 200 (similar to 0x15)
- Full analysis: `analysis/AG_WEAPONS_ANALYSIS.md`

✅ **Weapon Enums - 100%**
- WeaponType (11 values)
- IRLockSearchMode (2 values)
- WeaponKeyCode (6 values)
- DetectionModeState (6 values)
- All synced to IDA and registry

### Remaining Work (10%)

❌ **HARM Lock System - 0%**

**What needs to be found:**
1. Entity field: `radar_emitter_active` @ EntitySlotRecord +? (byte or bit flag)
   - Set for SAM sites, AAA radars when transmitting
   - Checked by HARM lock code to find targets
   - Cleared when radar shuts off

2. HARM lock code:
   - Function that scans entities for radar_emitter_active
   - Target selection/cycling (like IR lock but for emitters)
   - Lock tone when HARM acquires target
   - Dead-reckoning if emitter shuts off

**Where to look:**
- Type 0x19 handling in weapon spawn code
- Entity field +0x18 (mentioned in AG_WEAPONS_ANALYSIS.md as HARM target field)
- SAM site entity initialization (should set radar_emitter_active)
- Functions that write to entity fields in range +0x50 to +0xB0 (combat-related fields area)

**How to search:**
- Use IDA script to find entity field writes in SAM/AAA entity code
- Look for functions checking weapon type == 0x19
- Search for "HARM" or "ARM" strings in binary
- Check keyboard handler for HARM lock key (if separate from normal radar lock)

❌ **Bomb Ballistics - 0%**

**What needs to be found:**
1. Gravity constant (acceleration downward)
2. Drag coefficient application
3. CCIP (Continuously Computed Impact Point) calculation function
4. Impact point prediction display on HUD

**Where to look:**
- Dumb bomb types: 0x28 (and others with low damage, mid velocity)
- Physics system integration with weapon trajectory
- HUD rendering for CCIP pipper
- Release conditions (altitude, velocity checks)

❌ **Weapon Type Mapping - 50%**

**What's missing:**
- Exact names for types 0x14-0x32 (31 A-G weapons)
- Match types to manual weapon names (Mk82, Mk84, GBU-10/12, CBU-87, etc.)

**Where to look:**
- Loadout menu configuration data (menu system segment 0x7894)
- Weapon name strings in binary
- Loadout .BIN files (176×48 images, 8452 bytes each)
- Menu rendering code that displays weapon names

❌ **Selected Weapon Global - 0%**

**What's missing:**
- Global that stores currently selected weapon type
- Updated by Backspace (A-G select) and Enter (A-A select) keys
- Read by weapon fire logic

**Where to look:**
- Keyboard handlers @ 0x35D22 (Backspace), 0x30FBF (Enter)
- Weapon fire handler (Space @ 0x1FF73 dispatcher)
- Weapon display on HUD

---

## Registry Files

**All globals must be added to:** `registry/globals.yaml`

**All structs/enums must be added to:** `registry/structs.yaml`

**Then sync to IDA using scripts in:** `scripts/`

### Example: Adding Entity Field

```yaml
# In registry/structs.yaml under EntitySlotRecord:

- name: radar_emitter_active
  offset: 0x?? # Find this!
  size: 1
  type: byte
  doc: >
    Radar emitter active flag (0=off, 1=transmitting). Set for SAM sites and AAA radars
    when radar is on. Checked by HARM lock system to find targets. Cleared when radar
    shut off or destroyed.
  source: HARM_LOCK_ANALYSIS.md
```

Then run:
```batch
python scripts/sync_structs_to_ida.py
```

---

## Search Strategies for HARM Lock

### Strategy 1: Entity Field Write Search

Create IDA script to find all writes to entity fields in SAM/AAA entity types:

```python
# Search for entity field writes like:
# mov [bx+si+0x??], al
# where ?? is offset 0x50-0xB0 (combat fields area)
```

### Strategy 2: Type 0x19 References

Search for functions that check weapon type == 0x19 (already attempted, found few refs).

### Strategy 3: String Search

Search for "HARM", "ARM", "AGM", "RADIATION" strings in binary and check xrefs.

### Strategy 4: SAM Entity Analysis

Find SAM site entity initialization code and check what fields are set (radar on/off state must be stored somewhere).

### Strategy 5: Keyboard Handler Deep Dive

Trace from HARM select key through to lock acquisition (might be F key or special mode).

---

## Expected Deliverables

When HARM lock is found:

1. **HARM_LOCK_ANALYSIS.md** - Complete analysis document
2. **Entity field updated** - radar_emitter_active added to EntitySlotRecord
3. **Globals documented** - Any HARM lock globals found
4. **Registry updated** - All changes synced to registry/*.yaml
5. **IDA database updated** - Names synced to IDA
6. **Commit** - All changes committed with descriptive message

---

## Progress Tracking

**File:** `analysis/WEAPONS_PROGRESS_SUMMARY.md`

Update this file when making progress:
- IR Lock: 100%
- Radar Lock: 95%
- Weapon Queue: 100%
- A-G Weapons: 60% → update as you go
- HARM Lock: 0% → 100%
- Bomb Ballistics: 0% → 100%
- Overall: 90% → 95% → 100%

---

## Communication Pattern

When you (future agent) resume this work:

1. **Read this file first** for context
2. **Read docs/IDA_AUTOMATION_GUIDE.md** for IDA scripting
3. **Check analysis/AG_WEAPONS_ANALYSIS.md** for current findings
4. **Review registry/globals.yaml** and `registry/structs.yaml` to see what's already done
5. **Create focused IDA scripts** following the pattern above
6. **Document findings** in markdown files
7. **Update registry** as you discover new globals/fields
8. **Commit frequently** with clear messages
9. **Update progress** in WEAPONS_PROGRESS_SUMMARY.md

---

## Key Insight: Weapon System Architecture

The Falcon 3.0 weapon system is **polymorphic by weapon class**:

- **A-A Missiles** (0x12-13): 27-byte queue, inline initialization, IR/radar lock
- **Guns** (0x33-37): 27-byte queue, inline initialization, no lock
- **A-G Weapons** (0x14-0x32): 41-byte queue, separate dispatcher, varied guidance

Each class has optimized initialization for its guidance type. A-G weapons need more data (41 vs 27 bytes) for:
- Target coordinates
- Ballistics parameters
- Guidance mode (dumb/IR/TV/radar/laser)
- Release conditions

This polymorphism is elegant 1990s C design - dispatch by type range, separate initialization paths, shared entity system.

---

## Success Criteria

Weapons system is **100% complete** when:

- ✅ All weapon types identified and named
- ✅ All lock systems documented (IR ✓, radar ✓, HARM ?, laser ?)
- ✅ All weapon queues documented (A-A ✓, A-G ✓)
- ✅ All guidance systems analyzed (IR ✓, radar ✓, ballistics ?, laser ?)
- ✅ All relevant globals in registry
- ✅ All relevant entity fields in registry
- ✅ All major functions named in IDA
- ✅ All enums synced to IDA
- ✅ Comprehensive documentation in analysis/*.md
- ✅ Architecture document updated (docs/architecture/weapons.md)

**We're at 90%.** The remaining 10% is HARM lock, bomb ballistics, and weapon type mapping.

---

**End of agent instructions. Good luck!**
