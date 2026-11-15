import idaapi
import idc

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Renaming Path B functions with descriptive names...")

# Define renames based on analysis
renames = [
    # Already has good name, just add comment
    (0x205BF, "stub_to_205c3", "Far call dispatcher stub (Path B) - Used by HUD metrics, explosions, terrain, map overlay (20 callers)"),
    
    # Major rename: View transformation
    (0x207DD, "external_view_transform", "External view camera transformation - Applies rotation, transforms world→camera space, projects using trig tables (102B, Path B only)"),
    
    # Terrain setup for camera
    (0x128CD, "external_terrain_camera_setup", "Terrain setup for external view - Builds terrain grid from CAMERA position instead of aircraft (67B, Path B only)"),
    
    # Iterative processing
    (0x109660, "external_view_buffer_iterate", "External view iterative buffer processing - 19 iterations, likely smoothing/interpolation (107B, Path B only)"),
    
    # Terrain frame update
    (0x12910, "external_terrain_frame_update", "Terrain frame update for external view - Scans neighbors, updates counter, walks attributes (43B, Path B only)"),
    
    # Flag setters
    (0x1FE68, "farptr_render_flag_set", "Set far pointer rendering flag cs:0x1F75D = 1 - Marks start of saved state rendering (7B, Path B)"),
    
    (0x1FE6F, "farptr_render_flag_clear", "Clear far pointer rendering flag cs:0x1F75D = 0 - Marks end of saved state rendering (7B, Path B)"),
    
    # Vector normalization (already has good name, enhance comment)
    (0x210FE, "vec_delta_norm_1f6ee", "3D vector delta normalization - Calculates normalized direction from source to target (442B, Path B)"),
    
    # Far pointer functions (already named, enhance comments)
    (0x1F0C0, "active_farptr_set", "Save current far pointer state - Preserves EMS segment context for complex rendering (Path B)"),
    
    (0x1F0D7, "active_farptr_restore", "Restore far pointer state - Returns to saved EMS segment context (Path B)"),
    
    # Unknown functions - give descriptive temporary names
    (0x1FF5D, "external_view_unknown_1ff5d", "Path B function after vector normalization - Purpose unknown, needs investigation"),
    
    (0x21240, "external_view_unknown_21240", "Path B function in rendering section - Purpose unknown, needs investigation"),
    
    (0x20BCE, "external_view_unknown_20bce", "Path B function in rendering section - Purpose unknown, needs investigation"),
]

renamed_count = 0
comment_count = 0

for addr, new_name, description in renames:
    current_name = idc.get_func_name(addr)
    
    # Rename if different or if it's a generic name
    if current_name != new_name:
        if idc.set_name(addr, new_name, idc.SN_CHECK):
            print(f"  [+] Renamed 0x{addr:X}: {current_name} -> {new_name}")
            renamed_count += 1
        else:
            print(f"  [=] Kept existing name at 0x{addr:X}: {current_name}")
    else:
        print(f"  [=] Already named at 0x{addr:X}: {current_name}")
    
    # Always update function comment
    idc.set_func_cmt(addr, description, 1)
    comment_count += 1

# Add inline comments to key functions
print("\n[*] Adding inline comments...")

# external_view_transform (0x207DD)
idc.set_cmt(0x207DF, "Load segment 7B0E (trig/view data)", 0)
idc.set_cmt(0x207E6, "Apply scroll and rotation to view", 0)
idc.set_cmt(0x207F1, "Wrap angles to 0-0x3FFF range", 0)
idc.set_cmt(0x207F4, "Project using trigonometry tables", 0)
idc.set_cmt(0x20802, "Negate for inverse transform", 0)
idc.set_cmt(0x20820, "Store 4 transformed viewport coordinates", 0)
idc.set_cmt(0x20832, "Clip/cull check", 0)
idc.set_cmt(0x2083D, "Dispatch renderer based on mode", 0)
print("  [+] Added 8 inline comments to external_view_transform")

# external_terrain_camera_setup (0x128CD)
idc.set_cmt(0x128CF, "Load terrain segment 71C1", 0)
idc.set_cmt(0x128D7, "Store target pointer for terrain data", 0)
idc.set_cmt(0x128E1, "Copy 12 bytes (6 words) - camera position/orientation", 0)
idc.set_cmt(0x128E8, "Get altitude value", 0)
idc.set_cmt(0x128F1, "Clamp negative altitude to 0xF000", 0)
idc.set_cmt(0x128F8, "Get XY position", 0)
idc.set_cmt(0x12907, "Build terrain grid from CAMERA position", 0)
idc.set_cmt(0x1290A, "Advance terrain matrix for rendering", 0)
print("  [+] Added 8 inline comments to external_terrain_camera_setup")

# external_terrain_frame_update (0x12910)
idc.set_cmt(0x12912, "Load terrain segment 71C1", 0)
idc.set_cmt(0x12919, "Scan neighboring terrain tiles", 0)
idc.set_cmt(0x1291C, "Check if frame counter should increment", 0)
idc.set_cmt(0x1292A, "Increment terrain frame counter", 0)
idc.set_cmt(0x1292F, "Clear terrain processing flag", 0)
idc.set_cmt(0x12935, "Walk terrain attributes (LOD, visibility, streaming)", 0)
print("  [+] Added 6 inline comments to external_terrain_frame_update")

# farptr_render_flag_set (0x1FE68)
idc.set_cmt(0x1FE68, "Set flag = 1 to mark start of saved state rendering", 0)
print("  [+] Added 1 inline comment to farptr_render_flag_set")

# farptr_render_flag_clear (0x1FE6F)
idc.set_cmt(0x1FE6F, "Clear flag = 0 to mark end of saved state rendering", 0)
print("  [+] Added 1 inline comment to farptr_render_flag_clear")

# external_view_buffer_iterate (0x109660)
idc.set_cmt(0x10966D, "Source buffer: 6D60h", 0)
idc.set_cmt(0x109675, "Target buffer: 6E00h", 0)
idc.set_cmt(0x10967B, "Loop 19 times (0x13h)", 0)
idc.set_cmt(0x10968D, "Target buffer: 6E00h", 0)
idc.set_cmt(0x109695, "Working buffer: 6E78h", 0)
idc.set_cmt(0x1096B3, "Copy results back to source", 0)
idc.set_cmt(0x1096BE, "Copy final results", 0)
print("  [+] Added 7 inline comments to external_view_buffer_iterate")

# Also update r15_simulation_loop to note the Path B section
idc.set_cmt(0x108BAC, "Main simulation loop - Path A (cockpit) vs Path B (external view)", 0)
idc.set_cmt(0x108BB2, "Check external view flag: 0=cockpit, 1=external", 0)
idc.set_cmt(0x108BB7, "Path A: Cockpit view (37 calls)", 0)
idc.set_cmt(0x108CDF, "Path B: External view (46 calls, +24% overhead)", 0)
idc.set_cmt(0x108D19, "Path B start: View transformation pipeline", 0)
idc.set_cmt(0x108D71, "Path B: Save far pointer state", 0)
idc.set_cmt(0x108DAA, "Path B: Restore far pointer state", 0)
print("  [+] Added 7 inline comments to r15_simulation_loop")

print(f"\n[+] Batch rename complete!")
print(f"    Functions renamed: {renamed_count}")
print(f"    Function comments updated: {comment_count}")
print(f"    Inline comments added: 38")

# Exit IDA
idc.qexit(0)
