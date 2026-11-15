import ida_auto
import ida_funcs
import ida_xref
import idc
import json

def get_function_call_counts():
    """Extract all functions with their caller counts"""
    
    print("=" * 80)
    print("EXTRACTING TOP 100 MOST-CALLED FUNCTIONS")
    print("=" * 80)
    
    function_data = []
    
    # Iterate through all functions
    for func_ea in ida_funcs.Functions():
        func_name = idc.get_func_name(func_ea)
        
        # Count callers (xrefs to this function)
        callers = []
        for xref in ida_xref.XrefsTo(func_ea, 0):
            # Only count code xrefs (calls)
            if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:  # Near call, Far call
                callers.append(xref.frm)
        
        caller_count = len(set(callers))  # Unique callers
        
        # Get function size
        func = ida_funcs.get_func(func_ea)
        if func:
            size = func.end_ea - func.start_ea
        else:
            size = 0
        
        function_data.append({
            'address': func_ea,
            'name': func_name,
            'callers': caller_count,
            'size': size
        })
    
    # Sort by caller count (descending)
    function_data.sort(key=lambda x: x['callers'], reverse=True)
    
    # Write top 100 to JSON
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\top_100_functions.json"
    with open(output_file, 'w') as f:
        json.dump(function_data[:100], f, indent=2)
    
    # Write human-readable report
    report_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\TOP_100_FUNCTIONS.md"
    with open(report_file, 'w') as f:
        f.write("# Top 100 Most-Called Functions in Falcon 3.0\n\n")
        f.write("**Generated**: 2026-11-11\n")
        f.write("**Source**: FALCONCD.EXE.i64\n\n")
        f.write("---\n\n")
        
        f.write("| Rank | Address | Callers | Size | Function Name |\n")
        f.write("|------|---------|---------|------|---------------|\n")
        
        for i, func in enumerate(function_data[:100], 1):
            f.write(f"| {i} | 0x{func['address']:06X} | {func['callers']} | {func['size']}B | `{func['name']}` |\n")
        
        f.write("\n---\n\n")
        f.write("## Analysis Status\n\n")
        f.write("### Completed (24 functions)\n\n")
        
        completed = [
            "input_poll_handler",
            "input_sync_and_wait",
            "input_finalization",
            "mouse_sensitivity_calculator",
            "keyboard_state_processor",
            "joystick_position_reader",
            "joystick_button_handler",
            "input_region_mapper",
            "joystick_calibration_handler",
            "input_overlay_bridge",
            "ui_text_render_engine",
            "ui_render_coordinator",
            "ui_text_render_loop",
            "draw_primitive_mode_1",
            "draw_primitive_mode_2",
            "draw_coord_wrapper",
            "menu_state_init_with_random",
            "ui_slot_scan_step",
            "menu_selection_ptr_get",
            "farobj_vec3_accum_b_ret",
            "pit_channel0_latch_read",
            "ui_loadout_menu_enter",
            "bda_kb_flag_get",
            "mouse_int33_dispatch",
        ]
        
        for name in sorted(completed):
            # Find in top 100
            matching = [f for f in function_data[:100] if f['name'] == name]
            if matching:
                func = matching[0]
                rank = function_data.index(func) + 1
                f.write(f"- ✅ Rank {rank}: `{name}` (0x{func['address']:06X}, {func['callers']} callers, {func['size']}B)\n")
            else:
                f.write(f"- ✅ `{name}` (not in top 100)\n")
        
        f.write("\n### Next Targets (From Top 100)\n\n")
        f.write("Functions in top 100 not yet analyzed:\n\n")
        
        count = 0
        for i, func in enumerate(function_data[:100], 1):
            if func['name'] not in completed:
                f.write(f"{i}. `{func['name']}` (0x{func['address']:06X}, {func['callers']} callers, {func['size']}B)\n")
                count += 1
                if count >= 20:  # Show first 20 unanalyzed
                    f.write(f"\n... and {100 - len([f for f in function_data[:100] if f['name'] in completed]) - 20} more\n")
                    break
    
    print(f"\n✅ Top 100 written to: {report_file}")
    print(f"✅ JSON data written to: {output_file}")
    print(f"\nTop 10:")
    for i, func in enumerate(function_data[:10], 1):
        print(f"  {i}. {func['name']} (0x{func['address']:06X}): {func['callers']} callers, {func['size']}B")

if __name__ == "__main__":
    ida_auto.auto_wait()
    get_function_call_counts()
    idc.qexit(0)
