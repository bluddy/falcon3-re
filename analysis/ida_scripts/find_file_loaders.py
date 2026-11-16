"""
Find file loader functions for squadron, campaign, and pilot data.

We need to find:
1. .SQU file loader (squadron data, 2703 bytes)
2. .CAM file loader (campaign data, 11828 bytes)
3. NAMES.BIN loader (pilot names)
4. CALLSIGN.BIN loader (pilot callsigns)
5. sqdnames.str loader (squadron names)

These functions will reveal structure offsets through field access patterns.
"""
import idaapi
import idautils
import idc
import json

def find_string_references(search_strings):
    """Find all references to specific strings."""
    results = {}
    
    print("Searching for file name strings...")
    
    for search_str in search_strings:
        results[search_str] = []
        
        # Search all segments
        for seg_ea in idautils.Segments():
            seg = idaapi.getseg(seg_ea)
            seg_name = idaapi.get_segm_name(seg)
            
            # Search for string in this segment
            for ea in range(seg.start_ea, seg.end_ea):
                str_val = idc.get_strlit_contents(ea)
                if str_val:
                    try:
                        decoded = str_val.decode('ascii', errors='replace')
                        if search_str.lower() in decoded.lower():
                            # Found it! Now find xrefs
                            xrefs = list(idautils.DataRefsTo(ea))
                            
                            results[search_str].append({
                                "string_addr": ea,
                                "string_value": decoded,
                                "segment": seg_name,
                                "xrefs": []
                            })
                            
                            # Get functions that reference this string
                            for xref in xrefs:
                                func = idaapi.get_func(xref)
                                if func:
                                    func_name = idc.get_func_name(func.start_ea)
                                    results[search_str][-1]["xrefs"].append({
                                        "address": xref,
                                        "function": func_name,
                                        "func_start": func.start_ea
                                    })
                            
                            print(f"  Found '{decoded}' at 0x{ea:X} ({len(xrefs)} xrefs)")
                    except:
                        pass
    
    return results

def analyze_function_for_file_io(func_ea, func_name):
    """
    Analyze a function for file I/O patterns.
    Look for open, read, write, close operations.
    """
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    print(f"\nAnalyzing {func_name} at 0x{func_ea:X}...")
    
    result = {
        "address": func_ea,
        "name": func_name,
        "size": func.size(),
        "file_ops": [],
        "buffer_allocs": [],
        "structure_accesses": []
    }
    
    # Look for file operation calls
    file_op_functions = [
        "open", "close", "read", "write", 
        "fopen", "fclose", "fread", "fwrite",
        "file_open", "file_read", "file_close"
    ]
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        # Check for calls
        if mnem == "call":
            target = idc.get_operand_value(head, 0)
            target_name = idc.get_func_name(target) or ""
            
            # Check if it's a file operation
            for op in file_op_functions:
                if op in target_name.lower():
                    result["file_ops"].append({
                        "address": head,
                        "operation": target_name,
                        "target": target
                    })
                    print(f"  File op: {target_name} at 0x{head:X}")
        
        # Look for structure accesses [reg+offset]
        if "[" in disasm and "+" in disasm:
            # Extract offset if it's a structure access
            import re
            match = re.search(r'\[(\w+)\+([0-9A-Fa-fx]+)h?\]', disasm)
            if match:
                reg = match.group(1)
                try:
                    offset_str = match.group(2).replace('h', '').replace('0x', '')
                    offset = int(offset_str, 16)
                    
                    # Record structure access
                    result["structure_accesses"].append({
                        "address": head,
                        "instruction": disasm,
                        "register": reg,
                        "offset": offset,
                        "offset_hex": f"0x{offset:X}"
                    })
                except:
                    pass
    
    # Group structure accesses by offset
    if result["structure_accesses"]:
        offsets = {}
        for acc in result["structure_accesses"]:
            offset = acc["offset"]
            if offset not in offsets:
                offsets[offset] = 0
            offsets[offset] += 1
        
        print(f"  Structure offsets found: {sorted(offsets.keys())}")
        print(f"  Most common: {sorted(offsets.items(), key=lambda x: x[1], reverse=True)[:5]}")
    
    return result

def find_large_buffer_allocations():
    """
    Find functions that allocate large buffers (likely file read buffers).
    Look for:
    - enter N, 0 where N > 2000 (stack allocation)
    - malloc/calloc with large sizes
    """
    print("\n=== SEARCHING FOR LARGE BUFFER ALLOCATIONS ===\n")
    
    results = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        # Check first instruction for enter
        first_insn = func.start_ea
        mnem = idc.print_insn_mnem(first_insn)
        
        if mnem == "enter":
            # Get stack allocation size
            stack_size = idc.get_operand_value(first_insn, 0)
            
            # Check for large allocations
            if stack_size >= 2000:  # Relevant for .SQU (2703) and .CAM (11828)
                func_name = idc.get_func_name(func_ea)
                results.append({
                    "function": func_name,
                    "address": func_ea,
                    "stack_size": stack_size,
                    "size_hex": f"0x{stack_size:X}"
                })
                print(f"  {func_name:40} stack: {stack_size:6} (0x{stack_size:X}) bytes")
    
    # Sort by stack size
    results.sort(key=lambda x: x["stack_size"], reverse=True)
    
    return results

def main():
    print("="*70)
    print("FINDING FILE LOADER FUNCTIONS")
    print("="*70)
    print()
    
    # 1. Find file name string references
    file_names = [
        ".SQU", ".CAM", ".MIS", "NAMES.BIN", "CALLSIGN.BIN", 
        "sqdnames.str", "SQUAD", ".MTV", ".WAR"
    ]
    
    print("\n=== STEP 1: FIND FILE NAME REFERENCES ===\n")
    string_results = find_string_references(file_names)
    
    # 2. Find large buffer allocations
    print("\n=== STEP 2: FIND LARGE BUFFER ALLOCATIONS ===\n")
    buffer_results = find_large_buffer_allocations()
    
    # 3. Analyze candidate functions
    print("\n=== STEP 3: ANALYZE CANDIDATE FUNCTIONS ===\n")
    
    candidate_functions = set()
    
    # Add functions from string references
    for file_name, refs in string_results.items():
        for ref_entry in refs:
            for xref in ref_entry["xrefs"]:
                candidate_functions.add((xref["func_start"], xref["function"]))
    
    # Add functions with large allocations
    for buf in buffer_results[:10]:  # Top 10 by size
        candidate_functions.add((buf["address"], buf["function"]))
    
    print(f"Found {len(candidate_functions)} candidate functions\n")
    
    analyzed = []
    for func_addr, func_name in sorted(candidate_functions):
        analysis = analyze_function_for_file_io(func_addr, func_name)
        if analysis:
            analyzed.append(analysis)
    
    # 4. Save results
    output = {
        "string_references": string_results,
        "large_allocations": buffer_results,
        "analyzed_functions": analyzed
    }
    
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\file_loaders_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== RESULTS SAVED ===")
    print(f"Output: {output_path}")
    
    # 5. Generate summary
    print("\n=== SUMMARY ===\n")
    
    print("FILE NAME REFERENCES:")
    for file_name, refs in string_results.items():
        if refs:
            print(f"  {file_name}: {len(refs)} string(s) found")
            for ref_entry in refs:
                print(f"    '{ref_entry['string_value']}' at 0x{ref_entry['string_addr']:X}")
                for xref in ref_entry["xrefs"][:3]:  # First 3 xrefs
                    print(f"      → {xref['function']} (0x{xref['func_start']:X})")
    
    print()
    print("LARGE BUFFER FUNCTIONS (Top 5):")
    for buf in buffer_results[:5]:
        print(f"  {buf['function']:40} {buf['stack_size']:6} bytes (0x{buf['stack_size']:X})")
    
    print()
    print("RECOMMENDED ANALYSIS ORDER:")
    print("  1. Functions with .SQU references (squadron loader)")
    print("  2. Functions with ~2703 byte allocation")
    print("  3. Functions with .CAM references (campaign loader)")
    print("  4. Functions with ~11828 byte allocation")
    print("  5. Functions with NAMES.BIN/CALLSIGN.BIN references")

if __name__ == "__main__":
    main()
