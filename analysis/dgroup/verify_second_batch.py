"""
Verify second batch of renamings.
"""

import idc
import json

def main():
    print("Checking renamed functions (second batch)...")
    
    targets = [
        (0x13DE82, "ui_text_width_calculate"),
        (0x131530, "get_system_time_bios"),
        (0x02C58B, "overlay_bridge_to_menu_frame"),
        (0x135C57, "text_line_parser"),
        (0x11C707, "ui_text_render_entry"),
        (0x11D274, "menu_input_handler"),
        (0x13504F, "campaign_value_calculator"),
        (0x02C595, "overlay_bridge_to_r30_table_copy"),
    ]
    
    results = []
    for ea, expected_name in targets:
        actual_name = idc.get_func_name(ea)
        status = "✓" if actual_name == expected_name else "✗"
        results.append({
            'address': ea,
            'expected': expected_name,
            'actual': actual_name,
            'match': (actual_name == expected_name)
        })
        print(f"{status} 0x{ea:06X}: {actual_name}")
        if actual_name != expected_name:
            print(f"  Expected: {expected_name}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\second_batch_verify.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    success_count = sum(1 for r in results if r['match'])
    print(f"\n✓ {success_count}/{len(results)} renamings confirmed")

if __name__ == '__main__':
    main()

idc.qexit(0)
