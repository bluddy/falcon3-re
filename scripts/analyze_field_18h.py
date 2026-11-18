import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\field_18h_analysis.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Analyzing EntitySlotRecord field +0x18h...")
idaapi.auto_wait()

print("="*70)
print("SEARCHING FOR [si+18h] / [si+0x18] ACCESSES")
print("="*70 + "\n")

# Search for all accesses to field +0x18
field_18h_accesses = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    # Only search code segments
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for [si+18h], [di+18h], [bx+18h] patterns
        if ("[si+18h]" in disasm or "[di+18h]" in disasm or "[bx+18h]" in disasm or
            "[si+0x18]" in disasm.lower() or "[di+0x18]" in disasm.lower()):
            
            mnem = idc.print_insn_mnem(ea)
            func_name = idc.get_func_name(ea)
            
            field_18h_accesses.append({
                'addr': ea,
                'mnem': mnem,
                'disasm': disasm,
                'func': func_name
            })
        
        ea = idc.next_head(ea, seg.end_ea)

print(f"Found {len(field_18h_accesses)} accesses to field +0x18h\n")

# Group by function
by_function = {}
for access in field_18h_accesses:
    func = access['func']
    if func not in by_function:
        by_function[func] = []
    by_function[func].append(access)

print("="*70)
print("ACCESSES GROUPED BY FUNCTION")
print("="*70 + "\n")

# Sort by number of accesses
sorted_funcs = sorted(by_function.items(), key=lambda x: len(x[1]), reverse=True)

for func_name, accesses in sorted_funcs[:20]:
    print(f"\n{func_name} ({len(accesses)} accesses):")
    
    for access in accesses[:10]:  # Show first 10
        print(f"  0x{access['addr']:05X}: {access['disasm']}")
    
    if len(accesses) > 10:
        print(f"  ... ({len(accesses) - 10} more)")

print("\n" + "="*70)
print("CHECKING FOR 0xFFFF COMPARISONS")
print("="*70 + "\n")

# Find all CMP [X+18h], 0xFFFF patterns
ffff_comparisons = []

for access in field_18h_accesses:
    if access['mnem'] == 'cmp':
        disasm = access['disasm']
        if '0FFFFh' in disasm or 'FFFFh' in disasm:
            ffff_comparisons.append(access)

print(f"Found {len(ffff_comparisons)} comparisons with 0xFFFF:\n")

for cmp in ffff_comparisons[:20]:
    print(f"0x{cmp['addr']:05X} in {cmp['func']}:")
    print(f"  {cmp['disasm']}")
    
    # Show context (5 instructions after)
    print(f"  Context:")
    ctx_ea = cmp['addr']
    for i in range(8):
        ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
        marker = " <-- CMP HERE" if ctx_ea == cmp['addr'] else ""
        print(f"    0x{ctx_ea:05X}: {ctx_disasm}{marker}")
        ctx_ea = idc.next_head(ctx_ea, cmp['addr'] + 30)
    print()

print("\n" + "="*70)
print("ANALYZING WRITE OPERATIONS")
print("="*70 + "\n")

# Find all writes to [X+18h]
writes = [a for a in field_18h_accesses if a['mnem'] in ['mov', 'and', 'or', 'xor', 'add', 'sub']]

print(f"Found {len(writes)} write operations to field +0x18h:\n")

write_by_func = {}
for w in writes:
    func = w['func']
    if func not in write_by_func:
        write_by_func[func] = []
    write_by_func[func].append(w)

for func_name, func_writes in sorted(write_by_func.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    print(f"\n{func_name} ({len(func_writes)} writes):")
    
    for w in func_writes[:5]:
        print(f"  0x{w['addr']:05X}: {w['disasm']}")
    
    if len(func_writes) > 5:
        print(f"  ... ({len(func_writes) - 5} more)")

print("\n" + "="*70)
print("ANALYZING KEY CATEGORY ASSIGNMENT CONTEXTS")
print("="*70 + "\n")

# Look at the specific locations from aircraft category discovery
key_locations = [
    (0x3D404, "entity_physics_and_ai_update - Category 1 assignment"),
    (0x3D728, "entity_physics_and_ai_update - Category 0 reset"),
    (0x3F3ED, "ai_state_calculate_helper - Category 1 assignment"),
    (0x3F42D, "ai_state_calculate_helper - Category 2 assignment"),
]

for addr, description in key_locations:
    print(f"\n{description}:")
    print(f"Looking for [si+18h] check before 0x{addr:05X}...\n")
    
    # Search backwards for [si+18h] comparison
    search_ea = addr - 100
    found = False
    
    for i in range(50):
        disasm = idc.generate_disasm_line(search_ea, 0)
        
        if "[si+18h]" in disasm or "[si+0x18]" in disasm.lower():
            print(f"  Found @ 0x{search_ea:05X}: {disasm}")
            found = True
            
            # Show context
            ctx_ea = search_ea
            for j in range(10):
                ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
                
                marker = ""
                if ctx_ea == search_ea:
                    marker = " <-- FIELD +18h CHECK"
                elif ctx_ea == addr:
                    marker = " <-- CATEGORY ASSIGNMENT"
                
                print(f"    0x{ctx_ea:05X}: {ctx_disasm}{marker}")
                ctx_ea = idc.next_head(ctx_ea, addr + 5)
            print()
            break
        
        search_ea = idc.next_head(search_ea, addr)
    
    if not found:
        print(f"  No [si+18h] check found within 100 bytes before assignment")

print("\n" + "="*70)
print("FIELD VALUE ANALYSIS")
print("="*70 + "\n")

# Look for assignments of specific values to field +18h
print("Common values assigned to field +0x18h:\n")

value_assignments = []
for w in writes:
    if w['mnem'] == 'mov':
        disasm = w['disasm']
        
        # Extract the value being assigned
        # Look for patterns like "mov [si+18h], 0FFFFh" or "mov [si+18h], ax"
        if '0FFFFh' in disasm:
            value_assignments.append((w['addr'], w['func'], '0xFFFF'))
        elif '0' in disasm and 'FFFFh' not in disasm:
            value_assignments.append((w['addr'], w['func'], '0'))
        elif 'ax' in disasm or 'bx' in disasm or 'cx' in disasm or 'dx' in disasm:
            # Register assignment
            value_assignments.append((w['addr'], w['func'], 'register'))

print(f"Found {len(value_assignments)} MOV assignments:\n")

# Group by value
by_value = {}
for addr, func, value in value_assignments:
    if value not in by_value:
        by_value[value] = []
    by_value[value].append((addr, func))

for value, locs in by_value.items():
    print(f"\nValue {value}: {len(locs)} assignments")
    for addr, func in locs[:5]:
        print(f"  0x{addr:05X} in {func}")
    if len(locs) > 5:
        print(f"  ... ({len(locs) - 5} more)")

print("\nField +0x18h analysis complete.")
output_file.close()
idc.qexit(0)
