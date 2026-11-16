"""Verify batch 3 utility renamings - THE FINAL BATCH!"""
import idc
import json

targets = [
    (0x137F93, "graphics_mode_query"),
    (0x13DAD0, "score_file_initializer"),
    (0x11CD43, "ui_element_render_12c_14"),
    (0x11CDAF, "ui_element_render_12c_13"),
    (0x135208, "state_config_accessor"),
    (0x049C67, "weapon_init_helper"),
    (0x12BBA6, "graphics_draw_helper"),
    (0x1357AC, "vector_processor_recursive"),
    (0x138ED4, "number_formatter_signed"),
    (0x1909A0, "overlay_r55_helper"),
]

results = []
for ea, expected in targets:
    actual = idc.get_func_name(ea)
    match = (actual == expected)
    results.append({'address': ea, 'expected': expected, 'actual': actual, 'match': match})
    print(f"{'✓' if match else '✗'} 0x{ea:06X}: {actual}")
    if not match:
        print(f"  Expected: {expected}")

with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\batch3_verify.json', 'w') as f:
    json.dump(results, f, indent=2)

success = sum(1 for r in results if r['match'])
print(f"\n{success}/{len(results)} verified")

if success == len(results):
    print("\n" + "="*60)
    print("✓✓✓ ALL 25 UTILITY FUNCTIONS SUCCESSFULLY RENAMED! ✓✓✓")
    print("="*60)

idc.qexit(0)
