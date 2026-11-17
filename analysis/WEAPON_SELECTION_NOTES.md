# Weapon Selection System - Investigation Notes

**Date:** 2026-11-17  
**Status:** Partial - keyboard handlers found, selected_weapon global not yet located

---

## Keyboard Commands (from Manual)

**Weapon Selection:**
- **Backspace** (scancode 0x0E): A-G weapon select (bombs, AGMs)
- **Enter** (scancode 0x1C): A-A weapon select (missiles, gun)
- **Space** (scancode 0x39): Fire weapon
- **Z** (scancode 0x2C): Radar lock
- **' (apostrophe)** (scancode 0x28): Increase bomb ripple
- **; (semicolon)** (scancode 0x27): Decrease bomb ripple

**Weapon Display:**
- **V**: View stores (loadout)
- **\ (backslash)**: ILS HUD mode (weapon display)

---

## Keyboard Handlers Found

### Backspace (A-G Select) - 25 handlers
Key handlers checking scancode 0x0E:
- `aircraft_state_dispatcher` @ 0x33651 ✓
- `main_frame_update_loop` @ 0x31319
- `mode_phase_apply_core` @ 0x32214, 0x32277
- `menu_event_dispatch` @ 0x674C5
- Many others (see weapon_select_keys.json)

### Enter (A-A Select) - 24 handlers
Key handlers checking scancode 0x1C:
- Multiple functions, need to identify primary handler

### Space (Fire) - 8 handlers
Key handlers checking scancode 0x39:
- `undoc_3A003` @ 0x3A003
- `ai_index_bounds_check` @ 0x3F603
- `farobj_utility_1819` @ 0x4C3C7
- Others (see weapon_fire_call_chain.json)

### Z (Radar Lock) - Multiple handlers
Scancode 0x2C checks found in various functions

---

## Loadout System Globals (Already in Registry)

From registry/globals.yaml:

**Loadout Configuration:**
- `loadout_total_weight` @ 0x5000 (dword) - Total weight in pounds
- `loadout_fuel_capacity` @ 0x5004 (word) - Fuel capacity after weight
- `loadout_drag_coefficient` @ 0x5006 (word) - Aerodynamic drag
- `loadout_hardpoint_config` @ 0x5010 (18 bytes) - 9 hardpoints × 2 bytes
- `loadout_weapon_supply` @ 0x5030 (32 bytes) - 16 weapon types × 2 bytes

**Menu System:**
- `menu_loadout_data` @ 0x79E60 (segment 0x7894)
- `menu_loadout_mode_flag` @ 0x79EA4 (segment 0x7894)
- `menu_loadout_data_ptr` @ 0x79E60 (segment 0x7894)
- `menu_loadout_array_ptr` @ 0x1C72 (segment 0x7894)

---

## Missing Globals

**Still need to locate:**

1. **`selected_weapon_type`** (byte or word)
   - Current weapon type (0x12=AIM-9, 0x13=AIM-120, 0x33=gun, etc.)
   - Read by fire handler to determine which weapon to spawn
   - Written by Backspace/Enter handlers when cycling weapons

2. **`selected_weapon_index`** (byte)
   - Index into loadout array (0-15?)
   - Which slot in current loadout is selected
   - Used to index into loadout_weapon_supply

3. **`weapon_mode`** (byte)
   - A-A mode (missiles/gun) vs A-G mode (bombs/AGMs)
   - Toggled by Backspace/Enter keys
   - Affects which weapons are available for cycling

4. **`bomb_ripple_count`** (byte or word)
   - Number of bombs to drop per fire event
   - Adjusted by ' and ; keys
   - Used for multiple bomb releases

5. **`fire_request_flag`** (byte)
   - Set by Space bar handler
   - Checked by weapon spawn system
   - Cleared after weapon spawned

---

## Analysis Approach

### Method 1: Trace from Keyboard Handler ❌ Failed
- Found 25 functions checking Backspace (0x0E)
- Most are general input handlers, not weapon-specific
- No clear data segment writes in immediate vicinity
- Weapon selection logic may be in dispatched functions

### Method 2: Search loadout_weapon_supply Xrefs ❌ No Results
- Tried finding xrefs to 0x5030 (loadout_weapon_supply)
- No results - variable may not have xrefs tracked in IDA
- May need to search for offset patterns (e.g., [bx+0x5030])

### Method 3: Analyze HUD Weapon Display ⏳ Not Yet Tried
- `r57_loadout_display_handler` @ 0x1A7E27 renders weapon icons
- Must read selected_weapon to know which icon to highlight
- Could trace back from display code to find the global

### Method 4: Analyze weapon_spawn_gate_validate ⏳ Partial
- Function @ 0x3DC55 validates fire requests
- Must check selected_weapon_type to determine what to spawn
- Analyzed but no obvious selected_weapon global found
- May use entity field or code segment variable

---

## Hypothesis: Register-Based or Code Segment

The selected weapon state might be:

1. **In code segment** (cs: variables)
   - Like weapon_queue_head @ cs:0x2E10A
   - Would explain why data segment searches fail
   - Need to search code segment for weapon state

2. **In entity/player structure**
   - Entity field @ [si+offset] 
   - Part of player aircraft state
   - Access pattern: load player entity, read weapon field

3. **Implicit from loadout array**
   - No "selected" variable, just iterates loadout_weapon_supply
   - Backspace/Enter advance a counter
   - Counter indexes into loadout array

---

## Next Steps

1. **Analyze HUD weapon display code**
   - `r57_loadout_display_handler` @ 0x1A7E27
   - `hud_rowlist_panel_draw` (has weapon type refs)
   - Find what global/field determines highlighted weapon

2. **Disassemble weapon selection handlers**
   - `aircraft_state_dispatcher` @ 0x33651 (has Backspace)
   - Trace what happens after Backspace detected
   - Follow call chain to weapon cycle logic

3. **Search code segment for weapon state**
   - Look for cs: variables near weapon queue (0x2E10A area)
   - Weapon state might be stored with queue state

4. **Check player entity structure**
   - Look for entity fields around +0x60-0x80
   - Weapon selection might be per-aircraft state

5. **Analyze fire button handler chain**
   - Complete trace from Space (0x39) to weapon_spawn_gate_validate
   - Find where selected_weapon_type is passed/checked

---

## Weapon Type Reference (for Verification)

When we find selected_weapon_type, it should contain these values:

**A-A Weapons:**
- 0x12: AIM-9 Sidewinder (IR missile)
- 0x13: AIM-120 AMRAAM (radar missile)
- 0x33-0x37: M61A1 Vulcan gun variants

**A-G Weapons:**
- 0x14-0x18: Dumb bombs? (Mk82, Mk84, CBU-87)
- 0x19: AGM-88 HARM (anti-radiation)
- 0x1A-0x1F: AGM-65 Maverick variants?
- 0x20-0x32: Other A-G weapons

From `weapon_type_initialize_dispatch` @ 0x4C19E:
- Types 0x12-0x13: Missile initialization path
- Types 0x33-0x37: Gun initialization path
- Gap 0x14-0x32: Handled elsewhere or not through this dispatcher

---

## Code References

**Scripts created:**
- `find_weapon_select_keys.py` - Found 25 Backspace, 24 Enter handlers
- `find_selected_weapon_global.py` - Searched loadout area (no results)
- `analyze_aircraft_state_dispatcher.py` - Analyzed Backspace handler
- `sync_weapon_globals_simple.py` - Synced weapon globals to IDA

**Data collected:**
- weapon_select_keys.json - All keyboard handler locations
- selected_weapon_search.json - Loadout global search results
- aircraft_state_dispatcher_analysis.json - Dispatcher analysis

---

## Known Working Examples

**IR Lock System (for comparison):**
- `ir_lock_target_index` @ 0x44AA - Current lock target
- Set by `weapon_aim9_seeker_lock_check` @ 0x32B7F
- Read by entity targeting code
- Fully traced and documented

**Expected pattern for weapon selection:**
- Similar structure to IR lock
- selected_weapon_type should be read by weapon_spawn_gate_validate
- Should be written by Backspace/Enter handlers
- Should be displayed by HUD weapon icon code

---

## Conclusion

Keyboard handlers are identified, but the selected_weapon global remains elusive. The weapon selection state is either:
- In code segment (cs: variables)
- In player entity structure
- Implicitly derived from loadout array iteration

**Recommendation:** Start with HUD weapon display code analysis - it MUST read the selected weapon to display the correct icon. Trace backwards from display to find the source global.

**Progress:** 30% complete
- ✓ Keyboard handlers located
- ✓ Loadout globals documented  
- ✗ Selected weapon global not found
- ✗ Selection logic not traced
- ✗ Weapon cycling mechanism unknown
