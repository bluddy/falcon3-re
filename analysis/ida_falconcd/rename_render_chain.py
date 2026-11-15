import idc
import idaapi

# Rename functions discovered in render chain analysis
renames = [
    # Main rendering coordinators
    (0x15F5B8, "ui_campaign_render_coordinator", "Coordinates campaign UI rendering; checks graphics_mode_flag, dispatches to render helpers"),
    
    # Primary render helpers (called by coordinator)
    (0x1293F0, "ui_text_render_single_mode", "Renders single char with mode checking; wrapper for palette/simple renderers"),
    (0x129468, "ui_text_render_multi_mode", "Renders multiple chars with mode checking; loops calling ui_text_render_engine"),
    
    # Secondary helpers (called by primary)
    (0x129ED6, "ui_text_render_with_palette", "Text render with palette mode parameter"),
    (0x128AA6, "ui_text_render_simple", "Simple text render without palette"),
    (0x129C88, "ui_text_render_multi_palette", "Multi-char text render with palette mode"),
    
    # Other coordinator callees (need investigation)
    (0x139F76, "ui_render_state_update", "Called 3x in coordinator; likely updates render state/buffers"),
    (0x1320CC, "ui_font_config_apply", "Applies font/text configuration"),
    (0x138FF0, "string_copy_with_offset", "String manipulation helper"),
    (0x2C49B, "menu_finalize_render", "Final menu render step"),
    
    # sub_128518 investigation (16 callers, 123 bytes, just before ui_text_render_engine)
    (0x128518, "ui_text_render_setup", "Setup/wrapper before ui_text_render_engine; 123 bytes, 16 callers"),
]

print("=" * 70)
print("RENAMING RENDER CHAIN FUNCTIONS")
print("=" * 70)

renamed_count = 0
failed_count = 0

for addr, new_name, comment in renames:
    func = idaapi.get_func(addr)
    if not func:
        print(f"FAILED: 0x{addr:X} - not a function")
        failed_count += 1
        continue
    
    old_name = idc.get_func_name(addr)
    
    # Set name
    if idc.set_name(addr, new_name, idaapi.SN_NOWARN):
        # Set function comment
        idc.set_func_cmt(addr, comment, 0)
        print(f"✓ 0x{addr:X}: {old_name} → {new_name}")
        renamed_count += 1
    else:
        print(f"FAILED: 0x{addr:X}: {old_name} → {new_name}")
        failed_count += 1

print("=" * 70)
print(f"Renamed: {renamed_count}")
print(f"Failed: {failed_count}")
print("=" * 70)

idc.qexit(0)
