#!/usr/bin/env python3
import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    funcs_to_analyze = [
        ('sub_108A05', 0x108A05),
        ('r15_simulation_loop', 0x108BAC),
        ('sub_108FC2', 0x108FC2)
    ]
    
    results = []
    
    for name, addr in funcs_to_analyze:
        func = idaapi.get_func(addr)
        if func:
            results.append({
                'name': name,
                'addr': f'0x{addr:X}',
                'start': f'0x{func.start_ea:X}',
                'end': f'0x{func.end_ea:X}',
                'size': func.end_ea - func.start_ea
            })
            print(f"{name:25s} @ 0x{addr:X} size={func.end_ea - func.start_ea:5d} bytes")
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\reader_funcs_info.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nSaved to reader_funcs_info.json")
    idc.qexit(0)

if __name__ == "__main__":
    main()
