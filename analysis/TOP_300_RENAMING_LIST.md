# Top 300 Functions - Complete Renaming List

**Purpose**: Complete list of all 32 functions in ranks 201-300 that need renaming.  
**Status**: Analysis complete, ready for application.

---

## Complete Renaming List (32 Functions)

| Rank | Address | Current Name | New Name | Size | Category |
|------|---------|--------------|----------|------|----------|
| 202 | 0x02C527 | sub_2C527 | overlay_bridge_to_66a3d | 8B | Overlay |
| 206 | 0x11CD7F | undoc_11CD7F | ui_element_render_variant_a | 48B | UI |
| 207 | 0x11CDEB | undoc_11CDEB | ui_element_render_variant_b | 48B | UI |
| 208 | 0x127EFF | undoc_127EFF | graphics_clip_processor | 162B | Graphics |
| 209 | 0x129591 | undoc_129591 | ui_text_render_wrapper | 24B | UI |
| 211 | 0x1941E8 | sub_1941E8 | overlay_r54_ui_coordinator | 1376B | UI |
| 212 | 0x195F81 | sub_195F81 | overlay_r58_ui_coordinator | 1409B | UI |
| 213 | 0x1A2B37 | undoc_1A2B37 | overlay_r57_simple_helper | 26B | Overlay |
| 224 | 0x11CC39 | sub_11CC39 | ui_element_render_complex_a | 133B | UI |
| 225 | 0x11D074 | sub_11D074 | ui_element_render_with_draw | 143B | UI |
| 226 | 0x11D172 | undoc_11D172 | ui_element_render_triple_dispatch | 155B | UI |
| 227 | 0x13153A | undoc_13153A | menu_simple_helper | 55B | Menu |
| 228 | 0x135FCD | undoc_135FCD | ui_string_formatter_interactive | 358B | String |
| 229 | 0x139D85 | sub_139D85 | font_data_processor | 481B | Font |
| 230 | 0x13AD67 | undoc_13AD67 | menu_queue_processor | 348B | Menu |
| 240 | 0x02C4B9 | sub_2C4B9 | overlay_bridge_to_66988 | 8B | Overlay |
| 241 | 0x02C5D1 | sub_2C5D1 | overlay_bridge_to_66ea8 | 8B | Overlay |
| 245 | 0x1016A8 | sub_1016A8 | r01_segment_helper_a | 41B | Overlay |
| 246 | 0x106AD0 | sub_106AD0 | r06_segment_helper_a | 41B | Overlay |
| 247 | 0x11CE1B | undoc_11CE1B | ui_element_render_variant_c | 48B | UI |
| 248 | 0x11CE7B | undoc_11CE7B | ui_element_render_variant_d | 48B | UI |
| 249 | 0x13462B | sub_13462B | data_structure_processor | 221B | Data |
| 250 | 0x13DDC3 | sub_13DDC3 | math_helper_20b | 20B | Math |
| 251 | 0x160096 | undoc_160096 | state_processor_large | 357B | State |
| 275 | 0x04D75F | undoc_4D75F | weapon_helper_4d75f | 99B | Weapon |
| 276 | 0x10106C | sub_10106C | r01_processor_segment | 130B | Overlay |
| 277 | 0x1017D5 | sub_1017D5 | r01_segment_helper_b | 123B | Overlay |
| 278 | 0x106457 | sub_106457 | r06_processor_segment | 220B | Overlay |
| 280 | 0x11CBA8 | sub_11CBA8 | ui_element_render_complex_b | 145B | UI |
| 281 | 0x11CE4B | undoc_11CE4B | ui_element_render_variant_e | 48B | UI |
| 282 | 0x185569 | undoc_185569 | overlay_r55_helper_large | 179B | Overlay |
| 283 | 0x1AAACC | sub_1AAACC | overlay_processor_large_1aaacc | 498B | Overlay |

---

## IDA Python Script Format

```python
# Copy-paste into IDA Python console or script
import idc

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

for ea, name in renamings.items():
    idc.set_name(ea, name, idc.SN_NOWARN | idc.SN_NOCHECK)
    print(f"✓ 0x{ea:06X}: {name}")

print(f"\n✓ Renamed {len(renamings)} functions")
```

---

## Comments for Each Function

### Rank #202 - overlay_bridge_to_66a3d
"Overlay bridge trampoline to 66A3Dh (8B)."

### Rank #206 - ui_element_render_variant_a
"UI element renderer variant A (48B). Calls dispatch_220ec_invoke."

### Rank #207 - ui_element_render_variant_b
"UI element renderer variant B (48B). Calls dispatch_220ec_invoke."

### Rank #208 - graphics_clip_processor
"Graphics clipping processor (162B). Calls segment_clip_test."

### Rank #209 - ui_text_render_wrapper
"UI text rendering wrapper (24B). Calls ui_text_render_simple."

### Rank #211 - overlay_r54_ui_coordinator
"Overlay R54 UI coordinator (1376B). Calls ui_element_render_variant_a/b."

### Rank #212 - overlay_r58_ui_coordinator
"Overlay R58 UI coordinator (1409B). Calls ui_element_render_variant_a/b."

### Rank #213 - overlay_r57_simple_helper
"Overlay R57 simple helper (26B)."

### Rank #224 - ui_element_render_complex_a
"UI element renderer complex (133B). Calls dispatch_220ec_invoke, ui_text_width_calculate, table_dispatch_interpreter."

### Rank #225 - ui_element_render_with_draw
"UI element renderer with draw (143B). Calls dispatch_220ec_invoke and draw_coord_wrapper."

### Rank #226 - ui_element_render_triple_dispatch
"UI element renderer triple dispatch (155B). Calls dispatch_220ec_invoke 3x."

### Rank #227 - menu_simple_helper
"Menu system simple helper (55B)."

### Rank #228 - ui_string_formatter_interactive
"Interactive UI string formatter (358B). Calls int_to_string_converter, string_concatenate, mouse_gate_far_entry, op_dispatch_far_entry."

### Rank #229 - font_data_processor
"Font data processor (481B). Processes font file data."

### Rank #230 - menu_queue_processor
"Menu/queue processor (348B). Calls sub_13B1F4 and signed_diff_abs."

### Rank #240 - overlay_bridge_to_66988
"Overlay bridge trampoline to 66988h (8B)."

### Rank #241 - overlay_bridge_to_66ea8
"Overlay bridge trampoline to 66EA8h (8B)."

### Rank #245 - r01_segment_helper_a
"R01 segment helper A (41B). Utility for overlay R01."

### Rank #246 - r06_segment_helper_a
"R06 segment helper A (41B). Utility for overlay R06."

### Rank #247 - ui_element_render_variant_c
"UI element renderer variant C (48B). Calls dispatch_220ec_invoke."

### Rank #248 - ui_element_render_variant_d
"UI element renderer variant D (48B). Calls dispatch_220ec_invoke."

### Rank #249 - data_structure_processor
"Data structure processor (221B). General data processing function."

### Rank #250 - math_helper_20b
"Math helper function (20B). Small arithmetic utility."

### Rank #251 - state_processor_large
"State processor (357B). Handles game state processing."

### Rank #275 - weapon_helper_4d75f
"Weapon system helper (99B). Part of weapon subsystem."

### Rank #276 - r01_processor_segment
"R01 processor segment function (130B). Overlay R01 processing logic."

### Rank #277 - r01_segment_helper_b
"R01 segment helper B (123B). Additional R01 utility."

### Rank #278 - r06_processor_segment
"R06 processor segment function (220B). Overlay R06 processing logic."

### Rank #280 - ui_element_render_complex_b
"UI element renderer complex B (145B). Similar to complex_a variant."

### Rank #281 - ui_element_render_variant_e
"UI element renderer variant E (48B). Fifth 48B UI renderer variant."

### Rank #282 - overlay_r55_helper_large
"Overlay R55 helper (179B). Additional R55 processing function."

### Rank #283 - overlay_processor_large_1aaacc
"Large overlay processor (498B). Complex processing function."

---

**Total Functions**: 32  
**Ready for Application**: Yes  
**Date Prepared**: 2026-11-16
