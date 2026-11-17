"""
Find subsystem storage by tracing entity fields [di+0C9h] and [di+0CAh].

BREAKTHROUGH: damage_handler accesses:
- [di+0C9h] - Damage accumulation byte
- [di+0CAh] - Status flags (word with bits for different subsystems?)

Also found: table_dword_set writes to DS:0x7B0E:0x3052/3054 area
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\subsystem_storage_found.json"

def analyze_entity_damage_fields():
    """Analyze entity fields 0xC9 and 0xCA (damage fields)."""
    # Search for all references to [di+0C9h], [di+0CAh], [si+0C9h], etc.
    
    damage_field_refs = {
        "0xC9": [],  # Damage accumulation
        "0xCA": []   # Status flags
    }
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.GetDisasm(ea)
            
            # Look for [di+0C9h] or [si+0C9h]
            if "+0C9h]" in disasm or "+0CA]" in disasm or "+0CAh]" in disasm or "+0C9]" in disasm:
                func_name = idc.get_func_name(func_ea)
                
                # Determine field
                field = "0xCA" if "+0CA" in disasm else "0xC9"
                
                context = []
                ctx_ea = max(ea - 15, func.start_ea)
                ctx_end = min(ea + 15, func.end_ea)
                
                while ctx_ea < ctx_end:
                    context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                    ctx_ea = idc.next_head(ctx_ea, ctx_end)
                
                damage_field_refs[field].append({
                    "function": func_name,
                    "address": hex(ea),
                    "instruction": disasm,
                    "context": context
                })
            
            ea = idc.next_head(ea, func.end_ea)
    
    return damage_field_refs

def analyze_status_flags_0xCA():
    """Analyze [di+0CAh] field - likely bitfield for subsystem damage."""
    # From damage_handler: test word ptr [di+0CAh], 40h, 80h, 200h, 0C000h
    # These are bitmasks for different subsystems
    
    func_addr = 0x4113C  # flight_physics_integration_engine
    func = idaapi.get_func(func_addr)
    if not func:
        return {"error": "function not found"}
    
    bitmasks_found = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        
        # Look for test/and/or operations on [di+0CAh]
        if ("+0CAh]" in disasm or "+0CA]" in disasm) and any(x in idc.print_insn_mnem(ea) for x in ["test", "and", "or", "xor"]):
            # Get the bitmask
            op2 = idc.print_operand(ea, 1)
            
            bitmasks_found.append({
                "offset": hex(ea - func.start_ea),
                "instruction": disasm,
                "bitmask": op2,
                "address": hex(ea)
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return bitmasks_found

def find_op_dispatch_table():
    """Find the op_dispatch_table function pointer table."""
    # From op_dispatch: call cs:op_dispatch_table[bx]
    
    # Search for "op_dispatch_table" symbol
    table_addr = idc.get_name_ea_simple("op_dispatch_table")
    if table_addr == idc.BADADDR:
        return {"error": "op_dispatch_table not found"}
    
    # Read the table (series of far pointers)
    entries = []
    ea = table_addr
    
    for i in range(20):  # Read up to 20 entries
        # Read dword (segment:offset far pointer)
        offset = idc.get_wide_word(ea)
        segment = idc.get_wide_word(ea + 2)
        
        if offset == 0 and segment == 0:
            break  # End of table
        
        # Calculate linear address
        linear = (segment << 4) + offset
        
        # Get function name if exists
        func_name = idc.get_func_name(linear)
        if not func_name:
            func_name = f"sub_{linear:X}"
        
        entries.append({
            "index": i,
            "offset": hex(offset),
            "segment": hex(segment),
            "linear": hex(linear),
            "function": func_name
        })
        
        ea += 4  # Next entry (dword)
    
    return {
        "address": hex(table_addr),
        "entries": entries
    }

def analyze_damage_table_at_7b0e():
    """Analyze damage storage at DS:0x7B0E:0x3052."""
    # table_dword_set writes to [bx+3052h] and [bx+3054h]
    # BX is scaled by 4 (shl bx, 1; shl bx, 1)
    # So: bx=0 → 0x3052, bx=1 → 0x3056, bx=2 → 0x305A, etc.
    
    # This is an array of dwords (8 bytes per entry)
    # Number of entries = ?
    
    table_info = {
        "segment": "0x7B0E",
        "base_offset": "0x3052",
        "entry_size": 8,  # 2 dwords
        "description": "Damage state table indexed by entity/subsystem ID"
    }
    
    # Try to find references to this area
    linear_base = (0x7B0E << 4) + 0x3052
    
    # Search for xrefs to this address
    xrefs = list(idautils.XrefsTo(linear_base, 0))
    
    table_info["linear_address"] = hex(linear_base)
    table_info["xref_count"] = len(xrefs)
    table_info["xrefs"] = [hex(x.frm) for x in xrefs[:10]]
    
    return table_info

def find_subsystem_names():
    """Try to find subsystem name strings and map to indices."""
    # We know: ENG, HYD, FUEL, ELEC, RDR, ECM
    # Search for these strings
    
    subsystem_strings = {}
    known_subsystems = ["ENG", "HYD", "FUEL", "ELEC", "RDR", "RADAR", "ECM", "RWR", 
                        "GEAR", "FLAP", "FCC", "FC", "BRAKE", "AVION"]
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            if idc.is_strlit(idc.get_full_flags(head)):
                str_val = idc.get_strlit_contents(head)
                if str_val:
                    str_val_decoded = str_val.decode('ascii', errors='ignore').upper()
                    
                    # Check if this is a subsystem abbreviation
                    for subsys in known_subsystems:
                        if subsys in str_val_decoded:
                            # Get xrefs to this string
                            xrefs = list(idautils.XrefsTo(head, 0))
                            
                            if head not in subsystem_strings:
                                subsystem_strings[head] = {
                                    "string": str_val_decoded[:20],
                                    "address": hex(head),
                                    "xref_count": len(xrefs),
                                    "used_by": [idc.get_func_name(x.frm) for x in xrefs[:5] if idc.get_func_name(x.frm)]
                                }
    
    return list(subsystem_strings.values())[:20]

def main():
    try:
        idaapi.auto_wait()
        
        result = {
            "breakthrough": "Found damage fields at entity offsets 0xC9 and 0xCA",
            "entity_damage_fields": analyze_entity_damage_fields(),
            "status_flags_bitmasks": analyze_status_flags_0xCA(),
            "op_dispatch_table": find_op_dispatch_table(),
            "damage_table_7b0e": analyze_damage_table_at_7b0e(),
            "subsystem_name_strings": find_subsystem_names()
        }
        
        # Summary
        result["summary"] = {
            "damage_0xC9_refs": len(result["entity_damage_fields"]["0xC9"]),
            "status_0xCA_refs": len(result["entity_damage_fields"]["0xCA"]),
            "bitmasks_found": len(result["status_flags_bitmasks"]),
            "dispatch_entries": len(result["op_dispatch_table"].get("entries", [])),
            "subsystem_strings": len(result["subsystem_name_strings"])
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Damage field 0xC9: {result['summary']['damage_0xC9_refs']} references")
        print(f"Status field 0xCA: {result['summary']['status_0xCA_refs']} references")
        print(f"Bitmasks found: {result['summary']['bitmasks_found']}")
        print(f"Dispatch table: {result['summary']['dispatch_entries']} entries")
        print(f"Subsystem strings: {result['summary']['subsystem_strings']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
