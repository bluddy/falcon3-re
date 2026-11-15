"""
Rename Rank #11: overlay_r46_processor → theater_campaign_file_loader
Address: 0x15A8B0
Size: 2,553 bytes
Callers: 102
Callees: 70

Analysis shows:
- Loads theater/campaign files: .THEATER, .WAR, .SQUAD, .NWS, .SHP, .BIN
- 42 file I/O operations (op_dispatch_far_entry)
- 17 extended file operations (op_dispatch_far_wide)
- Uses int_to_string_converter and string_concatenate helpers
- Similar pattern to squadron_mission_file_loader but more comprehensive
- Likely loads theater configuration, war state, news, squadron data for campaign

IDA Python Script - Batch Mode
"""

import idc
import idaapi

# Wait for autoanalysis
idaapi.auto_wait()

addr = 0x15A8B0
old_name = idc.get_func_name(addr)
new_name = "theater_campaign_file_loader"

print(f"Renaming Rank #11 at 0x{addr:X}")
print(f"  Old name: {old_name}")
print(f"  New name: {new_name}")

success = idc.set_name(addr, new_name, idc.SN_CHECK)

if success:
    print(f"SUCCESS: Renamed to {new_name}")
else:
    print(f"FAILED: Could not rename")

# Add comprehensive function comment
comment = """Theater/campaign file loader - R46 overlay processor.

Loads multiple file types for theater/campaign initialization:
- .THEATER: Theater configuration (terrain, airbases, strategic data)
- .WAR: War state file (161 bytes, daily war summary)
- .SQUAD: Squadron files (menu/selection data)
- .NWS: News files (mission briefings, campaign events)
- .SHP: Shape/model files (3D assets, conditional loading)
- .BIN: Binary data files (theater-specific)

File I/O Statistics:
- 42× op_dispatch_far_entry calls (OPEN/READ/CLOSE operations)
- 17× op_dispatch_far_wide calls (extended read operations)
- 7× string_concatenate calls (path building)
- 2× int_to_string_converter calls (squadron numbers)

Similar pattern to squadron_mission_file_loader (0x17B437) but more comprehensive.
Loads complete theater/campaign environment, not just squadron selection.

70 callees including:
- int_to_string_converter, string_concatenate (path helpers)
- op_dispatch_far_entry, op_dispatch_far_wide (file I/O)
- menu_selection_ptr_get, menu_config_ptr_get (UI integration)
- mouse_gate_far_entry (input handling)
- menu_loadout_config_validate (data validation)

Rank #11 in top-100 by caller frequency (102 callers).
Called from campaign start, theater selection, and mission loading flows.

Analysis: analysis/THEATER_CAMPAIGN_FILE_LOADER_ANALYSIS.md (pending)
Related: squadron_mission_file_loader (0x17B437), mission_campaign.md
"""

idc.set_func_cmt(addr, comment, False)
print(f"\nAdded detailed function comment")

# Add inline comments at key locations
comments = [
    (0x15A8B6, "Read PIT timer for timing/randomization"),
    (0x15A930, "Convert squadron number to string (0-5 → \"0\"-\"5\")"),
    (0x15A953, "Build .SQUAD file path: base + squadron + \".SQUAD\""),
    (0x15A976, "Build .WAR file path: base + \".WAR\""),
    (0x15A99F, "Check graphics mode flag - skip certain loads in low-detail mode"),
    (0x15A9AA, "Initialize mouse/input handling"),
    (0x15A9C8, "Open .WAR file (operation 4 = open for read/write?)"),
    (0x15AA11, "Build .THEATER file path"),
    (0x15AA25, "Open .THEATER file (operation 6 = OPEN)"),
    (0x15AA45, "Read from .THEATER file (operation 0xA = READ)"),
    (0x15AAA3, "Extended file operation on .THEATER (0xE = ?)"),
    (0x15AC07, "Multiple READ operations in loop - loading theater data structures"),
]

print("\nAdding inline comments:")
for addr_cmt, cmt in comments:
    idc.set_cmt(addr_cmt, cmt, False)
    print(f"  {hex(addr_cmt)}: {cmt[:60]}...")

print(f"\nAdded {len(comments)} inline comments")

# Exit IDA
idc.qexit(0)
