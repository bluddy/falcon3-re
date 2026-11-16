"""Verify batch 2 utility renamings."""
import idc
import json

targets = [
    (0x134C3A, "mission_param_calculator_large"),
    (0x11C576, "ui_element_render_cc_13_alt"),
    (0x11CA9E, "ui_element_render_cc_13_var2"),
    (0x127FC4, "data_accessor_788d"),
    (0x135C07, "string_width_processor"),
    (0x11C504, "ui_element_render_cc_14_alt"),
    (0x13D77C, "string_format_builder"),
    (0x167F75, "ui_text_render_conditional"),
    (0x133CCF, "entity_data_processor_large"),
    (0x135DF4, "ui_button_handler"),
]

results = []
for ea, expected in targets:
    actual = idc.get_func_name(ea)
    match = (actual == expected)
    results.append({'address': ea, 'expected': expected, 'actual': actual, 'match': match})
    print(f"{'✓' if match else '✗'} 0x{ea:06X}: {actual}")
    if not match:
        print(f"  Expected: {expected}")

with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\batch2_verify.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{sum(1 for r in results if r['match'])}/{len(results)} verified")
idc.qexit(0)
