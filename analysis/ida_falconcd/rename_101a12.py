"""
Rename Rank #9: sub_101A12 → r03_screen_coordinator
"""
import idaapi
import idc

def main():
    addr = 0x101A12
    old_name = "sub_101A12"
    new_name = "r03_screen_coordinator"
    
    print(f"Renaming {old_name} at 0x{addr:06X} to {new_name}...")
    
    success = idc.set_name(addr, new_name, idc.SN_CHECK)
    
    if success:
        print(f"SUCCESS: Renamed to {new_name}")
        
        # Add function comment
        comment = """R03 overlay screen coordinator - typical Phase 2 specialized handler.
Medium-sized coordinator (1,719 bytes) with 104 callers.
Pattern: Sequential orchestration with single-subsystem focus.
Expected: ~50-70 callees across UI/state/input/rendering subsystems.
Fits between Rank #6 (945B small coordinator) and Rank #8 (6,799B large hybrid).
Overlay: R03_1CF6s (0x101010-0x102200)."""
        
        idc.set_func_cmt(addr, comment, 1)
        print("Added function comment")
        return 0
    else:
        print(f"ERROR: Failed to rename function at 0x{addr:06X}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
