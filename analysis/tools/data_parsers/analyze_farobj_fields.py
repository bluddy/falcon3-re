#!/usr/bin/env python3
"""
Analyze FarObj field access patterns to determine field semantics.

Reads farobj_si_fields.json and correlates field access with function purposes.
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict

def parse_field_offset(instruction):
    """Extract field offset from instruction like 'mov ax, [si+2Eh]'"""
    # Match patterns like [si+XX], [si+XXh], [si]
    match = re.search(r'\[si(?:\+([0-9A-Fa-fx]+))?\]', instruction)
    if match:
        if match.group(1):
            offset_str = match.group(1).rstrip('h')
            try:
                return int(offset_str, 16) if 'x' not in offset_str.lower() else int(offset_str, 0)
            except:
                return None
        else:
            return 0  # [si] with no offset
    return None

def categorize_function(func_name):
    """Categorize function by name patterns"""
    func_lower = func_name.lower()
    
    if any(x in func_lower for x in ['view', 'project', 'render', 'draw', 'pixel']):
        return 'rendering'
    elif any(x in func_lower for x in ['flight', 'aircraft', 'control', 'axis']):
        return 'flight_physics'
    elif any(x in func_lower for x in ['ai', 'behavior', 'attack', 'patrol']):
        return 'ai'
    elif any(x in func_lower for x in ['terrain', 'heightmap', 'tile']):
        return 'terrain'
    elif any(x in func_lower for x in ['weapon', 'missile', 'gun']):
        return 'weapons'
    elif any(x in func_lower for x in ['entity', 'farobj', 'slot']):
        return 'entity_core'
    elif any(x in func_lower for x in ['pos', 'move', 'velocity', 'angle']):
        return 'motion'
    elif any(x in func_lower for x in ['collision', 'hit', 'damage']):
        return 'collision'
    else:
        return 'unknown'

def classify_access_type(access_type, instruction):
    """Classify the type of field access"""
    inst_lower = instruction.lower()
    
    if access_type in ['read_word', 'read_byte']:
        return 'read'
    elif access_type in ['write_word', 'write_byte']:
        return 'write'
    elif access_type == 'alu_word' or 'add' in inst_lower or 'sub' in inst_lower or 'inc' in inst_lower or 'dec' in inst_lower:
        return 'modify'
    elif 'cmp' in inst_lower or 'test' in inst_lower:
        return 'test'
    else:
        return 'other'

def main():
    # Load the field access data
    json_path = Path('ida_falconcd/farobj_si_fields.json')
    
    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return
    
    print("="*80)
    print("FAROBJ FIELD ACCESS ANALYSIS")
    print("="*80)
    print()
    
    with open(json_path, 'r') as f:
        accesses = json.load(f)
    
    print(f"Loaded {len(accesses)} field access records")
    print()
    
    # Parse and categorize all accesses
    field_data = defaultdict(lambda: {
        'count': 0,
        'functions': set(),
        'access_types': Counter(),
        'categories': Counter(),
        'instructions': []
    })
    
    for access in accesses:
        offset = parse_field_offset(access.get('dis', ''))
        if offset is None:
            continue
        
        func_name = access.get('fn', 'unknown')
        access_type = access.get('type', 'unknown')
        instruction = access.get('dis', '')
        
        field_data[offset]['count'] += 1
        field_data[offset]['functions'].add(func_name)
        
        category = categorize_function(func_name)
        field_data[offset]['categories'][category] += 1
        
        acc_class = classify_access_type(access_type, instruction)
        field_data[offset]['access_types'][acc_class] += 1
        
        # Keep first 5 instruction examples
        if len(field_data[offset]['instructions']) < 5:
            field_data[offset]['instructions'].append(instruction)
    
    # Sort fields by access frequency
    sorted_fields = sorted(field_data.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print("="*80)
    print("TOP 30 MOST-ACCESSED FAROBJ FIELDS")
    print("="*80)
    print()
    
    for offset, data in sorted_fields[:30]:
        print(f"Field +0x{offset:02X} ({offset:3d}): {data['count']:4d} accesses")
        print(f"  Functions: {len(data['functions'])} unique")
        
        # Top 3 categories
        top_cats = data['categories'].most_common(3)
        print(f"  Categories: {', '.join(f'{cat}({cnt})' for cat, cnt in top_cats)}")
        
        # Access pattern
        acc_types = data['access_types']
        pattern = f"R:{acc_types.get('read', 0)} W:{acc_types.get('write', 0)} M:{acc_types.get('modify', 0)} T:{acc_types.get('test', 0)}"
        print(f"  Access pattern: {pattern}")
        
        # Sample instructions
        print(f"  Examples:")
        for inst in data['instructions'][:3]:
            print(f"    {inst}")
        
        print()
    
    # Generate field groups by category
    print("="*80)
    print("FIELD GROUPS BY PRIMARY CATEGORY")
    print("="*80)
    print()
    
    category_fields = defaultdict(list)
    for offset, data in sorted_fields:
        if data['count'] < 5:  # Skip rarely-used fields
            continue
        primary_cat = data['categories'].most_common(1)[0][0]
        category_fields[primary_cat].append((offset, data['count']))
    
    for category in sorted(category_fields.keys()):
        fields = category_fields[category]
        print(f"{category.upper()}: {len(fields)} fields")
        for offset, count in sorted(fields, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  +0x{offset:02X}: {count:4d} accesses")
        print()
    
    # Known field mapping (from farobj.md)
    print("="*80)
    print("KNOWN VS UNKNOWN FIELDS")
    print("="*80)
    print()
    
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
        0x12: "render_flags",
        0x13: "type_flags",
        0x14: "entity_class",
        0x15: "entity_class_hi",
        0x16: "attr_a",
        0x18: "attr_b",
        0x1A: "attr_c",
        0x1C: "field_1C (unknown)",
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
    
    print("High-access UNKNOWN fields (need investigation):")
    print()
    for offset, data in sorted_fields[:40]:
        if offset not in known_fields and data['count'] >= 10:
            print(f"+0x{offset:02X} ({offset:3d}): {data['count']:4d} accesses - {data['categories'].most_common(1)[0][0]}")
    
    print()
    print("="*80)
    print("FIELD SEMANTICS HYPOTHESES")
    print("="*80)
    print()
    
    # Generate hypotheses for top unknown fields
    for offset, data in sorted_fields[:20]:
        if offset in known_fields:
            continue
        
        print(f"Field +0x{offset:02X}:")
        
        # Analyze access pattern
        reads = data['access_types'].get('read', 0)
        writes = data['access_types'].get('write', 0)
        mods = data['access_types'].get('modify', 0)
        
        if writes > reads * 2:
            print(f"  Pattern: Write-heavy ({writes}W vs {reads}R) - likely OUTPUT field")
        elif reads > writes * 2:
            print(f"  Pattern: Read-heavy ({reads}R vs {writes}W) - likely INPUT/STATE field")
        elif mods > reads + writes:
            print(f"  Pattern: Modify-heavy ({mods}M) - likely COUNTER or ACCUMULATOR")
        else:
            print(f"  Pattern: Balanced ({reads}R, {writes}W, {mods}M) - likely STATE field")
        
        # Primary category
        primary_cat, cat_count = data['categories'].most_common(1)[0]
        print(f"  Primary use: {primary_cat} ({cat_count}/{data['count']} accesses)")
        
        # Hypothesis based on category
        if primary_cat == 'motion':
            print(f"  HYPOTHESIS: Position, velocity, or angle component")
        elif primary_cat == 'rendering':
            print(f"  HYPOTHESIS: LOD, visibility flag, or projected coordinate")
        elif primary_cat == 'flight_physics':
            print(f"  HYPOTHESIS: Aerodynamic state, control surface, or thrust")
        elif primary_cat == 'ai':
            print(f"  HYPOTHESIS: Behavior state, target, or decision variable")
        elif primary_cat == 'entity_core':
            print(f"  HYPOTHESIS: Entity management, lifecycle, or reference")
        
        # Sample functions
        sample_funcs = list(data['functions'])[:3]
        print(f"  Key functions: {', '.join(sample_funcs)}")
        print()
    
    # Output summary to file
    output_path = Path('analysis/farobj_field_analysis.txt')
    with open(output_path, 'w') as f:
        f.write("FAROBJ FIELD ACCESS SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        for offset, data in sorted_fields:
            if data['count'] < 5:
                break
            
            known = known_fields.get(offset, "UNKNOWN")
            f.write(f"+0x{offset:02X} ({offset:3d}): {data['count']:4d} accesses - {known}\n")
            f.write(f"  Functions: {len(data['functions'])}\n")
            f.write(f"  Primary category: {data['categories'].most_common(1)[0]}\n")
            f.write(f"  Pattern: {data['access_types']}\n")
            f.write("\n")
    
    print(f"\nDetailed results saved to: {output_path}")

if __name__ == '__main__':
    main()
