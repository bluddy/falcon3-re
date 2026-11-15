"""
Find SYSMENU string references and the loader function.
This will lead us to the code that displays War Room graphics.
"""
import idaapi
import idautils
import idc

def main():
    idaapi.auto_wait()
    
    output = []
    output.append("=" * 80)
    output.append("SYSMENU String References")
    output.append("=" * 80)
    output.append("")
    
    # Search for all SYSMENU-related strings
    search_strings = ['SYSMENU', 'SYSMENUF', 'SYSMENUM']
    
    all_refs = {}
    
    for search_str in search_strings:
        output.append(f"\n--- Searching for: {search_str} ---")
        
        # Find all occurrences of the string
        ea = idc.get_inf_attr(idc.INF_MIN_EA)
        max_ea = idc.get_inf_attr(idc.INF_MAX_EA)
        
        found_count = 0
        while ea < max_ea:
            ea = idc.find_text(ea, idc.SEARCH_DOWN, 0, 0, search_str)
            if ea == idc.BADADDR:
                break
            
            found_count += 1
            output.append(f"\nString found at: 0x{ea:X}")
            
            # Find xrefs to this string
            xrefs = list(idautils.XrefsTo(ea, 0))
            output.append(f"  Cross-references: {len(xrefs)}")
            
            for xref in xrefs:
                xref_addr = xref.frm
                func_addr = idc.get_func_attr(xref_addr, idc.FUNCATTR_START)
                
                if func_addr != idc.BADADDR:
                    func_name = idc.get_func_name(func_addr)
                    func_size = idc.get_func_attr(func_addr, idc.FUNCATTR_END) - func_addr
                    
                    output.append(f"  From: 0x{xref_addr:X}")
                    output.append(f"  Function: {func_name} @ 0x{func_addr:X} ({func_size}B)")
                    
                    # Store for detailed analysis
                    if func_addr not in all_refs:
                        all_refs[func_addr] = {
                            'name': func_name,
                            'size': func_size,
                            'refs': []
                        }
                    all_refs[func_addr]['refs'].append((xref_addr, search_str))
            
            ea = idc.next_head(ea)
        
        output.append(f"\nTotal occurrences: {found_count}")
    
    # Detailed analysis of loader functions
    if all_refs:
        output.append("\n\n" + "=" * 80)
        output.append("DETAILED ANALYSIS OF LOADER FUNCTIONS")
        output.append("=" * 80)
        
        for func_addr in sorted(all_refs.keys()):
            info = all_refs[func_addr]
            output.append(f"\n{info['name']} @ 0x{func_addr:X} ({info['size']}B)")
            output.append(f"References: {len(info['refs'])}")
            
            # Disassemble function to look for op_dispatch calls
            output.append("\nDisassembly:")
            
            ea = func_addr
            func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
            count = 0
            
            dispatch_calls = []
            
            while ea < func_end and ea != idc.BADADDR and count < 200:
                mnem = idc.print_insn_mnem(ea)
                disasm = idc.generate_disasm_line(ea, 0)
                
                # Look for calls to op_dispatch
                if mnem in ['call', 'lcall']:
                    for xref in idautils.XrefsFrom(ea, 0):
                        if xref.type in [idc.fl_CN, idc.fl_CF]:
                            target_name = idc.get_func_name(xref.to)
                            if target_name and 'dispatch' in target_name.lower():
                                dispatch_calls.append((ea, target_name))
                                output.append(f"  0x{ea:06X}: {disasm}  *** DISPATCH CALL ***")
                            else:
                                output.append(f"  0x{ea:06X}: {disasm}")
                else:
                    output.append(f"  0x{ea:06X}: {disasm}")
                
                ea = idc.next_head(ea)
                count += 1
            
            output.append(f"\nDispatch calls found: {len(dispatch_calls)}")
            if len(dispatch_calls) >= 3:
                output.append("*** Likely .IDX/.DAT loader (3+ dispatch calls) ***")
    else:
        output.append("\n\nNo SYSMENU strings found in database!")
        output.append("The loader might use dynamically constructed strings or")
        output.append("the strings might be in a different format.")
    
    result = '\n'.join(output)
    print(result)
    
    # Write output
    with open('sysmenu_loader_analysis.txt', 'w') as f:
        f.write(result)
    
    print(f"\n\nOutput written to sysmenu_loader_analysis.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
