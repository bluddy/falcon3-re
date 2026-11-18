import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\entity_functions.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Finding entity manipulation functions...")
idaapi.auto_wait()

print("=== STRATEGY ===")
print("Look for functions that:")
print("1. Reference entity slot array at 0x54AF:0x386F")
print("2. Use stride 0x5C (92 bytes)")
print("3. Have 'entity', 'slot', 'farobj' in name")
print()

# Find functions that reference the entity array base address
print("=== Functions Referencing Entity Array Base 0x386F ===\n")

entity_base = 0x386F
refs_to_base = []

# Search for the value 0x386F in code
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        
        while ea < seg_end:
            # Look for mov di, 386Fh or similar
            if idc.print_insn_mnem(ea) == "mov":
                try:
                    val = idc.get_operand_value(ea, 1)
                    if val == 0x386F:
                        func_name = idc.get_func_name(ea)
                        if func_name and func_name not in [f for _, f in refs_to_base]:
                            refs_to_base.append((ea, func_name))
                except:
                    pass
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(refs_to_base)} functions referencing 0x386F:\n")
for ea, fname in refs_to_base[:20]:
    print(f"  0x{ea:X}: {fname}")

# Search for functions using stride 0x5C
print("\n\n=== Functions Using Stride 0x5C (92 bytes) ===\n")

stride_refs = []
for seg_ea in idautils.Segments():
    seg_name = idc.get_segm_name(seg_ea)
    if "CODE" in seg_name or seg_name == "_TEXT":
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for mov bl, 5Ch (used in r12_farptr_load_thunk)
            if mnem == "mov":
                try:
                    if idc.print_operand(ea, 0) in ["bl", "cl"] and idc.get_operand_value(ea, 1) == 0x5C:
                        func_name = idc.get_func_name(ea)
                        if func_name:
                            stride_refs.append((ea, func_name))
                except:
                    pass
            
            # Look for imul with 0x5C
            elif mnem in ["imul", "mul"]:
                try:
                    # Check if 0x5C is involved
                    disasm = idc.generate_disasm_line(ea, 0)
                    if "5Ch" in disasm or "92" in disasm:
                        func_name = idc.get_func_name(ea)
                        if func_name:
                            stride_refs.append((ea, func_name))
                except:
                    pass
            
            ea = idc.next_head(ea, seg_end)

print(f"Found {len(stride_refs)} references to stride 0x5C:\n")

# Group by function
stride_funcs = {}
for ea, fname in stride_refs:
    if fname not in stride_funcs:
        stride_funcs[fname] = []
    stride_funcs[fname].append(ea)

for fname in sorted(stride_funcs.keys())[:15]:
    addrs = stride_funcs[fname]
    print(f"  {fname}: {len(addrs)} uses")
    for addr in addrs[:2]:
        print(f"    0x{addr:X}")

# Look at entity_physics_and_ai_update - it's huge and uses many fields
print("\n\n=== Analyzing entity_physics_and_ai_update @ 0x3D37F ===\n")
print("This 1319-byte function is the main entity update - analyzes many fields\n")

func_start = 0x3D37F
func_end = idc.find_func_end(func_start)
print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")

# Count instruction types
ea = func_start
mov_count = 0
cmp_count = 0
test_count = 0
call_count = 0
jump_count = 0

while ea < func_end:
    mnem = idc.print_insn_mnem(ea)
    if mnem in ["mov", "movb", "movw"]:
        mov_count += 1
    elif mnem == "cmp":
        cmp_count += 1
    elif mnem == "test":
        test_count += 1
    elif mnem in ["call", "lcall"]:
        call_count += 1
    elif mnem in ["jz", "jnz", "je", "jne", "jmp", "ja", "jb", "jl", "jg"]:
        jump_count += 1
    ea = idc.next_head(ea, func_end)

print(f"Instruction statistics:")
print(f"  MOV:  {mov_count}")
print(f"  CMP:  {cmp_count}")
print(f"  TEST: {test_count}")
print(f"  CALL: {call_count}")
print(f"  JUMP: {jump_count}")

# Find what it calls
print(f"\nFunctions called:\n")
ea = func_start
calls = []
while ea < func_end:
    if idc.print_insn_mnem(ea) in ["call", "lcall"]:
        target = idc.get_operand_value(ea, 0)
        target_name = idc.get_name(target)
        if target_name and target_name not in [name for _, name in calls]:
            calls.append((target, target_name))
    ea = idc.next_head(ea, func_end)

for target, name in calls[:20]:
    print(f"  {name}")

# Look at entity_slot_update_loop - coordinates entity processing
print("\n\n=== Analyzing entity_slot_update_loop @ 0x3C1BD ===\n")
print("This function loops through 16 entity slots (stride 0x5C)\n")

func_start = 0x3C1BD
func_end = idc.find_func_end(func_start)
print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")

# Show first 60 instructions
print("First 60 instructions:\n")
ea = func_start
count = 0
while ea < func_end and count < 60:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"  {disasm}")
    ea = idc.next_head(ea, func_end)
    count += 1

# Look for entity field initialization patterns
print("\n\n=== Looking for Entity Field Initialization ===\n")
print("Searching for functions that zero/initialize entity memory\n")

init_funcs = []
for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    if func_name and ('zero' in func_name.lower() or 'clear' in func_name.lower() or 'init' in func_name.lower()):
        # Check if it accesses entity-like offsets
        func_end = idc.find_func_end(func_ea)
        ea = func_ea
        has_entity_refs = False
        
        while ea < func_end:
            disasm = idc.generate_disasm_line(ea, 0)
            # Look for entity-like patterns
            if any(pattern in disasm for pattern in ['[si+', '[di+', '[bx+', '386Fh', '54AFh']):
                has_entity_refs = True
                break
            ea = idc.next_head(ea, func_end)
        
        if has_entity_refs:
            size = func_end - func_ea
            init_funcs.append((func_ea, func_name, size))

print(f"Found {len(init_funcs)} potential entity initialization functions:\n")
for addr, name, size in sorted(init_funcs, key=lambda x: x[2], reverse=True)[:15]:
    print(f"  0x{addr:X}: {name} ({size}B)")

print("\n\nEntity function discovery complete.")
output_file.close()
idc.qexit(0)
