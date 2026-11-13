#!/usr/bin/env python3
"""
Verify the relative-index hypothesis by decoding F-16 model completely.
Tests both interpretations: absolute-only vs signed-relative.
"""

import struct
import math
from pathlib import Path

def load_model(filepath):
    """Load model file and parse header."""
    data = Path(filepath).read_bytes()
    header = struct.unpack('<16H', data[0:32])
    
    return {
        'data': data,
        'file_size_minus_10': header[0],
        'vertex_count': header[1],
        'line_count': header[2],
        'unknown_06': header[3],
        'large_offset': header[4],
        'version': header[5],
        'feature_count': header[6],
    }

def load_vertices(model):
    """Load all vertices from model."""
    vertex_offset = 0xA0  # F-16 starts here
    vertex_count = model['vertex_count']
    data = model['data']
    
    vertices = []
    for i in range(vertex_count):
        offset = vertex_offset + (i * 6)
        x, y, z = struct.unpack('<hhh', data[offset:offset+6])
        vertices.append((x, y, z))
    
    return vertices

def edge_length(v1, v2):
    """Compute Euclidean distance between two vertices."""
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    dz = v2[2] - v1[2]
    return math.sqrt(dx*dx + dy*dy + dz*dz)

def decode_lines_absolute_only(model, vertices):
    """Decode lines assuming ALL indices are absolute."""
    line_offset = 0xA0 + (model['vertex_count'] * 6)
    line_count = model['line_count']
    vertex_count = model['vertex_count']
    data = model['data']
    
    edges = []
    errors = []
    
    for i in range(line_count):
        offset = line_offset + (i * 4)
        v1, v2 = struct.unpack('<HH', data[offset:offset+4])  # UNSIGNED
        
        # Check validity
        if v1 >= vertex_count or v2 >= vertex_count:
            errors.append((i, v1, v2, 'OUT_OF_RANGE'))
            continue
        
        # Valid edge
        length = edge_length(vertices[v1], vertices[v2])
        edges.append((i, v1, v2, length))
    
    return edges, errors

def decode_lines_signed_relative(model, vertices):
    """Decode lines using signed relative-index algorithm."""
    line_offset = 0xA0 + (model['vertex_count'] * 6)
    line_count = model['line_count']
    vertex_count = model['vertex_count']
    data = model['data']
    
    edges = []
    errors = []
    
    for i in range(line_count):
        offset = line_offset + (i * 4)
        v1_raw, v2_raw = struct.unpack('<hh', data[offset:offset+4])  # SIGNED
        
        # Decode indices
        # Hypothesis 1: negative = relative backward reference from current LINE
        # Hypothesis 2: negative = relative to current VERTEX being processed
        # Let's try: relative to the last-referenced vertex
        
        # For now, let's try: negative values reference vertices processed earlier
        # The "current position" might be a running vertex cursor, not line index
        
        # Simple interpretation: negative = absolute index (two's complement wrap)
        # Actually, let's try: negative is relative to vertex_count
        
        if v1_raw >= 0:
            v1 = v1_raw
        else:
            # Try interpretation: negative wraps from end
            # -1 = last vertex, -2 = second-to-last, etc
            v1 = vertex_count + v1_raw
        
        if v2_raw >= 0:
            v2 = v2_raw
        else:
            v2 = vertex_count + v2_raw
        
        # Check validity
        if v1 < 0 or v1 >= vertex_count or v2 < 0 or v2 >= vertex_count:
            errors.append((i, v1_raw, v2_raw, v1, v2, 'INVALID_AFTER_DECODE'))
            continue
        
        # Valid edge
        length = edge_length(vertices[v1], vertices[v2])
        edges.append((i, v1, v2, length, v1_raw, v2_raw))
    
    return edges, errors

def analyze_edge_lengths(edges):
    """Analyze distribution of edge lengths."""
    if not edges:
        return None
    
    lengths = [e[3] for e in edges]
    return {
        'count': len(lengths),
        'min': min(lengths),
        'max': max(lengths),
        'mean': sum(lengths) / len(lengths),
        'reasonable': sum(1 for L in lengths if 10 < L < 10000),
    }

def main():
    filepath = 'game/FALCOBJ.BIN'
    
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found")
        return
    
    print("="*80)
    print("RELATIVE-INDEX HYPOTHESIS VERIFICATION")
    print("="*80)
    print()
    
    # Load model
    model = load_model(filepath)
    print(f"Model: {Path(filepath).name}")
    print(f"  Vertices: {model['vertex_count']}")
    print(f"  Lines: {model['line_count']}")
    print(f"  Version: {model['version']}")
    print()
    
    # Load vertices
    vertices = load_vertices(model)
    print(f"Loaded {len(vertices)} vertices")
    print(f"  Sample V0: {vertices[0]}")
    print(f"  Sample V1: {vertices[1]}")
    print(f"  Sample V10: {vertices[10]}")
    print()
    
    # Test 1: Absolute-only interpretation
    print("-"*80)
    print("TEST 1: Absolute-Only Interpretation (all indices unsigned)")
    print("-"*80)
    edges_abs, errors_abs = decode_lines_absolute_only(model, vertices)
    stats_abs = analyze_edge_lengths(edges_abs)
    
    print(f"Results:")
    print(f"  Valid edges: {len(edges_abs)} / {model['line_count']} ({100*len(edges_abs)//model['line_count']}%)")
    print(f"  Errors: {len(errors_abs)} ({100*len(errors_abs)//model['line_count']}%)")
    
    if stats_abs:
        print(f"Edge length statistics:")
        print(f"  Min: {stats_abs['min']:.1f}")
        print(f"  Max: {stats_abs['max']:.1f}")
        print(f"  Mean: {stats_abs['mean']:.1f}")
        print(f"  Reasonable (10-10000): {stats_abs['reasonable']} / {stats_abs['count']}")
    
    if len(errors_abs) > 0:
        print(f"\nFirst 10 errors:")
        for i, v1, v2, reason in errors_abs[:10]:
            print(f"  Line {i}: v1={v1}, v2={v2} - {reason}")
    
    print()
    
    # Test 2: Signed relative interpretation
    print("-"*80)
    print("TEST 2: Signed Relative-Index Interpretation")
    print("-"*80)
    edges_rel, errors_rel = decode_lines_signed_relative(model, vertices)
    stats_rel = analyze_edge_lengths(edges_rel)
    
    print(f"Results:")
    print(f"  Valid edges: {len(edges_rel)} / {model['line_count']} ({100*len(edges_rel)//model['line_count']}%)")
    print(f"  Errors: {len(errors_rel)} ({100*len(errors_rel)//model['line_count']}%)")
    
    if stats_rel:
        print(f"Edge length statistics:")
        print(f"  Min: {stats_rel['min']:.1f}")
        print(f"  Max: {stats_rel['max']:.1f}")
        print(f"  Mean: {stats_rel['mean']:.1f}")
        print(f"  Reasonable (10-10000): {stats_rel['reasonable']} / {stats_rel['count']}")
    
    if len(errors_rel) > 0:
        print(f"\nErrors (should be zero if hypothesis correct):")
        for i, v1_raw, v2_raw, v1_dec, v2_dec, reason in errors_rel[:10]:
            print(f"  Line {i}: raw=({v1_raw}, {v2_raw}) -> decoded=({v1_dec}, {v2_dec}) - {reason}")
    
    print()
    
    # Sample decoded edges
    print("Sample decoded edges (first 20):")
    print("  #   | Raw Indices     | Decoded      | Length    | Notes")
    print("------+-----------------+--------------+-----------+------------------")
    for i, v1, v2, length, v1_raw, v2_raw in edges_rel[:20]:
        note = ""
        if v1_raw < 0:
            note += f"v1_rel "
        if v2_raw < 0:
            note += f"v2_rel "
        if not note:
            note = "absolute"
        
        print(f"{i:4d}  | ({v1_raw:5d}, {v2_raw:5d}) | V{v1:3d}->V{v2:3d} | {length:8.1f} | {note}")
    
    print()
    
    # Comparison
    print("="*80)
    print("COMPARISON & CONCLUSION")
    print("="*80)
    print()
    
    improvement = len(edges_rel) - len(edges_abs)
    print(f"Absolute-only: {len(edges_abs)} valid edges ({100*len(edges_abs)//model['line_count']}%)")
    print(f"Signed relative: {len(edges_rel)} valid edges ({100*len(edges_rel)//model['line_count']}%)")
    print(f"Improvement: +{improvement} edges (+{100*improvement//model['line_count']}%)")
    print()
    
    if len(errors_rel) == 0:
        print("SUCCESS - HYPOTHESIS CONFIRMED!")
        print("   All lines decode successfully with signed relative-index algorithm.")
        print("   KEY FINDING: Negative indices wrap from END of vertex array:")
        print("   -1 = last vertex, -2 = second-to-last, etc.")
    elif len(errors_rel) < len(errors_abs):
        print("WARNING - HYPOTHESIS PARTIALLY CONFIRMED")
        print(f"   Signed algorithm decodes {len(edges_rel)} lines vs {len(edges_abs)} absolute-only.")
        print(f"   Still {len(errors_rel)} errors remaining.")
    else:
        print("FAILED - HYPOTHESIS REJECTED")
        print("   Signed relative algorithm does not improve decoding.")
    
    print()
    
    # Edge length sanity check
    if stats_rel and stats_abs:
        print("Edge length sanity check:")
        print(f"  Absolute-only reasonable edges: {stats_abs['reasonable']} / {stats_abs['count']}")
        print(f"  Signed relative reasonable edges: {stats_rel['reasonable']} / {stats_rel['count']}")
        
        if stats_rel['reasonable'] > stats_abs['reasonable']:
            print("  SUCCESS: Signed relative produces more reasonable edge lengths")
        else:
            print("  WARNING: No improvement in edge length distribution")

if __name__ == '__main__':
    main()
