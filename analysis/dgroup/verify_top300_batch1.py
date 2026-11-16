"""Verify Top 300 batch 1 renamings."""
import idc
import json

targets = [
    (0x02C527, "overlay_bridge_to_66a3d"),
    (0x11CD7F, "ui_element_render_variant_a"),
    (0x11CDEB, "ui_element_render_variant_b"),
    (0x127EFF, "graphics_clip_processor"),
    (0x129591, "ui_text_render_wrapper"),
    (0x1941E8, "overlay_r54_ui_coordinator"),
    (0x195F81, "overlay_r58_ui_coordinator"),
    (0x1A2B37, "overlay_r57_simple_helper"),
    (0x11CC39, "ui_element_render_complex_a"),
    (0x11D074, "ui_element_render_with_draw"),
    (0x11D172, "ui_element_render_triple_dispatch"),
    (0x13153A, "menu_simple_helper"),
    (0x135FCD, "ui_string_formatter_interactive"),
    (0x139D85, "font_data_processor"),
    (0x13AD67, "menu_queue_processor"),
]

results = []
for ea, expected in targets:
    actual = idc.get_func_name(ea)
    match = (actual == expected)
    results.append({'address': ea, 'expected': expected, 'actual': actual, 'match': match})
    print(f"{'✓' if match else '✗'} 0x{ea:06X}: {actual}")
    if not match:
        print(f"  Expected: {expected}")

with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\top300_batch1_verify.json', 'w') as f:
    json.dump(results, f, indent=2)

success = sum(1 for r in results if r['match'])
print(f"\n{success}/{len(results)} verified")
idc.qexit(0)
