# Level-0 Batch 7 Analysis (ranks 81-95)

## Critical Discovery: The Value Cliff Wall

**ALL 15 functions in batch 7 have dyn_calls = 0**

This is not a gradual decline - it's a **hard cliff**:
- Batch 5: 9.2K → 4.6K calls (50% drop)
- Batch 6: 3.3K → 1.7K calls (73% drop from batch 5 top)
- **Batch 7: 0 → 0 calls (complete absence of dynamic evidence)**

## Batch 7 Function Characteristics

### Size Distribution
- Tiny (8-45B): 4 functions (27%)
- Small (59-99B): 4 functions (27%)
- **Medium (199-355B): 3 functions (20%)**
- **Large (618-756B): 4 functions (27%)**

**Pattern shift:** Batch 7 has much LARGER functions than batches 1-6
- Batches 1-6: 73% tiny (2-6B), only 10% medium-large
- Batch 7: 73% medium-large (59-756B), only 27% tiny

### Static Callers
- All 15 functions have **in_degree = 1** (exactly 1 static caller each)
- This means: code exists, is reachable, but NEVER executed in traces

### Function Addresses
Sample addresses show these are scattered across overlays:
- 0x16379A, 0x13DE82, 0x163704 - R14/R16 overlays
- 0x16C246, 0x1A1E9C, 0x1617C - R16/R18/R01 overlays  
- 0x168A70, 0x196BDB, 0x16D5D1 - R16/R17 overlays
- 0x43DCA, 0x438A7, 0x3E8D2 - R05 resident/overlay
- 0x2E269, 0x10233B, 0x10626E, 0x102646 - R01 overlay

## Why These Functions Were Never Called

**Possible reasons:**

1. **Unused features**: Code for features that exist but weren't accessed in test runs
   - Training modes, multiplayer, advanced options, cheats
   - Alternative UI flows, debug menus, developer tools

2. **Error/edge case handlers**: Paths that only execute on errors
   - Hardware detection failures
   - File I/O errors (missing files, corrupt data)
   - Out-of-memory conditions
   - Invalid state recovery

3. **Platform-specific code**: Paths for hardware not present in test environment
   - Different graphics cards (EGA vs VGA vs MCGA)
   - Sound card variants (SoundBlaster vs AdLib vs PC speaker)
   - Joystick/input device variations

4. **Dead code**: Remnants from development
   - Debugging functions left in release build
   - Obsolete features not fully removed
   - Experimental code paths

5. **Extremely rare conditions**: Requires specific game state
   - Achieving perfect score on certain missions
   - Specific combinations of damage/weather/time
   - Easter eggs or hidden features

## Decision: Stop Level-0 Naming at Batch 6

**Rationale:**
1. **66 named functions (22.8% of 289) captured the "hot path"**
   - Core game loop: dispatch, state, view, math, utilities
   - All high-frequency operations (1.7K-18K calls)
   - CS-segment state map 95% complete

2. **Remaining 223 functions (77%) have diminishing returns**
   - Batch 7 = complete cliff (0 dynamic calls)
   - Likely unused, rare, or platform-specific code
   - Large functions (100-700B) = complex, time-intensive to name

3. **Better investment: Level-1 naming**
   - 327 endpoints → 911 total nodes in call graph
   - Level-1 = callers of Level-0 = higher-level logic
   - Many have dynamic evidence (thousands to millions of calls)
   - Will provide architectural insight that Level-0 cannot

## Value Delivered by Level-0 Batches 1-6

**Functions named: 66 (22.8% of Level-0)**
**Findings documented: 203 (24 findings from S4 work)**

**Architectural discoveries:**
- CS-segment state map: 170+ bytes, 16 regions
- Dispatcher infrastructure: nested dispatch, parameter save/restore
- PRNG: triple LCG at CS:[0x35B7-0x35C7]
- String formatting: itoa_decimal_signed
- 3D vector operations: vec3_copy_clamp_xy_40
- View space: segment 0x7B0E indexed tables
- Data segment: 0x834A specialized operations

**Pattern analysis:**
- 67% CS-segment accessors (state variables)
- 20% dispatch stubs (function pointer arrays)
- 6% utilities (PRNG, itoa, math, coord transform)
- 5% complex dispatchers (nested, conditional)
- 3% indexed tables (view parameters)

## Recommendation

**STOP Level-0 naming after batch 6**

**Next priorities:**
1. Document finding 204 (the value cliff analysis)
2. Pivot to **Level-1 naming** (callers of Level-0)
   - Start with high dyn_calls Level-1 nodes
   - Bottom-up naming continues, but one level higher
   - Target: game loop, mode handlers, entity managers
3. Or: Fix deferred boundary errors (4 functions → 9 after splits)
4. Or: Generate summary report of S4 progress for status.md

The 66 Level-0 functions named represent the **core primitives** of the game engine.
Level-1 will reveal the **architectural patterns** that use these primitives.
