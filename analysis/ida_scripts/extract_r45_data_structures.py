"""
Extract data structures and enums from R45 menu code.

We're looking for:
1. Structure field access patterns (e.g., [bx+offset])
2. Enum values (comparisons with constants)
3. Array indexing patterns
4. Structure sizes (from multiplication/addition patterns)

Focus on:
- Pilot structure
- Squadron structure  
- Mission structure
- Status/rank enums
"""
import idaapi
import idautils
import idc
import json
import re

def analyze_structure_access(func_ea, func_name):
    """
    Analyze a function for structure field access patterns.
    Look for patterns like: [bx+offset], [si+offset], es:[bx+offset]
    """
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    accesses = []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        disasm = idc.GetDisasm(head)
        mnem = idc.print_insn_mnem(head)
        
        # Look for structure access patterns
        # [reg+offset], [reg+offset+field], es:[reg+offset]
        patterns = [
            r'\[(\w+)\+([0-9A-Fa-fx]+)h?\]',  # [bx+4] or [bx+4h]
            r'es:\[(\w+)\+([0-9A-Fa-fx]+)h?\]',  # es:[bx+4]
            r'word ptr \[(\w+)\+([0-9A-Fa-fx]+)h?\]',  # word ptr [bx+4]
            r'byte ptr \[(\w+)\+([0-9A-Fa-fx]+)h?\]',  # byte ptr [bx+4]
            r'dword ptr \[(\w+)\+([0-9A-Fa-fx]+)h?\]',  # dword ptr [bx+4]
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, disasm)
            for match in matches:
                reg = match[0]
                offset_str = match[1]
                
                # Parse offset (may be hex or decimal)
                try:
                    if 'h' in offset_str or offset_str.startswith('0x'):
                        offset = int(offset_str.replace('h', '').replace('0x', ''), 16)
                    else:
                        offset = int(offset_str)
                    
                    accesses.append({
                        "address": head,
                        "instruction": disasm,
                        "register": reg,
                        "offset": offset,
                        "offset_hex": f"0x{offset:X}"
                    })
                except:
                    pass
    
    return accesses

def analyze_array_multiplication(func_ea, func_name):
    """
    Find array indexing patterns: index * element_size
    Look for imul, shl (multiply by power of 2), or repeated additions
    """
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    multiplications = []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        # Look for multiplication instructions
        if mnem == "imul":
            # Get operands
            op1 = idc.print_operand(head, 0)
            op2 = idc.print_operand(head, 1)
            
            # Try to get immediate value
            if op2:
                try:
                    value = idc.get_operand_value(head, 1)
                    multiplications.append({
                        "address": head,
                        "instruction": disasm,
                        "multiplier": value,
                        "multiplier_hex": f"0x{value:X}"
                    })
                except:
                    pass
        
        # Look for shl (shift left = multiply by 2^n)
        elif mnem == "shl":
            op1 = idc.print_operand(head, 0)
            op2 = idc.print_operand(head, 1)
            try:
                shift = idc.get_operand_value(head, 1)
                multiplier = 1 << shift  # 2^shift
                multiplications.append({
                    "address": head,
                    "instruction": disasm,
                    "shift": shift,
                    "multiplier": multiplier,
                    "multiplier_hex": f"0x{multiplier:X}"
                })
            except:
                pass
    
    return multiplications

def analyze_enum_comparisons(func_ea, func_name):
    """
    Find enum comparisons: cmp reg, value
    Look for patterns where same value is compared multiple times
    or sequential comparisons (likely enum values)
    """
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    comparisons = []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        if mnem == "cmp":
            # Get operands
            op1 = idc.print_operand(head, 0)
            op2 = idc.print_operand(head, 1)
            
            # Try to get immediate value
            try:
                value = idc.get_operand_value(head, 1)
                if value < 256:  # Likely enum value
                    comparisons.append({
                        "address": head,
                        "instruction": disasm,
                        "operand": op1,
                        "value": value,
                        "value_hex": f"0x{value:X}"
                    })
            except:
                pass
    
    return comparisons

def analyze_function_arguments(func_ea, func_name):
    """
    Analyze function calls to understand parameter types.
    Look at what's pushed before calls.
    """
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    call_contexts = []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        
        if mnem == "call":
            # Look back for push instructions
            pushes = []
            scan_addr = head - 1
            
            # Scan up to 20 instructions back
            for i in range(20):
                scan_addr = idc.prev_head(scan_addr)
                if scan_addr == idc.BADADDR:
                    break
                
                scan_mnem = idc.print_insn_mnem(scan_addr)
                if scan_mnem == "push":
                    scan_disasm = idc.GetDisasm(scan_addr)
                    pushes.insert(0, {
                        "address": scan_addr,
                        "instruction": scan_disasm
                    })
                elif scan_mnem == "call":
                    # Hit another call, stop
                    break
            
            target = idc.get_operand_value(head, 0)
            target_name = idc.get_func_name(target) or f"sub_{target:X}"
            
            call_contexts.append({
                "address": head,
                "target": target,
                "target_name": target_name,
                "pushes": pushes
            })
    
    return call_contexts

def main():
    print("=== EXTRACTING DATA STRUCTURES FROM R45 ===\n")
    
    # Key functions to analyze
    functions = [
        (0x156945, "overlay_r45_logic"),           # Main state machine
        (0x1573C3, "r45_menu_element_dispatcher"), # Element dispatcher
        (0x1561B0, "r45_position_calculator"),     # Position calculator
    ]
    
    results = {
        "structure_accesses": {},
        "array_multiplications": {},
        "enum_comparisons": {},
        "function_calls": {}
    }
    
    for func_addr, func_name in functions:
        print(f"Analyzing {func_name} at 0x{func_addr:X}...")
        
        # Structure accesses
        accesses = analyze_structure_access(func_addr, func_name)
        if accesses:
            results["structure_accesses"][func_name] = accesses
            print(f"  Found {len(accesses)} structure field accesses")
            
            # Group by offset to find structure fields
            offsets = {}
            for acc in accesses:
                offset = acc["offset"]
                if offset not in offsets:
                    offsets[offset] = 0
                offsets[offset] += 1
            
            print(f"  Unique offsets: {sorted(offsets.keys())}")
        
        # Array multiplications
        mults = analyze_array_multiplication(func_addr, func_name)
        if mults:
            results["array_multiplications"][func_name] = mults
            print(f"  Found {len(mults)} array multiplications")
            
            # Group by multiplier
            multipliers = {}
            for mult in mults:
                m = mult.get("multiplier", 0)
                if m not in multipliers:
                    multipliers[m] = 0
                multipliers[m] += 1
            
            print(f"  Structure sizes: {sorted(multipliers.keys())}")
        
        # Enum comparisons
        comps = analyze_enum_comparisons(func_addr, func_name)
        if comps:
            results["enum_comparisons"][func_name] = comps
            print(f"  Found {len(comps)} enum comparisons")
            
            # Group by value
            values = {}
            for comp in comps:
                v = comp["value"]
                if v not in values:
                    values[v] = []
                values[v].append(comp["operand"])
            
            print(f"  Enum values: {sorted(values.keys())}")
        
        # Function calls
        calls = analyze_function_arguments(func_addr, func_name)
        if calls:
            results["function_calls"][func_name] = calls
            print(f"  Found {len(calls)} function calls with parameters")
        
        print()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_data_structures.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved to {output_path}")
    
    # Generate structure definitions
    print("\n=== GENERATING STRUCTURE DEFINITIONS ===\n")
    
    output_lines = []
    output_lines.append("# R45 Data Structures (Generated from Code Analysis)\n")
    
    # Analyze structure accesses
    for func_name, accesses in results["structure_accesses"].items():
        output_lines.append(f"\n## {func_name}\n")
        
        # Group by offset
        offsets = {}
        for acc in accesses:
            offset = acc["offset"]
            if offset not in offsets:
                offsets[offset] = []
            offsets[offset].append(acc["instruction"])
        
        output_lines.append("```c")
        output_lines.append("struct Unknown {")
        for offset in sorted(offsets.keys()):
            instr_sample = offsets[offset][0]
            count = len(offsets[offset])
            
            # Guess field type from instruction
            if "byte ptr" in instr_sample:
                field_type = "uint8_t"
            elif "word ptr" in instr_sample:
                field_type = "uint16_t"
            elif "dword ptr" in instr_sample:
                field_type = "uint32_t"
            else:
                field_type = "uint16_t"  # Default for 16-bit
            
            output_lines.append(f"    {field_type} field_{offset:03X};  // +0x{offset:X} ({count} accesses)")
        output_lines.append("};")
        output_lines.append("```")
        
        output_lines.append(f"\nSample accesses:")
        for offset in sorted(offsets.keys())[:5]:  # First 5 offsets
            output_lines.append(f"  +0x{offset:X}: {offsets[offset][0]}")
    
    # Save structure analysis
    struct_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_structures.md"
    with open(struct_path, 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Structure definitions saved to {struct_path}")

if __name__ == "__main__":
    main()
