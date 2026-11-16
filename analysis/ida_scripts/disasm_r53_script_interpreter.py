#!/usr/bin/env python3
"""
Disassemble the R53 script interpreter to understand mission script operations.
"""

import idc
import idaapi
import idautils
import json
import re

def analyze_switch_table(ea, func_end):
    """Try to identify switch/jump table patterns."""
    # Look for patterns like: jmp cs:jpt_XXXXX[bx]
    disasm = idc.generate_disasm_line(ea, 0)
    
    if 'jmp' in disasm and 'cs:' in disasm and '[' in disasm:
        # Extract jump table name
        match = re.search(r'cs:(jpt_[0-9A-Fa-f]+)', disasm)
        if match:
            return {
                'type': 'jump_table',
                'name': match.group(1),
                'address': hex(ea)
            }
    
    return None

def find_opcodes(func_addr, func_end):
    """Find opcode comparison patterns."""
    opcodes = []
    
    ea = func_addr
    while ea < func_end:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for comparisons that might be opcode checks
        if mnem == 'cmp':
            # Get the value being compared
            op1_type = idc.get_operand_type(ea, 1)
            if op1_type == idc.o_imm:
                value = idc.get_operand_value(ea, 1)
                
                # Look back to see what's being compared
                prev_ea = idc.prev_head(ea)
                prev_disasm = idc.generate_disasm_line(prev_ea, 0)
                
                # Look for patterns like: mov al, [opcode_source]; cmp al, value
                opcodes.append({
                    'addr': hex(ea),
                    'value': value,
                    'value_hex': hex(value),
                    'disasm': disasm,
                    'prev_insn': prev_disasm
                })
        
        ea = idc.next_head(ea, func_end)
    
    return opcodes

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("DISASSEMBLE R53 SCRIPT INTERPRETER")
    print("="*80)
    print()
    
    # Find the script interpreter function
    func_name = "r53_script_opcode_interpreter"
    func_addr = idc.get_name_ea_simple(func_name)
    
    if func_addr == idc.BADADDR:
        print(f"[!] Function {func_name} not found")
        idc.qexit(1)
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"[!] No function at {func_addr:#x}")
        idc.qexit(1)
    
    print(f"[+] Function: {func_name}")
    print(f"    Address: {func.start_ea:#x} - {func.end_ea:#x}")
    print(f"    Size: {func.end_ea - func.start_ea} bytes")
    print()
    
    # Find opcodes
    print("[*] Searching for opcode patterns...")
    opcodes = find_opcodes(func.start_ea, func.end_ea)
    
    print(f"[+] Found {len(opcodes)} potential opcode comparisons")
    print()
    
    # Group by value
    opcode_values = {}
    for op in opcodes:
        val = op['value']
        if val not in opcode_values:
            opcode_values[val] = []
        opcode_values[val].append(op)
    
    print("[*] Unique opcode values:")
    for val in sorted(opcode_values.keys()):
        count = len(opcode_values[val])
        print(f"    Opcode {val:#04x} ({val}): {count} occurrences")
    print()
    
    # Look for switch tables
    print("[*] Searching for switch/jump tables...")
    
    switch_tables = []
    ea = func.start_ea
    while ea < func.end_ea:
        switch_info = analyze_switch_table(ea, func.end_ea)
        if switch_info:
            switch_tables.append(switch_info)
            print(f"    [+] Found {switch_info['name']} at {switch_info['address']}")
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Found {len(switch_tables)} switch tables")
    print()
    
    # Analyze data references
    print("[*] Analyzing data references...")
    
    data_refs = []
    ea = func.start_ea
    ref_count = 0
    
    while ea < func.end_ea and ref_count < 100:
        for ref in idautils.DataRefsFrom(ea):
            ref_name = idc.get_name(ref)
            if ref_name and not ref_name.startswith('loc_') and not ref_name.startswith('sub_'):
                data_refs.append({
                    'address': hex(ref),
                    'name': ref_name,
                    'access_at': hex(ea)
                })
                ref_count += 1
                if ref_count >= 100:
                    break
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Found {len(data_refs)} data references")
    
    # Show unique data references
    unique_refs = set(r['name'] for r in data_refs)
    print(f"    Unique data items: {len(unique_refs)}")
    for ref_name in sorted(unique_refs)[:20]:
        count = sum(1 for r in data_refs if r['name'] == ref_name)
        print(f"        {ref_name}: {count} refs")
    print()
    
    # Extract first 200 instructions for manual analysis
    print("[*] Extracting first 200 instructions...")
    
    first_instructions = []
    ea = func.start_ea
    count = 0
    
    while ea < func.end_ea and count < 200:
        disasm = idc.generate_disasm_line(ea, 0)
        first_instructions.append({
            'addr': hex(ea),
            'disasm': disasm
        })
        count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    # Save full disassembly
    disasm_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_script_interpreter_disasm.txt'
    with open(disasm_path, 'w') as f:
        f.write(f"DISASSEMBLY: {func_name}\n")
        f.write(f"Address: {func.start_ea:#x} - {func.end_ea:#x}\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
        f.write("="*80 + "\n\n")
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            f.write(f"{ea:#x}  {disasm}\n")
            ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Full disassembly saved to {disasm_path}")
    
    # Save analysis
    result = {
        'function': {
            'name': func_name,
            'address': hex(func.start_ea),
            'size': func.end_ea - func.start_ea
        },
        'opcode_comparisons': {
            'total': len(opcodes),
            'unique_values': len(opcode_values),
            'values': {
                hex(val): len(ops) for val, ops in opcode_values.items()
            }
        },
        'switch_tables': switch_tables,
        'data_references': {
            'total': len(data_refs),
            'unique': len(unique_refs),
            'top_refs': [
                {
                    'name': ref_name,
                    'count': sum(1 for r in data_refs if r['name'] == ref_name)
                }
                for ref_name in sorted(unique_refs, 
                    key=lambda n: sum(1 for r in data_refs if r['name'] == n), 
                    reverse=True)[:20]
            ]
        },
        'first_200_instructions': first_instructions
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_script_interpreter_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Analysis saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
