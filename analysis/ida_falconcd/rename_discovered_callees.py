"""
Rename discovered callees from theater_campaign_file_loader analysis
Based on disassembly analysis of their behavior

IDA Python Script - Batch Mode
"""

import idc
import idaapi

# Wait for autoanalysis
idaapi.auto_wait()

# Functions to rename based on analysis
renames = [
    (0x13C980, "undoc_13C980", "temp_file_handler", "Temp file handler. Builds '.TEMP.DAT' file path, opens for read/write (op 4), reads data. Called during campaign initialization."),
    (0x13D6E4, "undoc_13D6E4", "event_irq_sync_handler", "Event/IRQ synchronization handler. Polls IRQ status, sets event mode, checks state mode. Ensures clean state transitions."),
    (0x15F5B8, "undoc_15F5B8", "ui_campaign_render_coordinator", "UI campaign rendering coordinator. Calls ui_text_render_engine (0x128518), checks graphics mode, handles menu display. 34 callers - high-traffic UI function."),
    (0x15B2A9, "sub_15B2A9", "msc_font_file_loader", "MSC file + font loader. Builds '*.MSC' file paths, opens/reads files, calls madfont_idx_dat_loader. Loads mission-specific fonts and graphics."),
]

print("Renaming discovered callees from theater_campaign_file_loader:\n")
print(f"{'Address':<12} {'Old Name':<35} {'New Name':<40} {'Status':<10}")
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
    
    print(f"{hex(addr):<12} {old_name:<35} {new_name:<40} {status:<10}")

print(f"\nSuccessfully renamed: {success_count}/{len(renames)}")

# Exit IDA
idc.qexit(0)
