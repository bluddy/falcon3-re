#!/usr/bin/env python3
"""
Find drawing/graphics functions in Falcon 3.0 by analyzing call patterns.
Look for functions that are called frequently with coordinate-like parameters.
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_disassembly_calls(disasm_file: Path) -> dict:
    """Extract all function calls and their contexts."""
    calls = defaultdict(list)
    
    if not disasm_file.exists():
        return calls
    
    with open(disasm_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        # Look for call instructions
        call_match = re.search(r'call\s+(\w+|sub_[0-9A-Fa-f]+)', line, re.IGNORECASE)
        if not call_match:
            continue
        
        target = call_match.group(1)
        
        # Get context (previous 5 lines to see parameter setup)
        start = max(0, i - 5)
        context_lines = lines[start:i+1]
        context = ''.join(context_lines)
        
        # Look for push instructions (parameters)
        pushes = re.findall(r'push\s+(\w+)', context, re.IGNORECASE)
        
        # Look for mov to registers before call
        mov_pattern = re.findall(r'mov\s+(ax|bx|cx|dx|si|di),\s*(\w+)', context, re.IGNORECASE)
        
        calls[target].append({
            'line': i + 1,
            'context': context,
            'pushes': pushes,
            'registers': mov_pattern
        })
    
    return calls

def analyze_call_patterns(calls: dict) -> list:
    """Identify functions that might be graphics primitives based on call patterns."""
    candidates = []
    
    for func_name, call_list in calls.items():
        if len(call_list) < 3:  # Must be called multiple times
            continue
        
        # Count parameter pushes
        param_counts = [len(call['pushes']) for call in call_list]
        avg_params = sum(param_counts) / len(param_counts) if param_counts else 0
        
        # Look for coordinate-like patterns (numbers, small values)
        has_coords = False
        for call in call_list[:5]:  # Check first 5 calls
            context = call['context']
            # Look for small immediate values (coordinates)
            if re.search(r'(mov|push)\s+\w+,\s*([0-9]+|0x[0-9A-Fa-f]{1,3})\b', context):
                has_coords = True
                break
        
        # Graphics functions typically have 2-6 parameters
        if 2 <= avg_params <= 6 or has_coords:
            candidates.append({
                'name': func_name,
                'call_count': len(call_list),
                'avg_params': avg_params,
                'has_coords': has_coords,
                'sample_calls': call_list[:3]
            })
    
    # Sort by call count
    candidates.sort(key=lambda x: x['call_count'], reverse=True)
    return candidates

def main():
    base_dir = Path('C:/Users/ybarnoy/projects/falcon3')
    analysis_dir = base_dir / 'analysis'
    
    # Analyze R53 which has lots of menu/UI code
    disasm_file = analysis_dir / 'r53_main_disasm.txt'
    
    print("=" * 80)
    print("GRAPHICS FUNCTION CANDIDATE SEARCH")
    print("=" * 80)
    print(f"\nAnalyzing: {disasm_file.name}")
    print()
    
    if not disasm_file.exists():
        print(f"ERROR: {disasm_file} not found")
        return
    
    # Parse calls
    print("Parsing function calls...")
    calls = parse_disassembly_calls(disasm_file)
    print(f"Found {len(calls)} unique functions called")
    print()
    
    # Analyze patterns
    print("Analyzing call patterns...")
    candidates = analyze_call_patterns(calls)
    print(f"Found {len(candidates)} candidate graphics functions")
    print()
    
    # Display top 20 candidates
    print("=" * 80)
    print("TOP CANDIDATE FUNCTIONS")
    print("=" * 80)
    print()
    
    for i, candidate in enumerate(candidates[:20], 1):
        print(f"{i}. {candidate['name']}")
        print(f"   Calls: {candidate['call_count']}")
        print(f"   Avg params: {candidate['avg_params']:.1f}")
        print(f"   Has coordinate-like values: {candidate['has_coords']}")
        print()
        
        # Show one example call
        if candidate['sample_calls']:
            call = candidate['sample_calls'][0]
            print(f"   Example (line {call['line']}):")
            # Show last 3 lines of context
            context_lines = call['context'].strip().split('\n')[-3:]
            for line in context_lines:
                print(f"     {line.strip()}")
            print()
    
    # Special analysis: Look for functions with X,Y coordinate patterns
    print("=" * 80)
    print("FUNCTIONS WITH COORDINATE PAIR PATTERNS")
    print("=" * 80)
    print()
    
    for func_name, call_list in calls.items():
        # Look for pattern: push Y, push X (typical graphics API)
        coord_pattern_count = 0
        
        for call in call_list:
            # Check if we have exactly 2 or 4 consecutive pushes (x,y or x1,y1,x2,y2)
            pushes = call['pushes']
            if len(pushes) in [2, 4, 6]:
                coord_pattern_count += 1
        
        # If more than 50% of calls have coordinate pattern
        if len(call_list) >= 3 and coord_pattern_count / len(call_list) > 0.5:
            print(f"{func_name}")
            print(f"  Total calls: {len(call_list)}")
            print(f"  Coordinate pattern calls: {coord_pattern_count}")
            print(f"  Pattern ratio: {coord_pattern_count / len(call_list):.1%}")
            
            # Show example
            for call in call_list[:1]:
                print(f"  Example (line {call['line']}):")
                context_lines = call['context'].strip().split('\n')[-4:]
                for line in context_lines:
                    print(f"    {line.strip()}")
            print()

if __name__ == '__main__':
    main()
