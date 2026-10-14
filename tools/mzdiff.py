#!/usr/bin/env python3
"""
Falcon 3.0 Track C - mzdiff replacement (Python)
Compares two DOS MZ executables at verified routine locations using function_bytes.json ground truth.
"""

import argparse
import json
import os
import struct
import sys

def read_mz_header(exe_path):
    """Read MZ header and return load info."""
    with open(exe_path, 'rb') as f:
        header = f.read(64)
    if header[:2] != b'MZ':
        raise ValueError(f"Not a valid MZ executable: {exe_path}")
    header_paras = struct.unpack('<H', header[8:10])[0]
    init_cs = struct.unpack('<H', header[22:24])[0]
    init_ip = struct.unpack('<H', header[20:22])[0]
    reloc_off = struct.unpack('<H', header[24:26])[0]
    return {
        'header_paras': header_paras,
        'init_cs': init_cs,
        'init_ip': init_ip,
        'reloc_off': reloc_off,
        'load_segment': None,
    }

def get_linear_offset(exe_path, segment, offset, header_paras):
    """Convert segment:offset to file offset in MZ executable.
    
    The load module starts at header_paras * 16 bytes into the file.
    IDA segment 0x1000 = first code segment at load module offset 0.
    File offset = header_paras * 16 + (segment - 0x1000) * 16 + offset
    """
    with open(exe_path, 'rb') as f:
        f.seek(8)
        header_paras = struct.unpack('<H', f.read(2))[0]
    load_offset = header_paras * 16
    linear_in_module = (segment - 0x1000) * 16 + offset
    return load_offset + linear_in_module

def load_function_bytes(json_path):
    """Load function bytes from function_bytes.json."""
    with open(json_path, 'r') as f:
        return json.load(f)

def extract_bytes(exe_path, segment, offset, length, header_paras):
    """Extract bytes from EXE at given segment:offset."""
    file_offset = get_linear_offset(exe_path, segment, offset, header_paras)
    with open(exe_path, 'rb') as f:
        f.seek(file_offset)
        return f.read(length)

def compare_routine(ref_exe, tgt_exe, routine_name, fb_entry, header_paras):
    """Compare a single routine between two EXEs."""
    ea = fb_entry['ea']
    segment = ea >> 4
    offset = ea & 0xF
    length = fb_entry['size']
    expected_bytes = bytes.fromhex(fb_entry['bytes'])
    
    ref_bytes = extract_bytes(ref_exe, segment, offset, length, header_paras)
    tgt_bytes = extract_bytes(tgt_exe, segment, offset, length, header_paras)
    
    if ref_bytes == expected_bytes and tgt_bytes == expected_bytes:
        return True, "MATCH (both match ground truth)"
    elif ref_bytes == tgt_bytes:
        if ref_bytes == expected_bytes:
            return True, "MATCH"
        else:
            return False, f"BOTH DIFFER FROM GROUND TRUTH (ref={ref_bytes.hex()}, gt={expected_bytes.hex()})"
    else:
        for i in range(min(len(ref_bytes), len(tgt_bytes))):
            if ref_bytes[i] != tgt_bytes[i]:
                return False, f"DIFF at byte {i}: ref={ref_bytes[i]:02x} tgt={tgt_bytes[i]:02x} (gt={expected_bytes[i]:02x})"
        if len(ref_bytes) != len(tgt_bytes):
            return False, f"LENGTH DIFF: ref={len(ref_bytes)} tgt={len(tgt_bytes)}"
        return False, "UNKNOWN DIFF"

def main():
    parser = argparse.ArgumentParser(description='Compare two MZ executables at verified Falcon 3.0 routine locations')
    parser.add_argument('ref_exe', help='Reference EXE (original FALCONCD.EXE)')
    parser.add_argument('tgt_exe', help='Target EXE (spliced FALCONCD.EXE)')
    parser.add_argument('--functions', default='analysis/ida_falconcd/function_bytes.json',
                        help='Path to function_bytes.json')
    parser.add_argument('--routines', default='registry/routines.yaml',
                        help='Path to routines.yaml for verified routine list')
    parser.add_argument('--verbose', action='store_true', help='Show all comparisons')
    
    args = parser.parse_args()
    
    fb = load_function_bytes(args.functions)
    ea_to_name = {v['ea']: k for k, v in fb.items()}
    
    # Load verified routines from routines.yaml
    verified_eas = set()
    if os.path.exists(args.routines):
        import yaml
        with open(args.routines, 'r') as f:
            data = yaml.safe_load(f)
        for entry in data.get('routines', []):
            if entry.get('verified') == 'MATCH':
                verified_eas.add(entry['ea'])
        print(f"Loaded {len(verified_eas)} verified routine EAs from {args.routines}")
    else:
        print(f"Warning: {args.routines} not found, comparing all functions")
        verified_eas = set(v['ea'] for v in fb.values())
    
    ref_header = read_mz_header(args.ref_exe)
    header_paras = ref_header['header_paras']
    print(f"Reference EXE: {args.ref_exe} (header_paras={header_paras})")
    print(f"Target EXE:    {args.tgt_exe}")
    
    matched = 0
    mismatched = 0
    missing = 0
    
    for ea in sorted(verified_eas):
        if ea not in ea_to_name:
            missing += 1
            if args.verbose:
                print(f"  EA 0x{ea:X}: NOT IN GROUND TRUTH")
            continue
        
        routine_name = ea_to_name[ea]
        fb_entry = fb[routine_name]
        ok, msg = compare_routine(args.ref_exe, args.tgt_exe, routine_name, fb_entry, header_paras)
        
        if ok:
            matched += 1
            if args.verbose:
                print(f"  {routine_name}: {msg}")
        else:
            mismatched += 1
            print(f"  {routine_name}: {msg}")
    
    print(f"\n=== Summary ===")
    print(f"Verified routines checked: {len(verified_eas)}")
    print(f"Matched:     {matched}")
    print(f"Mismatched:  {mismatched}")
    print(f"Missing:     {missing}")
    
    if mismatched > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()