"""
Comprehensive renaming of the entire view system in IDA.

Based on complete understanding:
- r15_external_view_flag -> might be acmi_playback_mode or view_pipeline_mode
- word_79F16 -> current_view_index
- All handlers, dispatchers, and tables

Plus add comprehensive comments throughout.
"""

import idc
import idaapi
import idautils

def rename_and_comment(addr, new_name, comment):
    """Rename an address and add a comment."""
    old_name = idc.get_name(addr)
    
    # Rename
    if idc.set_name(addr, new_name, idc.SN_NOWARN | idc.SN_NOCHECK):
        print(f"  ✓ Renamed 0x{addr:X}: {old_name} -> {new_name}")
    else:
        print(f"  ✗ Failed to rename 0x{addr:X} to {new_name}")
    
    # Add comment
    idc.set_cmt(addr, comment, 0)  # Regular comment
    return True

def add_comment_only(addr, comment, repeatable=False):
    """Add a comment without renaming."""
    idc.set_cmt(addr, comment, 1 if repeatable else 0)
    print(f"  ✓ Comment at 0x{addr:X}: {comment[:60]}...")

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("RENAMING VIEW SYSTEM - COMPLETE")
    print("="*80)
    
    # ========================================================================
    # PART 1: Core Variables
    # ========================================================================
    print("\n[1/7] CORE VARIABLES")
    print("-"*80)
    
    # View index variable (the key discovery!)
    rename_and_comment(
        0x79F16,
        "current_view_index",
        "Current view/camera index (0-9). Set by view key handlers, used by rendering dispatcher. Values: 0=?, 1-4=cockpit views (front/left/rear/right), 5-9=external views"
    )
    
    # Mode flag - might be ACMI vs sim!
    rename_and_comment(
        0x107762,
        "view_pipeline_mode",
        "View rendering pipeline selector. 0=Path A, 1=Path B. Set once at mission init by view_mode_set. Might control ACMI playback vs live simulation mode rather than cockpit vs external."
    )
    
    # Input queue
    rename_and_comment(
        0x79B66,
        "input_scan_code_queue",
        "Keyboard input queue. Stores scan code from last key press. Written by input_poll_handler, read by game mode coordinators to dispatch input."
    )
    
    # ========================================================================
    # PART 2: Input Capture
    # ========================================================================
    print("\n[2/7] INPUT CAPTURE")
    print("-"*80)
    
    # Number key capture loop
    add_comment_only(0x130709, "NUMBER KEY CAPTURE LOOP START: Scan keyboard for keys 1-9,0 (scan codes 0x02-0x0B)", repeatable=True)
    add_comment_only(0x130749, "Store captured scan code in input queue for later processing by dispatcher", repeatable=True)
    
    # ========================================================================
    # PART 3: Input Dispatchers
    # ========================================================================
    print("\n[3/7] INPUT DISPATCHERS")
    print("-"*80)
    
    # Dispatcher 1
    add_comment_only(
        0x12DFD6,
        "INPUT DISPATCHER: Read input_scan_code_queue, search table at cs:0x1E99 for matching scan code, dispatch to handler via jmp [bx+8]",
        repeatable=True
    )
    add_comment_only(0x12DFE0, "Load dispatch table address (4 entries)", repeatable=False)
    add_comment_only(0x12DFE3, "Loop: search table for matching scan code", repeatable=False)
    add_comment_only(0x12DFF1, "JUMP TABLE DISPATCH: jmp to handler at [bx+8]", repeatable=True)
    
    # Dispatcher 2  
    add_comment_only(
        0x182476,
        "INPUT DISPATCHER (R53): Read input_scan_code_queue, search table at cs:0x3225 for scan codes 0x01,0x03,0x04,0xFF. Dispatch to view handler.",
        repeatable=True
    )
    add_comment_only(0x182480, "Load dispatch table address (4 entries: 0x01,0x03,0x04,0xFF)", repeatable=False)
    add_comment_only(0x182491, "JUMP TABLE DISPATCH: jmp to handler at [bx+8]", repeatable=True)
    
    # ========================================================================
    # PART 4: View Key Handlers
    # ========================================================================
    print("\n[4/7] VIEW KEY HANDLERS")
    print("-"*80)
    
    # Handler examples from dispatcher 2
    add_comment_only(0x18249A, "VIEW KEY HANDLER: Set current_view_index = 7 (likely ground or external view)", repeatable=True)
    add_comment_only(0x1824A3, "VIEW KEY HANDLER: Push view index 8, call view setup (likely padlock view)", repeatable=True)
    
    # ========================================================================
    # PART 5: Rendering Dispatcher (The BIG Discovery!)
    # ========================================================================
    print("\n[5/7] RENDERING DISPATCHER")
    print("-"*80)
    
    # Main rendering dispatcher
    add_comment_only(
        0x156DC5,
        "VIEW RENDERING DISPATCHER: Read current_view_index (0-9), dispatch to appropriate view handler via 10-case jump table",
        repeatable=True
    )
    add_comment_only(0x156DCA, "Bounds check: current_view_index must be 0-9", repeatable=False)
    add_comment_only(0x156DD2, "Multiply by 2 for word offset into jump table", repeatable=False)
    add_comment_only(0x156DD4, "JUMP TABLE: 10 view handlers indexed by current_view_index", repeatable=True)
    
    # Jump table entries (with absolute addresses)
    jump_table_entries = [
        (0x156C29, "view_handler_0", "View handler case 0"),
        (0x156D0B, "view_handler_1_to_4_shared", "View handler cases 1-4 (shared - likely cockpit directions)"),
        (0x156D81, "view_handler_5", "View handler case 5"),
        (0x156E75, "view_handler_6", "View handler case 6"),
        (0x156FE0, "view_handler_7", "View handler case 7"),
        (0x1570EF, "view_handler_8", "View handler case 8"),
        (0x157118, "view_handler_9", "View handler case 9"),
    ]
    
    for addr, name, comment in jump_table_entries:
        if idc.is_mapped(addr):
            # Try to rename function
            func = idaapi.get_func(addr)
            if func and func.start_ea == addr:
                idc.set_name(addr, name, idc.SN_NOWARN)
                print(f"  ✓ Renamed function at 0x{addr:X} -> {name}")
            add_comment_only(addr, comment, repeatable=True)
        else:
            print(f"  ! Address 0x{addr:X} not mapped, skipping")
    
    # ========================================================================
    # PART 6: Mode/Path Selection
    # ========================================================================
    print("\n[6/7] MODE/PATH SELECTION")
    print("-"*80)
    
    # Simulation loop flag check
    add_comment_only(
        0x108BC5,
        "READ view_pipeline_mode to select rendering path. 0=Path A, 1=Path B. Might be: ACMI playback vs live sim, or internal vs external rendering pipeline.",
        repeatable=True
    )
    
    # View mode initialization
    rename_and_comment(
        0x1087B2,
        "view_pipeline_mode",  # This is an instruction, not function, so comment is key
        "SET view_pipeline_mode at mission initialization. This is the ONLY place the mode is written! Determines which rendering path for entire session."
    )
    
    # ========================================================================
    # PART 7: Function Names
    # ========================================================================
    print("\n[7/7] FUNCTION NAMES")
    print("-"*80)
    
    functions_to_rename = [
        (0x156945, "view_rendering_dispatcher", "Main view rendering dispatcher. Reads current_view_index, dispatches to 1 of 10 view handlers via jump table."),
        (0x12DB63, "tactical_screen_coordinator", "Tactical screen coordinator. Handles input dispatch and screen updates."),
        (0x182390, "game_mode_r53_coordinator", "Game mode R53 coordinator. Dispatches input including view keys (scan 0x03, 0x04)."),
    ]
    
    for addr, name, comment in functions_to_rename:
        func = idaapi.get_func(addr)
        if func:
            old_name = idc.get_func_name(addr)
            if idc.set_name(addr, name, idc.SN_NOWARN):
                print(f"  ✓ Renamed function 0x{addr:X}: {old_name} -> {name}")
                idc.set_func_cmt(addr, comment, 0)
            else:
                print(f"  ✗ Failed to rename function at 0x{addr:X}")
        else:
            print(f"  ! No function at 0x{addr:X}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("RENAMING COMPLETE")
    print("="*80)
    print("\nKey renamings:")
    print("  • word_79F16 -> current_view_index")
    print("  • r15_external_view_flag -> view_pipeline_mode")
    print("  • input_flag_pending_2 -> input_scan_code_queue")
    print("  • overlay_r45_logic -> view_rendering_dispatcher")
    print("  • Plus 10+ functions and 20+ comments added")
    print("\nNext: Review in IDA to verify all names make sense!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
