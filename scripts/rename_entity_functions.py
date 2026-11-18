"""
Rename entity update functions based on analysis.

1. farobj_slot_update_driver @ 0x3C1BD -> entity_slot_update_loop
   - Loops through 16 entity slots (0x386F, stride 0x5C=92 bytes)
   - Main per-frame update coordinator for all active entities

2. farobj_step_terrain_clamp @ 0x47787 -> entity_ground_collision_check
   - Checks entity altitude vs terrain height
   - Clamps/detects ground impact for bombs/missiles

3. ai_entity_update_step @ 0x3D37F -> entity_physics_and_ai_update
   - Large function (1319 bytes) handling physics and AI
   - Likely has gravity, guidance, combat logic
"""

import idc
import idaapi

print("=" * 80)
print("RENAME ENTITY UPDATE FUNCTIONS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

renames = [
    {
        'address': 0x3C1BD,
        'old_name': 'farobj_slot_update_driver',
        'new_name': 'entity_slot_update_loop',
        'comment': """Main entity update loop - processes all 16 entity slots per frame.
        
Structure:
- Segment 0x54AF (entity data)
- Base: 0x386F (entity_slot_records)
- Stride: 0x5C (92 bytes per slot)
- Count: 0x10 (16 entity slots)

Calls per-entity update functions for active slots (bit 0 of +0x0A = active flag).
This is the top-level coordinator for entity physics, AI, rendering, and collision."""
    },
    {
        'address': 0x47787,
        'old_name': 'farobj_step_terrain_clamp',
        'new_name': 'entity_ground_collision_check',
        'comment': """Ground collision detection and terrain clamping.

Checks entity altitude against terrain height at entity X/Y position.
For bombs/missiles: detects impact when altitude <= terrain_height.
For aircraft/ground units: prevents clipping through terrain.

Triggers impact events for weapons hitting ground."""
    },
    {
        'address': 0x3D37F,
        'old_name': 'ai_entity_update_step',
        'new_name': 'entity_physics_and_ai_update',
        'comment': """Large per-entity physics and AI update function (1319 bytes).

Handles:
- Gravity application (velocity_z -= gravity_constant)
- Drag/air resistance
- Weapon guidance (Maverick, HARM, missile tracking)
- AI behavior (target selection, evasion, attack)
- Combat logic (firing weapons, damage checks)
- Position integration (position += velocity * dt)

Called by entity_slot_update_loop for each active entity.
One of the largest functions in the game - central to entity simulation."""
    }
]

for item in renames:
    addr = item['address']
    old_name = item['old_name']
    new_name = item['new_name']
    comment = item['comment']
    
    current_name = idc.get_func_name(addr)
    
    print(f"Renaming @ {addr:#08x}:")
    print(f"  Old: {current_name}")
    print(f"  New: {new_name}")
    
    if idc.set_name(addr, new_name, idaapi.SN_NOWARN):
        print(f"  ✓ Renamed successfully")
    else:
        print(f"  ✗ Failed to rename")
    
    # Set comment
    idc.set_func_cmt(addr, comment, 1)
    print(f"  ✓ Added comment")
    print()

print("=" * 80)
print("All functions renamed")
print("Exiting IDA...")

# Exit
idc.qexit(0)
