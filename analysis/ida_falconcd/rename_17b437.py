"""
Rename Rank #10: overlay_r4B_logic → squadron_mission_file_loader
Based on actual disassembly showing .SQUAD, .MTV, .SHP, .TSK file loading
"""
import idaapi
import idc

def main():
    idaapi.auto_wait()
    
    addr = 0x17B437
    old_name = "overlay_r4B_logic"
    new_name = "squadron_mission_file_loader"
    
    print(f"Renaming {old_name} at 0x{addr:06X} to {new_name}...")
    
    success = idc.set_name(addr, new_name, idc.SN_CHECK)
    
    if success:
        print(f"SUCCESS: Renamed to {new_name}")
        
        # Add accurate function comment based on actual code
        comment = """Squadron and mission file loader for overlay R4B.
Loads campaign files: .SQUAD (squadron), .MTV (mission?), .SHP (ship/shape?), .TSK (task?).
Initializes 64×20-byte data structures for squadron/mission data.
Calls op_dispatch_far_entry for file I/O operations.
Calls menu_field_offset_calculate to build UI strings.
13 callees (file ops, menu, overlay handlers).
4,516 bytes, 104 callers, overlay R4B.
Early exit paths based on graphics_mode_flag and byte_7A310 checks."""
        
        idc.set_func_cmt(addr, comment, 1)
        print("Added accurate function comment")
        return 0
    else:
        print(f"ERROR: Failed to rename function at 0x{addr:06X}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    idc.qexit(exit_code)
