"""
Apply all Top 300 function names (ranks 201-300, 32 functions).
Follows IDA_AUTOMATION_GUIDE.md and IDA_NAMING_PROCESS.md guidelines.
"""

import idc
import idaapi
import json
from pathlib import Path

def main():
    print("="*70)
    print("APPLYING TOP 300 FUNCTION NAMES")
    print("="*70)
    
    # CRITICAL: Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # All 32 renamings for ranks 201-300
    renamings = {
        0x02C527: "overlay_bridge_to_66a3d",
        0x11CD7F: "ui_element_render_variant_a",
        0x11CDEB: "ui_element_render_variant_b",
        0x127EFF: "graphics_clip_processor",
        0x129591: "ui_text_render_wrapper",
        0x1941E8: "overlay_r54_ui_coordinator",
        0x195F81: "overlay_r58_ui_coordinator",
        0x1A2B37: "overlay_r57_simple_helper",
        0x11CC39: "ui_element_render_complex_a",
        0x11D074: "ui_element_render_with_draw",
        0x11D172: "ui_element_render_triple_dispatch",
        0x13153A: "menu_simple_helper",
        0x135FCD: "ui_string_formatter_interactive",
        0x139D85: "font_data_processor",
        0x13AD67: "menu_queue_processor",
        0x02C4B9: "overlay_bridge_to_66988",
        0x02C5D1: "overlay_bridge_to_66ea8",
        0x1016A8: "r01_segment_helper_a",
        0x106AD0: "r06_segment_helper_a",
        0x11CE1B: "ui_element_render_variant_c",
        0x11CE7B: "ui_element_render_variant_d",
        0x13462B: "data_structure_processor",
        0x13DDC3: "math_helper_20b",
        0x160096: "state_processor_large",
        0x04D75F: "weapon_helper_4d75f",
        0x10106C: "r01_processor_segment",
        0x1017D5: "r01_segment_helper_b",
        0x106457: "r06_processor_segment",
        0x11CBA8: "ui_element_render_complex_b",
        0x11CE4B: "ui_element_render_variant_e",
        0x185569: "overlay_r55_helper_large",
        0x1AAACC: "overlay_processor_large_1aaacc",
    }
    
    results = {
        'total': len(renamings),
        'renamed': 0,
        'already_correct': 0,
        'failed': [],
        'details': []
    }
    
    print(f"\nProcessing {len(renamings)} functions...")
    
    for ea, new_name in renamings.items():
        try:
            old_name = idc.get_func_name(ea)
            
            if old_name == new_name:
                print(f"✓ 0x{ea:06X}: Already named {new_name}")
                results['already_correct'] += 1
                results['details'].append({
                    'address': hex(ea),
                    'old_name': old_name,
                    'new_name': new_name,
                    'status': 'already_correct'
                })
            else:
                success = idc.set_name(ea, new_name, idc.SN_NOWARN | idc.SN_NOCHECK)
                if success:
                    print(f"✓ 0x{ea:06X}: {old_name} -> {new_name}")
                    results['renamed'] += 1
                    results['details'].append({
                        'address': hex(ea),
                        'old_name': old_name,
                        'new_name': new_name,
                        'status': 'renamed'
                    })
                else:
                    print(f"✗ 0x{ea:06X}: Failed to rename {old_name} to {new_name}")
                    results['failed'].append({
                        'address': hex(ea),
                        'old_name': old_name,
                        'new_name': new_name,
                        'error': 'set_name returned False'
                    })
        except Exception as e:
            print(f"✗ 0x{ea:06X}: Exception: {e}")
            results['failed'].append({
                'address': hex(ea),
                'new_name': new_name,
                'error': str(e)
            })
    
    # Save results
    output_path = Path(r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_naming_report_top300.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY:")
    print(f"  Total:            {results['total']}")
    print(f"  Renamed:          {results['renamed']}")
    print(f"  Already correct:  {results['already_correct']}")
    print(f"  Failed:           {len(results['failed'])}")
    print(f"\n✓ Results saved to: {output_path}")
    print(f"{'='*70}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)
