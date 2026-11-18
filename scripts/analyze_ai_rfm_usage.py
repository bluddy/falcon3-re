"""
Analyze how AI functions use cs:word_3B830 (RFM AI behavior pointer).
Extract the indexing patterns and data access patterns.
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\ai_rfm_usage_analysis.txt"

# All functions that reference cs:word_3B830 from our earlier analysis
rfm_refs = [
    (0x3C1C7, "entity_slot_update_loop", "WRITE"),
    (0x3C31F, "sub_3C319", "READ"),
    (0x3C340, "sub_3C319", "READ"),
    (0x3C366, "sub_3C319", "READ"),
    (0x3C3A5, "sub_3C38D", "READ"),
    (0x3CFD6, "ai_state_processor_core", "READ"),
    (0x3D054, "ai_state_processor_core", "READ"),
    (0x3D090, "ai_state_processor_core", "READ"),
    (0x3D106, "ai_state_processor_core", "READ"),
    (0x3D495, "entity_physics_and_ai_update", "READ"),
    (0x3D4CB, "entity_physics_and_ai_update", "READ"),
    (0x3D501, "entity_physics_and_ai_update", "READ"),
    (0x3D5EE, "entity_physics_and_ai_update", "READ"),
    (0x3D650, "entity_physics_and_ai_update", "READ"),
    (0x3D6D6, "entity_physics_and_ai_update", "READ"),
    (0x3D709, "entity_physics_and_ai_update", "READ"),
    (0x3E3CD, "ai_combat_maneuver_selector", "READ"),
    (0x3E41D, "ai_combat_maneuver_selector", "READ"),
    (0x3E454, "ai_combat_maneuver_selector", "READ"),
    (0x3E4B0, "ai_combat_maneuver_selector", "READ"),
    (0x41A5D, "farobj_slot_table_copy", "WRITE"),
]

with open(output_file, 'w') as f:
    f.write("=== AI RFM Usage Analysis ===\n\n")
    f.write("cs:word_3B830 = Pointer to RFM AI behavior data\n")
    f.write("Total references: {}\n\n".format(len(rfm_refs)))
    
    # Group by function
    funcs = {}
    for addr, func_name, access_type in rfm_refs:
        if func_name not in funcs:
            funcs[func_name] = []
        funcs[func_name].append((addr, access_type))
    
    f.write("=" * 80 + "\n")
    f.write("FUNCTIONS USING RFM DATA:\n")
    f.write("=" * 80 + "\n\n")
    
    for func_name in sorted(funcs.keys()):
        refs = funcs[func_name]
        f.write(f"\n{func_name}:\n")
        f.write(f"  References: {len(refs)}\n")
        
        # Get function info
        first_ref = refs[0][0]
        func = idaapi.get_func(first_ref)
        if func:
            f.write(f"  Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
            f.write(f"  Size: {func.end_ea - func.start_ea} bytes\n")
        
        f.write(f"\n  RFM data accesses:\n")
        
        # Analyze each reference
        for addr, access_type in refs:
            f.write(f"\n    @ 0x{addr:X} ({access_type}):\n")
            
            # Get context (5 instructions before and after)
            context_start = addr
            for _ in range(5):
                prev = idc.prev_head(context_start)
                if prev != idaapi.BADADDR:
                    context_start = prev
            
            # Extract the access pattern
            ea = context_start
            for i in range(11):
                disasm = idc.generate_disasm_line(ea, 0)
                marker = "    >>> " if ea == addr else "        "
                f.write(f"{marker}0x{ea:X}: {disasm}\n")
                
                ea = idc.next_head(ea)
                if ea == idaapi.BADADDR:
                    break
    
    # Analyze the indexing patterns
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("INDEXING PATTERN ANALYSIS:\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("Common patterns observed:\n\n")
    
    f.write("Pattern 1: Behavior flag indexing\n")
    f.write("  mov     ax, cs:word_3B830\n")
    f.write("  mov     ah, [si+14h]        ; Get byte from AI context\n")
    f.write("  mul     ah                  ; Multiply pointer by index\n")
    f.write("  shr     ax, cl              ; Shift result\n")
    f.write("  ; Result = maneuver parameter\n\n")
    
    f.write("Pattern 2: Direct offset\n")
    f.write("  mov     ax, cs:word_3B830\n")
    f.write("  shl     al, 1               ; Multiply by 2\n")
    f.write("  ; Access word-sized data\n\n")
    
    f.write("Pattern 3: Add to base\n")
    f.write("  mov     ax, cs:word_3B830\n")
    f.write("  add     ax, cs:word_3B830   ; Double the value\n")
    f.write("  ; Calculate offset into data structure\n\n")
    
    # Find common byte offsets accessed in AI contexts
    f.write("\n" + "=" * 80 + "\n")
    f.write("AI CONTEXT OFFSETS USED FOR INDEXING:\n")
    f.write("=" * 80 + "\n\n")
    
    offsets_found = set()
    
    for addr, func_name, access_type in rfm_refs:
        if access_type == "READ":
            # Look for [si+XX] or [di+XX] patterns near the reference
            ea = addr - 20  # Look 20 bytes before
            for _ in range(10):
                disasm = idc.generate_disasm_line(ea, 0)
                if "[si+" in disasm or "[di+" in disasm:
                    # Extract offset
                    if "[si+" in disasm:
                        parts = disasm.split("[si+")[1].split("]")[0]
                        try:
                            offset = int(parts.strip("h"), 16)
                            offsets_found.add((offset, func_name, ea))
                        except:
                            pass
                
                ea = idc.next_head(ea)
    
    f.write("Offsets accessed from AI context (SI/DI pointer):\n\n")
    
    for offset in sorted(set(x[0] for x in offsets_found)):
        f.write(f"  +0x{offset:02X}: ")
        funcs_using = set(x[1] for x in offsets_found if x[0] == offset)
        f.write(f"Used by {', '.join(sorted(funcs_using)[:3])}")
        if len(funcs_using) > 3:
            f.write(f" and {len(funcs_using)-3} more")
        f.write("\n")
    
    f.write("\n\nAnalysis complete.\n")

print(f"AI RFM usage analysis: {output_file}")
idc.qexit(0)
