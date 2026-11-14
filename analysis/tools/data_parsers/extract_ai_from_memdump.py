#!/usr/bin/env python3
"""
Extract AI context array from Falcon 3.0 memory dump

The AI contexts are at segment 0x65A7, offset 0x000C
In a linear memory dump, we need to calculate the linear address.

DOS real mode address calculation:
    Linear = (Segment × 16) + Offset
    
For 0x65A7:0x000C:
    Linear = (0x65A7 × 16) + 0x000C
    Linear = 0x65A70 + 0x000C
    Linear = 0x65A7C

The memory dumps appear to be 1MB (1048576 bytes) starting from some base.
We'll search for the pattern or extract at known offset.
"""

import struct
import sys
import os

def calculate_linear_address(segment, offset):
    """Calculate DOS real mode linear address"""
    return (segment * 16) + offset

def extract_ai_contexts(dump_path, output_path=None):
    """Extract 960 bytes of AI context array from memory dump"""
    
    # Calculate linear address
    segment = 0x65A7
    offset = 0x000C
    linear_addr = calculate_linear_address(segment, offset)
    
    print(f"AI Context Array Location:")
    print(f"  Segment:Offset = 0x{segment:04X}:0x{offset:04X}")
    print(f"  Linear address = 0x{linear_addr:06X} ({linear_addr})")
    print()
    
    # Read the memory dump
    try:
        with open(dump_path, 'rb') as f:
            dump_data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{dump_path}' not found")
        return None
    
    dump_size = len(dump_data)
    print(f"Memory dump size: {dump_size} bytes (0x{dump_size:X})")
    print()
    
    # Try to extract at the linear address
    # The dump might start at offset 0, or at some other base
    # Let's try a few possibilities
    
    possible_offsets = [
        linear_addr,                # Direct linear address
        linear_addr % dump_size,    # Wrapped if dump is smaller
        linear_addr - 0x10000,      # If dump starts at 64KB
        linear_addr - 0x1000,       # If dump starts at 4KB
    ]
    
    contexts_data = None
    used_offset = None
    
    for attempt_offset in possible_offsets:
        if attempt_offset < 0 or attempt_offset + 960 > dump_size:
            continue
        
        # Extract 960 bytes
        test_data = dump_data[attempt_offset:attempt_offset+960]
        
        # Quick validation: check if this looks like AI context data
        # Each 24-byte context starts with:
        #   - Byte 0: active flag (0 or 1 typically)
        #   - Bytes 1-2: entity_id (word)
        #   - Bytes 3-4: data_table_idx (word, often 0xFFFF if unused)
        
        # Count how many contexts look valid
        valid_count = 0
        for i in range(40):
            ctx_offset = i * 24
            if ctx_offset + 24 > len(test_data):
                break
            
            active = test_data[ctx_offset]
            entity_id = struct.unpack_from('<H', test_data, ctx_offset + 1)[0]
            data_idx = struct.unpack_from('<H', test_data, ctx_offset + 3)[0]
            
            # Heuristic: active should be 0 or 1, entity_id should be reasonable
            if active <= 1:
                valid_count += 1
        
        if valid_count >= 30:  # At least 30/40 contexts look valid
            contexts_data = test_data
            used_offset = attempt_offset
            print(f"[OK] Found valid AI context data at offset 0x{attempt_offset:06X}")
            print(f"  {valid_count}/40 contexts appear valid")
            break
    
    if contexts_data is None:
        print("[FAIL] Could not locate AI context array in memory dump")
        print("  Trying fallback: search for pattern...")
        
        # Fallback: search for a distinctive pattern
        # Look for multiple consecutive 24-byte blocks with reasonable data
        contexts_data, used_offset = search_for_contexts(dump_data)
    
    if contexts_data is None:
        print("[FAIL] Failed to find AI contexts in dump")
        return None
    
    # Write output
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(contexts_data)
        print(f"\n[OK] Extracted 960 bytes to: {output_path}")
    
    return contexts_data

def search_for_contexts(dump_data):
    """Search for AI context array pattern in dump"""
    print("  Searching for context pattern...")
    
    # Search every 16-byte aligned position (paragraphs)
    for offset in range(0, len(dump_data) - 960, 16):
        test_data = dump_data[offset:offset+960]
        
        valid_count = 0
        active_count = 0
        
        for i in range(40):
            ctx_offset = i * 24
            if ctx_offset + 24 > len(test_data):
                break
            
            active = test_data[ctx_offset]
            entity_id = struct.unpack_from('<H', test_data, ctx_offset + 1)[0]
            data_idx = struct.unpack_from('<H', test_data, ctx_offset + 3)[0]
            behavior = struct.unpack_from('<H', test_data, ctx_offset + 11)[0]
            
            # More strict heuristic
            if active <= 1:
                valid_count += 1
                if active == 1:
                    active_count += 1
        
        if valid_count >= 35 and active_count >= 1:
            print(f"  [OK] Found pattern at offset 0x{offset:06X}")
            print(f"    {valid_count}/40 valid, {active_count} active")
            return test_data, offset
    
    return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_ai_from_memdump.py <memdump.bin> [output.bin]")
        print()
        print("Example:")
        print("  python extract_ai_from_memdump.py memdump/MEMDUMP6_flight_takeoff.BIN ai_contexts.bin")
        sys.exit(1)
    
    dump_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "ai_contexts.bin"
    
    print("="*70)
    print("Falcon 3.0 AI Context Extractor")
    print("="*70)
    print()
    
    contexts_data = extract_ai_contexts(dump_path, output_path)
    
    if contexts_data:
        print()
        print("="*70)
        print("Extraction successful!")
        print()
        print("Next steps:")
        print(f"  python parse_ai_contexts.py {output_path}")
        print("="*70)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
