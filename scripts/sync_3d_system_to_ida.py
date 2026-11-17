"""
Sync 3D projection system discoveries to IDA database.
- Rename data variables
- Add structure definitions
- Add detailed comments
"""

import idc
import idaapi
import idautils

def set_name_safe(ea, name):
    """Set name with error handling."""
    current = idc.get_name(ea)
    if current == name:
        print(f"  {name} already set at 0x{ea:X}")
        return True
    
    if idc.set_name(ea, name, idc.SN_NOWARN):
        print(f"  ✓ Named 0x{ea:X} -> {name}")
        return True
    else:
        print(f"  ✗ Failed to name 0x{ea:X} -> {name}")
        return False

def set_comment_safe(ea, comment, repeatable=True):
    """Set comment with error handling."""
    func = idc.set_cmt if not repeatable else idc.set_func_cmt
    if func(ea, comment, repeatable):
        print(f"  ✓ Comment at 0x{ea:X}")
        return True
    else:
        print(f"  ✗ Failed comment at 0x{ea:X}")
        return False

def main():
    print("="*80)
    print("SYNCING 3D PROJECTION SYSTEM TO IDA")
    print("="*80)
    
    idaapi.auto_wait()
    
    changes = 0
    
    # ========================================================================
    # 1. Vector State Variables (cs segment)
    # ========================================================================
    print("\n1. Naming Vector State Variables (cs segment)")
    print("-"*80)
    
    vector_vars = {
        0x22C71: "vec3_x_component",
        0x22C73: "vec3_y_component", 
        0x22C75: "vec3_z_component",
    }
    
    for addr, name in vector_vars.items():
        if set_name_safe(addr, name):
            changes += 1
            idc.set_cmt(addr, "3D vector component (16-bit fixed-point)", 1)
    
    # ========================================================================
    # 2. Transform Matrix Elements (cs segment)
    # ========================================================================
    print("\n2. Naming Transform Matrix Elements (cs segment)")
    print("-"*80)
    
    matrix_vars = {
        0x22C7D: "matrix_scale_x",
        0x22C7F: "matrix_scale_y",
        0x22C81: "matrix_scale_z",
    }
    
    for addr, name in matrix_vars.items():
        if set_name_safe(addr, name):
            changes += 1
            idc.set_cmt(addr, "3D projection matrix element (transform/scale factor)", 1)
    
    # ========================================================================
    # 3. Fixed-Point Divisors (cs segment)
    # ========================================================================
    print("\n3. Naming Fixed-Point Divisors (cs segment)")
    print("-"*80)
    
    divisor_vars = {
        0x22C83: "fixedpoint_divisor_x",
        0x22C85: "fixedpoint_divisor_y",
        0x22C87: "fixedpoint_divisor_z",
    }
    
    for addr, name in divisor_vars.items():
        if set_name_safe(addr, name):
            changes += 1
            # Read actual value to document format
            value = idc.get_wide_word(addr)
            if value == 256:
                fmt = "8.8 fixed-point"
            elif value == 4096:
                fmt = "12.4 fixed-point"
            elif value == 65536:
                fmt = "16.16 fixed-point"
            else:
                fmt = f"custom scale (value={value})"
            idc.set_cmt(addr, f"Fixed-point normalization divisor ({fmt})", 1)
    
    # ========================================================================
    # 4. Function Comments
    # ========================================================================
    print("\n4. Adding Function Comments")
    print("-"*80)
    
    function_comments = {
        0x22C89: """farobj_vec3_accum_b_ret - 3D Vector Projection Wrapper
        
Wrapper that calls fixed_vec3_accumulate_a and returns result in AX.
Used throughout game for 3D-to-2D projection (51,000+ calls/frame).

Returns: AX = accumulated result from vector dot product
Uses: HUD, tactical map, cockpit objects, external view""",
        
        0x22C91: """fixed_vec3_accumulate_a - 3D Vector Math Core (68 bytes)

THE mathematical heart of Falcon 3.0's 3D engine.
Computes: Result = (X*ScaleX/DivX) + (Y*ScaleY/DivY) + (Z*ScaleZ/DivZ)

Input (cs segment):
  vec3_x/y/z_component (22C71/73/75) - 3D vector
  matrix_scale_x/y/z (22C7D/7F/81) - Transform matrix elements
  fixedpoint_divisor_x/y/z (22C83/85/87) - Normalization

Output: CX = accumulated result (fixed-point)

Uses 16-bit fixed-point arithmetic (no FPU).
Accumulator pattern stores remainders for pseudo-RNG variation.

Called by: HUD targeting, flight physics, sprite projection,
           tactical map display, loadout UI""",
        
        0x22CD5: """fixed_vec3_accumulate_b - Alternative Entry Point

Same as fixed_vec3_accumulate_a but different calling convention.
Performs identical 3D vector dot product calculation.""",
        
        0x1A163A: """waypoint_display_helper - Tactical Map 3D Projection

Projects waypoint 3D coordinates (X, Y, altitude) to screen.
Calls farobj_vec3_accum_b_ret twice:
  1. Project X coordinate
  2. Project Y coordinate
  
Pipeline:
  Waypoint (world coords) → Camera transform → 
  fixed_vec3_accumulate_a → Screen coords (pixel_x, pixel_y)""",
        
        0x1A0F10: """waypoint_display_processor - Display System Initialization

Sets up data pointers and buffers for tactical map display:
  - word_7A2EA/E8 - Display data pointer
  - word_7A2F6/F4 - Waypoint array pointer  
  - word_7A2DA/D8 - Additional buffer pointer
  
Initializes display state before projection.""",
        
        0x1A2441: """waypoint_coordinate_processor - Data Structure Marshaling

Converts between display data structures:
  - 18-byte input structures
  - 6-byte output records
  - 21-byte waypoint records
  
Does NOT perform coordinate transformation (that's in waypoint_display_helper).
Handles data copying and format conversion.""",
        
        0x12DB6A: """tactical_screen_coordinator - UI Event Coordinator

Main coordinator for tactical map screen:
  - Handles keyboard/mouse input
  - Manages graphics mode state
  - Coordinates between menu and display systems
  
Calls waypoint_display_processor to trigger map rendering.""",
        
        0x02245A: """draw_from_struct - Central Graphics Dispatcher (649 calls)

Main drawing API used throughout game.
Takes 5-word struct: [x1, y1, x2, y2, attr]
Dispatches via cs:22084 table to specific primitives:
  - Type 1: Line (graphics_line_draw_bresenham)
  - Type 2: Rectangle (graphics_rect_fill_tiled)
  - Type 3: Sprite/blit
  
VGA Mode: 320x200 256-color (mode 13h)""",
        
        0x028B08: """graphics_line_draw_bresenham - Bresenham Line Algorithm (409 bytes)

Classic Bresenham line rasterization.
Draws line from (x1,y1) to (x2,y2) in VGA memory.

Target: 0xA000 segment (VGA framebuffer)
Screen: 320x200, 1 byte per pixel
Offset: Y * 320 + X

Used for: Flight paths, waypoint connections, HUD lines""",
    }
    
    for addr, comment in function_comments.items():
        func = idaapi.get_func(addr)
        if func:
            if idc.set_func_cmt(func.start_ea, comment, 1):
                print(f"  ✓ Function comment at 0x{addr:X}")
                changes += 1
        else:
            print(f"  ⚠ No function at 0x{addr:X}")
    
    # ========================================================================
    # 5. Display System Data Pointers (segment 0x7894)
    # ========================================================================
    print("\n5. Naming Display System Pointers (segment 0x7894)")
    print("-"*80)
    
    # Note: These are in data segment, addresses are offsets
    display_pointers = {
        0x7A2EA: ("display_data_ptr_seg", "Display data far pointer (segment)"),
        0x7A2E8: ("display_data_ptr_off", "Display data far pointer (offset)"),
        0x7A2F6: ("waypoint_array_ptr_seg", "Waypoint array far pointer (segment)"),
        0x7A2F4: ("waypoint_array_ptr_off", "Waypoint array far pointer (offset)"),
        0x7A2F2: ("display_buffer_handle", "Display buffer handle"),
        0x7A2DA: ("display_buffer2_seg", "Secondary display buffer (segment)"),
        0x7A2D8: ("display_buffer2_off", "Secondary display buffer (offset)"),
        0x7A2E6: ("display_buffer3_seg", "Tertiary display buffer (segment)"),
        0x7A2E4: ("display_buffer3_off", "Tertiary display buffer (offset)"),
        0x7A2FA: ("display_buffer4_seg", "Fourth display buffer (segment)"),
        0x7A2F8: ("display_buffer4_off", "Fourth display buffer (offset)"),
    }
    
    for addr, (name, comment) in display_pointers.items():
        if set_name_safe(addr, name):
            changes += 1
            idc.set_cmt(addr, comment, 1)
    
    # ========================================================================
    # 6. Read and Document Fixed-Point Format
    # ========================================================================
    print("\n6. Detecting Fixed-Point Format")
    print("-"*80)
    
    div_x = idc.get_wide_word(0x22C83)
    div_y = idc.get_wide_word(0x22C85)
    div_z = idc.get_wide_word(0x22C87)
    
    print(f"  Divisor X: {div_x} (0x{div_x:X})")
    print(f"  Divisor Y: {div_y} (0x{div_y:X})")
    print(f"  Divisor Z: {div_z} (0x{div_z:X})")
    
    if div_x == 256 and div_y == 256 and div_z == 256:
        print("  → Format: 8.8 fixed-point (8 bits integer, 8 bits fractional)")
        fmt_desc = "8.8 fixed-point"
    elif div_x == 4096:
        print("  → Format: 12.4 fixed-point (12 bits integer, 4 bits fractional)")
        fmt_desc = "12.4 fixed-point"
    elif div_x == 65536:
        print("  → Format: 16.16 fixed-point (16 bits integer, 16 bits fractional)")
        fmt_desc = "16.16 fixed-point"
    else:
        print(f"  → Format: Custom (divisor={div_x})")
        fmt_desc = f"custom (divisor={div_x})"
    
    # Update function comment with format
    func_cmt = idc.get_func_cmt(0x22C91, 1)
    if func_cmt and "Fixed-point format:" not in func_cmt:
        updated_cmt = func_cmt + f"\n\nFixed-point format: {fmt_desc}"
        idc.set_func_cmt(0x22C91, updated_cmt, 1)
        print(f"  ✓ Updated function comment with format")
        changes += 1
    
    # ========================================================================
    # Summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"SYNC COMPLETE: {changes} changes made")
    print(f"{'='*80}")
    
    print(f"\nSummary:")
    print(f"  - Vector state variables: 3 named")
    print(f"  - Matrix elements: 3 named")
    print(f"  - Fixed-point divisors: 3 named")
    print(f"  - Function comments: 8 added/updated")
    print(f"  - Display pointers: 11 named")
    print(f"  - Format detected: {fmt_desc}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
