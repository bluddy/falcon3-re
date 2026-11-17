"""
Define damage bitfield enum in IDA and apply it to all entity[0xCA] references.
"""

import idc
import idaapi
import idautils

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\enum_creation_log.txt"

def create_damage_bitfield_enum():
    """Create enum for entity[0xCA] damage status bitfield."""
    
    log = []
    
    try:
        # Delete existing enum if it exists
        enum_id = idc.get_enum("DAMAGE_STATUS_FLAGS")
        if enum_id != idc.BADADDR:
            log.append(f"Deleting existing enum ID {enum_id}")
            idc.del_enum(enum_id)
        
        # Create new enum (bitfield type)
        enum_id = idc.add_enum(idc.BADADDR, "DAMAGE_STATUS_FLAGS", idaapi.hex_flag())
        
        if enum_id == idc.BADADDR:
            log.append("ERROR: Failed to create enum")
            return None, log
        
        log.append(f"Created enum DAMAGE_STATUS_FLAGS with ID {enum_id}")
        
        # Add enum members
        members = [
            ("DAMAGE_NAV", 0x0020, "Navigation system damaged (12 refs)"),
            ("DAMAGE_CRITICAL", 0x0200, "Critical damage flag - set when damage >= 4"),
            ("DAMAGE_FUEL", 0x2000, "Fuel system damaged"),
            ("DAMAGE_SEVERITY_MASK", 0xC000, "Damage severity level mask"),
            ("DAMAGE_SEVERITY_LIGHT", 0x4000, "Light damage (level 1)"),
            ("DAMAGE_SEVERITY_MODERATE", 0x8000, "Moderate damage (level 2)"),
            ("DAMAGE_SEVERITY_CRITICAL", 0xC000, "Critical damage (level 3)"),
            ("DAMAGE_HYDRAULICS", 0x0040, "Hydraulics damaged (medium confidence)"),
            ("DAMAGE_ELECTRICAL", 0x0080, "Electrical system damaged (medium confidence)"),
            ("DAMAGE_RADAR", 0x0100, "Radar damaged (medium confidence)"),
            ("STATUS_FLAG_0", 0x0001, "State flag 0"),
            ("STATUS_FLAG_1", 0x0002, "State flag 1"),
            ("STATUS_FLAG_2", 0x0004, "State flag 2"),
            ("STATUS_FLAG_3", 0x0008, "State flag 3"),
            ("STATUS_FLAG_4", 0x0010, "State flag 4"),
            ("STATUS_FLAG_10", 0x0400, "State flag 10"),
            ("STATUS_FLAG_11", 0x0800, "State flag 11"),
            ("STATUS_FLAG_12", 0x1000, "State flag 12"),
            ("STATUS_ALL_SUBSYSTEMS", 0x3FFF, "All status bits except severity"),
        ]
        
        for name, value, comment in members:
            result = idc.add_enum_member(enum_id, name, value, idc.BADADDR)
            if result == 0:
                log.append(f"  Added: {name} = 0x{value:04X}")
                # Set comment
                const_id = idc.get_enum_member_by_name(name)
                if const_id != idc.BADADDR:
                    idc.set_enum_cmt(const_id, comment, False)
            else:
                log.append(f"  ERROR adding {name}: result={result}")
        
        return enum_id, log
        
    except Exception as e:
        log.append(f"EXCEPTION: {e}")
        import traceback
        log.append(traceback.format_exc())
        return None, log

def apply_enum_to_all_0xCA_refs(enum_id):
    """Find all references to entity[0xCA] and apply enum to bitmask operands."""
    
    log = []
    count = 0
    
    try:
        # Search for all functions
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            ea = func.start_ea
            while ea < func.end_ea:
                disasm = idc.GetDisasm(ea)
                
                # Look for [di+0CAh], [si+0CAh], [bx+0CAh]
                if ("+0CAh]" in disasm or "+0CA]" in disasm):
                    mnem = idc.print_insn_mnem(ea)
                    
                    # For test/and/or/xor, operand 1 is the bitmask
                    if mnem in ["test", "and", "or", "xor"]:
                        # Check if operand 1 is immediate
                        if idc.get_operand_type(ea, 1) == idc.o_imm:
                            op_value = idc.get_operand_value(ea, 1)
                            
                            # Apply enum
                            result = idc.op_enum(ea, 1, enum_id, 0)
                            if result:
                                count += 1
                                log.append(f"Applied at {ea:08X}: {disasm}")
                
                ea = idc.next_head(ea, func.end_ea)
        
        log.append(f"\nTotal applied: {count}")
        return count, log
        
    except Exception as e:
        log.append(f"EXCEPTION: {e}")
        import traceback
        log.append(traceback.format_exc())
        return count, log

def add_entity_field_comments():
    """Add comments to entity offset accesses."""
    
    log = []
    count = 0
    
    try:
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            ea = func.start_ea
            while ea < func.end_ea:
                disasm = idc.GetDisasm(ea)
                
                # Check for damage field offsets
                if "+0C9h]" in disasm or "+0C9]" in disasm:
                    comment = "Entity damage accumulator (0-255)"
                    existing_cmt = idc.get_cmt(ea, 0)
                    if not existing_cmt or comment not in existing_cmt:
                        idc.set_cmt(ea, comment, 0)
                        count += 1
                
                elif "+0CAh]" in disasm or "+0CA]" in disasm:
                    comment = "Entity damage status bitfield (DAMAGE_STATUS_FLAGS)"
                    existing_cmt = idc.get_cmt(ea, 0)
                    if not existing_cmt or comment not in existing_cmt:
                        idc.set_cmt(ea, comment, 0)
                        count += 1
                
                ea = idc.next_head(ea, func.end_ea)
        
        log.append(f"Added {count} comments")
        return count, log
        
    except Exception as e:
        log.append(f"EXCEPTION: {e}")
        import traceback
        log.append(traceback.format_exc())
        return count, log

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        all_logs = []
        
        print("[1] Creating DAMAGE_STATUS_FLAGS enum...")
        enum_id, log = create_damage_bitfield_enum()
        all_logs.extend(log)
        
        for line in log:
            print(line)
        
        if not enum_id:
            print("\nFailed to create enum, aborting")
            with open(OUTPUT_FILE, 'w') as f:
                f.write('\n'.join(all_logs))
            idc.qexit(1)
            return
        
        print("\n[2] Applying enum to all entity[0xCA] bitmask references...")
        applied, log = apply_enum_to_all_0xCA_refs(enum_id)
        all_logs.extend(log)
        
        for line in log[-5:]:  # Show last 5
            print(line)
        print(f"\nApplied enum to {applied} locations")
        
        print("\n[3] Adding comments to entity damage field accesses...")
        comments, log = add_entity_field_comments()
        all_logs.extend(log)
        
        for line in log:
            print(line)
        
        # Save log
        with open(OUTPUT_FILE, 'w') as f:
            f.write('\n'.join(all_logs))
        
        print(f"\n✅ Done!")
        print(f"\nSummary:")
        print(f"  - Created enum: DAMAGE_STATUS_FLAGS")
        print(f"  - Applied to {applied} bitmask operations")
        print(f"  - Added {comments} field comments")
        print(f"  - Log saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
