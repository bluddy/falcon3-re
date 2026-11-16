"""
Analyze mission slot field assignments from the loader function
"""

import json
import sys

def analyze_mission_slots():
    """Analyze the squadron_mission_file_loader function to trace MissionSlot field assignments"""
    
    # Load the analysis data
    json_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\mission_slot_loader_analysis.json'
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print(f"Function: {data['name']}")
    print(f"Address: 0x{data['address']:X}")
    print(f"Size: {data['size']} bytes")
    print(f"Instructions: {data['instruction_count']}")
    print("=" * 80)
    print()
    
    print("MISSION SLOT OPERATIONS:")
    print("-" * 80)
    for op in data['mission_slot_operations']:
        print(f"  Offset +0x{op['offset']:04X} @ 0x{op['addr']:X}")
        print(f"    {op['disasm']}")
        print()
    
    print("\nMEMORY WRITES WITH INDEXING (potential field assignments):")
    print("-" * 80)
    
    # Look for es:[bx+offset] patterns
    for write in data['memory_writes']:
        disasm = write['disasm']
        dest = write['dest']
        
        # Check if this is a write through es:[bx+offset]
        if 'es:[bx' in dest:
            print(f"  Offset +0x{write['offset']:04X} @ 0x{write['addr']:X}")
            print(f"    {disasm}")
            
            # Try to extract the offset
            if '+' in dest:
                try:
                    offset_str = dest.split('+')[1].rstrip(']')
                    if offset_str.isdigit():
                        offset_val = int(offset_str)
                        print(f"    --> Field offset: +{offset_val} (0x{offset_val:X})")
                    elif offset_str.endswith('h'):
                        offset_val = int(offset_str[:-1], 16)
                        print(f"    --> Field offset: +{offset_val} (0x{offset_val:X})")
                except:
                    pass
            print()
    
    print("\nFILE OPERATIONS:")
    print("-" * 80)
    print(f"  Found {len(data['file_operations'])} DOS INT 21h calls")
    
    print("\nKEY DATA REFERENCES:")
    print("-" * 80)
    
    # Group data refs by name
    ref_counts = {}
    for ref in data['data_refs']:
        name = ref['data_name']
        if name not in ref_counts:
            ref_counts[name] = []
        ref_counts[name].append(ref)
    
    # Show most accessed
    for name, refs in sorted(ref_counts.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
        print(f"  {name}: {len(refs)} references")
        if 'dword_79' in name or 'byte_79' in name or 'word_79' in name:
            print(f"    First reference at +0x{refs[0]['offset']:04X}: {refs[0]['disasm']}")
    
    print("\nKEY FINDINGS:")
    print("-" * 80)
    print(f"1. Mission slot pointer (dword_79D3E) is loaded {len(data['mission_slot_operations'])} times")
    print(f"2. Memory writes with indexing: {sum(1 for w in data['memory_writes'] if 'es:[bx' in w['dest'])}")
    print(f"3. Function calls: {len(data['calls'])}")
    print(f"4. Data references: {len(data['data_refs'])}")

if __name__ == '__main__':
    analyze_mission_slots()
