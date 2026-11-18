"""
Analyze the structure of ai_entity_behavior_dispatcher (2580 bytes).
Focus on understanding the dispatch mechanism and routing logic.
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\dispatcher_structure.txt"

dispatcher_addr = 0x03CE92

with open(output_file, 'w') as f:
    f.write("=== AI Entity Behavior Dispatcher - Structure Analysis ===\n\n")
    
    func = idaapi.get_func(dispatcher_addr)
    if not func:
        f.write("ERROR: Function not found at 0x3CE92!\n")
        f.write("Trying to find function by name...\n\n")
        
        # Search for function by name
        for func_addr in idautils.Functions():
            name = idc.get_func_name(func_addr)
            if "dispatcher" in name.lower() and "ai" in name.lower():
                f.write(f"Found: {name} @ 0x{func_addr:X}\n")
                func = idaapi.get_func(func_addr)
                dispatcher_addr = func_addr
                break
    
    if not func:
        f.write("ERROR: Could not locate dispatcher function!\n")
        idc.qexit(1)
        return
    
    size = func.end_ea - func.start_ea
    f.write(f"Function: ai_entity_behavior_dispatcher\n")
    f.write(f"Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
    f.write(f"Size: {size} bytes\n\n")
    
    # Get basic stats
    f.write("=" * 80 + "\n")
    f.write("BASIC STATISTICS\n")
    f.write("=" * 80 + "\n\n")
    
    instruction_count = 0
    ea = func.start_ea
    while ea < func.end_ea:
        ea = idc.next_head(ea)
        instruction_count += 1
    
    f.write(f"Instruction count: ~{instruction_count}\n")
    f.write(f"Average bytes per instruction: {size / instruction_count:.1f}\n\n")
    
    # Analyze first 80 instructions to find dispatch pattern
    f.write("=" * 80 + "\n")
    f.write("FUNCTION ENTRY ANALYSIS (first 80 instructions)\n")
    f.write("=" * 80 + "\n\n")
    
    ea = func.start_ea
    for i in range(80):
        if ea >= func.end_ea:
            break
        
        disasm = idc.generate_disasm_line(ea, 0)
        mnem = idc.print_insn_mnem(ea)
        
        # Highlight important instructions
        marker = ""
        if mnem == "cmp":
            marker = " ← COMPARE"
        elif mnem.startswith("j") and mnem != "jmp":
            marker = " ← BRANCH"
        elif mnem == "call":
            marker = " ← CALL"
        elif "[" in disasm and "jmp" in disasm:
            marker = " ← JUMP TABLE!"
        
        f.write(f"{i:3d}. 0x{ea:X}: {disasm}{marker}\n")
        ea = idc.next_head(ea)
    
    f.write("\n")
    
    # Find all jump instructions
    f.write("=" * 80 + "\n")
    f.write("JUMP ANALYSIS\n")
    f.write("=" * 80 + "\n\n")
    
    jump_count = 0
    conditional_jumps = {}
    unconditional_jumps = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem.startswith("j"):
            jump_count += 1
            if mnem == "jmp":
                disasm = idc.generate_disasm_line(ea, 0)
                unconditional_jumps.append((ea, disasm))
            else:
                if mnem not in conditional_jumps:
                    conditional_jumps[mnem] = 0
                conditional_jumps[mnem] += 1
        ea = idc.next_head(ea)
    
    f.write(f"Total jumps: {jump_count}\n")
    f.write(f"Conditional jumps: {sum(conditional_jumps.values())}\n")
    f.write(f"Unconditional jumps: {len(unconditional_jumps)}\n\n")
    
    f.write("Conditional jump types:\n")
    for jmp_type, count in sorted(conditional_jumps.items(), key=lambda x: x[1], reverse=True):
        f.write(f"  {jmp_type}: {count}\n")
    
    f.write("\nUnconditional jumps (first 20):\n")
    for i, (jmp_ea, disasm) in enumerate(unconditional_jumps[:20]):
        f.write(f"  {i+1}. 0x{jmp_ea:X}: {disasm}\n")
    
    if len(unconditional_jumps) > 20:
        f.write(f"  ... and {len(unconditional_jumps) - 20} more\n")
    f.write("\n")
    
    # Find comparison patterns
    f.write("=" * 80 + "\n")
    f.write("COMPARISON PATTERNS\n")
    f.write("=" * 80 + "\n\n")
    
    cmp_values = []
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem == "cmp" or mnem == "test":
            disasm = idc.generate_disasm_line(ea, 0)
            # Try to extract the comparison value
            if ", " in disasm:
                parts = disasm.split(", ")
                if len(parts) == 2:
                    cmp_values.append((ea, mnem, disasm))
        ea = idc.next_head(ea)
    
    f.write(f"Total comparisons: {len(cmp_values)}\n\n")
    f.write("Comparison samples (first 30):\n")
    for i, (cmp_ea, mnem, disasm) in enumerate(cmp_values[:30]):
        f.write(f"  {i+1}. 0x{cmp_ea:X}: {disasm}\n")
    
    if len(cmp_values) > 30:
        f.write(f"  ... and {len(cmp_values) - 30} more\n")
    f.write("\n")
    
    # Find all function calls
    f.write("=" * 80 + "\n")
    f.write("FUNCTION CALLS\n")
    f.write("=" * 80 + "\n\n")
    
    call_targets = {}
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            if target:
                target_name = idc.get_func_name(target)
                if target_name:
                    if target_name not in call_targets:
                        call_targets[target_name] = []
                    call_targets[target_name].append(ea)
        ea = idc.next_head(ea)
    
    f.write(f"Unique functions called: {len(call_targets)}\n")
    f.write(f"Total call sites: {sum(len(v) for v in call_targets.values())}\n\n")
    
    f.write("Most frequently called (top 20):\n")
    sorted_calls = sorted(call_targets.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (func_name, call_sites) in enumerate(sorted_calls[:20]):
        f.write(f"  {i+1}. {func_name}: {len(call_sites)} times\n")
    
    if len(sorted_calls) > 20:
        f.write(f"  ... and {len(sorted_calls) - 20} more\n")
    f.write("\n")
    
    # Look for data structure access patterns
    f.write("=" * 80 + "\n")
    f.write("DATA STRUCTURE ACCESS PATTERNS\n")
    f.write("=" * 80 + "\n\n")
    
    # Find [si+offset] and [di+offset] patterns
    si_offsets = set()
    di_offsets = set()
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Extract [si+XX] patterns
        if "[si+" in disasm:
            try:
                offset = disasm.split("[si+")[1].split("]")[0].strip("h")
                if len(offset) <= 3:
                    si_offsets.add(offset)
            except:
                pass
        
        # Extract [di+XX] patterns
        if "[di+" in disasm:
            try:
                offset = disasm.split("[di+")[1].split("]")[0].strip("h")
                if len(offset) <= 3:
                    di_offsets.add(offset)
            except:
                pass
        
        ea = idc.next_head(ea)
    
    f.write(f"SI-based accesses: {len(si_offsets)} unique offsets\n")
    if si_offsets:
        sorted_si = sorted(si_offsets, key=lambda x: int(x, 16))
        f.write(f"  Offsets: {', '.join(['0x' + o for o in sorted_si[:20]])}\n")
    
    f.write(f"\nDI-based accesses: {len(di_offsets)} unique offsets\n")
    if di_offsets:
        sorted_di = sorted(di_offsets, key=lambda x: int(x, 16))
        f.write(f"  Offsets: {', '.join(['0x' + o for o in sorted_di[:20]])}\n")
    
    f.write("\n")
    
    # Try to identify basic blocks
    f.write("=" * 80 + "\n")
    f.write("STRUCTURE HYPOTHESIS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("Based on analysis:\n")
    f.write(f"  - {len(cmp_values)} comparisons suggest complex branching logic\n")
    f.write(f"  - {jump_count} jumps indicate state machine or dispatch table\n")
    f.write(f"  - {len(call_targets)} unique function calls suggest behavior routing\n")
    f.write(f"  - {len(si_offsets) + len(di_offsets)} unique offsets indicate entity structure access\n\n")
    
    if len(unconditional_jumps) > 20:
        f.write("LIKELY STRUCTURE: Large jump table dispatcher\n")
        f.write("  - Multiple unconditional jumps suggest computed jump table\n")
        f.write("  - Index likely based on entity type or behavior state\n")
    elif len(conditional_jumps) > 50:
        f.write("LIKELY STRUCTURE: Decision tree or cascading if-else\n")
        f.write("  - Many conditional jumps suggest sequential state checks\n")
        f.write("  - Pattern: compare → branch → handle → next\n")
    else:
        f.write("LIKELY STRUCTURE: Mixed dispatch with embedded logic\n")
        f.write("  - Combination of table dispatch and inline handling\n")
    
    f.write("\n")

print(f"Dispatcher structure analysis: {output_file}")
idc.qexit(0)
