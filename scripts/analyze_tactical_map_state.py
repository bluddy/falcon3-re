"""
Analyze tactical map camera/view state by examining data accesses.
Focus on segment 0x4FC2 where map state is likely stored.
"""

import idc
import idaapi
import idautils

def analyze_segment_4fc2():
    """Analyze variables in segment 0x4FC2 (waypoint/map segment)."""
    
    print("="*80)
    print("TACTICAL MAP STATE ANALYSIS - Segment 0x4FC2")
    print("="*80)
    
    # Key addresses we found in tactical_screen_coordinator
    map_vars = {
        0x13E002: "unknown_map_var1",
        0x13E004: "unknown_map_var2", 
        0x13E006: "unknown_map_var3",
        0x13E008: "unknown_map_var4",
        0x13E00E: "unknown_map_var5",
        0x13E010: "unknown_map_var6",
    }
    
    # Waypoint array is at 0x13E168 (segment 0x4FC2, offset 0x168)
    # So these are BEFORE the waypoint array
    
    print("\nVariables BEFORE waypoint array (0x13E168):")
    print("-"*80)
    
    for addr in sorted(map_vars.keys()):
        offset_from_waypoints = 0x13E168 - addr
        
        # Try to read value
        value = idc.get_wide_word(addr)
        name = idc.get_name(addr) or map_vars.get(addr, "unnamed")
        
        # Check for cross-references
        xrefs_to = list(idautils.XrefsTo(addr, 0))
        xrefs_count = len(xrefs_to)
        
        print(f"\n0x{addr:08X}  {name:30s}  = {value:5d} (0x{value:04X})")
        print(f"  Offset from waypoint array: -{offset_from_waypoints} (0x{offset_from_waypoints:X})")
        print(f"  Cross-references: {xrefs_count}")
        
        # Show first few xrefs
        if xrefs_count > 0:
            print(f"  Referenced by:")
            for xref in list(xrefs_to)[:5]:
                func = idaapi.get_func(xref.frm)
                if func:
                    func_name = idc.get_name(func.start_ea) or f"sub_{func.start_ea:X}"
                    print(f"    {func_name} @ 0x{xref.frm:X}")
    
    # Check for zoom/scale variables (likely small positive integers 1-999)
    print(f"\n{'='*80}")
    print("SEARCHING FOR ZOOM/SCALE VARIABLES")
    print(f"{'='*80}")
    
    # Scan area before waypoint array for zoom-like values
    for addr in range(0x13E000, 0x13E168, 2):  # Every word
        value = idc.get_wide_word(addr)
        
        # Zoom is likely 1-999, camera coords might be larger
        if 1 <= value <= 999:
            name = idc.get_name(addr) or "(unnamed)"
            xrefs = len(list(idautils.XrefsTo(addr, 0)))
            
            if xrefs > 0:  # Only show if referenced
                print(f"0x{addr:08X}  {name:30s}  = {value:4d}  (xrefs: {xrefs})")
    
    # Check camera-like coordinates (could be large values)
    print(f"\n{'='*80}")
    print("POTENTIAL CAMERA COORDINATES (large values)")
    print(f"{'='*80}")
    
    for addr in range(0x13E000, 0x13E168, 2):
        value = idc.get_wide_word(addr)
        signed_value = value if value < 32768 else value - 65536
        
        # Camera coordinates might be in range -10000 to +10000
        if abs(signed_value) > 100 and abs(signed_value) < 10000:
            name = idc.get_name(addr) or "(unnamed)"
            xrefs = len(list(idautils.XrefsTo(addr, 0)))
            
            if xrefs > 0:
                print(f"0x{addr:08X}  {name:30s}  = {signed_value:6d}  (xrefs: {xrefs})")

def analyze_view_state():
    """Check HUD view state variables that might be shared."""
    
    print(f"\n{'='*80}")
    print("HUD/VIEW SYSTEM VARIABLES (might be shared with tactical map)")
    print(f"{'='*80}")
    
    view_vars = {
        0x810: "view_horizontal_angle (yaw)",
        0x814: "view_vertical_angle (pitch)",
        0x80E: "view_h_direction",
        0x812: "view_v_direction",
        0xC55: "view_mode_attribute",
    }
    
    for addr, name in view_vars.items():
        value = idc.get_wide_word(addr) if addr not in [0x80E, 0x812, 0xC55] else idc.get_wide_byte(addr)
        xrefs = len(list(idautils.XrefsTo(addr, 0)))
        print(f"0x{addr:08X}  {name:40s}  = {value:5d}  (xrefs: {xrefs})")

def main():
    print("Waiting for IDA analysis...")
    idaapi.auto_wait()
    
    analyze_segment_4fc2()
    analyze_view_state()
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print("\nNext steps:")
    print("1. Name variables based on usage patterns")
    print("2. Trace coordinate updates during map pan/zoom")  
    print("3. Identify which vars are camera position vs zoom")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
