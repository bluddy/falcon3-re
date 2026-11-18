"""
Analyze AI targeting, weapon, and angle calculation functions.
Focus on functions that support combat decisions.
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\ai_targeting_weapons_analysis.txt"

# Functions to analyze - targeting, weapons, angles
ai_functions = [
    # Targeting functions
    (0x03D180, "ai_target_tracking_update", "Target tracking update, 178B"),
    (0x03F0F1, "ai_target_pursuit_update", "Target pursuit, 178B"),
    
    # Weapon functions
    (0x03DF1E, "ai_weapon_fire_check", "Weapon firing check, 69B"),
    (0x03DC55, "weapon_spawn_gate_validate", "Weapon spawn validation"),
    
    # Angle/geometry functions
    (0x03E8C5, "ai_angle_calculate", "Angle calculation, 42B"),
    (0x03FB5E, "ai_angle_calculate_helper", "Angle helper, 99B"),
    (0x040C6A, "ai_angle_from_offset", "Angle from offset, 9B"),
    
    # Vector/movement functions
    (0x03F07D, "ai_movement_vector_accumulate", "Vector accumulate, 130B"),
    (0x040C2A, "ai_vector_accumulate", "Vector accumulate, 14B"),
    (0x040C54, "ai_vector_accumulate_alt", "Vector accumulate alt, 14B"),
    
    # Record/field access
    (0x040BC8, "ai_record_field_read", "Record field read, 14B"),
    (0x040BFC, "ai_field_offset_calc", "Field offset calc, 16B"),
    (0x03F0E1, "ai_record_offset_get", "Record offset get"),
    
    # State/condition checks
    (0x03F3A8, "ai_state_calculate_helper", "State calculate helper, 256B"),
    (0x03F1D4, "ai_state_condition_check", "Condition check, 80B"),
    (0x03F224, "ai_state_range_check", "Range check, 52B"),
    
    # Entity/terrain
    (0x0407C0, "ai_entity_terrain_position_update", "Terrain position, 131B"),
    (0x040D26, "ai_position_scale_calculate", "Position scaling"),
]

with open(output_file, 'w') as f:
    f.write("=== AI Targeting, Weapons, and Geometry Analysis ===\n\n")
    f.write("Analyzing mid-level AI functions that support combat decisions\n\n")
    
    for addr, name, desc in ai_functions:
        f.write("=" * 80 + "\n")
        f.write(f"{name} @ 0x{addr:X}\n")
        f.write(f"{desc}\n")
        f.write("=" * 80 + "\n\n")
        
        func = idaapi.get_func(addr)
        if not func:
            f.write("ERROR: Function not found!\n\n")
            continue
        
        size = func.end_ea - func.start_ea
        f.write(f"Size: {size} bytes\n")
        f.write(f"Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n\n")
        
        # Get callers
        callers = []
        for xref in idautils.XrefsTo(func.start_ea):
            if xref.type in [idc.fl_CF, idc.fl_CN]:
                caller_func = idaapi.get_func(xref.frm)
                if caller_func:
                    caller_name = idc.get_func_name(xref.frm)
                    callers.append(caller_name)
        
        caller_count = len(set(callers))
        f.write(f"Called by: {caller_count} functions\n")
        if callers:
            for i, caller in enumerate(sorted(set(callers))[:8]):
                f.write(f"  {i+1}. {caller}\n")
            if caller_count > 8:
                f.write(f"  ... and {caller_count - 8} more\n")
        f.write("\n")
        
        # Get callees
        callees = set()
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == "call":
                target = idc.get_operand_value(ea, 0)
                if target:
                    target_name = idc.get_func_name(target)
                    if target_name:
                        callees.add(target_name)
            ea = idc.next_head(ea)
        
        f.write(f"Calls: {len(callees)} functions\n")
        if callees:
            for i, callee in enumerate(sorted(callees)[:8]):
                f.write(f"  {i+1}. {callee}\n")
            if len(callees) > 8:
                f.write(f"  ... and {len(callees) - 8} more\n")
        f.write("\n")
        
        # Analyze code structure
        cmp_count = 0
        test_count = 0
        mov_count = 0
        call_count = 0
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "cmp":
                cmp_count += 1
            elif mnem == "test":
                test_count += 1
            elif mnem == "mov":
                mov_count += 1
            elif mnem == "call":
                call_count += 1
            ea = idc.next_head(ea)
        
        f.write(f"Instructions:\n")
        f.write(f"  CMP: {cmp_count}\n")
        f.write(f"  TEST: {test_count}\n")
        f.write(f"  MOV: {mov_count}\n")
        f.write(f"  CALL: {call_count}\n")
        f.write(f"  Complexity: {'High' if cmp_count + test_count > 10 else 'Medium' if cmp_count + test_count > 3 else 'Low'}\n\n")
        
        # Look for interesting patterns
        f.write("Key patterns:\n")
        
        # Check for behavior flag access
        ea = func.start_ea
        flag_refs = []
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            if "[si+0Bh]" in disasm or "[di+0Bh]" in disasm:
                flag_refs.append((ea, disasm))
            ea = idc.next_head(ea)
        
        if flag_refs:
            f.write(f"  Behavior flag access: {len(flag_refs)} times\n")
            for ref_ea, disasm in flag_refs[:3]:
                f.write(f"    0x{ref_ea:X}: {disasm}\n")
        
        # Check for offset/field access patterns
        ea = func.start_ea
        field_patterns = []
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for [si+XX] or [di+XX] patterns
            if "[si+" in disasm or "[di+" in disasm:
                # Extract the offset
                if "[si+" in disasm:
                    try:
                        offset_str = disasm.split("[si+")[1].split("]")[0].strip("h")
                        if len(offset_str) <= 3:  # Reasonable offset
                            field_patterns.append(offset_str)
                    except:
                        pass
            ea = idc.next_head(ea)
        
        if field_patterns:
            unique_offsets = sorted(set(field_patterns))
            f.write(f"  Context field accesses: {len(unique_offsets)} unique offsets\n")
            f.write(f"    Offsets: {', '.join(['0x' + o + 'h' for o in unique_offsets[:10]])}\n")
        
        # Check for multiplication/division (angle/scaling operations)
        ea = func.start_ea
        math_ops = []
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ["mul", "imul", "div", "idiv", "shl", "shr", "sal", "sar"]:
                disasm = idc.generate_disasm_line(ea, 0)
                math_ops.append((ea, mnem, disasm))
            ea = idc.next_head(ea)
        
        if math_ops:
            f.write(f"  Math operations: {len(math_ops)}\n")
            for op_ea, mnem, disasm in math_ops[:5]:
                f.write(f"    0x{op_ea:X}: {disasm}\n")
        
        f.write("\n\n")
    
    # Create a functional grouping
    f.write("=" * 80 + "\n")
    f.write("FUNCTIONAL GROUPS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("TARGETING GROUP:\n")
    f.write("  ai_target_tracking_update - Maintains target lock\n")
    f.write("  ai_target_pursuit_update - Pursuit calculations\n")
    f.write("  ai_angle_calculate - Computes angles to target\n")
    f.write("  ai_angle_calculate_helper - Angle computation helper\n\n")
    
    f.write("WEAPONS GROUP:\n")
    f.write("  ai_weapon_fire_check - Validates firing conditions\n")
    f.write("  weapon_spawn_gate_validate - Checks spawn conditions\n\n")
    
    f.write("GEOMETRY GROUP:\n")
    f.write("  ai_vector_accumulate - Vector math\n")
    f.write("  ai_movement_vector_accumulate - Movement vectors\n")
    f.write("  ai_position_scale_calculate - Position scaling\n")
    f.write("  ai_entity_terrain_position_update - Terrain relative position\n\n")
    
    f.write("DATA ACCESS GROUP:\n")
    f.write("  ai_record_field_read - Read AI record fields\n")
    f.write("  ai_field_offset_calc - Calculate field offsets\n")
    f.write("  ai_record_offset_get - Get record offset\n\n")
    
    f.write("VALIDATION GROUP:\n")
    f.write("  ai_state_calculate_helper - State calculations\n")
    f.write("  ai_state_condition_check - Condition validation\n")
    f.write("  ai_state_range_check - Range validation\n\n")

print(f"AI targeting/weapons analysis: {output_file}")
idc.qexit(0)
