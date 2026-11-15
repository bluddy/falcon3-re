"""
Extract menu system seed functions from registry for call-graph expansion.
Run in IDA: File > Script file > extract_menu_seeds2.py
"""

import idaapi
import idc
import json

def extract_menu_seeds():
    """Extract all menu system functions from the registry."""
    
    # Menu system addresses from registry
    menu_addrs = [
        0x0385ad,  # menu_list_script_step
        0x04aec4,  # farobj_3d_model_rotate_step
        0x066e62,  # ui_menu_panel_initialize
        0x067480,  # menu_index_step_dispatch
        0x0674a0,  # menu_event_dispatch
        0x067800,  # menu_page_change
        0x067d3b,  # menu_cursor_position_set
        0x067d65,  # menu_field_value_get
        0x067d9b,  # menu_field_value_set
        0x067dd1,  # menu_field_bounds_check
        0x067e0f,  # menu_field_next
        0x067e2d,  # menu_field_prev
        0x067e4b,  # menu_field_validate
        0x067e81,  # menu_field_highlight
        0x067ebf,  # menu_state_flags_update
        0x067ef5,  # menu_input_handler
        0x068125,  # menu_option_select
        0x068159,  # menu_option_deselect
        0x068189,  # menu_list_scroll_up
        0x0681b9,  # menu_list_scroll_down
        0x0681e9,  # menu_page_validate
        0x068219,  # menu_field_offset_calculate
        0x06825d,  # menu_loadout_data_engine
        0x0687e0,  # menu_field_draw
        0x068b1f,  # menu_input_keypress_handler
        0x068d5e,  # menu_cursor_move
        0x068f9d,  # menu_field_type_dispatch
        0x0691dc,  # menu_option_toggle
        0x06941b,  # menu_numeric_input_handler
        0x06965a,  # menu_text_input_handler
        0x069899,  # menu_selection_confirm
        0x069ad8,  # menu_selection_cancel
        0x069d17,  # menu_help_display
        0x069f56,  # menu_tooltip_show
        0x06a195,  # menu_animation_step
        0x06a3d4,  # menu_sound_play
        0x06a613,  # menu_background_draw
        0x06a852,  # menu_overlay_show
        0x06aa91,  # menu_overlay_hide
        0x06acd0,  # menu_transition_start
        0x06af0f,  # menu_transition_complete
        0x06b14e,  # menu_state_save
        0x06b38d,  # menu_state_restore
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
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\menu_seeds2.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Extracted {len(results)} menu seed functions")
    print(f"✓ Saved to: {output_file}")
    return results

if __name__ == '__main__':
    idaapi.auto_wait()
    extract_menu_seeds()
