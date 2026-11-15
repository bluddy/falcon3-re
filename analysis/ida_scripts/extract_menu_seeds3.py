"""
Extract menu system seed functions from registry for call-graph expansion (round 2).
Run in IDA: File > Script file > extract_menu_seeds3.py
"""

import idaapi
import idc
import json

def extract_menu_seeds():
    """Extract all 43 menu system functions from the registry."""
    
    # Menu system addresses from registry (confirmed via grep)
    menu_addrs = [
        0x0674a0,  # menu_event_dispatch
        0x06760a,  # ui_menu_frame_enter
        0x06798c,  # ui_loadout_slot_record_fill
        0x067ad3,  # menu_page_jump_stub
        0x067ae1,  # menu_pending_task_step
        0x067ba6,  # menu_choice_tail_dispatch
        0x067baf,  # ui_menu_transition_animate
        0x067f96,  # ui_record_field_clear_frag
        0x06a651,  # squad_campaign_file_loader
        0x163122,  # ui_loadout_hardpoint_manager
        0x133adc,  # ui_menu_panel_renderer
        0x13142e,  # font_file_parser
        0x1365a7,  # ui_slot_list_builder
        0x130bf0,  # ui_coordinate_transform
        0x1635ec,  # ui_loadout_pylon_config
        0x06e43b,  # menu_state_buffer_allocate (also file_buffer_allocator)
        0x163d33,  # menu_loadout_weapon_data_get
        0x163fdb,  # menu_loadout_weight_table_lookup
        0x163dbd,  # menu_loadout_hardpoint_data_get
        0x138f9c,  # menu_field_offset_calculate
        0x13d633,  # menu_record_field_copy
        0x138e1d,  # menu_loadout_config_validate
        0x163c88,  # menu_weapon_compatibility_check
        0x12c412,  # menu_event_key_mapper
        0x127ed2,  # menu_panel_background_draw
        0x130a2f,  # menu_cursor_position_set
        0x04aae2,  # menu_3d_model_frame_step
        0x137f70,  # menu_list_index_clamp
        0x16394a,  # menu_loadout_supply_decrement
        0x12fa41,  # menu_field_highlight_toggle
        0x066b41,  # menu_button_state_read
        0x066c65,  # menu_selection_index_get
        0x138630,  # menu_row_count_get
        0x1381ca,  # menu_page_flag_check
    ]
    
    results = []
    
    for addr in menu_addrs:
        name = idc.get_func_name(addr)
        if not name:
            print(f"Warning: No function at 0x{addr:x}")
            continue
            
        func = idaapi.get_func(addr)
        if not func:
            print(f"Warning: Not a function at 0x{addr:x} ({name})")
            continue
        
        size = func.end_ea - func.start_ea
        
        results.append({
            'address': f'0x{addr:x}',
            'name': name,
            'size': size
        })
        print(f"Added: 0x{addr:06x} {name:50s} ({size:4d}B)")
    
    # Write results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\menu_seeds3.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Extracted {len(results)} menu seed functions")
    print(f"✓ Saved to: {output_file}")
    return results

if __name__ == '__main__':
    idaapi.auto_wait()
    extract_menu_seeds()
