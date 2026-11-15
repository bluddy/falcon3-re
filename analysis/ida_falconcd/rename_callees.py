"""
Rename callees of squadron_mission_file_loader based on analysis
Renames discovered helper functions and adds comments

IDA Python Script - Batch Mode
"""

import idc
import idaapi

# Wait for autoanalysis to complete
idaapi.auto_wait()

# Functions to rename
renames = [
    (0x138E6A, "undoc_138E6A", "int_to_string_converter", "Converts integer to ASCII string. Handles negative numbers with '-' prefix. Uses divide-by-10 with digit reversal. EXCLUSIVE to squadron_mission_file_loader."),
    (0x138F9C, "sub_138F9C", "string_concatenate", "Concatenates two strings into output buffer. Handles both 0x00 and 0xFF terminators. Called 2x per file for path building. EXCLUSIVE to squadron_mission_file_loader."),
    (0x225B6, "op_dispatch_far_wide", "op_dispatch_far_wide", "Extended parameter wrapper for op_dispatch. Encodes parameters via mov ch,bl. Used for READ_EXT operation (0xC)."),
    (0x13B243, "sub_13B243", "menu_dispatcher_19ops", "Master menu/overlay dispatcher with 19-operation jump table at CS:0x3A52. Provides menu state access, path building, UI updates. Called by 50 functions."),
]

print("Renaming callees of squadron_mission_file_loader:\n")
print(f"{'Address':<12} {'Old Name':<35} {'New Name':<35} {'Status':<10}")
print("=" * 100)

success_count = 0
for addr, old_name, new_name, comment in renames:
    current_name = idc.get_func_name(addr)
    
    # Rename function
    if current_name != new_name:
        result = idc.set_name(addr, new_name, idc.SN_CHECK)
        status = "✓ RENAMED" if result else "✗ FAILED"
        if result:
            success_count += 1
    else:
        status = "= SAME"
        success_count += 1
    
    # Add function comment
    idc.set_func_cmt(addr, comment, False)
    
    print(f"{hex(addr):<12} {old_name:<35} {new_name:<35} {status:<10}")

print(f"\nSuccessfully renamed: {success_count}/{len(renames)}")

# Add comment to main function
main_addr = 0x17B437
main_comment = """Squadron mission file loader - loads .SQUAD/.MTV/.SHP/.TSK files during mission planning.

Called from War Room UI when squadron is selected.

Two-layer architecture:
1. Menu System Integration (via menu_dispatcher_19ops):
   - Gets squadron selection (0-5)
   - Converts to string via int_to_string_converter
   - Builds paths via string_concatenate
   
2. File I/O Operations:
   - op_dispatch_far_entry: OPEN(6), READ(0xA), CLOSE(8)
   - op_dispatch_far_wide: READ_EXT(0xC) for .SHP extended data
   
File loading sequence:
- .SQUAD (unknown format, squadron menu data)
- .MTV (182-202B, mission description text)
- .SHP (6B, conditional: 1B + 5B extended read)
- .TSK (1902B, mission task definitions)

Initializes 64×20-byte mission slot array at far pointer 0x7894:0x79D3E.

Path building: 2 calls per file:
  Call 1: base_dir + squadron_name
  Call 2: result + file_extension

Analysis: analysis/SQUADRON_MISSION_FILE_LOADER_ANALYSIS.md
Callee Analysis: analysis/CALLEE_ANALYSIS_FINDINGS.md
"""

idc.set_func_cmt(main_addr, main_comment, False)
print(f"\nAdded detailed comment to squadron_mission_file_loader (0x{main_addr:X})")

# Add comments to key code locations within main function
comments = [
    (0x17B45E, "Initialize 64×20-byte mission slot array. Each slot: [0]=0x20 (space), [1]=0x00 (null)"),
    (0x17B493, "Call initialization routine"),
    (0x17B4BF, "Check graphics mode - skip file loading in certain modes"),
    (0x17B4EB, "Branch point: test word_14F8BE bit 0. If clear→load files, if set→update state"),
    (0x17B4FC, "Build .SQUAD file path via menu_dispatcher + string_concatenate"),
    (0x17B576, "Open .SQUAD file (operation 6=OPEN, mode 2=read-only)"),
    (0x17B54F, "Build .MTV file path (mission description text)"),
    (0x17B5EA, "Conditional .SHP load: check flag at 0x7A32:0xAD4B"),
    (0x17B5F4, "Build .SHP file path (shape/model reference, 6 bytes)"),
    (0x17B602, "Clear file I/O state flag before open"),
    (0x17B613, "Open .SHP file"),
    (0x17B630, "Read 1 byte from .SHP → 0x602E:0x0689"),
    (0x17B645, "Read 5 bytes from .SHP via extended operation (0xC) → 0x602E:0x068A"),
    (0x17B6B9, "Build .TSK file path (task definitions, 1902 bytes)"),
    (0x17B6E2, "Open .TSK file"),
    (0x17B700, "Read 1902 bytes (0x76E) from .TSK → 0x602E:0x068F"),
    (0x17B71C, "Set file I/O success flag after .TSK load"),
]

print("\nAdding inline comments to key code locations:")
for addr, comment in comments:
    idc.set_cmt(addr, comment, False)
    print(f"  {hex(addr)}: {comment[:60]}...")

print(f"\nAdded {len(comments)} inline comments")

# Exit IDA
idc.qexit(0)
