"""
Verify batch 1 utility renamings.
"""

import idc
import json

targets = [
    (0x13BD06, "overlay_dispatcher_indexed"),
    (0x11C884, "ui_element_render_cc_14"),
    (0x11C90F, "ui_element_render_cc_13"),
    (0x11C642, "ui_element_render_102_14"),
    (0x12C2F7, "timing_frame_limiter"),
]

results = []
for ea, expected in targets:
    actual = idc.get_func_name(ea)
    match = (actual == expected)
    results.append({'address': ea, 'expected': expected, 'actual': actual, 'match': match})
    print(f"{'✓' if match else '✗'} 0x{ea:06X}: {actual}")
    if not match:
        print(f"  Expected: {expected}")

output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\batch1_verify.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{sum(1 for r in results if r['match'])}/{len(results)} verified")

idc.qexit(0)
