"""
Extract detailed information about AI state machine functions.
Focus on the core decision-making and behavior functions.
"""

import idc
import idaapi
import idautils
import json

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\ai_state_machine_functions.txt"

# Key AI state machine functions to analyze
ai_functions = [
    (0x03CF9D, "ai_state_processor_core", "Core state processing, 886B, 4 RFM refs"),
    (0x03EBA5, "ai_behavior_decision_tree", "814B decision tree, 87 comparisons"),
    (0x03E2D3, "ai_combat_maneuver_selector", "505B maneuver selector, 4 RFM refs"),
    (0x03D37F, "entity_physics_and_ai_update", "1319B entity update, 7 RFM refs"),
    (0x0407B0, "ai_state_value_get", "32B, 21 callers - MOST USED"),
    (0x042838, "ai_state_flag_validate", "64B flag validator, 22 callers"),
    (0x03E8C5, "ai_angle_calculate", "Angle/heading calc, 11 callers"),
]

with open(output_file, 'w') as f:
    f.write("=== AI State Machine Functions - Detailed Analysis ===\n\n")
    
    for addr, name, desc in ai_functions:
        f.write("=" * 80 + "\n")
        f.write(f"{name} @ 0x{addr:X}\n")
        f.write(f"{desc}\n")
        f.write("=" * 80 + "\n\n")
        
        func = idaapi.get_func(addr)
        if not func:
            f.write("ERROR: Function not found!\n\n")
            continue
        
        f.write(f"Address range: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n\n")
        
        # Get all xrefs TO this function (callers)
        callers = []
        for xref in idautils.XrefsTo(func.start_ea):
            if xref.type in [idc.fl_CF, idc.fl_CN]:  # Call refs only
                caller_func = idaapi.get_func(xref.frm)
                if caller_func:
                    caller_name = idc.get_func_name(xref.frm)
                    callers.append((xref.frm, caller_name))
        
        f.write(f"Callers: {len(callers)}\n")
        if callers:
            for i, (call_addr, caller_name) in enumerate(sorted(set(callers), key=lambda x: x[1])[:15]):
                f.write(f"  {i+1}. {caller_name} @ 0x{call_addr:X}\n")
            if len(callers) > 15:
                f.write(f"  ... and {len(callers) - 15} more\n")
        f.write("\n")
        
        # Get all functions this function CALLS
        callees = []
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == "call":
                target = idc.get_operand_value(ea, 0)
                if target:
                    target_name = idc.get_func_name(target)
                    if target_name:
                        callees.append((target, target_name))
            ea = idc.next_head(ea)
        
        f.write(f"Callees: {len(set(callees))}\n")
        if callees:
            for i, (target_addr, target_name) in enumerate(sorted(set(callees), key=lambda x: x[1])[:15]):
                f.write(f"  {i+1}. {target_name} @ 0x{target_addr:X}\n")
            if len(set(callees)) > 15:
                f.write(f"  ... and {len(set(callees)) - 15} more\n")
        f.write("\n")
        
        # Find interesting patterns in the code
        f.write("Code patterns:\n")
        
        # Count comparisons
        cmp_count = 0
        test_count = 0
        jmp_count = 0
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "cmp":
                cmp_count += 1
            elif mnem == "test":
                test_count += 1
            elif mnem.startswith("j"):  # All jumps
                jmp_count += 1
            ea = idc.next_head(ea)
        
        f.write(f"  CMP instructions: {cmp_count}\n")
        f.write(f"  TEST instructions: {test_count}\n")
        f.write(f"  Jump instructions: {jmp_count}\n")
        f.write(f"  Total branches: {cmp_count + test_count + jmp_count}\n")
        
        # Look for behavior flag tests ([si+0Bh])
        f.write("\n  Behavior flag tests ([si+0Bh]):\n")
        ea = func.start_ea
        flag_tests = []
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            if "[si+0Bh]" in disasm or "[si+0xB]" in disasm or "[si+11]" in disasm:
                flag_tests.append((ea, disasm))
            ea = idc.next_head(ea)
        
        if flag_tests:
            for test_ea, disasm in flag_tests[:10]:
                f.write(f"    0x{test_ea:X}: {disasm}\n")
            if len(flag_tests) > 10:
                f.write(f"    ... and {len(flag_tests) - 10} more\n")
        else:
            f.write("    None found\n")
        
        # Look for RFM data accesses (cs:word_3B830)
        f.write("\n  RFM data accesses (cs:word_3B830):\n")
        ea = func.start_ea
        rfm_refs = []
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            if "word_3B830" in disasm or "3B830" in disasm:
                rfm_refs.append((ea, disasm))
            ea = idc.next_head(ea)
        
        if rfm_refs:
            for rfm_ea, disasm in rfm_refs:
                f.write(f"    0x{rfm_ea:X}: {disasm}\n")
        else:
            f.write("    None found\n")
        
        f.write("\n\n")
    
    # Create a call graph summary
    f.write("=" * 80 + "\n")
    f.write("CALL GRAPH SUMMARY\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("High-level flow:\n")
    f.write("  entity_slot_update_loop (main loop)\n")
    f.write("    → entity_physics_and_ai_update (per-entity)\n")
    f.write("      → ai_state_processor_core (state machine)\n")
    f.write("        → ai_behavior_decision_tree (decisions)\n")
    f.write("        → ai_combat_maneuver_selector (tactics)\n")
    f.write("        → ai_state_flag_validate (validation)\n")
    f.write("        → ai_angle_calculate (geometry)\n")
    f.write("        → ai_state_value_get (state queries)\n\n")

print(f"AI state machine analysis: {output_file}")
idc.qexit(0)
