#!/usr/bin/env python3
"""Update registry with render chain functions discovered in ui_campaign_render_coordinator analysis"""

import yaml
import sys
from pathlib import Path

# New functions to add/update
new_functions = [
    {
        "address": 0x15F5B8,
        "name": "ui_campaign_render_coordinator",
        "system": "ui",
        "size": 745,
        "callers": 34,
        "doc": "Coordinates campaign UI rendering. Checks graphics_mode_flag, branches on display mode flags, calls render helpers in sequence. Two code paths: detailed (uses ui_text_render_single_mode) vs compact (uses ui_text_render_multi_mode).",
        "source": "Rank #11 callee deep dive - render chain analysis"
    },
    {
        "address": 0x1293F0,
        "name": "ui_text_render_single_mode",
        "system": "ui",
        "size": 120,
        "doc": "Renders single character with display mode checking. Checks byte_7A302 (rendering mode), byte_14E5A0 (display mode 1/2/3). Calls ui_text_render_with_palette or ui_text_render_simple based on mode.",
        "source": "Callee of ui_campaign_render_coordinator (called 4x)"
    },
    {
        "address": 0x129468,
        "name": "ui_text_render_multi_mode",
        "system": "ui",
        "size": 297,
        "doc": "Renders multiple characters with display mode checking. Contains loop that calls ui_text_render_engine (0x128598) repeatedly. Same mode logic as single-char version but with counter/length parameter.",
        "source": "Callee of ui_campaign_render_coordinator (called 4x)"
    },
    {
        "address": 0x129ED6,
        "name": "ui_text_render_with_palette",
        "system": "ui",
        "doc": "Text rendering with palette mode parameter. Called by ui_text_render_single_mode when mode flags are set.",
        "source": "Callee of ui_text_render_single_mode"
    },
    {
        "address": 0x128AA6,
        "name": "ui_text_render_simple",
        "system": "ui",
        "doc": "Simple text rendering without palette mode. Called by ui_text_render_single_mode when mode flags are not set.",
        "source": "Callee of ui_text_render_single_mode"
    },
    {
        "address": 0x129C88,
        "name": "ui_text_render_multi_palette",
        "system": "ui",
        "doc": "Multi-character text rendering with palette mode. Called by ui_text_render_multi_mode in loop.",
        "source": "Callee of ui_text_render_multi_mode"
    },
    {
        "address": 0x139F76,
        "name": "ui_render_state_update",
        "system": "ui",
        "doc": "Updates UI render state/buffers. Called 3 times in ui_campaign_render_coordinator between render operations.",
        "source": "Callee of ui_campaign_render_coordinator (called 3x)"
    },
    {
        "address": 0x1320CC,
        "name": "ui_font_config_apply",
        "system": "ui",
        "doc": "Applies font/text configuration settings. Called once in ui_campaign_render_coordinator.",
        "source": "Callee of ui_campaign_render_coordinator"
    },
    {
        "address": 0x138FF0,
        "name": "string_copy_with_offset",
        "system": "utility",
        "doc": "String manipulation helper with offset parameter. Called from ui_campaign_render_coordinator.",
        "source": "Callee of ui_campaign_render_coordinator"
    },
    {
        "address": 0x2C49B,
        "name": "menu_finalize_render",
        "system": "ui",
        "doc": "Final menu render step. Called at end of ui_campaign_render_coordinator path A.",
        "source": "Callee of ui_campaign_render_coordinator"
    },
    {
        "address": 0x128518,
        "name": "ui_text_render_setup",
        "system": "ui",
        "size": 123,
        "callers": 16,
        "doc": "Setup/wrapper function before ui_text_render_engine. 123 bytes, located immediately before ui_text_render_engine (0x128598). May prepare parameters or check state.",
        "source": "Address verification during render chain analysis"
    },
]

def update_registry(registry_path):
    """Update registry with new functions"""
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data or 'functions' not in data:
        print("ERROR: Invalid registry format")
        return False
    
    functions = data['functions']
    
    # Track updates
    added = 0
    updated = 0
    
    for new_func in new_functions:
        addr = new_func['address']
        
        # Check if exists
        existing_idx = None
        for idx, func in enumerate(functions):
            if func.get('address') == addr:
                existing_idx = idx
                break
        
        if existing_idx is not None:
            # Update existing
            old_name = functions[existing_idx].get('name', 'unknown')
            functions[existing_idx].update(new_func)
            print(f"UPDATED: 0x{addr:X} ({old_name} → {new_func['name']})")
            updated += 1
        else:
            # Add new (insert in sorted position)
            insert_idx = len(functions)
            for idx, func in enumerate(functions):
                if func.get('address', 0xFFFFFF) > addr:
                    insert_idx = idx
                    break
            functions.insert(insert_idx, new_func)
            print(f"ADDED: 0x{addr:X} ({new_func['name']})")
            added += 1
    
    # Write back
    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
    
    print(f"\nRegistry updated: {added} added, {updated} updated")
    return True

if __name__ == '__main__':
    registry_path = Path(__file__).parent.parent / 'registry' / 'functions.yaml'
    
    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}")
        sys.exit(1)
    
    if update_registry(registry_path):
        print("✓ Registry update complete")
    else:
        print("✗ Registry update failed")
        sys.exit(1)
