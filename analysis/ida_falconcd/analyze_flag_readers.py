#!/usr/bin/env python3
"""
Analyze the functions that read r15_external_view_flag.
Get their disassembly to understand context.
"""

import idc
import idaapi
import idautils
import json

def get_func_info(func_addr):
    """Get basic info about a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    return {
        'name': idc.get_func_name(func_addr),
        'start': f'0x{func.start_ea:X}',
        'end': f'0x{func.end_ea:X}',
        'size': func.end_ea - func.start_ea
    }

def get_func_disasm_context(func_addr, target_ea, context_lines=20):
    """Get disassembly around a specific address within a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    lines = []
    ea = func.start_ea
    all_insns = []
    
    # Collect all instructions
    while ea < func.end_ea:
        all_insns.append({
            'addr': ea,
            'disasm': idc.generate_disasm_line(ea, 0)
        })
        ea = idc.next_head(ea, func.end_ea)
    
    # Find target instruction
    target_idx = None
    for i, insn in enumerate(all_insns):
        if insn['addr'] == target_ea:
            target_idx = i
            break
    
    if target_idx is None:
        return all_insns  # Return full function if target not found
    
    # Get context
    start_idx = max(0, target_idx - context_lines)
    end_idx = min(len(all_insns), target_idx + context_lines + 1)
    
    context = []
    for i in range(start_idx, end_idx):
        marker = " >>> " if i == target_idx else "     "
        context.append({
            'marker': marker,
            'addr': f'0x{all_insns[i]["addr"]:X}',
            'disasm': all_insns[i]['disasm']
        })
    
    return context

def main():
    idaapi.auto_wait()
    
    # Load previous results
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\flag_readers_writers.json', 'r') as f:
        data = json.load(f)
    
    print("[*] Analyzing functions that read r15_external_view_flag...")
    print()
    
    results = {}
    
    for reader in data['readers']:
        func_name = reader['func']
        func_addr = int(reader['func_addr'], 16)
        read_addr = int(reader['addr'], 16)
        
        if func_name not in results:
            print(f"{'='*70}")
            print(f"Function: {func_name} @ {reader['func_addr']}")
            print(f"{'='*70}")
            
            info = get_func_info(func_addr)
            if info:
                print(f"Size: {info['size']} bytes ({info['start']} - {info['end']})")
            
            results[func_name] = {
                'info': info,
                'reads': []
            }
        
        print(f"\nRead at {reader['addr']}:")
        print(f"  {reader['insn']}")
        print(f"\nContext:")
        
        context = get_func_disasm_context(func_addr, read_addr, context_lines=10)
        for line in context:
            print(f"{line['marker']}{line['addr']}: {line['disasm']}")
        
        results[func_name]['reads'].append({
            'addr': reader['addr'],
            'insn': reader['insn'],
            'context': context
        })
        
        print()
    
    # Save detailed analysis
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\flag_readers_detailed.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"{'='*70}")
    print("[+] Detailed analysis saved to flag_readers_detailed.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
