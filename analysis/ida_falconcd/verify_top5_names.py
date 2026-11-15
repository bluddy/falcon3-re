"""
Verify that Ranks #1-5 are correctly named in IDA database
"""
import idaapi
import idc
import idautils

def main():
    expected_names = [
        (0x1744B0, "game_mode_r48_main_coordinator"),
        (0x1820B0, "game_mode_r53_main_coordinator"),
        (0x1793C0, "overlay_r4F_handler"),
        (0x18F610, "overlay_r55_dispatcher"),
        (0x166F80, "r38_loadout_menu_dispatcher"),
    ]
    
    print("Verifying Top 5 function names in IDA...")
    print("=" * 70)
    
    all_correct = True
    for addr, expected_name in expected_names:
        current_name = idc.get_func_name(addr)
        status = "✓" if current_name == expected_name else "✗"
        print(f"{status} 0x{addr:06X}: {current_name}")
        if current_name != expected_name:
            print(f"    EXPECTED: {expected_name}")
            all_correct = False
    
    print("=" * 70)
    if all_correct:
        print("SUCCESS: All Ranks #1-5 are correctly named")
    else:
        print("WARNING: Some functions need renaming")
    
    return 0 if all_correct else 1

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
