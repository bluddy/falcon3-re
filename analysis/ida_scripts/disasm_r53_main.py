#!/usr/bin/env python3
"""
Disassemble the main R53 coordinator function with analysis.
"""

import idc
import idaapi
import idautils
import json
import re

def analyze_instruction(ea):
    """Analyze a single instruction for interesting patterns."""
    mnem = idc.print_insn_mnem(ea)
    disasm = idc.generate_disasm_line(ea, 0)
    
    result = {
        'addr': hex(ea),
        'mnem': mnem,
        'disasm': disasm
    }
    
    # Check for calls
    if mnem in ['call', 'lcall']:
        # Try to get target
        op0_type = idc.get_operand_type(ea, 0)
        if op0_type in [idc.o_near, idc.o_far]:
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR and target != 0:
                target_name = idc.get_name(target)
                if not target_name:
                    target_name = idc.get_func_name(target)
                if target_name:
                    result['call_target'] = target_name
                    result['call_addr'] = hex(target)
    
    # Check for data references
    if '[' in disasm:
        # Extract segment:offset patterns
        seg_match = re.search(r'(\w+):(\w+)', disasm)
        if seg_match:
            result['seg_ref'] = seg_match.group(1)
            result['offset_ref'] = seg_match.group(2)
        
        # Check for specific known segments
        if 'es:' in disasm:
            result['uses_es'] = True
        if 'ds:' in disasm:
            result['uses_ds'] = True
    
    # Check for comparisons with small values (potential enum checks)
    if mnem == 'cmp':
        op1_val = idc.get_operand_value(ea, 1)
        if 0 <= op1_val <= 20:
            result['cmp_value'] = op1_val
    
    return result

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("DISASSEMBLE R53 MAIN COORDINATOR")
    print("="*80)
    print()
    
    # Find game_mode_r53_main_coordinator
    func_name = "game_mode_r53_main_coordinator"
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
    
    # Disassemble with analysis
    print("[*] Analyzing instructions...")
    
    instructions = []
    calls = []
    data_refs = []
    comparisons = []
    
    ea = func.start_ea
    count = 0
    
    while ea < func.end_ea:
        info = analyze_instruction(ea)
        instructions.append(info)
        
        # Track calls
        if 'call_target' in info:
            calls.append({
                'addr': info['addr'],
                'target': info['call_target'],
                'target_addr': info['call_addr']
            })
        
        # Track data references
        if 'seg_ref' in info or 'offset_ref' in info:
            data_refs.append({
                'addr': info['addr'],
                'disasm': info['disasm'],
                'segment': info.get('seg_ref', ''),
                'offset': info.get('offset_ref', '')
            })
        
        # Track comparisons
        if 'cmp_value' in info:
            comparisons.append({
                'addr': info['addr'],
                'disasm': info['disasm'],
                'value': info['cmp_value']
            })
        
        count += 1
        if count % 500 == 0:
            print(f"    Processed {count} instructions...")
        
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Processed {len(instructions)} instructions")
    print(f"[+] Found {len(calls)} calls")
    print(f"[+] Found {len(data_refs)} data references")
    print(f"[+] Found {len(comparisons)} comparisons with small values")
    print()
    
    # Analyze calls
    if calls:
        print("[*] Function calls:")
        call_targets = {}
        for call in calls:
            target = call['target']
            if target not in call_targets:
                call_targets[target] = []
            call_targets[target].append(call['addr'])
        
        for target in sorted(call_targets.keys()):
            print(f"    {target}: {len(call_targets[target])} calls")
            for addr in call_targets[target][:3]:
                print(f"        at {addr}")
            if len(call_targets[target]) > 3:
                print(f"        ... and {len(call_targets[target])-3} more")
        print()
    
    # Analyze data references by segment
    if data_refs:
        print("[*] Data references by segment:")
        seg_refs = {}
        for ref in data_refs:
            seg = ref['segment'] if ref['segment'] else 'unknown'
            if seg not in seg_refs:
                seg_refs[seg] = []
            seg_refs[seg].append(ref)
        
        for seg in sorted(seg_refs.keys()):
            refs = seg_refs[seg]
            print(f"    {seg}: {len(refs)} references")
            
            # Show unique offsets
            offsets = set(r['offset'] for r in refs if r['offset'])
            if offsets:
                print(f"        Unique offsets: {len(offsets)}")
                for offset in sorted(list(offsets))[:10]:
                    print(f"            {offset}")
                if len(offsets) > 10:
                    print(f"            ... and {len(offsets)-10} more")
        print()
    
    # Analyze comparisons
    if comparisons:
        print("[*] Comparisons with small values (potential enums):")
        cmp_values = {}
        for cmp in comparisons:
            val = cmp['value']
            if val not in cmp_values:
                cmp_values[val] = []
            cmp_values[val].append(cmp)
        
        for val in sorted(cmp_values.keys()):
            cmps = cmp_values[val]
            print(f"    Value {val}: {len(cmps)} comparisons")
            for cmp in cmps[:3]:
                print(f"        {cmp['addr']}: {cmp['disasm']}")
            if len(cmps) > 3:
                print(f"        ... and {len(cmps)-3} more")
        print()
    
    # Save full disassembly
    disasm_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_main_disasm.txt'
    with open(disasm_path, 'w') as f:
        f.write(f"DISASSEMBLY: {func_name}\n")
        f.write(f"Address: {func.start_ea:#x} - {func.end_ea:#x}\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
        f.write("="*80 + "\n\n")
        
        for insn in instructions:
            f.write(f"{insn['addr']}  {insn['disasm']}\n")
            
            # Add annotations
            if 'call_target' in insn:
                f.write(f"                ; -> {insn['call_target']}\n")
            if 'cmp_value' in insn:
                f.write(f"                ; comparing with {insn['cmp_value']}\n")
    
    print(f"[+] Full disassembly saved to {disasm_path}")
    
    # Save analysis
    result = {
        'function': {
            'name': func_name,
            'address': hex(func.start_ea),
            'size': func.end_ea - func.start_ea,
            'instruction_count': len(instructions)
        },
        'calls': calls,
        'call_targets': {target: len(addrs) for target, addrs in call_targets.items()} if calls else {},
        'data_references': {
            'total': len(data_refs),
            'by_segment': {seg: len(refs) for seg, refs in seg_refs.items()}
        } if data_refs else {},
        'comparisons': {
            'total': len(comparisons),
            'by_value': {val: len(cmps) for val, cmps in cmp_values.items()}
        } if comparisons else {}
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_main_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Analysis saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
