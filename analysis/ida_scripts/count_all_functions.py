"""
Count all functions in IDA and compare to registry.

Usage:
    idat.exe -A -S"count_all_functions.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def main():
    print("="*80)
    print("COUNTING ALL FUNCTIONS IN IDA")
    print("="*80)
    
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    all_functions = []
    undocumented = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        size = func.end_ea - func.start_ea if func else 0
        
        all_functions.append({
            'address': func_ea,
            'name': func_name,
            'size': size
        })
        
        if func_name.startswith('sub_') or func_name.startswith('loc_'):
            undocumented.append({
                'address': func_ea,
                'name': func_name,
                'size': size
            })
    
    print(f"\nTotal functions in IDA: {len(all_functions)}")
    print(f"Undocumented (sub_/loc_): {len(undocumented)}")
    print(f"Documented: {len(all_functions) - len(undocumented)}")
    
    if len(undocumented) > 0:
        print(f"\n{'='*80}")
        print(f"TOP 50 LARGEST UNDOCUMENTED FUNCTIONS")
        print("="*80)
        by_size = sorted(undocumented, key=lambda x: x['size'], reverse=True)[:50]
        for i, f in enumerate(by_size, 1):
            print(f"{i:2}. {f['address']:#08x}: {f['name']:20} ({f['size']:4}B)")
    
    # Save report
    output_path = Path(__file__).parent.parent / "ida_function_count.json"
    report = {
        'timestamp': '2026-11-15',
        'total_functions': len(all_functions),
        'undocumented': len(undocumented),
        'documented': len(all_functions) - len(undocumented),
        'undocumented_list': undocumented[:100]  # Top 100
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Report saved to: {output_path}")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
