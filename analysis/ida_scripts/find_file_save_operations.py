import idaapi
import idc
import idautils
import json

def find_dos_file_writes():
    """
    Search for DOS INT 21h file write operations (AH=40h).
    These are used to save mission files.
    """
    results = {
        "int_21h_calls": [],
        "file_write_candidates": [],
        "file_handle_refs": []
    }
    
    print("[*] Searching for DOS INT 21h file operations...")
    
    # Search for INT 21h instructions
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        for head in idautils.Heads(seg_ea, seg_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: int 21h
            if "int" in disasm.lower() and "21h" in disasm:
                # Get context - look for AH=40h (write) or AH=3Ch (create)
                context = []
                check_head = head
                
                # Look back 20 instructions for AH setup
                for i in range(20):
                    check_head = idc.prev_head(check_head)
                    if check_head == idc.BADADDR:
                        break
                    
                    ctx_disasm = idc.generate_disasm_line(check_head, 0)
                    context.insert(0, {
                        "addr": hex(check_head),
                        "disasm": ctx_disasm
                    })
                    
                    # Check for file operations
                    if "ah" in ctx_disasm.lower():
                        # AH=40h = write file
                        # AH=3Ch = create file
                        # AH=3Dh = open file
                        # AH=3Eh = close file
                        if "40h" in ctx_disasm or "3Ch" in ctx_disasm or "3Dh" in ctx_disasm:
                            results["file_write_candidates"].append({
                                "int_addr": hex(head),
                                "function": idc.get_func_name(head),
                                "segment": seg_name,
                                "operation": "40h=write, 3Ch=create, 3Dh=open" if any(x in ctx_disasm for x in ["40h", "3Ch", "3Dh"]) else "unknown",
                                "context": context[-10:]  # Last 10 instructions
                            })
                            print(f"[+] Found file operation in {idc.get_func_name(head)} @ {hex(head)}")
                
                # Store all INT 21h calls
                results["int_21h_calls"].append({
                    "addr": hex(head),
                    "function": idc.get_func_name(head),
                    "segment": seg_name,
                    "context": context[-5:]
                })
    
    return results

def find_mis_file_references():
    """
    Search for .MIS filename strings and references.
    """
    results = {
        "mis_strings": [],
        "squad_strings": []
    }
    
    print("\n[*] Searching for .MIS file string references...")
    
    # Search all strings
    for str_addr in idautils.Strings():
        str_val = str(str_addr).upper()
        
        # Look for .MIS extensions
        if ".MIS" in str_val or "MIS" in str_val:
            # Find cross-references
            for xref in idautils.XrefsTo(str_addr.ea):
                results["mis_strings"].append({
                    "string": str(str_addr),
                    "string_addr": hex(str_addr.ea),
                    "xref_addr": hex(xref.frm),
                    "xref_func": idc.get_func_name(xref.frm),
                    "xref_segment": idc.get_segm_name(xref.frm)
                })
                print(f"[+] Found '.MIS' in '{str(str_addr)}' @ {hex(str_addr.ea)}")
                print(f"    Referenced by {idc.get_func_name(xref.frm)} @ {hex(xref.frm)}")
        
        # Look for SQUAD filenames
        if "SQUAD" in str_val:
            for xref in idautils.XrefsTo(str_addr.ea):
                results["squad_strings"].append({
                    "string": str(str_addr),
                    "string_addr": hex(str_addr.ea),
                    "xref_addr": hex(xref.frm),
                    "xref_func": idc.get_func_name(xref.frm)
                })
                print(f"[+] Found 'SQUAD' string: '{str(str_addr)}' @ {hex(str_addr.ea)}")
    
    return results

def find_buffer_write_patterns():
    """
    Search for code that prepares mission data buffers before writing.
    Look for patterns like copying FlightRecord or MissionSlot data.
    """
    results = {
        "memcpy_patterns": [],
        "buffer_fill_loops": []
    }
    
    print("\n[*] Searching for buffer preparation patterns...")
    
    # Search in R55 (mission editor) segment
    target_funcs = [
        ("mission_editor_main_loop", 0x18BC28),
        ("squadron_mission_file_loader", 0x17B437)
    ]
    
    for func_name, func_addr in target_funcs:
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            print(f"[-] Function {func_name} not found")
            continue
        
        print(f"[*] Checking {func_name}...")
        
        # Look for rep movsb/movsw (memory copy operations)
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            if "rep" in disasm.lower() and ("movsb" in disasm.lower() or "movsw" in disasm.lower()):
                # Found memory copy - get context
                context = []
                ctx_head = head
                for i in range(10):
                    ctx_head = idc.prev_head(ctx_head)
                    if ctx_head == idc.BADADDR:
                        break
                    context.insert(0, {
                        "addr": hex(ctx_head),
                        "disasm": idc.generate_disasm_line(ctx_head, 0)
                    })
                
                results["memcpy_patterns"].append({
                    "function": func_name,
                    "addr": hex(head),
                    "disasm": disasm,
                    "context": context
                })
                print(f"  [+] Found memcpy pattern @ {hex(head)}")
            
            # Look for loops that fill buffers (common save pattern)
            if "loop" in disasm.lower() or "jnz" in disasm.lower():
                # Check if we're storing to a buffer
                prev_head = idc.prev_head(head)
                if prev_head != idc.BADADDR:
                    prev_disasm = idc.generate_disasm_line(prev_head, 0)
                    if "mov" in prev_disasm.lower() and "[" in prev_disasm:
                        results["buffer_fill_loops"].append({
                            "function": func_name,
                            "addr": hex(head),
                            "disasm": disasm,
                            "prev_store": prev_disasm
                        })
    
    return results

def search_near_mission_functions():
    """
    Search for functions near known mission-related functions that might be save operations.
    """
    results = {
        "nearby_functions": []
    }
    
    print("\n[*] Searching for functions near mission editor...")
    
    # Start from mission_editor_main_loop
    base_addr = 0x18BC28
    search_range = 0x10000  # 64KB range
    
    # Get all functions in range
    for func_addr in idautils.Functions(base_addr, base_addr + search_range):
        func_name = idc.get_func_name(func_addr)
        func_size = idc.get_func_attr(func_addr, idc.FUNCATTR_END) - func_addr
        
        # Look for functions that might be save operations
        # Typically smaller utility functions near the main loop
        if 100 < func_size < 2000:  # Reasonable size for save function
            # Check if it contains INT 21h
            has_int_21h = False
            has_file_ops = False
            
            for head in idautils.Heads(func_addr, idc.get_func_attr(func_addr, idc.FUNCATTR_END)):
                disasm = idc.generate_disasm_line(head, 0)
                if "int" in disasm.lower() and "21h" in disasm:
                    has_int_21h = True
                if any(x in disasm.lower() for x in ["40h", "3ch", "3dh", "3eh"]):
                    has_file_ops = True
            
            if has_int_21h or has_file_ops:
                results["nearby_functions"].append({
                    "name": func_name,
                    "addr": hex(func_addr),
                    "size": func_size,
                    "offset_from_editor": hex(func_addr - base_addr),
                    "has_int_21h": has_int_21h,
                    "has_file_ops": has_file_ops
                })
                print(f"[+] Candidate: {func_name} @ {hex(func_addr)}, size={func_size}")
    
    return results

def main():
    print("="*80)
    print("File Save Operation Discovery")
    print("="*80)
    
    results = {}
    
    # Search for DOS file operations
    results["dos_operations"] = find_dos_file_writes()
    
    # Search for .MIS file references
    results["file_references"] = find_mis_file_references()
    
    # Search for buffer preparation
    results["buffer_patterns"] = find_buffer_write_patterns()
    
    # Search nearby functions
    results["nearby_functions"] = search_near_mission_functions()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\file_save_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"[+] Results saved to: {output_path}")
    print("="*80)
    
    # Summary
    print(f"\n[*] Summary:")
    print(f"    INT 21h calls: {len(results['dos_operations']['int_21h_calls'])}")
    print(f"    File write candidates: {len(results['dos_operations']['file_write_candidates'])}")
    print(f"    .MIS string references: {len(results['file_references']['mis_strings'])}")
    print(f"    SQUAD string references: {len(results['file_references']['squad_strings'])}")
    print(f"    Memcpy patterns: {len(results['buffer_patterns']['memcpy_patterns'])}")
    print(f"    Buffer fill loops: {len(results['buffer_patterns']['buffer_fill_loops'])}")
    print(f"    Nearby candidate functions: {len(results['nearby_functions']['nearby_functions'])}")
    print("\n[+] Analysis complete!")

if __name__ == "__main__":
    main()
