"""
Rename and document the top 8 uncategorized functions based on analysis.
"""

import idc
import idaapi

def set_function_name_and_comment(ea, name, comment):
    """Set function name and add comment."""
    success = idc.set_name(ea, name, idc.SN_NOWARN | idc.SN_NOCHECK)
    if success:
        idc.set_func_cmt(ea, comment, 0)
        print(f"✓ 0x{ea:06X}: {name}")
    else:
        print(f"✗ 0x{ea:06X}: Failed to rename to {name}")
    return success

def main():
    print("Renaming top uncategorized functions...")
    
    renamings = [
        # Rank #5: 32-bit signed multiply
        (0x13DD40, "signed_mul_32bit", 
         "32-bit signed multiplication helper. Takes AX:DX * CX, handles sign, returns result in DX:AX."),
        
        # Rank #7: Mouse input sync
        (0x12805C, "mouse_input_sync_wait",
         "Mouse input synchronization. Calls mouse_gate_far_entry, sets FFFF flag, syncs with far callbacks."),
        
        # Rank #8: 32-bit signed divide
        (0x13DD83, "signed_div_32bit",
         "32-bit signed division helper. Divides AX:DX by CX, handles sign, returns quotient in AX, remainder in DX."),
        
        # Rank #9: Overlay bridge
        (0x02C59F, "overlay_bridge_to_66e97",
         "Overlay bridge trampoline. Loads overlay and jumps to 66E97h."),
        
        # Rank #10: Overlay bridge
        (0x02C4FF, "overlay_bridge_to_r30_state_init",
         "Overlay bridge to r30_state_init_all. Loads overlay and jumps to state initialization."),
        
        # Rank #19: Table dispatcher
        (0x13DE3A, "table_dispatch_interpreter",
         "Table-driven dispatcher/interpreter. Reads table from segment 642Fh, loops through entries, dispatches to handlers via dispatch_220a8_stub."),
        
        # Rank #26: Self-modifying code
        (0x088384, "dynamic_farcall_patcher",
         "Patches dynamic far call instruction. Writes opcode 9Ah (far call) and target address to memory location [BX-5]. Used for overlay/callback patching."),
        
        # Rank #30: Overlay bridge
        (0x02C351, "overlay_bridge_to_66a05",
         "Overlay bridge trampoline. Loads overlay and jumps to 66A05h."),
    ]
    
    success_count = 0
    for ea, name, comment in renamings:
        if set_function_name_and_comment(ea, name, comment):
            success_count += 1
    
    print(f"\n✓ Successfully renamed {success_count}/{len(renamings)} functions")
    
    # Save database
    print("\nSaving IDA database...")
    idc.save_database(idc.get_idb_path(), idc.DBFL_TEMP)
    print("✓ Database saved")

if __name__ == '__main__':
    main()
