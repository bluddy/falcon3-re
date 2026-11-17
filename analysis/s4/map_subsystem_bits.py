"""
Map subsystem bits in entity damage bitfield [di+0xCA].

GOAL: Identify which bits correspond to which subsystems (ENG, HYD, FUEL, etc.)

STRATEGY:
1. Scan for test/and/or instructions on [di+0CAh] or [si+0CAh]
2. Extract the bitmask values
3. Look for nearby subsystem name strings
4. Cross-reference with fault panel display functions

Known bits so far:
- Bit 5 (0x0020): Navigation system
- Bit 6 (0x0040): Unknown system 1
- Bit 7 (0x0080): Unknown system 2
- Bit 8 (0x0100): Overlay system
- Bit 9 (0x0200): Critical damage flag
- Bit 13 (0x2000): Fuel system
- Bits 14-15 (0xC000): Damage severity level (0-3)
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\subsystem_bit_mapping.json"

def find_0xCA_references():
    """Find all references to entity[0xCA] status bitfield."""
    refs = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.GetDisasm(ea)
            
            # Look for [di+0CAh], [si+0CAh], etc.
            if "+0CAh]" in disasm or "+0CA]" in disasm:
                func_name = idc.get_func_name(func_ea)
                mnem = idc.print_insn_mnem(ea)
                
                # Get operands
                op1 = idc.print_operand(ea, 0)
                op2 = idc.print_operand(ea, 1)
                
                # Extract bitmask if this is test/and/or
                bitmask = None
                operation = None
                
                if mnem in ["test", "and", "or", "xor"]:
                    operation = mnem.upper()
                    # Try to parse the bitmask from op2
                    if op2.endswith("h"):
                        try:
                            bitmask = int(op2[:-1], 16)
                        except:
                            bitmask = op2
                    elif op2.isdigit():
                        bitmask = int(op2)
                    else:
                        bitmask = op2
                
                refs.append({
                    "function": func_name,
                    "address": hex(ea),
                    "offset": hex(ea - func.start_ea),
                    "instruction": disasm,
                    "operation": operation,
                    "bitmask": bitmask
                })
            
            ea = idc.next_head(ea, func.end_ea)
    
    return refs

def group_by_bitmask(refs):
    """Group references by bitmask value."""
    by_mask = {}
    
    for ref in refs:
        mask = ref.get("bitmask")
        if mask and isinstance(mask, int):
            if mask not in by_mask:
                by_mask[mask] = []
            by_mask[mask].append(ref)
    
    return by_mask

def find_subsystem_strings():
    """Find subsystem name strings and their references."""
    subsystems = ["ENG", "HYD", "FUEL", "ELEC", "RDR", "RADAR", "ECM", "RWR", 
                  "FCC", "GEAR", "NAV", "FLAP", "BRAKE", "AVION"]
    
    found = {}
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            if idc.is_strlit(idc.get_full_flags(head)):
                str_val = idc.get_strlit_contents(head)
                if str_val:
                    str_decoded = str_val.decode('ascii', errors='ignore').upper()
                    
                    for subsys in subsystems:
                        if subsys in str_decoded:
                            xrefs = list(idautils.XrefsTo(head, 0))
                            
                            if subsys not in found:
                                found[subsys] = []
                            
                            found[subsys].append({
                                "string": str_decoded[:30],
                                "address": hex(head),
                                "xref_count": len(xrefs),
                                "used_by": [idc.get_func_name(x.frm) for x in xrefs[:5]]
                            })
                            break
    
    return found

def find_fault_panel_functions():
    """Find functions that might display the fault panel."""
    keywords = ["fault", "panel", "warning", "status", "display", "view"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0
                    })
                    break
    
    return funcs[:20]

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete")
        
        print("\n[1] Finding all references to entity[0xCA]...")
        refs = find_0xCA_references()
        print(f"Found {len(refs)} references")
        
        print("\n[2] Grouping by bitmask...")
        by_mask = group_by_bitmask(refs)
        print(f"Found {len(by_mask)} distinct bitmasks")
        
        for mask in sorted(by_mask.keys()):
            count = len(by_mask[mask])
            print(f"  Mask 0x{mask:04X}: {count} references")
        
        print("\n[3] Finding subsystem name strings...")
        subsys_strings = find_subsystem_strings()
        for subsys, refs in subsys_strings.items():
            print(f"  {subsys}: {len(refs)} occurrences")
        
        print("\n[4] Finding fault panel display functions...")
        fault_funcs = find_fault_panel_functions()
        print(f"Found {len(fault_funcs)} candidate functions")
        
        result = {
            "all_references": refs,
            "grouped_by_bitmask": {hex(k): v for k, v in by_mask.items()},
            "subsystem_strings": subsys_strings,
            "fault_panel_functions": fault_funcs,
            "summary": {
                "total_refs": len(refs),
                "unique_bitmasks": len(by_mask),
                "subsystems_found": len(subsys_strings),
                "fault_functions": len(fault_funcs)
            }
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[5] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
