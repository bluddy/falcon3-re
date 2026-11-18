import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\category_upper_bits.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Analyzing object_category upper bits (0x3FF mask)...")
idaapi.auto_wait()

print("="*70)
print("INVESTIGATING 0x3FF MASK IN ag_weapon_entity_initialize")
print("="*70 + "\n")

# The pattern is: AND CX, 3FFh then MOV [si+0Ch], CX
# This means object_category is 10 bits: bits 0-9

print("Mask 0x3FF = 0b0000001111111111 (10 bits)")
print("  Bits 0-4: Category value (0-19)")
print("  Bits 5-9: Unknown purpose (5 bits = 32 possible values)")
print()

# Search for all AND CX, 3FFh operations
print("Searching for 'AND CX, 3FFh' instructions...\n")

and_operations = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == "and":
            disasm = idc.generate_disasm_line(ea, 0)
            
            if "cx, 3FFh" in disasm or "cx, 0x3ff" in disasm.lower():
                func_name = idc.get_func_name(ea)
                and_operations.append((ea, func_name, disasm))
        
        ea = idc.next_head(ea, seg.end_ea)

print(f"Found {len(and_operations)} 'AND CX, 3FFh' operations:\n")

for addr, func, disasm in and_operations:
    print(f"0x{addr:05X} in {func}:")
    print(f"  {disasm}")
    
    # Show what happens before (where does CX come from?)
    print("  Before (CX source):")
    ctx_ea = addr - 30
    for i in range(8):
        ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
        if "cx" in ctx_disasm.lower():
            print(f"    0x{ctx_ea:05X}: {ctx_disasm} <-- CX")
        ctx_ea = idc.next_head(ctx_ea, addr)
    
    # Show what happens after (where does masked CX go?)
    print("  After (CX usage):")
    next_ea = idc.next_head(addr, addr + 50)
    for i in range(5):
        next_disasm = idc.generate_disasm_line(next_ea, 0)
        marker = ""
        if "[si+0Ch]" in next_disasm or "[di+0Ch]" in next_disasm:
            marker = " <-- CATEGORY WRITE"
        print(f"    0x{next_ea:05X}: {next_disasm}{marker}")
        next_ea = idc.next_head(next_ea, addr + 50)
    print()

print("\n" + "="*70)
print("ANALYZING fixed_vec3_accumulate_a RETURN VALUE")
print("="*70 + "\n")

# The function that returns CX
func_addr = idc.get_name_ea_simple("fixed_vec3_accumulate_a")

if func_addr == idc.BADADDR:
    print("Function 'fixed_vec3_accumulate_a' not found by name.")
    print("Searching for call pattern...\n")
    
    # Find it by looking for calls before AND CX, 3FFh
    if and_operations:
        call_site = and_operations[0][0] - 20
        
        # Search backwards for CALL
        for i in range(10):
            if idc.print_insn_mnem(call_site) == "call":
                target = idc.get_operand_value(call_site, 0)
                if target != idc.BADADDR:
                    func_addr = target
                    print(f"Found by backtracking from AND: 0x{func_addr:05X}")
                    break
            call_site = idc.prev_head(call_site)

if func_addr != idc.BADADDR:
    func = idaapi.get_func(func_addr)
    if func:
        func_start = func.start_ea
        func_end = func.end_ea
        func_size = func_end - func_start
        func_name = idc.get_func_name(func_addr)
        
        print(f"\nAnalyzing {func_name} @ 0x{func_start:05X}")
        print(f"Size: {func_size} bytes\n")
        
        # Disassemble looking for CX assignments
        print("Disassembly (looking for CX operations):\n")
        
        ea = func_start
        cx_ops = []
        
        while ea < func_end and ea != idc.BADADDR:
            disasm = idc.generate_disasm_line(ea, 0)
            mnem = idc.print_insn_mnem(ea)
            
            marker = ""
            if "cx" in disasm.lower():
                marker = " <-- CX"
                cx_ops.append((ea, disasm))
            
            if mnem == "ret" or mnem == "retf":
                marker = " <-- RETURN"
            
            print(f"0x{ea:05X}: {disasm:50s}{marker}")
            
            ea = idc.next_head(ea, func_end)
            
            if ea - func_start > 200:
                print("\n... (truncated, function too long)")
                break
        
        print(f"\n\nFound {len(cx_ops)} CX operations in function")
    else:
        print(f"Function @ 0x{func_addr:05X} not valid")
else:
    print("Could not locate fixed_vec3_accumulate_a")

print("\n" + "="*70)
print("SEARCHING FOR BIT MANIPULATION ON object_category")
print("="*70 + "\n")

# Look for operations that might access upper bits
# Patterns: SHR, SHL, AND with masks, etc. on [si+0Ch] value

print("Looking for SHR/SHL operations on loaded [si+0Ch] values...\n")

bit_ops = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        # Look for: MOV AX, [si+0Ch] followed by shift/mask operations
        if idc.print_insn_mnem(ea) == "mov":
            disasm = idc.generate_disasm_line(ea, 0)
            
            if ("[si+0Ch]" in disasm or "[di+0Ch]" in disasm) and ("ax," in disasm or "dx," in disasm):
                # Found a load of object_category
                # Check next few instructions for bit operations
                check_ea = idc.next_head(ea, seg.end_ea)
                
                for i in range(5):
                    check_mnem = idc.print_insn_mnem(check_ea)
                    check_disasm = idc.generate_disasm_line(check_ea, 0)
                    
                    if check_mnem in ["shr", "shl", "ror", "rol", "and", "or", "xor"]:
                        if any(reg in check_disasm for reg in ["ax", "al", "ah", "dx", "dl", "dh"]):
                            func_name = idc.get_func_name(ea)
                            bit_ops.append({
                                'load_addr': ea,
                                'load_disasm': disasm,
                                'op_addr': check_ea,
                                'op_disasm': check_disasm,
                                'func': func_name
                            })
                            break
                    
                    check_ea = idc.next_head(check_ea, seg.end_ea)
        
        ea = idc.next_head(ea, seg.end_ea)

print(f"Found {len(bit_ops)} potential bit manipulation sequences:\n")

for op in bit_ops[:20]:
    print(f"In {op['func']}:")
    print(f"  0x{op['load_addr']:05X}: {op['load_disasm']}")
    print(f"  0x{op['op_addr']:05X}: {op['op_disasm']}")
    
    # Show more context
    ctx_ea = op['op_addr']
    for i in range(3):
        ctx_ea = idc.next_head(ctx_ea, op['op_addr'] + 20)
        ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
        print(f"  0x{ctx_ea:05X}: {ctx_disasm}")
    print()

if len(bit_ops) > 20:
    print(f"... ({len(bit_ops) - 20} more)")

print("\n" + "="*70)
print("CHECKING DISPATCH TABLE INDEX CALCULATION")
print("="*70 + "\n")

# At dispatch @ 0x3C258: MOV DI, [si+0Ch]
# Then @ 0x3C25B: SHL DI, 1

print("Dispatch sequence @ 0x3C258-0x3C261:")
print("  0x3C258: mov di, [si+0Ch]     ; Load object_category (10 bits)")
print("  0x3C25B: shl di, 1             ; Multiply by 2 (word index)")
print("  0x3C25D: mov bx, table[di]     ; Load function offset")
print()
print("Question: Does SHL DI, 1 just multiply for word index,")
print("          or does it also shift out/mask upper bits?")
print()
print("Analysis:")
print("  If object_category = 0b00XXXCCCCC (X=upper bits, C=category)")
print("  After SHL DI, 1:")
print("  object_category = 0b0XXXCCCCC0")
print()
print("  Table has 20 entries (max index 19)")
print("  0-19 in binary: 0b00000 - 0b10011 (5 bits)")
print("  After shift: 0-38 (0b000000 - 0b100110)")
print()
print("  Upper 5 bits (bits 5-9 of original) are now bits 6-10 after shift")
print("  These would index beyond table unless masked!")
print()
print("Conclusion: Either:")
print("  1. Upper bits are always 0 (only lower 5 bits used)")
print("  2. Table is actually larger than 20 entries")
print("  3. Upper bits serve different purpose after entity created")

print("\n" + "="*70)
print("ANALYZING CATEGORY VALUE DISTRIBUTION")
print("="*70 + "\n")

# Check actual values written to [si+0Ch]
print("Checking what values are actually written to [si+0Ch]...\n")

# From ag_weapon_entity_initialize analysis, CX comes from fixed_vec3_accumulate_a
# masked to 0x3FF

print("From ag_weapon_entity_initialize pattern:")
print("  CALL fixed_vec3_accumulate_a  ; Returns unknown value in CX")
print("  AND  CX, 3FFh                  ; Mask to 10 bits")
print("  MOV  [si+0Ch], CX              ; Write to object_category")
print()
print("Hypothesis: fixed_vec3_accumulate_a returns some calculation result")
print("that happens to have category in lower bits plus other data in upper bits.")
print()
print("The mask 0x3FF preserves 10 bits, but only 5 bits (0-19) are used for")
print("dispatch table indexing. This suggests:")
print("  Bits 0-4: Category index (0-19)")
print("  Bits 5-9: Additional flags or sub-type (31 possible values)")
print()
print("To confirm, would need to trace actual CX values from fixed_vec3_accumulate_a.")

print("\nCategory upper bits analysis complete.")
output_file.close()
idc.qexit(0)
