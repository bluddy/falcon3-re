import idaapi
import idautils
import idc
import json

def analyze_ranks_101_110():
    """Analyze functions ranked 101-110"""
    
    # Load top 200
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\top_200_functions.json') as f:
        top_200 = json.load(f)
    
    # Get ranks 101-110
    batch = top_200[100:110]
    
    results = []
    
    for rank, func_data in enumerate(batch, 101):
        addr = int(func_data['address'], 16)
        name = func_data['name']
        
        print(f"\n[*] Rank #{rank}: {name} @ 0x{addr:X}")
        
        # Get all instructions
        func = idaapi.get_func(addr)
        if not func:
            print(f"  [!] No function at {name}")
            continue
        
        instructions = []
        for head in idautils.Heads(func.start_ea, func.end_ea):
            if idc.is_code(idc.get_full_flags(head)):
                disasm = idc.generate_disasm_line(head, 0)
                instructions.append({
                    'addr': f'0x{head:X}',
                    'disasm': disasm
                })
        
        # Get callers
        callers = []
        for xref in idautils.XrefsTo(addr):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                caller_name = idc.get_func_name(xref.frm)
                callers.append({
                    'addr': f'0x{xref.frm:X}',
                    'name': caller_name
                })
        
        # Get callees
        callees = []
        for head in idautils.Heads(func.start_ea, func.end_ea):
            for xref in idautils.XrefsFrom(head, 0):
                if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                    callee_name = idc.get_func_name(xref.to)
                    if callee_name and callee_name != name:
                        callees.append({
                            'addr': f'0x{xref.to:X}',
                            'name': callee_name
                        })
        
        result = {
            'rank': rank,
            'name': name,
            'address': f'0x{addr:X}',
            'size': func_data['size'],
            'calls': func_data['calls'],
            'instruction_count': len(instructions),
            'instructions': instructions,
            'callers': callers[:10],  # Limit output
            'callees': list({c['name']: c for c in callees}.values())[:10]
        }
        
        results.append(result)
        
        print(f"  Instructions: {len(instructions)}")
        print(f"  Callers: {len(callers)}")
        print(f"  Callees: {len(callees)}")
        
        # Save individual file
        output_path = rf'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\func_{addr:x}_full.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  Saved to func_{addr:x}_full.json")
    
    # Save batch
    batch_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\batch_101_110_analysis.json'
    with open(batch_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[+] Batch analysis complete: {batch_path}")

if __name__ == '__main__':
    analyze_ranks_101_110()
