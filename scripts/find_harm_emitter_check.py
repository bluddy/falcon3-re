"""
Find HARM radar emitter detection code.

AGM-88 HARM (0x19) needs to lock onto active enemy radar emitters.
Looking for:
- Entity field reads checking radar emission status
- HARM lock tone/indicator code
- References to weapon type 0x19 in lock context
"""

import idaapi
import idautils
import idc

def find_harm_type_refs():
    """Find all references to weapon type 0x19 (AGM-88 HARM)."""
    print("=" * 80)
    print("HARM WEAPON TYPE (0x19) REFERENCES")
    print("=" * 80)
    
    harm_refs = []
    
    # Search for immediate value 0x19 in code
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if seg_name != ".text":
            continue
            
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        ea = seg_start
        while ea < seg_end:
            insn = idaapi.insn_t()
            insn_len = idaapi.decode_insn(insn, ea)
            if insn_len == 0:
                ea += 1
                continue
            
            # Look for cmp/test/mov with 0x19
            if insn.itype in [idaapi.NN_cmp, idaapi.NN_test, idaapi.NN_mov]:
                for op in insn.ops:
                    if op.type == idaapi.o_imm and op.value == 0x19:
                        func = idaapi.get_func(ea)
                        func_name = idc.get_func_name(ea) if func else "no_func"
                        disasm = idc.generate_disasm_line(ea, 0)
                        harm_refs.append((ea, func_name, disasm))
                        break
            
            ea += insn_len
    
    print(f"\nFound {len(harm_refs)} references to 0x19:")
    for ea, func, disasm in harm_refs[:50]:
        print(f"  {ea:#08x} in {func}: {disasm}")
    
    return harm_refs

def analyze_entity_radar_fields():
    """Look for entity field accesses that could be radar emission status."""
    print("\n" + "=" * 80)
    print("ENTITY FIELD ACCESSES (potential radar_emitter_active)")
    print("=" * 80)
    
    # Common entity base registers: BX, SI, DI
    # EntitySlotRecord is 92-175 bytes
    # Likely fields for radar emission:
    # - Boolean flags (byte at various offsets)
    # - Could be near other combat-related fields
    
    # Search for patterns like:
    # cmp byte ptr [bx+0xNN], 0
    # test byte ptr [si+0xNN], 0xFF
    # mov al, [di+0xNN]
    
    field_accesses = {}
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if seg_name != ".text":
            continue
            
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        ea = seg_start
        while ea < seg_end:
            insn = idaapi.insn_t()
            insn_len = idaapi.decode_insn(insn, ea)
            if insn_len == 0:
                ea += 1
                continue
            
            # Look for [reg+offset] patterns
            for i, op in enumerate(insn.ops):
                if op.type == idaapi.o_displ:  # [base+disp]
                    base_reg = op.reg
                    offset = op.addr
                    
                    # Filter for entity-like base registers and reasonable offsets
                    if base_reg in [idaapi.R_bx, idaapi.R_si, idaapi.R_di] and 0 <= offset < 200:
                        key = (base_reg, offset)
                        if key not in field_accesses:
                            field_accesses[key] = []
                        
                        func = idaapi.get_func(ea)
                        func_name = idc.get_func_name(ea) if func else "no_func"
                        disasm = idc.generate_disasm_line(ea, 0)
                        field_accesses[key].append((ea, func_name, disasm))
            
            ea += insn_len
    
    # Sort by frequency
    sorted_fields = sorted(field_accesses.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"\nTop 30 entity field accesses by frequency:")
    print("(Looking for potential radar_emitter_active field)")
    print()
    
    reg_names = {idaapi.R_bx: "bx", idaapi.R_si: "si", idaapi.R_di: "di"}
    
    for (reg, offset), accesses in sorted_fields[:30]:
        reg_name = reg_names.get(reg, f"reg{reg}")
        print(f"\n[{reg_name}+{offset:#x}] - {len(accesses)} accesses:")
        
        # Show first 5 examples
        for ea, func, disasm in accesses[:5]:
            print(f"  {ea:#08x} in {func}: {disasm}")
        
        if len(accesses) > 5:
            print(f"  ... and {len(accesses) - 5} more")

def find_harm_lock_functions():
    """Search for functions that might handle HARM lock logic."""
    print("\n" + "=" * 80)
    print("SEARCHING FOR HARM LOCK FUNCTIONS")
    print("=" * 80)
    
    # Look for functions near farobj_utility_1819 (0x4C3C7)
    harm_handler = 0x4C3C7
    
    print(f"\nFunctions near farobj_utility_1819 @ {harm_handler:#x}:")
    
    # Scan ±4KB around handler
    start = harm_handler - 0x1000
    end = harm_handler + 0x1000
    
    funcs_found = []
    for func_ea in idautils.Functions(start, end):
        func_name = idc.get_func_name(func_ea)
        func_size = idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
        funcs_found.append((func_ea, func_name, func_size))
    
    for func_ea, func_name, func_size in sorted(funcs_found):
        print(f"  {func_ea:#08x}: {func_name} ({func_size} bytes)")
        
        # Quick scan for entity field accesses and 0x19 checks
        has_harm_check = False
        entity_fields = set()
        
        for insn_ea in idautils.FuncItems(func_ea):
            insn = idaapi.insn_t()
            if idaapi.decode_insn(insn, insn_ea) == 0:
                continue
            
            # Check for 0x19
            for op in insn.ops:
                if op.type == idaapi.o_imm and op.value == 0x19:
                    has_harm_check = True
            
            # Check for entity field access
            for op in insn.ops:
                if op.type == idaapi.o_displ and op.reg in [idaapi.R_bx, idaapi.R_si, idaapi.R_di]:
                    if 0 <= op.addr < 200:
                        entity_fields.add(op.addr)
        
        if has_harm_check:
            print(f"    -> Contains HARM type check (0x19)")
        if entity_fields:
            fields_str = ", ".join(f"{f:#x}" for f in sorted(entity_fields)[:10])
            print(f"    -> Entity fields accessed: {fields_str}")

def main():
    print("Finding HARM radar emitter detection code...")
    print()
    
    harm_refs = find_harm_type_refs()
    analyze_entity_radar_fields()
    find_harm_lock_functions()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Examine functions with HARM type checks")
    print("2. Look for entity field reads in HARM context")
    print("3. Find HARM lock tone/indicator code")
    print("4. Identify radar_emitter_active field offset")

if __name__ == "__main__":
    idaapi.auto_wait()  # CRITICAL: Wait for auto-analysis
    main()
    idc.qexit(0)  # CRITICAL: Exit explicitly to prevent hang
