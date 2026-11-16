#!/usr/bin/env python3
"""
Analyze segment 6E1E which appears to be the mission data segment.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("ANALYZE SEGMENT 6E1E (Mission Data Segment)")
    print("="*80)
    print()
    
    # Find segment R14 which contains address 0x6E1C9
    target_seg = None
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        # Check if segment contains 0x6E1C9
        if seg_ea <= 0x6E1C9 < seg_end:
            target_seg = {
                'name': seg_name,
                'start': seg_ea,
                'end': seg_end,
                'size': seg_end - seg_ea
            }
            break
    
    if not target_seg:
        print("[!] Segment containing 0x6E1C9 not found")
        idc.qexit(1)
    
    print(f"[+] Segment: {target_seg['name']}")
    print(f"    Address: {target_seg['start']:#x} - {target_seg['end']:#x}")
    print(f"    Size: {target_seg['size']} bytes")
    print()
    
    # Find all named variables in this segment
    print("[*] Named variables in segment:")
    
    variables = []
    ea = target_seg['start']
    
    while ea < target_seg['end']:
        name = idc.get_name(ea)
        if name and not name.startswith('loc_') and not name.startswith('sub_'):
            # Get size (distance to next named item)
            next_ea = idc.next_head(ea, target_seg['end'])
            size = next_ea - ea if next_ea != idc.BADADDR else 1
            
            # Get type if available
            tinfo = idaapi.tinfo_t()
            type_str = "unknown"
            if idaapi.get_tinfo(tinfo, ea):
                type_str = str(tinfo)
            
            # Get value/data
            data_bytes = []
            for i in range(min(size, 16)):  # First 16 bytes
                data_bytes.append(idc.get_wide_byte(ea + i))
            
            variables.append({
                'address': hex(ea),
                'name': name,
                'type': type_str,
                'size': size,
                'data_preview': ' '.join(f'{b:02X}' for b in data_bytes)
            })
            
            print(f"    {ea:#x}: {name} ({type_str}, ~{size} bytes)")
            if size <= 16:
                print(f"        Data: {' '.join(f'{b:02X}' for b in data_bytes)}")
        
        ea = idc.next_head(ea, target_seg['end'])
    
    print()
    print(f"[+] Found {len(variables)} named variables")
    print()
    
    # Look for potential structure arrays by checking for patterns
    print("[*] Looking for structure array patterns...")
    
    # Check for byte_6E1C9 which is heavily referenced
    byte_6e1c9_addr = idc.get_name_ea_simple("byte_6E1C9")
    if byte_6e1c9_addr != idc.BADADDR:
        print(f"\n[+] Found byte_6E1C9 at {byte_6e1c9_addr:#x}")
        
        # Extract first 256 bytes
        data = []
        for i in range(256):
            data.append(idc.get_wide_byte(byte_6e1c9_addr + i))
        
        print("    First 256 bytes (hex):")
        for i in range(0, 256, 16):
            hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(16))
            ascii_str = ''.join(chr(data[i+j]) if 32 <= data[i+j] < 127 else '.' for j in range(16))
            print(f"        +{i:#04x}: {hex_str}  {ascii_str}")
        
        # Check what's at the offsets we saw in R53
        print("\n    Checking known offsets from R53:")
        offsets_to_check = [0x17, 0x1B, 0x45, 0x47, 0x49, 0x4D]
        for offset in offsets_to_check:
            value_byte = idc.get_wide_byte(byte_6e1c9_addr + offset)
            value_word = idc.get_wide_word(byte_6e1c9_addr + offset)
            value_dword = idc.get_wide_dword(byte_6e1c9_addr + offset)
            print(f"        +{offset:#04x}: byte={value_byte:#04x} word={value_word:#06x} dword={value_dword:#010x}")
    
    # Check for pointers in the segment
    print("\n[*] Looking for far pointers (dword values that might be seg:off)...")
    
    pointers = []
    ea = target_seg['start']
    
    while ea < target_seg['end'] - 4:
        name = idc.get_name(ea)
        if name and name.startswith('dword_'):
            offset = idc.get_wide_word(ea)
            segment = idc.get_wide_word(ea + 2)
            
            pointers.append({
                'address': hex(ea),
                'name': name,
                'offset': hex(offset),
                'segment': hex(segment),
                'full': f"{segment:04X}:{offset:04X}"
            })
            
            print(f"    {ea:#x}: {name} = {segment:04X}:{offset:04X}")
        
        ea = idc.next_head(ea, target_seg['end'])
    
    print()
    print(f"[+] Found {len(pointers)} far pointers")
    print()
    
    # Save results
    result = {
        'segment': {
            'name': target_seg['name'],
            'start': hex(target_seg['start']),
            'end': hex(target_seg['end']),
            'size': target_seg['size']
        },
        'variables': variables,
        'pointers': pointers
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\segment_6e1e_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Results saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
