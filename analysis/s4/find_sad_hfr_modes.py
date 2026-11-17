"""
Find SAD and HFR radar mode strings and their usage.

These are likely radar submodes in the realistic mode.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\sad_hfr_modes.json"

def find_exact_string(search_str):
    """Find exact string match."""
    results = []
    
    for s in idautils.Strings():
        str_val = str(s)
        
        # Case-insensitive search for the exact term
        if search_str.upper() in str_val.upper():
            xrefs = list(idautils.XrefsTo(s.ea, 0))
            
            # Get context from xrefs
            xref_details = []
            for xref in xrefs[:10]:
                func_name = idc.get_func_name(xref.frm)
                if func_name:
                    # Get instruction at xref
                    insn = idc.GetDisasm(xref.frm)
                    
                    xref_details.append({
                        "function": func_name,
                        "address": hex(xref.frm),
                        "instruction": insn
                    })
            
            results.append({
                "address": hex(s.ea),
                "string": str_val,
                "length": len(str_val),
                "xref_count": len(xrefs),
                "xrefs": xref_details
            })
    
    return results

def analyze_mode_switch_function():
    """Analyze key_mode_switch_step function in detail."""
    
    func_name = "key_mode_switch_step"
    func_ea = idc.get_name_ea_simple(func_name)
    
    if func_ea == idc.BADADDR:
        return {"error": "Function not found"}
    
    func = idaapi.get_func(func_ea)
    if not func:
        return {"error": "Not a function"}
    
    # Extract disassembly
    disasm = []
    string_refs = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idc.GetDisasm(ea)
        disasm.append(f"{ea:08X}: {insn}")
        
        # Look for string references
        for xref in idautils.XrefsFrom(ea, 0):
            # Check if xref points to a string
            if idc.is_strlit(idc.get_full_flags(xref.to)):
                str_val = idc.get_strlit_contents(xref.to)
                if str_val:
                    string_refs.append({
                        "offset": hex(ea - func.start_ea),
                        "address": hex(ea),
                        "string_addr": hex(xref.to),
                        "string": str_val.decode('ascii', errors='ignore'),
                        "instruction": insn
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "name": func_name,
        "address": hex(func.start_ea),
        "size": func.end_ea - func.start_ea,
        "disassembly": disasm,
        "string_references": string_refs
    }

def search_all_3_letter_strings():
    """Search for all 3-letter uppercase strings (likely mode abbreviations)."""
    
    three_letter = []
    
    for s in idautils.Strings():
        str_val = str(s)
        
        # Exactly 3 letters, all uppercase
        if len(str_val) == 3 and str_val.isupper() and str_val.isalpha():
            xrefs = list(idautils.XrefsTo(s.ea, 0))
            
            if xrefs:  # Only if referenced
                three_letter.append({
                    "address": hex(s.ea),
                    "string": str_val,
                    "xref_count": len(xrefs),
                    "used_by": [idc.get_func_name(x.frm) for x in xrefs[:3] if idc.get_func_name(x.frm)]
                })
    
    # Sort alphabetically
    three_letter.sort(key=lambda x: x['string'])
    
    return three_letter

def find_radar_mode_tables():
    """Find arrays/tables of mode names."""
    
    # Look for consecutive string pointers
    # Pattern: series of addresses pointing to short strings
    
    tables = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Look in data/const segments
        if not any(x in seg_name.lower() for x in ["data", "const", "rodata"]):
            continue
        
        ea = seg_ea
        end_ea = idc.get_segm_end(seg_ea)
        
        while ea < end_ea:
            # Check if this looks like a pointer
            if idc.get_wide_word(ea + 2) != 0:  # Segment part non-zero
                # Try to read as far pointer
                offset = idc.get_wide_word(ea)
                segment = idc.get_wide_word(ea + 2)
                
                # Calculate linear address
                linear = (segment << 4) + offset
                
                # Check if it points to a string
                if linear < 0x200000:  # Reasonable address
                    if idc.is_strlit(idc.get_full_flags(linear)):
                        str_val = idc.get_strlit_contents(linear)
                        if str_val and len(str_val) <= 10:
                            # Found one! Look for more nearby
                            table_start = ea
                            strings_found = [str_val.decode('ascii', errors='ignore')]
                            
                            # Check next few entries
                            next_ea = ea + 4
                            for i in range(10):
                                if next_ea >= end_ea:
                                    break
                                
                                next_off = idc.get_wide_word(next_ea)
                                next_seg = idc.get_wide_word(next_ea + 2)
                                next_lin = (next_seg << 4) + next_off
                                
                                if next_lin < 0x200000 and idc.is_strlit(idc.get_full_flags(next_lin)):
                                    next_str = idc.get_strlit_contents(next_lin)
                                    if next_str and len(next_str) <= 10:
                                        strings_found.append(next_str.decode('ascii', errors='ignore'))
                                        next_ea += 4
                                    else:
                                        break
                                else:
                                    break
                            
                            if len(strings_found) >= 3:
                                tables.append({
                                    "address": hex(table_start),
                                    "segment": seg_name,
                                    "count": len(strings_found),
                                    "strings": strings_found
                                })
                            
                            ea = next_ea
                        else:
                            ea += 4
                    else:
                        ea += 4
                else:
                    ea += 4
            else:
                ea += 2
    
    return tables[:20]

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Searching for 'SAD' string...")
        sad_results = find_exact_string("SAD")
        print(f"Found {len(sad_results)} occurrences of 'SAD'")
        for r in sad_results:
            print(f"  '{r['string']}' @ {r['address']} ({r['xref_count']} refs)")
        
        print("\n[2] Searching for 'HFR' string...")
        hfr_results = find_exact_string("HFR")
        print(f"Found {len(hfr_results)} occurrences of 'HFR'")
        for r in hfr_results:
            print(f"  '{r['string']}' @ {r['address']} ({r['xref_count']} refs)")
        
        print("\n[3] Analyzing key_mode_switch_step function...")
        mode_switch = analyze_mode_switch_function()
        if "error" not in mode_switch:
            print(f"Function {mode_switch['name']}: {mode_switch['size']} bytes")
            print(f"String references found: {len(mode_switch['string_references'])}")
            for ref in mode_switch['string_references'][:10]:
                print(f"  '{ref['string']}' @ offset {ref['offset']}")
        
        print("\n[4] Searching for all 3-letter mode abbreviations...")
        three_letter = search_all_3_letter_strings()
        print(f"Found {len(three_letter)} three-letter strings")
        for s in three_letter[:20]:
            print(f"  {s['string']} @ {s['address']} ({s['xref_count']} refs)")
        
        print("\n[5] Searching for radar mode string tables...")
        tables = find_radar_mode_tables()
        print(f"Found {len(tables)} potential string tables")
        for t in tables[:5]:
            print(f"  {t['address']}: {t['count']} strings - {t['strings']}")
        
        result = {
            "sad_strings": sad_results,
            "hfr_strings": hfr_results,
            "mode_switch_function": mode_switch,
            "three_letter_strings": three_letter,
            "mode_string_tables": tables
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[6] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
