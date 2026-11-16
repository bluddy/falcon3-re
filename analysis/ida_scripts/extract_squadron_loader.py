"""
Extract and analyze squad_campaign_file_loader function.
Address: 0x6A651 (435793)

This function loads .SQU and .CAM files, so it should reveal
the Pilot and Squadron structure offsets.
"""
import idaapi
import idautils
import idc
import json

def extract_function_complete(address, name):
    """Extract complete function with all details."""
    func = idaapi.get_func(address)
    if not func:
        print(f"ERROR: No function at 0x{address:X}")
        return None
    
    print(f"Extracting {name} at 0x{address:X}...")
    print(f"  Size: {func.size()} bytes")
    
    result = {
        "address": address,
        "name": name,
        "size": func.size(),
        "calls": [],
        "data_refs": [],
        "strings": [],
        "structure_accesses": [],
        "constants": [],
        "instructions": []
    }
    
    # Extract all instructions
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        result["instructions"].append({
            "address": head,
            "offset": head - func.start_ea,
            "mnem": mnem,
            "disasm": disasm
        })
        
        # Check for calls
        if mnem == "call":
            target = idc.get_operand_value(head, 0)
            target_name = idc.get_func_name(target) or f"sub_{target:X}"
            result["calls"].append({
                "addr": head,
                "target": target,
                "name": target_name
            })
        
        # Check for constants (especially size values like 2703, 11828)
        if mnem in ["mov", "push", "cmp", "add", "sub"]:
            for i in range(2):  # Check both operands
                op_type = idc.get_operand_type(head, i)
                if op_type == idc.o_imm:  # Immediate value
                    value = idc.get_operand_value(head, i)
                    # Look for interesting sizes
                    if value in [2703, 0xA8F, 11828, 0x2E34, 66, 0x42, 
                                 1980, 663, 60, 30]:  # Known sizes
                        result["constants"].append({
                            "address": head,
                            "value": value,
                            "hex": f"0x{value:X}",
                            "instruction": disasm
                        })
        
        # Check for structure accesses [reg+offset]
        import re
        patterns = [
            r'\[(\w+)\+([0-9A-Fa-fx]+)h?\]',
            r'byte ptr \[(\w+)\+([0-9A-Fa-fx]+)h?\]',
            r'word ptr \[(\w+)\+([0-9A-Fa-fx]+)h?\]',
            r'dword ptr \[(\w+)\+([0-9A-Fa-fx]+)h?\]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, disasm)
            for match in matches:
                reg = match[0]
                try:
                    offset_str = match[1].replace('h', '').replace('0x', '')
                    offset = int(offset_str, 16)
                    
                    result["structure_accesses"].append({
                        "address": head,
                        "instruction": disasm,
                        "register": reg,
                        "offset": offset,
                        "offset_hex": f"0x{offset:X}"
                    })
                except:
                    pass
        
        # Check for data references
        for ref in idautils.DataRefsFrom(head):
            ref_name = idc.get_name(ref) or f"data_{ref:X}"
            
            # Check if it's a string
            str_val = idc.get_strlit_contents(ref)
            if str_val:
                result["strings"].append({
                    "address": ref,
                    "value": str_val.decode('ascii', errors='replace')
                })
            
            result["data_refs"].append({
                "addr": head,
                "target": ref,
                "name": ref_name
            })
    
    return result

def analyze_structure_patterns(func_data):
    """Analyze structure access patterns to find field offsets."""
    print("\n=== STRUCTURE ACCESS ANALYSIS ===\n")
    
    # Group by offset
    offsets = {}
    for acc in func_data["structure_accesses"]:
        offset = acc["offset"]
        if offset not in offsets:
            offsets[offset] = []
        offsets[offset].append(acc)
    
    print(f"Found {len(offsets)} unique offsets:")
    for offset in sorted(offsets.keys()):
        count = len(offsets[offset])
        sample = offsets[offset][0]["instruction"]
        print(f"  +0x{offset:03X} ({offset:4d}): {count:2d} accesses - {sample}")
    
    return offsets

def analyze_constants(func_data):
    """Analyze constants to identify structure sizes and counts."""
    print("\n=== CONSTANT ANALYSIS ===\n")
    
    if not func_data["constants"]:
        print("No interesting constants found")
        return
    
    print("Interesting constants found:")
    for const in func_data["constants"]:
        print(f"  0x{const['address']:X}: {const['value']:6d} (0x{const['value']:04X}) - {const['instruction']}")
    
    # Group by value
    values = {}
    for const in func_data["constants"]:
        val = const["value"]
        if val not in values:
            values[val] = 0
        values[val] += 1
    
    print("\nConstant frequency:")
    for val in sorted(values.keys()):
        count = values[val]
        print(f"  {val:6d} (0x{val:04X}): {count} occurrences")
        
        # Interpret known values
        if val == 2703:
            print(f"    → .SQU file size")
        elif val == 11828:
            print(f"    → .CAM file size")
        elif val == 66 or val == 0x42:
            print(f"    → PilotRecord size")
        elif val == 30:
            print(f"    → Number of pilots")
        elif val == 60:
            print(f"    → Header size (2 × 30)?")
        elif val == 1980:
            print(f"    → 30 pilots × 66 bytes")
        elif val == 663:
            print(f"    → Extended pilot data size")

def main():
    print("="*70)
    print("EXTRACTING SQUADRON/CAMPAIGN FILE LOADER")
    print("="*70)
    print()
    
    # Extract the function
    loader_addr = 0x6A651
    func_data = extract_function_complete(loader_addr, "squad_campaign_file_loader")
    
    if not func_data:
        print("ERROR: Failed to extract function")
        return
    
    print(f"\nExtracted function:")
    print(f"  Size: {func_data['size']} bytes")
    print(f"  Instructions: {len(func_data['instructions'])}")
    print(f"  Calls: {len(func_data['calls'])}")
    print(f"  Structure accesses: {len(func_data['structure_accesses'])}")
    print(f"  Constants: {len(func_data['constants'])}")
    print(f"  Strings: {len(func_data['strings'])}")
    
    # Analyze patterns
    offsets = analyze_structure_patterns(func_data)
    analyze_constants(func_data)
    
    # Show called functions
    print("\n=== CALLED FUNCTIONS ===\n")
    for call in func_data["calls"][:20]:  # First 20
        print(f"  0x{call['addr']:X}: {call['name']}")
    
    if len(func_data["calls"]) > 20:
        print(f"  ... and {len(func_data['calls']) - 20} more")
    
    # Show strings
    if func_data["strings"]:
        print("\n=== STRINGS REFERENCED ===\n")
        for s in func_data["strings"]:
            print(f"  0x{s['address']:X}: '{s['value']}'")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\squadron_loader_extract.json"
    with open(output_path, 'w') as f:
        json.dump(func_data, f, indent=2)
    
    print(f"\n=== SAVED ===")
    print(f"Output: {output_path}")
    
    # Generate summary
    print("\n=== SUMMARY ===\n")
    print("This function likely:")
    print("  1. Opens .SQU or .CAM file")
    print("  2. Reads entire file into buffer")
    print("  3. Parses file structure")
    print("  4. Copies data into in-memory structures")
    print()
    print("NEXT STEPS:")
    print("  1. Analyze structure access patterns to map offsets")
    print("  2. Find where parsed data is copied to memory")
    print("  3. Match offsets to Pilot/Squadron/Campaign fields")
    print("  4. Update structures.yaml with discovered offsets")

if __name__ == "__main__":
    main()
