"""
Find references to BUTTON1/BUTTON2/BUTTON3 strings in IDA database.
Quick script to identify button graphics loader functions.
"""
import idaapi
import idautils
import idc

def find_string_refs(search_str):
    """Find all references to a specific string."""
    refs = []
    
    # Search for string
    ea = idc.get_inf_attr(idc.INF_MIN_EA)
    max_ea = idc.get_inf_attr(idc.INF_MAX_EA)
    
    while ea < max_ea:
        ea = idc.find_text(ea, idc.SEARCH_DOWN, 0, 0, search_str)
        if ea == idc.BADADDR:
            break
            
        # Find function containing this string
        func_ea = idc.get_func_attr(ea, idc.FUNCATTR_START)
        if func_ea != idc.BADADDR:
            func_name = idc.get_func_name(func_ea)
            refs.append({
                'string_ea': ea,
                'func_ea': func_ea,
                'func_name': func_name,
                'func_size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
        
        ea = idc.next_head(ea)
    
    return refs

def main():
    idaapi.auto_wait()
    
    output = []
    output.append("=== BUTTON File String References ===\n")
    
    for button_name in ['BUTTON1', 'BUTTON2', 'BUTTON3']:
        output.append(f"\n--- {button_name} ---")
        refs = find_string_refs(button_name)
        
        if not refs:
            output.append(f"No references found for {button_name}")
            continue
            
        output.append(f"Found {len(refs)} reference(s):")
        for ref in refs:
            output.append(f"  String at 0x{ref['string_ea']:X}")
            output.append(f"  Function: {ref['func_name']} @ 0x{ref['func_ea']:X} ({ref['func_size']}B)")
            
            # Get xrefs to this string
            xrefs = []
            for xref in idautils.XrefsTo(ref['string_ea'], 0):
                xref_func = idc.get_func_name(xref.frm)
                if xref_func and xref.frm != ref['string_ea']:
                    xrefs.append(f"    Xref from {xref_func} @ 0x{xref.frm:X}")
            
            if xrefs:
                output.append("  Cross-references:")
                output.extend(xrefs)
    
    result = '\n'.join(output)
    print(result)
    
    # Write output
    with open('button_strings.txt', 'w') as f:
        f.write(result)
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
