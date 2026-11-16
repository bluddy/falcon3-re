#!/usr/bin/env python3
"""
Map the complete R14 segment (mission data segment) structure.
"""

import idc
import idaapi
import idautils
import json

def dump_memory_region(start_ea, size, label=""):
    """Dump memory as hex and ASCII."""
    lines = []
    
    if label:
        lines.append(f"\n{label}")
        lines.append("="*80)
    
    for offset in range(0, size, 16):
        if start_ea + offset >= idc.get_segm_end(idc.get_segm_start(start_ea)):
            break
        
        # Get 16 bytes
        hex_bytes = []
        ascii_str = []
        for i in range(16):
            if offset + i < size:
                b = idc.get_wide_byte(start_ea + offset + i)
                hex_bytes.append(f"{b:02X}")
                ascii_str.append(chr(b) if 32 <= b < 127 else '.')
            else:
                hex_bytes.append("  ")
                ascii_str.append(" ")
        
        hex_str = ' '.join(hex_bytes)
        lines.append(f"  {start_ea + offset:#08x}: {hex_str}  {''.join(ascii_str)}")
    
    return '\n'.join(lines)

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("MAP R14 MISSION DATA SEGMENT")
    print("="*80)
    print()
    
    # Find R14 segment (contains 0x6E1C9)
    target_seg = None
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        if seg_ea <= 0x6E1C9 < seg_end:
            target_seg = {
                'name': seg_name,
                'start': seg_ea,
                'end': seg_end,
                'size': seg_end - seg_ea
            }
            break
    
    if not target_seg:
        print("[!] R14 segment not found")
        idc.qexit(1)
    
    print(f"[+] Segment: {target_seg['name']}")
    print(f"    Address: {target_seg['start']:#x} - {target_seg['end']:#x}")
    print(f"    Size: {target_seg['size']} bytes")
    print()
    
    # Focus on byte_6E1C9 region
    byte_6e1c9_addr = idc.get_name_ea_simple("byte_6E1C9")
    if byte_6e1c9_addr == idc.BADADDR:
        print("[!] byte_6E1C9 not found")
        idc.qexit(1)
    
    print(f"[+] Found byte_6E1C9 at {byte_6e1c9_addr:#x}")
    print()
    
    # Dump 512 bytes starting from byte_6E1C9
    print("[*] Dumping byte_6E1C9 region (512 bytes)...")
    dump_text = dump_memory_region(byte_6e1c9_addr, 512, "byte_6E1C9 Memory Dump")
    print(dump_text)
    print()
    
    # Check specific offsets we know about from R53
    print("[*] Known offsets from R53 analysis:")
    known_offsets = {
        0x17: "Loop counter / Pilot index",
        0x1B: "Far pointer",
        0x45: "Bit flags (masked with 7)",
        0x47: "Pointer to pilot array",
        0x49: "Data field",
        0x4D: "Bit flags (masked with 1)"
    }
    
    for offset, description in sorted(known_offsets.items()):
        addr = byte_6e1c9_addr + offset
        
        # Read as different types
        byte_val = idc.get_wide_byte(addr)
        word_val = idc.get_wide_word(addr)
        dword_val = idc.get_wide_dword(addr)
        
        print(f"  +{offset:#04x} ({offset:3d}): {description}")
        print(f"      Byte:  {byte_val:#04x} ({byte_val})")
        print(f"      Word:  {word_val:#06x} ({word_val})")
        print(f"      Dword: {dword_val:#010x} (seg:off = {(dword_val >> 16):#06x}:{(dword_val & 0xFFFF):#06x})")
    print()
    
    # Find all far pointers (dword values) in byte_6E1C9 region
    print("[*] Scanning for far pointers in byte_6E1C9 region...")
    
    pointers_found = []
    for offset in range(0, 256, 2):  # Check every word boundary
        addr = byte_6e1c9_addr + offset
        if addr >= target_seg['end']:
            break
        
        # Check if this looks like a far pointer
        dword_val = idc.get_wide_dword(addr)
        segment = (dword_val >> 16) & 0xFFFF
        off = dword_val & 0xFFFF
        
        # Check if segment looks reasonable (in range 0x1000-0xF000)
        if 0x1000 <= segment <= 0xF000 and off < 0xFFF0:
            # Check if the target exists
            linear_addr = (segment << 4) + off  # Real mode addressing
            
            pointers_found.append({
                'offset': offset,
                'offset_hex': hex(offset),
                'segment': hex(segment),
                'offset_val': hex(off),
                'full': f"{segment:04X}:{off:04X}",
                'linear': hex(linear_addr)
            })
            
            print(f"    +{offset:#04x}: {segment:04X}:{off:04X}")
    
    print(f"[+] Found {len(pointers_found)} potential far pointers")
    print()
    
    # Look for arrays of known structure sizes
    print("[*] Searching for structure array patterns...")
    
    # Known sizes: 0x42 (66 PilotRecord), 0x82 (130 FlightRecord), 0x1C (28 MenuElement)
    struct_sizes = {
        0x42: "PilotRecord",
        0x82: "FlightRecord",
        0x1C: "MenuElement"
    }
    
    # Save complete dump
    dump_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r14_mission_data_dump.txt'
    with open(dump_path, 'w') as f:
        f.write("R14 MISSION DATA SEGMENT - COMPLETE DUMP\n")
        f.write("="*80 + "\n\n")
        f.write(f"Segment: {target_seg['name']}\n")
        f.write(f"Address: {target_seg['start']:#x} - {target_seg['end']:#x}\n")
        f.write(f"Size: {target_seg['size']} bytes\n\n")
        
        # Dump entire segment
        dump = dump_memory_region(target_seg['start'], target_seg['size'], 
                                   "Complete Segment Dump")
        f.write(dump)
        f.write("\n\n")
        
        # Annotated byte_6E1C9 region
        f.write("\n" + "="*80 + "\n")
        f.write("byte_6E1C9 ANNOTATED DUMP\n")
        f.write("="*80 + "\n\n")
        
        for offset, description in sorted(known_offsets.items()):
            addr = byte_6e1c9_addr + offset
            byte_val = idc.get_wide_byte(addr)
            word_val = idc.get_wide_word(addr)
            dword_val = idc.get_wide_dword(addr)
            
            f.write(f"+{offset:#04x} ({offset:3d}): {description}\n")
            f.write(f"    Byte:  {byte_val:#04x} ({byte_val})\n")
            f.write(f"    Word:  {word_val:#06x} ({word_val})\n")
            f.write(f"    Dword: {dword_val:#010x}\n\n")
    
    print(f"[+] Complete dump saved to {dump_path}")
    
    # Save analysis
    result = {
        'segment': {
            'name': target_seg['name'],
            'start': hex(target_seg['start']),
            'end': hex(target_seg['end']),
            'size': target_seg['size']
        },
        'byte_6E1C9': {
            'address': hex(byte_6e1c9_addr),
            'known_offsets': {
                hex(k): v for k, v in known_offsets.items()
            },
            'values': {
                hex(offset): {
                    'description': description,
                    'byte': idc.get_wide_byte(byte_6e1c9_addr + offset),
                    'word': idc.get_wide_word(byte_6e1c9_addr + offset),
                    'dword': idc.get_wide_dword(byte_6e1c9_addr + offset)
                }
                for offset, description in known_offsets.items()
            }
        },
        'far_pointers': pointers_found
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r14_mission_data_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Analysis saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
