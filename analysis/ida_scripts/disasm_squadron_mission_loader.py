#!/usr/bin/env python3
"""
Disassemble squadron_mission_file_loader function to find mission data structures.
"""

import idc
import idaapi
import idautils
import json

def analyze_function(func_addr, func_name):
    """Analyze a function in detail."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    # Count instructions
    insn_count = 0
    ea = func.start_ea
    while ea < func.end_ea:
        insn_count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    # Find data references
    data_refs = []
    ea = func.start_ea
    while ea < func.end_ea:
        for ref in idautils.DataRefsFrom(ea):
            ref_name = idc.get_name(ref)
            if ref_name and not ref_name.startswith('loc_') and not ref_name.startswith('sub_'):
                data_refs.append({
                    'addr': hex(ref),
                    'name': ref_name,
                    'access_at': hex(ea)
                })
        ea = idc.next_head(ea, func.end_ea)
    
    # Find function calls
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR and target != 0:
                target_name = idc.get_func_name(target)
                if target_name:
                    calls.append({
                        'addr': hex(ea),
                        'target': hex(target),
                        'name': target_name
                    })
        ea = idc.next_head(ea, func.end_ea)
    
    # Look for structure size multiplications
    multiplications = []
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        if mnem == 'imul':
            # Extract the multiplier
            if 'dx' in disasm or 'cx' in disasm or 'bx' in disasm:
                # Get operand value
                op1_type = idc.get_operand_type(ea, 1)
                if op1_type == idc.o_imm:
                    mult_val = idc.get_operand_value(ea, 1)
                    if mult_val in [0x1C, 0x42, 0x82]:  # Known structure sizes
                        multiplications.append({
                            'addr': hex(ea),
                            'value': mult_val,
                            'value_hex': hex(mult_val),
                            'disasm': disasm
                        })
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Get unique data references
    unique_refs = {}
    for ref in data_refs:
        name = ref['name']
        if name not in unique_refs:
            unique_refs[name] = []
        unique_refs[name].append(ref['access_at'])
    
    return {
        'name': func_name,
        'address': hex(func.start_ea),
        'size': func.end_ea - func.start_ea,
        'instructions': insn_count,
        'calls': calls,
        'data_refs': data_refs,
        'unique_data_refs': {k: len(v) for k, v in unique_refs.items()},
        'structure_multiplications': multiplications
    }

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("DISASSEMBLE SQUADRON MISSION FILE LOADER")
    print("="*80)
    print()
    
    # Find the function
    func_name = "squadron_mission_file_loader"
    func_addr = idc.get_name_ea_simple(func_name)
    
    if func_addr == idc.BADADDR:
        print(f"[!] Function {func_name} not found")
        print("[*] Searching for similar names...")
        
        found = []
        for seg_ea in idautils.Segments():
            for func_ea in idautils.Functions(seg_ea, idc.get_segm_end(seg_ea)):
                name = idc.get_func_name(func_ea)
                if name and ('squadron' in name.lower() or 'mission' in name.lower()):
                    found.append((hex(func_ea), name))
        
        if found:
            print(f"[+] Found {len(found)} related functions:")
            for addr, name in found[:20]:
                print(f"    {addr}: {name}")
        
        idc.qexit(1)
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"[!] No function at {func_addr:#x}")
        idc.qexit(1)
    
    print(f"[+] Function: {func_name}")
    print(f"    Address: {func.start_ea:#x} - {func.end_ea:#x}")
    print(f"    Size: {func.end_ea - func.start_ea} bytes")
    print()
    
    # Analyze function
    print("[*] Analyzing function...")
    analysis = analyze_function(func_addr, func_name)
    
    print(f"    Instructions: {analysis['instructions']}")
    print(f"    Function calls: {len(analysis['calls'])}")
    print(f"    Data references: {len(analysis['unique_data_refs'])}")
    print(f"    Structure multiplications: {len(analysis['structure_multiplications'])}")
    print()
    
    # Show structure multiplications
    if analysis['structure_multiplications']:
        print("[*] Structure size multiplications found:")
        for mult in analysis['structure_multiplications']:
            size_name = {
                0x1C: "MenuElement (28 bytes)",
                0x42: "PilotRecord (66 bytes)",
                0x82: "FlightRecord (130 bytes)"
            }.get(mult['value'], f"Unknown ({mult['value']} bytes)")
            
            print(f"    {mult['addr']}: × {mult['value_hex']} ({size_name})")
            print(f"        {mult['disasm']}")
        print()
    
    # Show top data references
    if analysis['unique_data_refs']:
        print("[*] Top 20 data references:")
        sorted_refs = sorted(analysis['unique_data_refs'].items(), 
                            key=lambda x: x[1], reverse=True)
        for name, count in sorted_refs[:20]:
            print(f"    {name}: {count} refs")
        print()
    
    # Show function calls
    if analysis['calls']:
        print(f"[*] Function calls ({len(analysis['calls'])} total):")
        call_counts = {}
        for call in analysis['calls']:
            name = call['name']
            call_counts[name] = call_counts.get(name, 0) + 1
        
        for name, count in sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"    {name}: {count} calls")
        print()
    
    # Save full disassembly
    disasm_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\squadron_mission_loader_disasm.txt'
    with open(disasm_path, 'w') as f:
        f.write(f"DISASSEMBLY: {func_name}\n")
        f.write(f"Address: {func.start_ea:#x} - {func.end_ea:#x}\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
        f.write(f"Instructions: {analysis['instructions']}\n")
        f.write("="*80 + "\n\n")
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Add annotations for interesting instructions
            annotation = ""
            mnem = idc.print_insn_mnem(ea)
            
            # Annotate structure multiplications
            if mnem == 'imul':
                for mult in analysis['structure_multiplications']:
                    if int(mult['addr'], 16) == ea:
                        size_name = {
                            0x1C: "MenuElement",
                            0x42: "PilotRecord",
                            0x82: "FlightRecord"
                        }.get(mult['value'], "Unknown")
                        annotation = f"  ; Multiply by {size_name} size"
                        break
            
            # Annotate calls to important functions
            if mnem == 'call':
                for call in analysis['calls']:
                    if int(call['addr'], 16) == ea:
                        if 'file' in call['name'].lower() or 'read' in call['name'].lower():
                            annotation = f"  ; -> {call['name']}"
                        break
            
            f.write(f"{ea:#x}  {disasm}{annotation}\n")
            ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Full disassembly saved to {disasm_path}")
    
    # Look for first 200 instructions patterns
    print("\n[*] Extracting first 200 instructions for pattern analysis...")
    first_200 = []
    ea = func.start_ea
    count = 0
    
    while ea < func.end_ea and count < 200:
        disasm = idc.generate_disasm_line(ea, 0)
        first_200.append({
            'addr': hex(ea),
            'disasm': disasm
        })
        count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    # Save analysis
    result = {
        'function': analysis,
        'first_200_instructions': first_200
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\squadron_mission_loader_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Analysis saved to {output_path}")
    
    # Create summary
    summary_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\squadron_mission_loader_summary.txt'
    with open(summary_path, 'w') as f:
        f.write("SQUADRON MISSION FILE LOADER - ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Function: {func_name}\n")
        f.write(f"Address: {analysis['address']}\n")
        f.write(f"Size: {analysis['size']} bytes\n")
        f.write(f"Instructions: {analysis['instructions']}\n\n")
        
        f.write(f"Structure Multiplications ({len(analysis['structure_multiplications'])}):\n")
        for mult in analysis['structure_multiplications']:
            f.write(f"  {mult['addr']}: {mult['disasm']}\n")
        
        f.write(f"\nTop Data References:\n")
        for name, count in sorted(analysis['unique_data_refs'].items(), 
                                  key=lambda x: x[1], reverse=True)[:20]:
            f.write(f"  {name}: {count} refs\n")
        
        f.write(f"\nFunction Calls:\n")
        call_counts = {}
        for call in analysis['calls']:
            name = call['name']
            call_counts[name] = call_counts.get(name, 0) + 1
        
        for name, count in sorted(call_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {name}: {count} calls\n")
    
    print(f"[+] Summary saved to {summary_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
