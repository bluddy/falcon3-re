import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\aircraft_spawn.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Finding aircraft entity spawn functions...")
idaapi.auto_wait()

print("="*70)
print("SEARCHING FOR CATEGORY 1/2/3 ASSIGNMENTS")
print("="*70 + "\n")

# Search for MOV [X+0Ch], 1/2/3 patterns
aircraft_categories = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    # Only search code segments
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == "mov":
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for [X+0Ch], immediate value 1/2/3
            if ("[si+0Ch]" in disasm or "[di+0Ch]" in disasm or "[bx+0Ch]" in disasm):
                # Check if source is 1, 2, or 3
                op1 = idc.print_operand(ea, 1)
                
                if op1 in ["1", "2", "3", "0001h", "0002h", "0003h"]:
                    func_name = idc.get_func_name(ea)
                    
                    aircraft_categories.append({
                        'addr': ea,
                        'category': op1,
                        'disasm': disasm,
                        'func': func_name
                    })
                    
                    print(f"Found: 0x{ea:05X} in {func_name}")
                    print(f"  {disasm}")
                    print(f"  Category: {op1}\n")
        
        ea = idc.next_head(ea, seg.end_ea)

print(f"Total aircraft category assignments found: {len(aircraft_categories)}\n")

if not aircraft_categories:
    print("No direct assignments of 1/2/3 to [X+0Ch] found.")
    print("Categories might be set via register or computed value.\n")
    
    print("="*70)
    print("ALTERNATIVE: SEARCH FOR entity_slot_create CALLERS")
    print("="*70 + "\n")
    
    # Look for entity_slot_create @ 0x2EBCD
    print("Functions that call entity_slot_create (0x2EBCD):\n")
    
    callers = []
    for xref in idautils.XrefsTo(0x2EBCD):
        caller_addr = xref.frm
        caller_func = idc.get_func_name(caller_addr)
        
        # Get function name and check if it looks aircraft-related
        is_aircraft = any(keyword in caller_func.lower() for keyword in 
                         ['aircraft', 'ai', 'flight', 'mig', 'f16', 'plane'])
        
        marker = " <-- AIRCRAFT?" if is_aircraft else ""
        print(f"  0x{caller_addr:05X} in {caller_func}{marker}")
        
        if is_aircraft:
            callers.append((caller_addr, caller_func))
    
    print(f"\nPotential aircraft spawners: {len(callers)}\n")
    
    # Analyze top candidates
    for caller_addr, caller_func in callers[:5]:
        print(f"\n{'-'*70}")
        print(f"Analyzing: {caller_func} @ 0x{caller_addr:05X}")
        print(f"{'-'*70}\n")
        
        # Get function bounds
        func_ea = idc.get_func_attr(caller_addr, idc.FUNCATTR_START)
        if func_ea == idc.BADADDR:
            continue
        
        func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
        
        # Look for [X+0Ch] writes in this function
        ea = func_ea
        writes = []
        
        while ea < func_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem == "mov":
                disasm = idc.generate_disasm_line(ea, 0)
                if ("[si+0Ch]" in disasm or "[di+0Ch]" in disasm or "[bx+0Ch]" in disasm):
                    writes.append((ea, disasm))
            ea = idc.next_head(ea, func_end)
        
        if writes:
            print(f"  Found {len(writes)} writes to [X+0Ch]:\n")
            for addr, disasm in writes:
                print(f"    0x{addr:05X}: {disasm}")
                
                # Show context
                ctx_ea = addr - 20
                print(f"      Context:")
                for i in range(6):
                    ctx_disasm = idc.generate_disasm_line(ctx_ea, 0)
                    marker = " <-- HERE" if ctx_ea == addr else ""
                    print(f"        0x{ctx_ea:05X}: {ctx_disasm}{marker}")
                    ctx_ea = idc.next_head(ctx_ea, addr + 5)
                print()

print("\n" + "="*70)
print("SEARCHING FOR AI LEVEL/TYPE DECISIONS")
print("="*70 + "\n")

# Search for code that might decide AI level based on enemy type
# Look for comparisons followed by category assignment

print("Looking for patterns: CMP X, Y followed by MOV [si+0Ch], Z\n")

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    seg_name = idaapi.get_segm_name(seg)
    
    if not seg_name.startswith("R") or "44AF" in seg_name:
        continue
    
    ea = seg.start_ea
    
    while ea < seg.end_ea and ea != idc.BADADDR:
        mnem = idc.print_insn_mnem(ea)
        
        # Look for CMP followed by conditional jump, then MOV [X+0Ch]
        if mnem == "cmp":
            # Check next few instructions
            next_ea = idc.next_head(ea, seg.end_ea)
            
            # Look ahead up to 10 instructions
            for i in range(10):
                check_ea = next_ea
                for j in range(i):
                    check_ea = idc.next_head(check_ea, seg.end_ea)
                
                check_disasm = idc.generate_disasm_line(check_ea, 0)
                
                if "[si+0Ch]" in check_disasm or "[di+0Ch]" in check_disasm:
                    # Found potential pattern
                    func_name = idc.get_func_name(ea)
                    
                    print(f"Pattern found in {func_name}:")
                    
                    # Show instruction sequence
                    seq_ea = ea
                    for k in range(i+2):
                        seq_disasm = idc.generate_disasm_line(seq_ea, 0)
                        marker = " <-- CATEGORY WRITE" if seq_ea == check_ea else ""
                        print(f"  0x{seq_ea:05X}: {seq_disasm}{marker}")
                        seq_ea = idc.next_head(seq_ea, check_ea + 5)
                    print()
                    break
        
        ea = idc.next_head(ea, seg.end_ea)

print("\nAircraft spawn search complete.")
output_file.close()
idc.qexit(0)
