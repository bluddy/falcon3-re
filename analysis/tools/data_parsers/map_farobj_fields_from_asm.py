#!/usr/bin/env python3
"""
Map FarObj field usage by analyzing disassembly patterns.

Extract field access patterns from actual assembly code.
"""

import re
from pathlib import Path
from collections import defaultdict, Counter

def analyze_disassembly_fields():
    """
    Scan disassembly for [si+XXh] patterns and correlate with operations.
    """
    
    ida_dir = Path("ida_falconcd")
    
    field_usage = defaultdict(lambda: {
        'reads': [],
        'writes': [],
        'compares': [],
        'arithmetic': [],
        'functions': set(),
    })
    
    # Patterns to extract
    si_field_pattern = re.compile(r'\[si\+([0-9A-Fa-f]+)h?\]')
    
    # Operation classifiers
    read_ops = ['mov.*,.*\\[si', 'cmp.*,.*\\[si', 'test.*,.*\\[si', 'add.*,.*\\[si', 'sub.*,.*\\[si']
    write_ops = ['mov.*\\[si.*,', 'inc.*\\[si', 'dec.*\\[si', 'and.*\\[si', 'or.*\\[si', 'xor.*\\[si']
    cmp_ops = ['cmp.*\\[si', 'test.*\\[si']
    alu_ops = ['add.*\\[si', 'sub.*\\[si', 'inc.*\\[si', 'dec.*\\[si']
    
    print("Scanning disassembly files...")
    
    for txt_file in sorted(ida_dir.glob("level*.txt")):
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        current_function = None
        
        for i, line in enumerate(lines):
            # Track function context
            if '#' in line and 'ea=' in line:
                func_match = re.search(r'#\\d+ (\\S+)\\s+ea=', line)
                if func_match:
                    current_function = func_match.group(1)
            
            # Look for field accesses
            match = si_field_pattern.search(line)
            if match:
                offset_str = match.group(1)
                try:
                    offset = int(offset_str, 16)
                except:
                    continue
                
                # Classify operation
                line_lower = line.lower()
                
                if any(re.search(pat, line_lower) for pat in write_ops):
                    field_usage[offset]['writes'].append(line.strip())
                elif any(re.search(pat, line_lower) for pat in cmp_ops):
                    field_usage[offset]['compares'].append(line.strip())
                elif any(re.search(pat, line_lower) for pat in alu_ops):
                    field_usage[offset]['arithmetic'].append(line.strip())
                elif any(re.search(pat, line_lower) for pat in read_ops):
                    field_usage[offset]['reads'].append(line.strip())
                
                if current_function:
                    field_usage[offset]['functions'].add(current_function)
    
    return field_usage

def categorize_field_purpose(offset, usage_data):
    """Infer field purpose from usage patterns."""
    
    reads = len(usage_data['reads'])
    writes = len(usage_data['writes'])
    cmps = len(usage_data['compares'])
    alus = len(usage_data['arithmetic'])
    
    # Get sample instruction
    sample = None
    if usage_data['reads']:
        sample = usage_data['reads'][0]
    elif usage_data['writes']:
        sample = usage_data['writes'][0]
    elif usage_data['arithmetic']:
        sample = usage_data['arithmetic'][0]
    
    # Pattern analysis
    if 'byte ptr' in (sample or ''):
        size = 'byte'
    elif 'word ptr' in (sample or ''):
        size = 'word'
    else:
        size = 'unknown'
    
    # Purpose inference
    if alus > reads + writes:
        purpose = "COUNTER/ACCUMULATOR"
    elif cmps > reads:
        purpose = "STATE_FLAG"
    elif writes > reads * 2:
        purpose = "OUTPUT"
    elif reads > writes * 2:
        purpose = "INPUT/CACHED"
    else:
        purpose = "STATE_VARIABLE"
    
    return size, purpose

def main():
    print("="*80)
    print("FAROBJ FIELD MAPPING FROM ASSEMBLY")
    print("="*80)
    print()
    
    field_usage = analyze_disassembly_fields()
    
    # Sort by total usage
    field_stats = []
    for offset, data in field_usage.items():
        total = len(data['reads']) + len(data['writes']) + len(data['compares']) + len(data['arithmetic'])
        field_stats.append((offset, total, data))
    
    field_stats.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(field_stats)} unique field offsets")
    print()
    
    # Known fields from farobj.md
    known_fields = {
        0x00: "world_x_lo",
        0x02: "world_x_hi",
        0x04: "world_y_lo",
        0x06: "world_y_hi",
        0x08: "world_z_lo",
        0x0A: "world_z_hi",
        0x0C: "angle_heading",
        0x0E: "angle_pitch",
        0x10: "angle_roll",
        0x11: "angle_roll_hi",
        0x12: "render_flags",
        0x13: "type_flags",
        0x14: "entity_class",
        0x15: "entity_class_hi",
        0x16: "attr_a",
        0x18: "attr_b",
        0x1A: "attr_c",
        0x1C: "field_1C",
        0x1E: "frame_timer",
        0x20: "cmd_field",
        0x22: "object_kind",
        0x24: "state_flags",
        0x26: "slot_flags",
        0x27: "slot_id",
        0x28: "type_ext_0",
        0x2A: "type_base",
        0x2C: "type_ext_A",
        0x74: "active",
        0x7A: "self_slot_idx",
        0xD1: "timer_active",
    }
    
    print("="*80)
    print("TOP 40 MOST-ACCESSED FIELDS")
    print("="*80)
    print()
    
    for offset, total, data in field_stats[:40]:
        known = known_fields.get(offset, "UNKNOWN")
        size, purpose = categorize_field_purpose(offset, data)
        
        reads = len(data['reads'])
        writes = len(data['writes'])
        cmps = len(data['compares'])
        alus = len(data['arithmetic'])
        funcs = len(data['functions'])
        
        print(f"Field +0x{offset:02X} ({offset:3d}): {total:3d} accesses - {known}")
        print(f"  Type: {size:6s}  Purpose: {purpose}")
        print(f"  Pattern: R:{reads:2d} W:{writes:2d} CMP:{cmps:2d} ALU:{alus:2d}  Functions:{funcs}")
        
        # Show sample instructions
        if data['writes'] and len(data['writes']) <= 3:
            print(f"  Writes:")
            for w in data['writes'][:3]:
                # Extract just the instruction part
                inst = re.search(r'(mov|inc|dec|add|sub|and|or|xor).*', w)
                if inst:
                    print(f"    {inst.group()}")
        elif data['arithmetic']:
            print(f"  Arithmetic:")
            for a in data['arithmetic'][:2]:
                inst = re.search(r'(add|sub|inc|dec).*', a)
                if inst:
                    print(f"    {a}")
        elif data['reads']:
            print(f"  Read example:")
            inst = re.search(r'(mov|cmp).*', data['reads'][0])
            if inst:
                print(f"    {inst.group()}")
        
        # Sample functions
        sample_funcs = list(data['functions'])[:3]
        if sample_funcs:
            print(f"  Functions: {', '.join(sample_funcs)}")
        
        print()
    
    # Focus on UNKNOWN high-usage fields
    print("="*80)
    print("HIGH-PRIORITY UNKNOWN FIELDS (need documentation)")
    print("="*80)
    print()
    
    for offset, total, data in field_stats:
        if offset not in known_fields and total >= 5:
            size, purpose = categorize_field_purpose(offset, data)
            
            reads = len(data['reads'])
            writes = len(data['writes'])
            cmps = len(data['compares'])
            alus = len(data['arithmetic'])
            
            print(f"+0x{offset:02X}: {total:3d} accesses - {size} {purpose}")
            print(f"       R:{reads} W:{writes} CMP:{cmps} ALU:{alus}")
            
            # Key functions
            funcs = list(data['functions'])[:5]
            if funcs:
                print(f"       Functions: {', '.join(funcs)}")
            
            # Best example instruction
            best_example = None
            if data['arithmetic']:
                best_example = data['arithmetic'][0]
            elif data['writes']:
                best_example = data['writes'][0]
            elif data['reads']:
                best_example = data['reads'][0]
            
            if best_example:
                inst = re.search(r'0x[0-9A-F]+: (.+)', best_example)
                if inst:
                    print(f"       Example: {inst.group(1)}")
            
            print()
    
    # Output to file
    output_path = Path("analysis/farobj_field_mapping.txt")
    with open(output_path, 'w') as f:
        f.write("FAROBJ FIELD MAPPING FROM DISASSEMBLY\\n")
        f.write("="*80 + "\\n\\n")
        
        for offset, total, data in field_stats:
            known = known_fields.get(offset, "UNKNOWN")
            size, purpose = categorize_field_purpose(offset, data)
            
            f.write(f"+0x{offset:02X}: {total} accesses - {known}\\n")
            f.write(f"  Type: {size}, Purpose: {purpose}\\n")
            f.write(f"  R:{len(data['reads'])} W:{len(data['writes'])} ")
            f.write(f"CMP:{len(data['compares'])} ALU:{len(data['arithmetic'])}\\n")
            f.write(f"  Functions: {', '.join(list(data['functions'])[:5])}\\n")
            f.write("\\n")
    
    print(f"\\nComplete mapping saved to: {output_path}")

if __name__ == '__main__':
    main()
