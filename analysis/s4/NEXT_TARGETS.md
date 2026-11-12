# Next Analysis Targets - Exciting Discoveries Await!

Based on verified findings, here are the most interesting targets:

## 🔥 HOT TARGETS (High Impact)

### 1. sub_256A3 - Called from Main Game Loop ⭐⭐⭐
**Why exciting**: Called directly from `game_frame_pipeline_step` at position 10/44
- Address: 0x256A3 (seg020:5FE3)
- Unknown function, needs naming
- Uses DGROUP:0x4287 (3D coordinate structure)
- In main rendering path

**What we'll discover**: Core rendering operation between terrain and entity updates

### 2. overlay_tail_bridge (0x166F) ⭐⭐
**Why exciting**: Only discovered through API verification
- Called by view_projection
- Manages overlay swaps during rendering
- May reveal overlay system architecture
- Could explain dynamic code loading

**What we'll discover**: How Falcon 3.0 swaps code overlays on the fly

### 3. terrain_frame_update_driver (0x3805) ⭐⭐⭐
**Why exciting**: Called from main loop, big terrain system
- Likely manages all terrain rendering
- May connect to heightmap system
- Could reveal LOD for terrain
- Performance critical

**What we'll discover**: How Falcon 3.0 renders massive terrain on 386/486

### 4. viewlist_project_flagged (0x0) ⭐⭐
**Why exciting**: Called early in frame pipeline
- Projects view list items
- "flagged" suggests selective processing
- May be first culling pass

**What we'll discover**: How view frustum culling works

### 5. r32_hud_phase_dispatch (0x3FBB) ⭐
**Why exciting**: HUD rendering entry point
- Called after all 3D processing done
- "phase_dispatch" suggests multi-stage HUD
- r32 prefix suggests overlay 32

**What we'll discover**: Complete HUD rendering pipeline

## 🎯 MEDIUM TARGETS (Interesting Details)

### 6. farobj_slot_project_step (0xCC2)
**Called 4x per frame** - what are the 4 categories?

### 7. entity_update_batch (0x49BA)
Entity simulation system

### 8. view_rotation_build (0x4E76)
Camera/view matrix construction

### 9. viewobj_table64_project (0x2E0F)
One of 3 viewobj projection functions - why 3 different tables?

### 10. farobj_batch_build_project
Batch processing caller of farobj_sort_and_step

## 🔍 DEEP DIVES (Architecture Understanding)

### 11. Complete Overlay System
- Map all overlay segments (R15, R32, R39, etc.)
- Understand swap triggers
- Document overlay table structure

### 12. Entity System
- entity_update_batch
- entity_move_project_step  
- entity_state_load
- How entities are simulated and rendered

### 13. Terrain System
- terrain_frame_update_driver
- terrain_vm_flag_gate
- terrain_state_reinit
- Heightmap and LOD system

### 14. Input → Simulation → Render Pipeline
- Map complete frame from input to display
- Understand timing and synchronization
- Find the actual display swap

### 15. Memory Management
- Slot-based object pools
- Queue management
- Overlay loading
- Dynamic allocations (if any)

## 🎮 GAMEPLAY SYSTEMS

### 16. Flight Physics
Likely in overlays, but connections to main loop

### 17. Weapons System
Missile simulation, gun ballistics

### 18. AI System
Enemy plane behavior, targeting

### 19. Mission System
Objectives, waypoints, triggers

### 20. Sound System
How audio integrates with frame pipeline

## 📊 ANALYSIS PRIORITIES

### Immediate (This Session)
Pick one HOT TARGET and fully map it:
- ✅ **Option A**: sub_256A3 (unknown main loop function)
- ✅ **Option B**: overlay_tail_bridge (overlay system)
- ✅ **Option C**: terrain_frame_update_driver (terrain rendering)

### Short-term (Next Session)
- Map 2-3 more HOT TARGETS
- Start entity system documentation
- Begin overlay system mapping

### Long-term
- Complete all gameplay systems
- Full input-to-display pipeline
- Write "Falcon 3.0 Architecture Guide"

---

## My Recommendation: Start with sub_256A3

**Why**:
1. Called from main game loop (position 10/44)
2. Between terrain and entity processing
3. Uses 3D coordinate structure (DGROUP:0x4287)
4. Unknown name = discovery potential
5. Quick win (single function analysis)

**What we'll learn**:
- Core rendering operation
- 3D coordinate structure layout
- Another piece of frame pipeline puzzle

**Time estimate**: 30-60 minutes to fully analyze

---

**What sounds most exciting to you?** 🚀
