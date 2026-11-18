import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\category_assignment.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Finding object_category assignment locations...")
idaapi.auto_wait()

print("="*70)
print("SEARCHING FOR MOV [SI+0Ch], X PATTERNS")
print("="*70 + "\n")

# Search for instructions that write to [si+0Ch] or [di+0Ch]
# Pattern: MOV [SI+0Ch], immediate or register

category_writes = []

# Search through code segments
for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    # Only search code segments
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    print(f"Searching segment {seg_name} (0x{seg.start_ea:X}-0x{seg.end_ea:X})...")
    
    ea = seg.start_ea
    count = 0
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        # Get mnemonic
        mnem = idc.print_insn_mnem(ea)
        
        # Look for MOV instructions
        if mnem == "mov":
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Check for writes to [si+0Ch], [di+0Ch], [bx+0Ch], etc
            if ("[si+0Ch]" in disasm or "[di+0Ch]" in disasm or 
                "[bx+0Ch]" in disasm or "[bp+si+0Ch]" in disasm or
                "[si+0xc]" in disasm.lower() or "[di+0xc]" in disasm.lower()):
                
                # Get source operand
                op1 = idc.print_operand(ea, 1)
                
                # Get function name
                func = idaapi.get_func(ea)
                func_name = idc.get_func_name(ea) if func else "no_function"
                
                # Get instruction bytes
                size = idc.get_item_size(ea)
                byte_list = [idc.get_wide_byte(ea + i) for i in range(min(size, 6))]
                byte_str = " ".join(f"{b:02X}" for b in byte_list)
                
                category_writes.append({
                    'addr': ea,
                    'disasm': disasm,
                    'source': op1,
                    'func': func_name,
                    'bytes': byte_str
                })
                
                count += 1
        
        ea = idc.next_head(ea, seg.end_ea)
    
    print(f"  Found {count} writes to [X+0Ch] in {seg_name}\n")

print(f"\nTotal writes found: {len(category_writes)}\n")

print("="*70)
print("CATEGORY ASSIGNMENT LOCATIONS")
print("="*70 + "\n")

print(f"{'Address':<10} {'Function':<40} {'Source':<15} {'Instruction'}")
print("-"*100)

for entry in category_writes:
    addr = entry['addr']
    func = entry['func'][:38]
    source = entry['source'][:13]
    disasm = entry['disasm'][:60]
    
    print(f"0x{addr:05X}   {func:<40} {source:<15} {disasm}")

print("\n" + "="*70)
print("DETAILED ANALYSIS OF KEY LOCATIONS")
print("="*70 + "\n")

# Group by function
by_function = {}
for entry in category_writes:
    func = entry['func']
    if func not in by_function:
        by_function[func] = []
    by_function[func].append(entry)

# Focus on functions with multiple writes (entity initializers)
print("Functions with multiple category writes:\n")

for func_name, entries in sorted(by_function.items(), key=lambda x: len(x[1]), reverse=True):
    if len(entries) >= 3:
        print(f"\n{func_name} ({len(entries)} writes):")
        
        # Get function bounds
        if entries[0]['addr']:
            func_ea = idc.get_func_attr(entries[0]['addr'], idc.FUNCATTR_START)
            if func_ea != idc.BADADDR:
                func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
                func_size = func_end - func_ea
                print(f"  Address: 0x{func_ea:05X}-0x{func_end:05X} ({func_size} bytes)")
        
        print(f"  Writes:")
        for entry in entries:
            print(f"    0x{entry['addr']:05X}: {entry['disasm']}")
        
        # Show context around first write
        print(f"\n  Context around first write @ 0x{entries[0]['addr']:05X}:")
        ctx_ea = entries[0]['addr'] - 20
        for i in range(10):
            ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
            marker = " <-- CATEGORY WRITE" if ctx_ea == entries[0]['addr'] else ""
            print(f"    0x{ctx_ea:05X}: {ctx_disasm}{marker}")
            ctx_ea = idc.next_head(ctx_ea, entries[0]['addr'] + 20)

# ============================================================================
# SEARCH FOR SPECIFIC PATTERNS
# ============================================================================

print("\n" + "="*70)
print("SEARCHING FOR AIRCRAFT SPAWN PATTERNS")
print("="*70 + "\n")

# Look for entity_slot_create calls followed by category writes
print("Functions that call entity_slot_create (0x2EBCD):\n")

entity_create_callers = []
for xref in idautils.XrefsTo(0x2EBCD):
    caller_addr = xref.frm
    caller_func = idc.get_func_name(caller_addr)
    
    # Check if this function also writes to [X+0Ch]
    has_category_write = any(e['func'] == caller_func for e in category_writes)
    
    if has_category_write:
        print(f"✓ 0x{caller_addr:05X} in {caller_func} - writes category!")
        entity_create_callers.append(caller_func)
    else:
        print(f"  0x{caller_addr:05X} in {caller_func}")

print(f"\nFunctions that both call entity_slot_create AND write category: {len(entity_create_callers)}")

# ============================================================================
# SEARCH IN ag_weapon_entity_initialize
# ============================================================================

print("\n" + "="*70)
print("ANALYZING ag_weapon_entity_initialize @ 0x4C3C7")
print("="*70 + "\n")

ag_weapon_func = 0x4C3C7
ag_writes = [e for e in category_writes if e['func'] == idc.get_func_name(ag_weapon_func)]

print(f"Found {len(ag_writes)} writes to [si+0Ch] in ag_weapon_entity_initialize\n")

if ag_writes:
    print("All category writes in function:\n")
    for i, entry in enumerate(ag_writes, 1):
        print(f"{i}. 0x{entry['addr']:05X}: {entry['disasm']}")
        print(f"   Bytes: {entry['bytes']}")
        print(f"   Source: {entry['source']}")
        
        # Show what CX contains before this write
        print(f"   Context (looking for CX assignment):")
        ctx_ea = entry['addr'] - 30
        for j in range(8):
            ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
            if "cx" in ctx_disasm.lower():
                print(f"     0x{ctx_ea:05X}: {ctx_disasm} <-- CX USAGE")
            ctx_ea = idc.next_head(ctx_ea, entry['addr'])
        print()

print("\nCategory assignment search complete.")
output_file.close()
idc.qexit(0)
