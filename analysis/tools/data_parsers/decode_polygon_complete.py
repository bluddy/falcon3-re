#!/usr/bin/env python3
"""
Complete polygon section decoder - test all hypotheses.

Goals:
1. Parse Section 1: 0xFFFF-terminated vertex index lists
2. Identify Section 2: Test normal vector vs LOD coordinate hypothesis
3. Decode Section 3: Data at large_offset
"""

import struct
import math
from pathlib import Path
from collections import Counter

def load_model(filepath):
    """Load complete model with metadata."""
    data = Path(filepath).read_bytes()
    header = struct.unpack('<16H', data[0:32])
    
    vertex_count = header[1]
    line_count = header[2]
    feature_count = header[6]
    large_offset = header[4]
    
    vertex_offset = 0xA0
    line_offset = vertex_offset + (vertex_count * 6)
    polygon_offset = line_offset + (line_count * 4)
    
    # Load actual vertices for analysis
    vertices = []
    for i in range(vertex_count):
        pos = vertex_offset + (i * 6)
        x, y, z = struct.unpack('<3h', data[pos:pos+6])
        vertices.append((x, y, z))
    
    return {
        'filename': Path(filepath).name,
        'data': data,
        'vertices': vertices,
        'vertex_count': vertex_count,
        'line_count': line_count,
        'feature_count': feature_count,
        'large_offset': large_offset,
        'vertex_offset': vertex_offset,
        'line_offset': line_offset,
        'polygon_offset': polygon_offset,
    }

def parse_section1_polygons(model):
    """
    Parse Section 1: Vertex index lists terminated by 0xFFFF.
    
    Returns list of polygon records, each containing vertex indices.
    """
    data = model['data']
    offset = model['polygon_offset']
    vertex_count = model['vertex_count']
    
    polygons = []
    pos = offset
    max_bytes = 1000  # Don't parse beyond reasonable section 1 size
    
    while pos < offset + max_bytes and pos < len(data) - 1:
        indices = []
        start_pos = pos
        
        # Read indices until 0xFFFF terminator
        while pos < len(data) - 1:
            raw_idx = struct.unpack('<h', data[pos:pos+2])[0]
            pos += 2
            
            if raw_idx == -1:  # 0xFFFF terminator
                break
            
            # Resolve negative indices (wrap from end)
            if raw_idx < 0:
                resolved = vertex_count + raw_idx
            else:
                resolved = raw_idx
            
            # Validate
            valid = (0 <= resolved < vertex_count)
            indices.append({
                'raw': raw_idx,
                'resolved': resolved,
                'valid': valid
            })
            
            # Safety: max 20 indices per polygon
            if len(indices) > 20:
                break
        
        if indices:
            valid_count = sum(1 for idx in indices if idx['valid'])
            polygons.append({
                'polygon_id': len(polygons),
                'offset': start_pos,
                'size': pos - start_pos,
                'indices': indices,
                'valid_count': valid_count,
                'invalid_count': len(indices) - valid_count,
            })
        
        # Stop when we hit section 2 (values > vertex_count consistently)
        if pos < len(data) - 6:
            peek = struct.unpack('<3h', data[pos:pos+6])
            if all(abs(v) > 1000 for v in peek):  # Likely section 2
                break
    
    return polygons, pos  # Return end position (start of section 2)

def analyze_section2_normals(model, section2_start):
    """
    Test hypothesis: Section 2 contains surface normal vectors.
    
    Normals should be unit vectors (magnitude ~1.0) in fixed-point.
    """
    data = model['data']
    large_offset = model['large_offset']
    
    # Parse triplets from section2_start to large_offset
    normals = []
    pos = section2_start
    
    while pos < large_offset and pos < len(data) - 5:
        x, y, z = struct.unpack('<3h', data[pos:pos+6])
        pos += 6
        
        # Calculate magnitude (assuming fixed-point scale ~8192 = 1.0)
        # Try different scales
        for scale in [4096, 8192, 16384]:
            fx, fy, fz = x/scale, y/scale, z/scale
            mag = math.sqrt(fx*fx + fy*fy + fz*fz)
            
            if 0.8 < mag < 1.2:  # Close to unit length
                normals.append({
                    'offset': pos - 6,
                    'raw': (x, y, z),
                    'normalized': (fx, fy, fz),
                    'magnitude': mag,
                    'scale': scale,
                })
                break
        
        # Limit to first 50 for analysis
        if len(normals) >= 50:
            break
    
    # Calculate statistics
    if normals:
        mags = [n['magnitude'] for n in normals]
        avg_mag = sum(mags) / len(mags)
        mag_variance = sum((m - 1.0)**2 for m in mags) / len(mags)
        
        return {
            'hypothesis': 'surface_normals',
            'normals': normals,
            'count': len(normals),
            'avg_magnitude': avg_mag,
            'variance_from_unity': mag_variance,
            'likely': mag_variance < 0.05,  # Low variance = likely normals
        }
    
    return {'hypothesis': 'surface_normals', 'likely': False}

def analyze_section2_coordinates(model, section2_start, polygons):
    """
    Test hypothesis: Section 2 contains alternative coordinates (LOD, etc).
    
    Should have similar count to polygons, different scale from main vertices.
    """
    data = model['data']
    large_offset = model['large_offset']
    
    coords = []
    pos = section2_start
    
    while pos < large_offset and pos < len(data) - 5:
        x, y, z = struct.unpack('<3h', data[pos:pos+6])
        coords.append({
            'offset': pos,
            'coords': (x, y, z),
        })
        pos += 6
    
    # Get actual vertex coordinate ranges for comparison
    vertices = model['vertices']
    v_xs = [v[0] for v in vertices]
    v_ys = [v[1] for v in vertices]
    v_zs = [v[2] for v in vertices]
    
    c_xs = [c['coords'][0] for c in coords]
    c_ys = [c['coords'][1] for c in coords]
    c_zs = [c['coords'][2] for c in coords]
    
    return {
        'hypothesis': 'alternative_coordinates',
        'count': len(coords),
        'vertex_range': {
            'x': (min(v_xs), max(v_xs)),
            'y': (min(v_ys), max(v_ys)),
            'z': (min(v_zs), max(v_zs)),
        },
        'section2_range': {
            'x': (min(c_xs), max(c_xs)),
            'y': (min(c_ys), max(c_ys)),
            'z': (min(c_zs), max(c_zs)),
        },
        'ratio_to_polygons': len(coords) / len(polygons) if polygons else 0,
        'likely': len(coords) > len(polygons) * 2,  # Many more than polygons
    }

def decode_section3_metadata(model):
    """
    Decode Section 3: Data pointed to by large_offset.
    
    This section appears to have mixed data: indices, coordinates, flags.
    """
    data = model['data']
    large_offset = model['large_offset']
    vertex_count = model['vertex_count']
    
    # Parse first 100 bytes as various types
    section3_data = data[large_offset:large_offset + 100]
    
    # Try as int16 array
    words = struct.unpack(f'<{len(section3_data)//2}h', section3_data[:len(section3_data)//2*2])
    
    # Classify each word
    classified = []
    for i, word in enumerate(words):
        offset = large_offset + (i * 2)
        
        # Classify
        if word == -1:
            type_ = 'TERMINATOR'
        elif 0 <= word < vertex_count:
            type_ = 'VERTEX_INDEX'
        elif abs(word) < 200:
            type_ = 'SMALL_INT'
        elif 1000 < abs(word) < 10000:
            type_ = 'COORDINATE'
        else:
            type_ = 'UNKNOWN'
        
        classified.append({
            'offset': offset,
            'value': word,
            'type': type_,
        })
    
    # Find structure (look for 0xFFFF terminators)
    records = []
    current_record = []
    
    for item in classified:
        if item['type'] == 'TERMINATOR':
            if current_record:
                records.append(current_record)
                current_record = []
        else:
            current_record.append(item)
    
    if current_record:
        records.append(current_record)
    
    return {
        'offset': large_offset,
        'words': classified[:30],  # First 30 words
        'records': records,
        'record_count': len(records),
    }

def main():
    models = [
        'game/FALCOBJ.BIN',  # F-16
        'game/HORNOBJ.BIN',  # F/A-18
        'game/FULCOBJ.BIN',  # MiG-29
    ]
    
    for filepath in models:
        if not Path(filepath).exists():
            print(f"Skipping {filepath} (not found)")
            continue
        
        print("="*80)
        print(f"COMPLETE POLYGON ANALYSIS: {Path(filepath).name}")
        print("="*80)
        print()
        
        model = load_model(filepath)
        
        print(f"Model Statistics:")
        print(f"  Vertices: {model['vertex_count']}")
        print(f"  Lines: {model['line_count']}")
        print(f"  Feature count: {model['feature_count']}")
        print(f"  Polygon section start: 0x{model['polygon_offset']:04X}")
        print(f"  Large offset (Section 3): 0x{model['large_offset']:04X}")
        print()
        
        # === SECTION 1: POLYGONS ===
        print("--- SECTION 1: POLYGON VERTEX LISTS ---")
        print()
        
        polygons, section2_start = parse_section1_polygons(model)
        
        print(f"Found {len(polygons)} polygon records")
        print(f"Section 1 ends at: 0x{section2_start:04X}")
        print(f"Section 1 size: {section2_start - model['polygon_offset']} bytes")
        print()
        
        # Show first few polygons
        for poly in polygons[:10]:
            valid_pct = (poly['valid_count'] / len(poly['indices']) * 100) if poly['indices'] else 0
            print(f"Polygon {poly['polygon_id']:2d} @ 0x{poly['offset']:04X}: "
                  f"{len(poly['indices'])} indices, {poly['valid_count']} valid ({valid_pct:.0f}%)")
            
            # Show indices
            for i, idx in enumerate(poly['indices'][:8]):
                wrap = " (wrap)" if idx['raw'] < 0 else ""
                valid = "OK" if idx['valid'] else "XX"
                print(f"    [{i}] {valid} {idx['raw']:5d} -> V{idx['resolved']:3d}{wrap}")
            if len(poly['indices']) > 8:
                print(f"    ... +{len(poly['indices']) - 8} more")
        
        if len(polygons) > 10:
            print(f"  ... +{len(polygons) - 10} more polygons")
        print()
        
        # Polygon index count distribution
        index_counts = Counter([len(p['indices']) for p in polygons])
        print(f"Index count distribution (polygon types):")
        for count, freq in sorted(index_counts.items()):
            poly_type = {3: "triangles", 4: "quads", 5: "pentagons", 6: "hexagons"}.get(count, "")
            print(f"  {count} indices: {freq:3d} polygons {poly_type}")
        print()
        
        # === SECTION 2: HYPOTHESIS TESTING ===
        print("--- SECTION 2: HYPOTHESIS TESTING ---")
        print()
        
        # Test normal vector hypothesis
        normals_result = analyze_section2_normals(model, section2_start)
        print(f"Hypothesis: Surface Normals")
        print(f"  Tested: {normals_result['count']} triplets")
        if normals_result['likely']:
            print(f"  [YES] LIKELY - Average magnitude: {normals_result['avg_magnitude']:.3f}")
            print(f"  Variance from unity: {normals_result['variance_from_unity']:.4f}")
            print(f"  Sample normals:")
            for n in normals_result['normals'][:5]:
                print(f"    ({n['normalized'][0]:6.3f}, {n['normalized'][1]:6.3f}, {n['normalized'][2]:6.3f}) "
                      f"mag={n['magnitude']:.3f} scale={n['scale']}")
        else:
            print(f"  [NO] UNLIKELY - Not unit vectors")
        print()
        
        # Test coordinate hypothesis
        coords_result = analyze_section2_coordinates(model, section2_start, polygons)
        print(f"Hypothesis: Alternative Coordinates (LOD)")
        print(f"  Count: {coords_result['count']} coordinate triplets")
        print(f"  Vertex range: X={coords_result['vertex_range']['x']}, "
              f"Y={coords_result['vertex_range']['y']}, "
              f"Z={coords_result['vertex_range']['z']}")
        print(f"  Section2 range: X={coords_result['section2_range']['x']}, "
              f"Y={coords_result['section2_range']['y']}, "
              f"Z={coords_result['section2_range']['z']}")
        print(f"  Ratio to polygons: {coords_result['ratio_to_polygons']:.1f}:1")
        if coords_result['likely']:
            print(f"  ? POSSIBLE - Different range, many coordinates")
        else:
            print(f"  ? UNCERTAIN")
        print()
        
        # === SECTION 3: METADATA ===
        print("--- SECTION 3: METADATA AT large_offset ---")
        print()
        
        section3 = decode_section3_metadata(model)
        print(f"Located at: 0x{section3['offset']:04X}")
        print(f"Found {section3['record_count']} records (separated by 0xFFFF)")
        print()
        
        print(f"First 30 words (classified):")
        for word in section3['words']:
            print(f"  0x{word['offset']:04X}: {word['value']:6d} (0x{word['value'] & 0xFFFF:04X}) - {word['type']}")
        print()
        
        print(f"Record structure:")
        for i, record in enumerate(section3['records'][:5]):
            print(f"  Record {i}: {len(record)} values")
            types = Counter([item['type'] for item in record])
            for type_, count in types.items():
                print(f"    {type_}: {count}")
        print()
        
        print()

if __name__ == '__main__':
    main()
