"""
Analyze the massive ai_entity_behavior_dispatcher function (2580 bytes).
This is likely a central dispatch table for AI behaviors.
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\ai_dispatcher_analysis.txt"

dispatcher_addr = 0x03CE92

with open(output_file, 'w') as f:
    f.write("=== AI Entity Behavior Dispatcher Analysis ===\n\n")
    f.write("ai_entity_behavior_dispatcher @ 0x3CE92\n")
    f.write("Size: 2580 bytes (2.5KB) - MASSIVE FUNCTION\n\n")
    
    func = idaapi.get_func(dispatcher_addr)
    if not func:
        f.write("ERROR: Function not found!\n")
        idc.qexit(1)
        return
    
    size = func.end_ea - func.start_ea
    f.write(f"Actual size: {size} bytes\n")
    f.write(f"Address range: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n\n")
    
    # Get callers
    f.write("=" * 80 + "\n")
    f.write("CALLERS:\n")
    f.write("=" * 80 + "\n\n")
    
    callers = []
    for xref in idautils.XrefsTo(func.start_ea):
        if xref.type in [idc.fl_CF, idc.fl_CN]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                callers.append((xref.frm, caller_name))
    
    f.write(f"Called by {len(set(callers))} functions:\n")
    for i, (call_addr, caller_name) in enumerate(sorted(set(callers), key=lambda x: x[1])[:20]):
        f.write(f"  {i+1}. {caller_name} @ 0x{call_addr:X}\n")
    f.write("\n")
    
    # Analyze instruction patterns
    f.write("=" * 80 + "\n")
    f.write("INSTRUCTION ANALYSIS:\n")
    f.write("=" * 80 + "\n\n")
    
    cmp_count = 0
    test_count = 0
    jmp_count = 0
    call_count = 0
    mov_count = 0
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem == "cmp":
            cmp_count += 1
        elif mnem == "test":
            test_count += 1
        elif mnem.startswith("j"):
            jmp_count += 1
        elif mnem == "call":
            call_count += 1
        elif mnem == "mov":
            mov_count += 1
        ea = idc.next_head(ea)
    
    f.write(f"CMP instructions: {cmp_count}\n")
    f.write(f"TEST instructions: {test_count}\n")
    f.write(f"Jump instructions: {jmp_count}\n")
    f.write(f"CALL instructions: {call_count}\n")
    f.write(f"MOV instructions: {mov_count}\n")
    f.write(f"Total branches: {cmp_count + test_count + jmp_count}\n")
    f.write(f"Branch density: {(cmp_count + test_count + jmp_count) / size * 100:.1f}%\n\n")
    
    # Find dispatch patterns
    f.write("=" * 80 + "\n")
    f.write("DISPATCH PATTERN ANALYSIS:\n")
    f.write("=" * 80 + "\n\n")
    
    # Look for jump tables
    ea = func.start_ea
    jump_tables = []
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        if "jmp" in disasm and "[" in disasm:
            jump_tables.append((ea, disasm))
        ea = idc.next_head(ea)
    
    if jump_tables:
        f.write(f"Jump table instructions found: {len(jump_tables)}\n")
        for jmp_ea, disasm in jump_tables[:10]:
            f.write(f"  0x{jmp_ea:X}: {disasm}\n")
        f.write("\n")
    
    # Find all unique functions called
    f.write("=" * 80 + "\n")
    f.write("CALLED FUNCTIONS:\n")
    f.write("=" * 80 + "\n\n")
    
    called_funcs = {}
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            target = idc.get_operand_value(ea, 0)
            if target:
                target_name = idc.get_func_name(target)
                if target_name:
                    if target_name not in called_funcs:
                        called_funcs[target_name] = 0
                    called_funcs[target_name] += 1
        ea = idc.next_head(ea)
    
    f.write(f"Calls {len(called_funcs)} unique functions\n")
    f.write(f"Total call sites: {sum(called_funcs.values())}\n\n")
    
    f.write("Most frequently called:\n")
    for i, (func_name, count) in enumerate(sorted(called_funcs.items(), key=lambda x: x[1], reverse=True)[:15]):
        f.write(f"  {i+1}. {func_name}: {count} times\n")
    f.write("\n")
    
    # Look for behavior flag tests
    f.write("=" * 80 + "\n")
    f.write("BEHAVIOR FLAG TESTS:\n")
    f.write("=" * 80 + "\n\n")
    
    ea = func.start_ea
    flag_tests = []
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        if "[si+0Bh]" in disasm or "[di+0Bh]" in disasm:
            flag_tests.append((ea, disasm))
        ea = idc.next_head(ea)
    
    if flag_tests:
        f.write(f"Behavior flag accesses: {len(flag_tests)}\n\n")
        for test_ea, disasm in flag_tests[:15]:
            f.write(f"  0x{test_ea:X}: {disasm}\n")
        if len(flag_tests) > 15:
            f.write(f"  ... and {len(flag_tests) - 15} more\n")
    else:
        f.write("No direct behavior flag tests found\n")
    f.write("\n")
    
    # Look for RFM data access
    f.write("=" * 80 + "\n")
    f.write("RFM DATA ACCESS:\n")
    f.write("=" * 80 + "\n\n")
    
    ea = func.start_ea
    rfm_refs = []
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        if "word_3B830" in disasm or "3B830" in disasm:
            rfm_refs.append((ea, disasm))
        ea = idc.next_head(ea)
    
    if rfm_refs:
        f.write(f"RFM data references: {len(rfm_refs)}\n\n")
        for rfm_ea, disasm in rfm_refs:
            f.write(f"  0x{rfm_ea:X}: {disasm}\n")
    else:
        f.write("No RFM data access found\n")
    f.write("\n")
    
    # Sample the first 100 instructions to understand structure
    f.write("=" * 80 + "\n")
    f.write("FUNCTION ENTRY (first 40 instructions):\n")
    f.write("=" * 80 + "\n\n")
    
    ea = func.start_ea
    for i in range(40):
        disasm = idc.generate_disasm_line(ea, 0)
        if disasm:
            f.write(f"0x{ea:X}: {disasm}\n")
        ea = idc.next_head(ea)
        if ea >= func.end_ea:
            break
    
    f.write("\n")

print(f"AI dispatcher analysis: {output_file}")
idc.qexit(0)
