#!/usr/bin/env python3
"""
Extract function bytes from IDA database (with fixups applied).
Run via: idat.exe -A -S"extract_ida_bytes.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import json
import idautils
import idc
import idaapi

def main():
    # Load survey.json to get function list
    with open('analysis/ida_falconcd/survey.json', 'r') as f:
        survey = json.load(f)
    
    funcs = survey['functions']
    func_bytes = {}
    
    for f in funcs:
        ea = f['ea']
        size = f['size']
        name = f['name']
        
        # Get bytes from IDA database
        try:
            bytes_data = idaapi.get_bytes(ea, size)
            if bytes_data:
                func_bytes[name] = {
                    'ea': ea,
                    'size': size,
                    'bytes': bytes_data.hex(),
                    'is_far': f['is_far']
                }
            else:
                func_bytes[name] = {
                    'ea': ea,
                    'size': size,
                    'bytes': None,
                    'is_far': f['is_far'],
                    'error': 'No bytes'
                }
        except Exception as e:
            func_bytes[name] = {
                'ea': ea,
                'size': size,
                'bytes': None,
                'is_far': f['is_far'],
                'error': str(e)
            }
    
    # Save to file
    with open('analysis/ida_falconcd/function_bytes.json', 'w') as f:
        json.dump(func_bytes, f, indent=2)
    
    print(f"Extracted bytes for {len(func_bytes)} functions")
    idaapi.qexit(0)

if __name__ == '__main__':
    main()