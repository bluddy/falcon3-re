"""
Rename Rank #8: sub_12DF6A → r29_tactical_screen_coordinator
"""
import idaapi
import idc

def main():
    addr = 0x12DF6A
    old_name = "sub_12DF6A"
    new_name = "r29_tactical_screen_coordinator"
    
    print(f"Renaming {old_name} at 0x{addr:06X} to {new_name}...")
    
    success = idc.set_name(addr, new_name, idc.SN_CHECK)
    
    if success:
        print(f"SUCCESS: Renamed to {new_name}")
        
        # Add function comment
        comment = """R29 overlay tactical planning/mission editor screen coordinator.
Interactive menu with 11-item selectable grid, coordinate transformation, mouse/input tracking.
Manages: UI state, coordinate mapping (320x200 VGA), input polling, rendering updates.
Data structures: 0x82-byte records (aircraft/tactical objects) with 0xC-byte sub-elements.
Jump table dispatcher (4 cases) at cs:[1E99h+8].
120 callers, 6,799 bytes - HYBRID pattern (large specialized handler).
Segments: 0x7894 (game state), 0x4FC2 (graphics buffer)."""
        
        idc.set_func_cmt(addr, comment, 1)
        print("Added function comment")
        return 0
    else:
        print(f"ERROR: Failed to rename function at 0x{addr:06X}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
