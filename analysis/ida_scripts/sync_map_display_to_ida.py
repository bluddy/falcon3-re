import idaapi
import idc
import idautils

def name_map_display_pointers():
    """
    Name data pointers discovered during map display analysis.
    """
    pointers = [
        (0x7A2F6, "waypoint_display_array_seg", "Waypoint array segment for display"),
        (0x7A2F4, "waypoint_display_array_off", "Waypoint array offset for display"),
        (0x7A2EA, "display_data_seg", "Display data segment"),
        (0x7A2E8, "display_data_off", "Display data offset"),
        (0x7A2F2, "display_buffer_handle", "Display buffer or file handle")
    ]
    
    print("[*] Naming map display data pointers...")
    
    for addr, name, comment in pointers:
        old_name = idc.get_name(addr)
        if old_name and not old_name.startswith("word_") and not old_name.startswith("dword_"):
            print(f"[!] {hex(addr)} already named as '{old_name}', skipping")
            continue
        
        success = idc.set_name(addr, name, idc.SN_CHECK)
        if success:
            print(f"[+] Named {hex(addr)} as '{name}'")
            idc.set_cmt(addr, comment, 0)
        else:
            print(f"[-] Failed to name {hex(addr)}")
    
    return len(pointers)

def add_structure_comments():
    """
    Add comments for structure sizes and access patterns in display functions.
    """
    print("\n[*] Adding structure size comments...")
    
    # Functions to annotate
    functions = [
        ("waypoint_coordinate_processor", 0x1A2441),
        ("waypoint_display_processor", 0x1A0F10),
        ("waypoint_display_helper", 0x1A163A),
        ("tactical_screen_coordinator", 0x12DB6A)
    ]
    
    comment_count = 0
    
    for func_name, func_addr in functions:
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            print(f"[-] Function {func_name} not found")
            continue
        
        print(f"[*] Processing {func_name}...")
        
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Add comment for 0x15 (waypoint size)
            if "15h" in disasm and "mov" in disasm.lower() and "dx" in disasm.lower():
                existing = idc.get_cmt(head, 0)
                if not existing or "Waypoint size" not in existing:
                    idc.set_cmt(head, "Waypoint size (21 bytes)", 0)
                    comment_count += 1
            
            # Add comment for 0x12 (18-byte structure)
            if "12h" in disasm and "mov" in disasm.lower() and "dx" in disasm.lower():
                existing = idc.get_cmt(head, 0)
                if not existing or "18-byte" not in existing:
                    idc.set_cmt(head, "18-byte display input structure", 0)
                    comment_count += 1
            
            # Add comment for 0x06 (6-byte output record)
            if ", 6" in disasm and "mov" in disasm.lower() and "dx" in disasm.lower():
                existing = idc.get_cmt(head, 0)
                if not existing or "6-byte" not in existing:
                    idc.set_cmt(head, "6-byte display output record", 0)
                    comment_count += 1
    
    print(f"[+] Added {comment_count} structure comments")
    return comment_count

def verify_function_names():
    """
    Verify that map display functions are properly named.
    """
    print("\n[*] Verifying function names...")
    
    functions = [
        (0x1A2441, "waypoint_coordinate_processor"),
        (0x1A0F10, "waypoint_display_processor"),
        (0x1A163A, "waypoint_display_helper"),
        (0x12DB6A, "tactical_screen_coordinator")
    ]
    
    verified = 0
    
    for addr, expected_name in functions:
        current_name = idc.get_func_name(addr)
        if current_name == expected_name:
            print(f"[+] {hex(addr)}: '{expected_name}' ✓")
            verified += 1
        else:
            print(f"[!] {hex(addr)}: '{current_name}' != '{expected_name}'")
            # Try to rename
            success = idc.set_name(addr, expected_name, idc.SN_CHECK)
            if success:
                print(f"    [+] Renamed to '{expected_name}'")
                verified += 1
    
    return verified

def add_waypoint_array_pointer_comment():
    """
    Add detailed comment about the display waypoint array pointer.
    """
    print("\n[*] Adding waypoint array pointer documentation...")
    
    # Document word_7A2F6 (segment)
    addr_seg = 0x7A2F6
    comment_seg = """Waypoint array segment for display code.
Forms far pointer with waypoint_display_array_off.
Compare to mission editor's 0x4FC2:0x168.
May point to same array or display buffer."""
    idc.set_cmt(addr_seg, comment_seg, 1)  # Repeatable comment
    
    # Document word_7A2F4 (offset)
    addr_off = 0x7A2F4
    comment_off = """Waypoint array offset for display code.
Combined with waypoint_display_array_seg to access waypoints.
Used in waypoint_coordinate_processor."""
    idc.set_cmt(addr_off, comment_off, 1)
    
    print("[+] Added detailed waypoint array documentation")

def document_dispatcher_calls():
    """
    Add comments to dispatcher calls with their codes.
    """
    print("\n[*] Documenting dispatcher calls...")
    
    func_addr = 0x1A2441  # waypoint_coordinate_processor
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    
    if func_end == idc.BADADDR:
        return 0
    
    comment_count = 0
    
    for head in idautils.Heads(func_addr, func_end):
        disasm = idc.generate_disasm_line(head, 0)
        
        if "call" in disasm.lower() and "dispatch" in disasm.lower():
            # Look back for push with dispatch code
            check_head = head
            for i in range(5):
                check_head = idc.prev_head(check_head)
                if check_head == idc.BADADDR:
                    break
                
                check_disasm = idc.generate_disasm_line(check_head, 0)
                if "push" in check_disasm.lower():
                    if "6" in check_disasm:
                        idc.set_cmt(head, "Dispatcher code 6 - graphics/UI operation", 0)
                        comment_count += 1
                        break
                    elif "0Ah" in check_disasm or ", 10" in check_disasm:
                        idc.set_cmt(head, "Dispatcher code 0xA (10) - graphics/UI operation", 0)
                        comment_count += 1
                        break
    
    print(f"[+] Added {comment_count} dispatcher call comments")
    return comment_count

def main():
    print("="*80)
    print("Map Display - Sync to IDA Database")
    print("="*80)
    
    total_changes = 0
    
    # Verify function names
    verified = verify_function_names()
    print(f"\n[*] Verified: {verified}/4 functions")
    total_changes += verified
    
    # Name data pointers
    named = name_map_display_pointers()
    total_changes += named
    
    # Add structure comments
    comments = add_structure_comments()
    total_changes += comments
    
    # Add waypoint pointer documentation
    add_waypoint_array_pointer_comment()
    total_changes += 2
    
    # Document dispatcher calls
    dispatcher_comments = document_dispatcher_calls()
    total_changes += dispatcher_comments
    
    print("\n" + "="*80)
    print(f"[+] Sync complete! Total changes: {total_changes}")
    print("="*80)
    print("\n[*] Summary:")
    print(f"    Functions verified: {verified}")
    print(f"    Pointers named: {named}")
    print(f"    Structure comments: {comments}")
    print(f"    Dispatcher comments: {dispatcher_comments}")
    print(f"    Waypoint pointer docs: 2")
    print("\n[+] IDA database updated!")

if __name__ == "__main__":
    main()
