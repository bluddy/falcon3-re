import idaapi
import idc

def main():
    """Name the waypoint array base pointer in IDA database"""
    print("="*80)
    print("Naming Waypoint Array Base Pointer")
    print("="*80)
    
    # Calculate linear address for segment 0x4FC2, offset 0x168
    seg_addr = 0x4FC2 << 4  # Segment to linear: 0x4FC2 * 16 = 0x4FC20
    linear_addr = seg_addr + 0x168  # 0x4FC20 + 0x168 = 0x4FD88
    
    print(f"[*] Waypoint array base pointer:")
    print(f"    Segment:Offset = 0x4FC2:0x0168")
    print(f"    Linear address = 0x{linear_addr:05X}")
    
    # Try to name the location
    old_name = idc.get_name(linear_addr)
    if old_name:
        print(f"[*] Current name at 0x{linear_addr:05X}: {old_name}")
    else:
        print(f"[*] No name currently set at 0x{linear_addr:05X}")
    
    # Set the name
    new_name = "waypoint_array_base"
    success = idc.set_name(linear_addr, new_name, idc.SN_CHECK)
    
    if success:
        print(f"[+] Successfully named 0x{linear_addr:05X} as '{new_name}'")
    else:
        print(f"[-] Failed to name 0x{linear_addr:05X} (may not exist in database)")
        print(f"[*] This is normal if address is in unallocated memory")
    
    # Add a comment to document the structure
    comment = "Waypoint coordinate array base pointer. Array of N × 21-byte Waypoint structures. Accessed as: segment 0x4FC2, offset [waypoint_index * 21 + 0x168]"
    idc.set_cmt(linear_addr, comment, 0)
    print(f"[+] Added comment to document the array")
    
    # List all references to segment 0x4FC2 in known functions
    print("\n" + "="*80)
    print("References to Waypoint Array (0x4FC2 segment)")
    print("="*80)
    
    functions = [
        ("mission_editor_main_loop", 0x18BC28),
        ("waypoint_flags_processor", 0x18DE3B),
        ("waypoint_display_helper", 0x1A163A)
    ]
    
    for func_name, func_addr in functions:
        print(f"\n[*] Checking {func_name} @ 0x{func_addr:X}:")
        
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            print(f"    [-] Function not found or not analyzed")
            continue
        
        found_refs = []
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: mov ax, 4FC2h
            if "4FC2h" in disasm or "4fc2h" in disasm.lower():
                # Check next few instructions for offset 168h
                next_head = head
                for i in range(5):
                    next_head = idc.next_head(next_head)
                    if next_head == idc.BADADDR:
                        break
                    next_disasm = idc.generate_disasm_line(next_head, 0)
                    
                    if "168h" in next_disasm or "0x168" in next_disasm:
                        found_refs.append({
                            "addr": head,
                            "offset": head - func_addr,
                            "disasm": disasm,
                            "access": next_disasm
                        })
                        break
        
        if found_refs:
            print(f"    [+] Found {len(found_refs)} waypoint array accesses:")
            for ref in found_refs:
                print(f"        0x{ref['addr']:X} (+0x{ref['offset']:X}): {ref['disasm']}")
                print(f"            → {ref['access']}")
        else:
            print(f"    [-] No waypoint array accesses found")
    
    print("\n" + "="*80)
    print("[+] Waypoint array pointer naming complete!")
    print("="*80)

if __name__ == "__main__":
    import idautils
    main()
