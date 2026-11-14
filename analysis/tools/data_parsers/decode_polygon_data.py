#!/usr/bin/env python3
"""
Decode the polygon/surface data section that comes after lines in *OBJ.BIN files.
This is the remaining 5-7KB of unknown data.
"""

import struct
from pathlib import Path

def load_model_header(filepath):
    """Load and parse model file header."""
    data = Path(filepath).read_bytes()
    header = struct.unpack('<16H', data[0:32])
    
    return {
        'data': data,
        'file_size': len(data),
        'file_size_minus_10': header[0],
        'vertex_count': header[1],
        'line_count': header[2],
        'unknown_06': header[3],
        'large_offset': header[4],  # This might point to polygon data!
        'version': header[5],
        'feature_count': header[6],  # This might be polygon/surface count
        'unknown_0E': header[7],
        'unknown_10': header[8],
        'unknown_12': header[9],
        'scale_factor': header[10],
        'flag_constant': header[11],
        'constant_18': header[12],
        'unknown_1A': header[13],
        'terminator': header[14],
        'constant_1E': header[15],
    }

def compute_offsets(model):
    """Compute where each section starts and ends."""
    vertex_offset = 0xA0  # Known for F-16
    vertex_size = 6
    line_size = 4
    
    vertex_end = vertex_offset + (model['vertex_count'] * vertex_size)
    line_offset = vertex_end
    line_end = line_offset + (model['line_count'] * line_size)
    polygon_offset = line_end
    polygon_size = model['file_size'] - polygon_offset
    
    return {
        'vertex_offset': vertex_offset,
        'vertex_end': vertex_end,
        'line_offset': line_offset,
        'line_end': line_end,
        'polygon_offset': polygon_offset,
        'polygon_size': polygon_size,
    }

def analyze_polygon_section_patterns(data, offset, size):
    """Look for patterns in the polygon data section."""
    patterns = {
        'zeros': 0,
        'ones': 0,
        'ffs': 0,
        'low_bytes': 0,  # Values 0-127
        'high_bytes': 0,  # Values 128-255
        'word_patterns': {},
    }
    
    # Byte-level analysis
    for i in range(min(size, len(data) - offset)):
        byte = data[offset + i]
        if byte == 0x00:
            patterns['zeros'] += 1
        elif byte == 0xFF:
            patterns['ffs'] += 1
        elif byte < 128:
            patterns['low_bytes'] += 1
        else:
            patterns['high_bytes'] += 1
    
    # Word-level analysis (look for repeating patterns)
    for i in range(0, min(size - 1, len(data) - offset - 1), 2):
        word = struct.unpack('<H', data[offset+i:offset+i+2])[0]
        patterns['word_patterns'][word] = patterns['word_patterns'].get(word, 0) + 1
    
    return patterns

def look_for_structures(data, offset, size, vertex_count, line_count):
    """Look for structured data that might reference vertices/lines."""
    
    # Try to find patterns that look like indices
    potential_indices = []
    
    # Check as words (2 bytes)
    for i in range(0, min(size - 1, len(data) - offset - 1), 2):
        word = struct.unpack('<H', data[offset+i:offset+i+2])[0]
        
        # Could this be a vertex index?
        if 0 <= word < vertex_count or (word >= 0xFF00):  # Absolute or negative
            potential_indices.append(('vertex?', offset + i, word))
        
        # Could this be a line index?
        if 0 <= word < line_count:
            potential_indices.append(('line?', offset + i, word))
    
    return potential_indices[:100]  # First 100 potential indices

def analyze_by_feature_count(data, offset, size, feature_count):
    """Try to parse data as feature_count records."""
    if size < feature_count * 2:
        return None
    
    # Try different record sizes
    for record_size in [2, 4, 6, 8, 10, 12, 16, 20, 24, 32]:
        if size % record_size != 0:
            continue
        
        actual_count = size // record_size
        if actual_count == feature_count:
            print(f"  MATCH: {feature_count} records of {record_size} bytes each!")
            return analyze_fixed_records(data, offset, record_size, feature_count)
        elif abs(actual_count - feature_count) < 10:
            print(f"  NEAR MATCH: {actual_count} records of {record_size} bytes (expected {feature_count})")
    
    return None

def analyze_fixed_records(data, offset, record_size, count):
    """Analyze data as fixed-size records."""
    records = []
    for i in range(min(count, 20)):  # First 20 records
        rec_offset = offset + (i * record_size)
        rec_data = data[rec_offset:rec_offset+record_size]
        
        # Try different interpretations
        if record_size == 2:
            val = struct.unpack('<H', rec_data)[0]
            records.append(f"Record {i}: 0x{val:04X} ({val})")
        elif record_size == 4:
            v1, v2 = struct.unpack('<HH', rec_data)
            records.append(f"Record {i}: ({v1:5d}, {v2:5d}) = 0x{v1:04X}, 0x{v2:04X}")
        elif record_size == 6:
            v1, v2, v3 = struct.unpack('<HHH', rec_data)
            records.append(f"Record {i}: ({v1:5d}, {v2:5d}, {v3:5d})")
        elif record_size >= 8:
            words = struct.unpack(f'<{record_size//2}H', rec_data)
            records.append(f"Record {i}: {words}")
    
    return records

def check_large_offset_field(model, offsets):
    """Check if header's large_offset field points to something meaningful."""
    large_offset = model['large_offset']
    
    print(f"\nChecking large_offset field: 0x{large_offset:04X} ({large_offset})")
    
    if large_offset < model['file_size']:
        # It's within the file - what's there?
        position_name = "UNKNOWN"
        if large_offset < offsets['vertex_end']:
            position_name = "INSIDE vertex data"
        elif large_offset < offsets['line_end']:
            position_name = "INSIDE line data"
        else:
            position_name = "INSIDE polygon data"
        
        print(f"  Points to: {position_name}")
        print(f"  File sections:")
        print(f"    Vertices: 0x{offsets['vertex_offset']:04X} - 0x{offsets['vertex_end']:04X}")
        print(f"    Lines:    0x{offsets['line_offset']:04X} - 0x{offsets['line_end']:04X}")
        print(f"    Polygons: 0x{offsets['polygon_offset']:04X} - EOF")
        
        # Show what's at that offset
        if large_offset < len(model['data']) - 8:
            sample = model['data'][large_offset:large_offset+16]
            print(f"  Data at offset: {' '.join(f'{b:02X}' for b in sample)}")
            
            # Try as words
            words = struct.unpack('<8H', sample)
            print(f"  As words: {words}")
    
    return large_offset

def main():
    files = [
        ('game/FALCOBJ.BIN', 'F-16 Fighting Falcon'),
        ('game/HORNOBJ.BIN', 'F/A-18 Hornet'),
        ('game/FULCOBJ.BIN', 'MiG-29 Fulcrum'),
    ]
    
    for filepath, name in files:
        if not Path(filepath).exists():
            print(f"Skipping {name} - file not found")
            continue
        
        print("="*80)
        print(f"ANALYZING: {name}")
        print("="*80)
        
        model = load_model_header(filepath)
        offsets = compute_offsets(model)
        
        print(f"\nFile: {Path(filepath).name}")
        print(f"  Total size: {model['file_size']} bytes")
        print(f"  Vertices: {model['vertex_count']}")
        print(f"  Lines: {model['line_count']}")
        print(f"  Feature count (header[6]): {model['feature_count']}")
        print(f"  Version: {model['version']}")
        
        print(f"\nSection layout:")
        print(f"  Vertices: 0x{offsets['vertex_offset']:04X} - 0x{offsets['vertex_end']:04X} ({offsets['vertex_end'] - offsets['vertex_offset']} bytes)")
        print(f"  Lines:    0x{offsets['line_offset']:04X} - 0x{offsets['line_end']:04X} ({offsets['line_end'] - offsets['line_offset']} bytes)")
        print(f"  Polygons: 0x{offsets['polygon_offset']:04X} - EOF ({offsets['polygon_size']} bytes)")
        
        # Check large_offset field
        check_large_offset_field(model, offsets)
        
        # Analyze polygon section
        print(f"\nPolygon section analysis ({offsets['polygon_size']} bytes):")
        patterns = analyze_polygon_section_patterns(
            model['data'], 
            offsets['polygon_offset'], 
            offsets['polygon_size']
        )
        
        print(f"  Byte patterns:")
        print(f"    Zeros (0x00): {patterns['zeros']}")
        print(f"    Ones (0xFF): {patterns['ffs']}")
        print(f"    Low bytes (0-127): {patterns['low_bytes']}")
        print(f"    High bytes (128-255): {patterns['high_bytes']}")
        
        # Most common words
        top_words = sorted(patterns['word_patterns'].items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"  Top 10 most common words:")
        for word, count in top_words:
            print(f"    0x{word:04X} ({word:5d}): appears {count} times")
        
        # Look for index-like structures
        print(f"\nLooking for vertex/line index references:")
        indices = look_for_structures(
            model['data'],
            offsets['polygon_offset'],
            offsets['polygon_size'],
            model['vertex_count'],
            model['line_count']
        )
        
        if indices:
            print(f"  Found {len(indices)} potential indices (showing first 20):")
            for typ, off, val in indices[:20]:
                print(f"    @0x{off:04X}: {typ} = {val}")
        else:
            print(f"  No obvious index patterns found")
        
        # Try to match feature_count
        print(f"\nTrying to parse as {model['feature_count']} records:")
        analyze_by_feature_count(
            model['data'],
            offsets['polygon_offset'],
            offsets['polygon_size'],
            model['feature_count']
        )
        
        # Hex dump first 128 bytes of polygon section
        print(f"\nHex dump (first 128 bytes of polygon section):")
        dump_size = min(128, offsets['polygon_size'])
        for i in range(0, dump_size, 16):
            hex_str = ' '.join(f'{model["data"][offsets["polygon_offset"]+i+j]:02X}' 
                               for j in range(min(16, dump_size - i)))
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' 
                               for b in model['data'][offsets["polygon_offset"]+i:offsets["polygon_offset"]+i+16])
            print(f"  {offsets['polygon_offset']+i:04X}: {hex_str:48s} {ascii_str}")
        
        print()

if __name__ == '__main__':
    main()
