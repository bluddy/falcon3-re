"""
Rename Rank #9: r03_screen_coordinator → input_device_calibration_init
Based on ACTUAL disassembly analysis showing joystick detection and calibration
"""
import idaapi
import idc

def main():
    idaapi.auto_wait()
    
    addr = 0x101A12
    old_name = "r03_screen_coordinator"
    new_name = "input_device_calibration_init"
    
    print(f"Renaming {old_name} at 0x{addr:06X} to {new_name}...")
    
    success = idc.set_name(addr, new_name, idc.SN_CHECK)
    
    if success:
        print(f"SUCCESS: Renamed to {new_name}")
        
        # Add accurate function comment based on actual code
        comment = """Input device initialization and calibration coordinator.
Detects and initializes joystick, mouse, keyboard input devices.
Performs joystick calibration with retry logic and validation loops.
Saves/restores viewport extent shadow state during initialization.
26 callees: joystick detection (4), mouse (2), view extent (2), dispatchers (3).
Main flow: Check joystick presence → calibrate if present → save viewport → 
initialize input handlers → restore viewport → validation loops.
1,719 bytes, 104 callers, overlay R03_1CF6s."""
        
        idc.set_func_cmt(addr, comment, 1)
        print("Added accurate function comment")
        return 0
    else:
        print(f"ERROR: Failed to rename function at 0x{addr:06X}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
