import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\rename_rfm_globals.txt"

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== Renaming RFM Globals ===\n\n")
        
        # Rename cs:word_3B832 to rfm_turn_rate_scalar
        addr = 0x3B832
        old_name = idc.get_name(addr)
        new_name = "rfm_turn_rate_scalar"
        
        f.write(f"Address 0x{addr:X}:\n")
        f.write(f"  Old name: {old_name}\n")
        
        result = idc.set_name(addr, new_name, idc.SN_CHECK)
        if result:
            f.write(f"  New name: {new_name} ✓\n")
        else:
            f.write(f"  Failed to rename (might already exist)\n")
        
        # Verify
        current_name = idc.get_name(addr)
        f.write(f"  Verified: {current_name}\n\n")
        
        # Also rename the three new functions we discovered
        renames = [
            (0x3CE92, "ai_heading_adjustment_gate"),
            (0x3CEDD, "ai_entity_data_copy_18byte"),
            (0x3CEF4, "ai_grid_position_update"),
        ]
        
        f.write("=== Renaming Functions ===\n\n")
        
        for addr, new_name in renames:
            old_name = idc.get_func_name(addr)
            f.write(f"Address 0x{addr:X}:\n")
            f.write(f"  Old name: {old_name}\n")
            
            result = idc.set_name(addr, new_name, idc.SN_CHECK)
            if result:
                f.write(f"  New name: {new_name} ✓\n")
            else:
                f.write(f"  Failed to rename\n")
            
            current_name = idc.get_func_name(addr)
            f.write(f"  Verified: {current_name}\n\n")
        
        # Check if there are other related RFM globals we should verify
        f.write("=== Verifying Other RFM Globals ===\n\n")
        
        rfm_globals = [
            (0x2F677, "rfm_data_pointer"),
            (0x3B830, "rfm_ai_behavior_ptr"),
            (0x3B834, "rfm_related_word_3"),
            (0x2F679, "rfm_related_word_1"),
        ]
        
        for addr, expected_name in rfm_globals:
            current_name = idc.get_name(addr)
            f.write(f"0x{addr:X}: {current_name}")
            if current_name != expected_name:
                f.write(f" (expected: {expected_name})")
                # Try to rename
                result = idc.set_name(addr, expected_name, idc.SN_CHECK)
                if result:
                    f.write(f" → renamed ✓")
            f.write("\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
