#!/usr/bin/env python3
"""
Deep analysis of polygon structure.
The data at 0x078C (F-16) looks like sequences of vertex indices!
"""

import struct
from pathlib import Path

def load_model(filepath):
    """Load complete model."""
    data = Path(filepath).read_bytes()
    header = struct.unpack('<16H', data[0:32])
    
    vertex_count = header[1]
    line_count = header[2]
    vertex_offset = 0xA0
    line_offset = vertex_offset + (vertex_count * 6)
    polygon_offset = line_offset + (line_count * 4)
    
    return {
        'data': data,
        'vertex_count': vertex_count,
        'line_count': line_count,
        'feature_count': header[6],
        'large_offset': header[4],
        'vertex_offset': vertex_offset,
        'line_offset': line_offset,
        'polygon_offset': polygon_offset,
    }

def parse_polygon_records(model):
    """Try to parse polygon section as vertex index lists."""
    data = model['data']
    offset = model['polygon_offset']
    vertex_count = model['vertex_count']
    
    records = []
    pos = offset
    record_num = 0
    
    print(f"Parsing polygon records from 0x{offset:04X}...")
    print()
    
    while pos < len(data) - 2:
        indices = []
        start_pos = pos
        
        # Read indices until we hit 0xFFFF or run out of valid indices
        while pos < len(data) - 1:
            idx = struct.unpack('<h', data[pos:pos+2])[0]  # SIGNED!
            pos += 2
            
            if idx == -1:  # 0xFFFF terminator
                break
            
            # Resolve index (negative = wrap from end)
            if idx >= 0:
                resolved = idx
            else:
                resolved = vertex_count + idx
            
            # Check if valid
            if 0 <= resolved < vertex_count:
                indices.append((idx, resolved))
            else:
                # Invalid index - this might not be a polygon record
                indices.append((idx, None))
        
        if indices:
            records.append({
                'record_num': record_num,
                'start_offset': start_pos,
                'end_offset': pos,
                'size': pos - start_pos,
                'indices': indices,
            })
            record_num += 1
            
            # Stop after reasonable number
            if record_num >= 30:
                break
    
    return records

def main():
    filepath = 'game/FALCOBJ.BIN'
    
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found")
        return
    
    print("="*80)
    print("POLYGON STRUCTURE ANALYSIS - F-16")
    print("="*80)
    print()
    
    model = load_model(filepath)
    
    print(f"Model info:")
    print(f"  Vertices: {model['vertex_count']}")
    print(f"  Lines: {model['line_count']}")
    print(f"  Feature count: {model['feature_count']}")
    print(f"  Polygon offset: 0x{model['polygon_offset']:04X}")
    print(f"  Large offset (header[4]): 0x{model['large_offset']:04X}")
    print()
    
    # Parse polygon records
    records = parse_polygon_records(model)
    
    print(f"Found {len(records)} polygon records:")
    print()
    
    for rec in records[:20]:  # First 20
        valid_count = sum(1 for _, resolved in rec['indices'] if resolved is not None)
        invalid_count = len(rec['indices']) - valid_count
        
        print(f"Record {rec['record_num']:2d} @ 0x{rec['start_offset']:04X} ({rec['size']} bytes):")
        print(f"  Indices: {len(rec['indices'])} total, {valid_count} valid, {invalid_count} invalid")
        
        # Show first 10 indices
        for i, (raw, resolved) in enumerate(rec['indices'][:10]):
            if resolved is not None:
                wrap_note = " (wrap)" if raw < 0 else ""
                print(f"    [{i}] raw={raw:5d} -> V{resolved:3d}{wrap_note}")
            else:
                print(f"    [{i}] raw={raw:5d} -> INVALID")
        
        if len(rec['indices']) > 10:
            print(f"    ... and {len(rec['indices']) - 10} more")
        print()
    
    # Statistics
    print("="*80)
    print("STATISTICS")
    print("="*80)
    print()
    
    sizes = [rec['size'] for rec in records]
    index_counts = [len(rec['indices']) for rec in records]
    
    print(f"Record sizes:")
    print(f"  Min: {min(sizes)} bytes")
    print(f"  Max: {max(sizes)} bytes")
    print(f"  Mean: {sum(sizes) / len(sizes):.1f} bytes")
    print()
    
    print(f"Index counts per record:")
    print(f"  Min: {min(index_counts)} indices")
    print(f"  Max: {max(index_counts)} indices")
    print(f"  Mean: {sum(index_counts) / len(index_counts):.1f} indices")
    print()
    
    # Most common index counts (might reveal polygon types)
    from collections import Counter
    count_dist = Counter(index_counts)
    print(f"Most common index counts:")
    for count, freq in count_dist.most_common(10):
        print(f"  {count} indices: {freq} records")
        if count == 3:
            print(f"    ^ Triangles!")
        elif count == 4:
            print(f"    ^ Quads!")
        elif count == 5:
            print(f"    ^ Pentagons")
    print()
    
    # Check if large_offset points to a specific record
    large_offset = model['large_offset']
    for rec in records:
        if rec['start_offset'] <= large_offset < rec['end_offset']:
            print(f"large_offset (0x{large_offset:04X}) points to Record {rec['record_num']}")
            break
        elif rec['start_offset'] == large_offset:
            print(f"large_offset (0x{large_offset:04X}) is the start of Record {rec['record_num']}")
            break

if __name__ == '__main__':
    main()
