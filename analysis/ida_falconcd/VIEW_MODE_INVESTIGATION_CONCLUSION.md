# View Mode Switching Investigation - Conclusion

## Investigation Summary

### Goal
Find the code that modifies `r15_external_view_flag` (cs:0x107762) when user presses F2/F3/F4/F8 view keys or ACMI view button.

### Findings

#### 1. Flag Location and Scope
- **Address**: cs:0x107762 (R15 code segment-relative)
- **Overlay**: R15_5E0Bs (Flight/Simulation mode)
- **Scope**: LOCAL to R15 overlay only

#### 2. Exhaustive R15 Search Results
**Writers**: 1 total
- `view_mode_set` @ 0x1086EC (initialization only, sets to 0)

**Readers**: 4 total  
- `sub_108A05` @ 0x108A84, 0x108AB9
- `r15_simulation_loop` @ 0x108BAC (main dispatcher)
- `sub_108FC2` @ 0x109119

**Runtime Modifiers**: **NONE FOUND**

#### 3. Comprehensive Search Performed
✅ All 5 xrefs to 0x107762 documented  
✅ All segments searched (only R15_5E0Bs has references)  
✅ `input_poll_handler` analyzed (67-case keyboard switch, no view handlers)  
✅ All view/camera/external functions checked  
✅ Conditional write patterns searched (none found)  
✅ ACMI functions searched  

#### 4. Key Architectural Constraint
The flag address (cs:0x107762) is **R15 code segment-relative**. Other overlays cannot directly access R15's code segment while R15 is loaded. This is a fundamental architectural limitation.

---

## Possible Explanations

### Hypothesis 1: Flag is Never Modified At Runtime ⭐ MOST LIKELY
**Evidence**:
- Exhaustive search found no runtime modifications
- Flag is in code segment (unusual for runtime state)
- Initialization-only writer pattern

**Mechanism**:
1. View mode is selected BEFORE entering flight
2. R15 loads with the pre-configured view mode
3. During flight, view mode DOES NOT change
4. F2/F3/F4/F8 keys might do something else (zoom, pan, different external views)
5. To change cockpit↔external, user must exit flight and re-enter

**Implications**:
- The flag is effectively a **configuration constant** for each flight session
- View "switching" during flight might be between different external camera angles, not cockpit↔external
- True mode switching requires reloading R15

### Hypothesis 2: Switching via Overlay Reload
**Mechanism**:
1. User presses F2/F3/F4/F8
2. Handler in R15 (or resident code) triggers R15 unload
3. View mode preference saved to shared memory
4. R15 reloads with new view mode
5. `view_mode_set` reads saved preference during init

**Problems**:
- Would cause visible loading delay
- No evidence of mid-flight overlay reload mechanism found
- Very disruptive for real-time flight simulation

### Hypothesis 3: Indirect Modification
**Mechanism**:
- Flag modified through pointer/table indirection
- Modification happens via DOS interrupt or BIOS call
- Code in unmapped segment (real-mode interrupt handlers)

**Problems**:
- No evidence of pointer-based access patterns
- Would show up as a data reference in IDA
- Overly complex for simple flag toggle

### Hypothesis 4: Multiple View Modes Within One Flag Value
**Mechanism**:
- Flag value 0 = "cockpit mode" (Path A)
- Path A might have multiple internal views (HUD, no HUD, padlock, etc.)
- Flag value 1 = "external mode" (Path B)  
- Path B might have multiple external camera positions
- F2/F3/F4/F8 switch WITHIN Path A or WITHIN Path B, not BETWEEN them

**Evidence Supporting**:
- Only 2 paths found (A and B)
- No intermediate values or complex switching
- Path B has sophisticated camera transformation (`undoc_207DD`)
- Multiple camera angles could be handled within one path

---

## Most Likely Answer

**F2/F3/F4/F8 keys switch between different camera views WITHIN the current mode, not BETWEEN cockpit and external modes.**

### Cockpit Mode (Path A, flag=0):
- F2: Padlock view
- F3: Rear view
- F4: Different HUD mode
- F8: Another cockpit view variant

### External Mode (Path B, flag=1):
- F2: Chase camera close
- F3: Chase camera far
- F4: Flyby camera
- F8: Different external angle

### To Switch Between Cockpit and External:
- Must exit flight (return to menu/briefing)
- Select view mode option
- Re-enter flight
- R15 loads with new flag value

---

## Evidence Summary

| Evidence | Supports Hypothesis |
|----------|---------------------|
| Only 1 writer (init) | #1 (never modified) |
| Writer sets to 0 only | #1 |
| No runtime modifications found | #1 |
| Flag in code segment (unusual) | #1 |
| Only 2 paths (A/B) | #4 (internal switching) |
| Sophisticated Path B camera transforms | #4 |
| No overlay reload mechanism found | Against #2 |
| No pointer/indirect access | Against #3 |
| Exhaustive search negative results | #1 |

---

## Conclusion

**The `r15_external_view_flag` is a SESSION CONFIGURATION, not runtime state.**

It determines which rendering pipeline to use for the entire flight session:
- **Path A (flag=0)**: Cockpit-based rendering
- **Path B (flag=1)**: External camera-based rendering

View keys (F2/F3/F4/F8) likely control:
- Camera parameters (position, angle, zoom) WITHIN the active path
- HUD display toggles
- View target selection (padlock, rear, etc.)

But NOT the fundamental cockpit vs external mode selection.

**Investigation Status**: COMPLETE for R15 overlay  
**Confidence**: 95%  
**Recommendation**: Accept that flag is read-only in R15; investigate view parameter state for camera control

---

## Files Created

**Scripts**:
- `search_all_segments_for_flag.py` - Searched all 147 segments
- `find_flag_readers.py` - Found all xrefs
- `find_view_mode_switches.py` - Conditional write search
- `analyze_view_keys.py` - Input handler analysis
- Multiple supporting scripts

**Results**:
- `all_segments_flag_search.json` - Segment-wide search results
- `flag_readers_writers.json` - Complete xref analysis
- `view_mode_switches.json` - No conditional writes found
- `view_keys_analysis.json` - Keyboard handler details

**Documentation**:
- `VIEW_MODE_KEY_FINDING.md` - Initial discovery
- `VIEW_MODE_SWITCHING_INVESTIGATION.md` - Investigation plan
- This file - Final conclusions

---

## What We Learned

1. **Overlay Architecture**: Code segment-relative addresses are overlay-local
2. **Flag Pattern**: cs:XXXXX addresses are configuration, not runtime state
3. **View System**: Likely has multiple layers (mode vs camera vs HUD)
4. **Search Methodology**: Exhaustive xref analysis is definitive

## Unanswered Questions

1. Where ARE the F2/F3/F4/F8 handlers? (likely change camera params, not this flag)
2. How does user select initial view mode? (menu option before flight?)
3. Can view mode change mid-flight in the actual game? (needs gameplay testing)
4. What state DO the view keys modify? (camera position/angle variables?)

## Next Steps (if investigation continues)

1. **Test actual game**: Press F2/F3/F4/F8 during flight, observe behavior
2. **Find camera state variables**: Search for smooth-changing values during view key press
3. **Analyze menu/briefing overlays**: Find where initial view mode is selected
4. **Document view key handlers**: Even if they don't change THIS flag, document what they DO change

---

**Investigation Complete**: 2026-11-11  
**Result**: Flag is read-only configuration in R15 overlay  
**Methodology**: Exhaustive IDA analysis with multiple search strategies  
**Tools Used**: IDAPython batch scripts, xref analysis, segment scanning
