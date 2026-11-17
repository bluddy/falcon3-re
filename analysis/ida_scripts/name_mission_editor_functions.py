"""
Name mission editor functions and structures in IDA
Based on our reverse engineering findings
"""

import idaapi
import idc
import idautils

def name_functions():
    """Apply proper names to identified functions"""
    
    print("Naming mission editor functions...")
    print("=" * 80)
    
    # Function names to apply
    functions_to_name = {
        # R55 Mission Editor
        0x18BC28: "mission_editor_main_loop",
        0x18DE3B: "waypoint_flags_processor",
        
        # R63 Waypoint Display
        0x1A0F10: "waypoint_display_processor",
        0x1A163A: "waypoint_display_helper",
        0x1A2441: "waypoint_coordinate_processor",  # 8 accesses!
        
        # R29 Flight/Tactical
        0x12DB6A: "tactical_screen_coordinator",
        0x1231FB: "flight_record_handler",  # 45 accesses!
        0x68541: "loadout_menu_enter",
        
        # Already named, but verify
        0x17B437: "squadron_mission_file_loader",
        0x1820B0: "mission_briefing_coordinator",
    }
    
    renamed_count = 0
    
    for addr, new_name in functions_to_name.items():
        old_name = idc.get_func_name(addr)
        
        if old_name and old_name != new_name:
            if idc.set_name(addr, new_name, idc.SN_CHECK):
                print(f"✓ Renamed 0x{addr:06X}: {old_name} → {new_name}")
                renamed_count += 1
            else:
                print(f"✗ Failed to rename 0x{addr:06X}: {old_name} → {new_name}")
        elif not old_name:
            if idc.set_name(addr, new_name, idc.SN_CHECK):
                print(f"✓ Named 0x{addr:06X}: → {new_name}")
                renamed_count += 1
        else:
            print(f"  Already named: {new_name}")
    
    print(f"\nRenamed {renamed_count} functions")
    return renamed_count

def add_structure_comments():
    """Add comments to structure size constants"""
    
    print("\n" + "=" * 80)
    print("Adding structure size comments...")
    print("=" * 80)
    
    # Known structure sizes
    structures = {
        0x14: "MissionSlot size (20 bytes)",
        0x15: "Waypoint size (21 bytes)",
        0x17: "LoadoutRecord size (23 bytes)",
        0x42: "PilotRecord size (66 bytes)",
        0x82: "FlightRecord size (130 bytes)",
        0x1C: "MenuElement size (28 bytes)",
    }
    
    comment_count = 0
    
    # Search for immediate values in mov instructions
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == 'mov':
                op0 = idc.print_operand(ea, 0)
                
                if op0 == 'dx' and idc.get_operand_type(ea, 1) == idc.o_imm:
                    imm_value = idc.get_operand_value(ea, 1)
                    
                    if imm_value in structures:
                        comment = structures[imm_value]
                        
                        # Check if next instruction is imul
                        next_ea = idc.next_head(ea, func.end_ea)
                        if next_ea < func.end_ea and idc.print_insn_mnem(next_ea) == 'imul':
                            # Add comment to mov instruction
                            if idc.set_cmt(ea, comment, 0):
                                comment_count += 1
            
            ea = idc.next_head(ea, func.end_ea)
    
    print(f"Added {comment_count} structure size comments")
    return comment_count

def name_data_pointers():
    """Add names/comments to mission data pointers"""
    
    print("\n" + "=" * 80)
    print("Naming mission data pointers...")
    print("=" * 80)
    
    # Known pointers in segment 0x7894
    pointers = {
        0x79D3E: ("mission_slot_array_ptr", "Pointer to 64×20 byte MissionSlot array"),
        0x79E3A: ("mission_context_ptr", "Pointer to mission context (60B + 30 pilots)"),
        0x79BEC: ("flight_array_ptr", "Pointer to flight array (N × 130 bytes)"),
        0x79EDE: ("mission_data_ptr", "Pointer to additional mission data"),
        0x79B62: ("current_flight_index", "Current flight index (word)"),
        0x79E32: ("mission_word_E32", "Mission-related word"),
        0x79D1E: ("mission_word_D1E", "Mission-related word"),
    }
    
    named_count = 0
    
    for addr, (name, comment) in pointers.items():
        # Try to set name
        old_name = idc.get_name(addr)
        if old_name != name:
            if idc.set_name(addr, name, idc.SN_CHECK):
                print(f"✓ Named 0x{addr:06X}: {old_name} → {name}")
                named_count += 1
            else:
                print(f"  Already exists or failed: {name}")
        
        # Add comment
        if idc.set_cmt(addr, comment, 1):  # Repeatable comment
            print(f"  Added comment: {comment}")
    
    print(f"\nNamed {named_count} data pointers")
    return named_count

def main():
    print("Starting IDA database update...")
    idaapi.auto_wait()
    
    # Apply names
    func_count = name_functions()
    comment_count = add_structure_comments()
    ptr_count = name_data_pointers()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Functions named: {func_count}")
    print(f"Structure comments added: {comment_count}")
    print(f"Data pointers named: {ptr_count}")
    print(f"Total updates: {func_count + comment_count + ptr_count}")
    
    print("\nIDA database updated successfully!")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
