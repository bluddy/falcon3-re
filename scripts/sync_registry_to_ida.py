import idaapi
import idc

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\registry_sync.txt"

# Functions to rename with corrected addresses
functions = [
    (0x40784, "ai_state_value_dispatcher"),
    (0x40708, "ai_entity_distance_with_physics"),
    (0x428A1, "ai_state_value_get"),
    (0x428D4, "ai_field_pair_compare_debug"),
    (0x40C73, "ai_heading_delta_monitor"),
    (0x40BF8, "ai_formation_position_gate"),
    (0x40CC5, "ai_range_threshold_evaluator"),
]

# Globals to rename
globals_list = [
    (0x15B3, "global_ground_attack_mode", "DS"),
    (0x3D41A, "behavior_state_code", "CS"),
    (0x3D41B, "behavior_sub_param", "CS"),
    (0x3E346, "range_threshold_1", "CS"),
    (0x3E348, "range_threshold_2", "CS"),
    (0x3E34A, "behavior_angle_param", "CS"),
    (0x3E34C, "behavior_timer", "CS"),
    (0x40C68, "heading_delta_timer", "CS"),
]

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== Syncing Registry to IDA ===\n\n")
        
        # Rename functions
        f.write("=== Functions ===\n\n")
        for addr, new_name in functions:
            func = idaapi.get_func(addr)
            if func:
                old_name = idc.get_func_name(addr)
                f.write(f"{addr:#x}: {old_name} -> {new_name}\n")
                
                result = idc.set_name(addr, new_name, idc.SN_CHECK)
                if result:
                    f.write(f"  ✓ Renamed\n")
                else:
                    f.write(f"  ✗ Failed (name may already exist)\n")
            else:
                f.write(f"{addr:#x}: No function found\n")
        
        f.write("\n=== Globals ===\n\n")
        for addr, new_name, segment in globals_list:
            # For CS segment, address is already absolute
            # For DS segment, would need to add segment base
            if segment == "CS":
                actual_addr = addr
            else:
                # DS globals - just use address as-is for now
                actual_addr = addr
            
            old_name = idc.get_name(actual_addr)
            f.write(f"{segment}:{addr:#x}: {old_name} -> {new_name}\n")
            
            result = idc.set_name(actual_addr, new_name, idc.SN_CHECK)
            if result:
                f.write(f"  ✓ Renamed\n")
            else:
                f.write(f"  ✗ Failed or already exists\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
