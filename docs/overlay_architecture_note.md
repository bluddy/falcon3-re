# Overlay Architecture: Game Mode Isolation

**Date:** 2026-11-11  
**Source:** User observation + text analysis  
**Status:** WORKING HYPOTHESIS

## Key Insight

The different overlay records correspond to **different game modes**, not shared libraries or utilities. This explains several architectural patterns observed during Finding 206 analysis.

## Evidence

**From text strings in overlays:**
- Joystick calibration overlay
- Menu during flight overlay
- Flight engine overlay  
- Waypoint planning overlay
- (Others: briefing, debriefing, loadout, mission planning, etc.)

**Architectural implications:**
- Overlays are **mutually exclusive** (only one active at a time)
- Limited cross-calling between overlays (mode isolation)
- Wrapper pattern exists for mode entry/exit
- Dispatcher table (~29 entries in sub_263F6) = mode state machine

## Why This Matters

### For Overlay Analysis

**What we thought:** Shared code libraries loaded on demand  
**What it actually is:** Complete game mode implementations

**Implication for Finding 206:**
- Top 30 named overlays = most-used game modes (flight, menus, setup)
- Unnamed overlays = rare modes or error paths
- The 97% coverage means we've named the hot modes

### For Dispatcher Analysis (Finding 206 sub_263F6)

The 29-entry dispatch table likely maps to:
- Main menu
- Flight modes (different phases)
- Mission planning
- Briefing/debriefing
- Loadout configuration
- Options/settings
- Calibration
- Error/recovery states
- etc.

### For Call Graph Analysis

**Why overlay wrappers dominate Level-1:**
- Each mode has entry points (wrappers)
- Real logic is isolated within each overlay
- Cross-mode calls are rare by design
- Mode transitions go through resident code

## Architecture Model

```
Resident Code (Always loaded)
├── Mode dispatcher (sub_263F6?)
├── Overlay loader (sub_1AFBD?)
├── Shared utilities (DGROUP accessors, etc.)
└── Mode entry wrappers (Level-1 functions)

Overlay Records (Load on demand, mutually exclusive)
├── R01-R04: Core/bootstrap modes?
├── R05: Large mode (257KB) - Flight engine?
├── R27-R29: Menu/UI modes?
├── R30-R68: Specific game modes
└── R69+: Rare/special modes

Each overlay contains:
├── Mode-specific logic
├── UI rendering for that mode
├── Input handling
├── Local data structures
└── Mode exit/cleanup
```

## Impact on Decompilation Strategy

### What This Changes

**Priority shifts:**
1. ~~Analyze cross-overlay calls~~ → Focus on mode-internal logic
2. ~~Map overlay dependencies~~ → Document mode transitions
3. ~~Find shared libraries~~ → Understand mode lifecycle

**Naming strategy:**
- Name by game mode context (flight_*, menu_*, briefing_*, etc.)
- Overlay number less important than mode identity
- Text strings are excellent naming hints

**Analysis approach:**
- Study one complete mode (e.g., flight) end-to-end
- Understand mode entry/exit patterns
- Map mode state machines within each overlay
- Resident code = mode coordination layer

### What Stays the Same

- Following call frequencies still valid (hot modes = hot code)
- Boundary fixes still needed
- DGROUP analysis still critical (shared state)
- sub_10BDB still missing and blocking

## Related Findings

- **Finding 206:** Overlay target analysis (confirmed mode isolation via call patterns)
- **Finding 204:** Multi-layer overlay wrapper architecture (mode entry infrastructure)
- **Finding 176:** VGRAPH as separate mode (graphics driver overlay)

## Questions This Raises

1. **How do modes transition?**
   - Through resident dispatcher?
   - Via sub_1AFBD overlay hook?
   - Mode exit → loader → mode entry?

2. **What's the mode lifecycle?**
   - Load → Initialize → Run → Cleanup → Unload?
   - Can modes nest or only flat transitions?

3. **Is there mode state persistence?**
   - DGROUP stores cross-mode state?
   - Mode-local state in overlay data?
   - Save/restore mechanism?

4. **Why 29 modes in dispatcher?**
   - All distinct game states?
   - Including error/debug modes?
   - Some slots unused/reserved?

## Next Steps

**With this context:**

1. **Analyze mode transitions** (Priority: HIGH)
   - Study sub_1AFBD (overlay entry hook, 41K calls)
   - Find mode exit pattern
   - Map resident dispatcher logic

2. **Document mode boundaries** (Priority: MEDIUM)
   - Which overlays = which modes
   - Text string analysis per overlay
   - Mode call frequency ranking

3. **Complete DGROUP analysis** (Priority: HIGH, blocked by sub_10BDB)
   - What shared state crosses modes?
   - Player state, save data, etc.

4. **Deep dive one mode** (Priority: MEDIUM)
   - Pick flight mode (largest, most complex)
   - Understand one complete mode lifecycle
   - Use as template for others

## User Guidance Noted

> "I don't think there's going to be too much in terms of transitions between them."

**Interpretation:** Modes are largely independent, minimal cross-mode calls, transitions are discrete events not gradual handoffs.

**Implication:** Focus analysis within modes, not between them. Mode coordination is likely thin layer in resident code.

