"""
Rename Rank #6: sub_103C99 → mission_session_init_coordinator
"""
import idaapi
import idc

def main():
    addr = 0x103C99
    old_name = "sub_103C99"
    new_name = "mission_session_init_coordinator"
    
    print(f"Renaming {old_name} at 0x{addr:06X} to {new_name}...")
    
    success = idc.set_name(addr, new_name, idc.SN_CHECK)
    
    if success:
        print(f"SUCCESS: Renamed to {new_name}")
        
        # Add function comment
        comment = """Mission/game session initialization coordinator.
Orchestrates transition from menu/campaign state into active gameplay.
Initializes: FarObj table (EMS), view system, dispatchers, resources, game logic.
144 callers from menu/campaign transitions.
Single caller: sub_2BDC5 (via tail-call jmp).
Validation gates at sub_104773 and sub_10470B; exits to 0x104464 on failure."""
        
        idc.set_func_cmt(addr, comment, 1)
        print("Added function comment")
        return 0
    else:
        print(f"ERROR: Failed to rename function at 0x{addr:06X}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
